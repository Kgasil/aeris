# Read-only origin comparison. A byte match is not legal authorization.
param([Parameter(Mandatory)][string]$Bundle,[Parameter(Mandatory)][string]$EvidencePath)
$ErrorActionPreference='Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') { throw 'Disposable CI only' }
$base = (Resolve-Path -LiteralPath $Bundle).Path
$pf = [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
$sdk = Join-Path $pf 'Windows Kits\10\Redist'
$vswhere = Join-Path $pf 'Microsoft Visual Studio\Installer\vswhere.exe'
$roots = @()
if (Test-Path -LiteralPath $sdk) {
    $roots += @(Get-ChildItem -LiteralPath $sdk -Directory -Recurse -Filter x64 | Where-Object { $_.FullName -match '\\ucrt\\DLLs\\x64$' })
}
if (Test-Path -LiteralPath $vswhere) {
    $installations = @(& $vswhere -all -products '*' -property installationPath)
    foreach ($installation in $installations) {
        $redist = Join-Path $installation 'VC\Redist\MSVC'
        if (Test-Path -LiteralPath $redist) {
            $roots += @(Get-ChildItem -LiteralPath $redist -Directory -Recurse | Where-Object { $_.FullName -match '\\x64\\Microsoft\.VC\d+\.CRT$' })
        }
    }
}
$files = @(Get-ChildItem -LiteralPath (Join-Path $base '_internal') -File | Where-Object { $_.Name -match '^(api-ms-win-.*|ucrtbase|vcruntime140(?:_1)?)\.dll$' })
if ($files.Count -ne 46) { throw 'Unexpected Microsoft component inventory' }
$rows = @()
foreach ($file in $files) {
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $matches = @()
    $candidates = @()
    foreach ($root in $roots) {
        $other = Join-Path $root.FullName $file.Name
        if (Test-Path -LiteralPath $other -PathType Leaf) {
            $otherHash = (Get-FileHash -LiteralPath $other -Algorithm SHA256).Hash.ToLowerInvariant()
            $candidates += [pscustomobject]@{path=$other;sha256=$otherHash}
            if ($hash -eq $otherHash) { $matches += $other }
        }
    }
    $sig = Get-AuthenticodeSignature -LiteralPath $file.FullName
    $rows += [pscustomobject]@{name=$file.Name;sha256=$hash;signature=$sig.Status.ToString();matches=$matches;candidates=$candidates;status=if($matches.Count -gt 0){'EXACT_REDIST_MATCH'}else{'UNRESOLVED'}}
}
$report = [ordered]@{scope='Exact RC3 bytes compared only to locally installed x64 SDK/VC REDIST directories; not a proof of rights or original build provenance';roots=@($roots | ForEach-Object {$_.FullName});components=$rows.Count;exact_matches=@($rows | Where-Object {$_.status -eq 'EXACT_REDIST_MATCH'}).Count;unresolved=@($rows | Where-Object {$_.status -eq 'UNRESOLVED'}).Count;files=$rows;redistribution_approved=$false;release_approved=$false}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $EvidencePath -Encoding utf8
