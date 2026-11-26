# Run only on a disposable GitHub-hosted Windows x64 runner.
# Tests a freshly built, unsigned candidate. Never publishes or retains binaries.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Stage,
    [Parameter(Mandatory=$true)][string]$Evidence,
    [Parameter(Mandatory=$true)][switch]$ConfirmDisposableRunner
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $ConfirmDisposableRunner -or $env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or $env:OS -ne 'Windows_NT' -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Disposable GitHub-hosted Windows x64 runner required' }
$stagePath = (Resolve-Path -LiteralPath $Stage).Path
$evidencePath = (Resolve-Path -LiteralPath $Evidence).Path
$version = '1.1.0rc1'
$setupName = "Aeris-$version-Windows-x64-Setup.exe"
$portableName = "Aeris-$version-Windows-x64-portable.zip"
$setup = Join-Path $stagePath $setupName
$portable = Join-Path $stagePath $portableName
$install = Join-Path $env:LOCALAPPDATA 'Programs\KGVision\Aeris'
$data = Join-Path $env:LOCALAPPDATA 'Aeris'
$exe = Join-Path $install 'Aeris.exe'
$result = [ordered]@{commit=$env:GITHUB_SHA; version=$version; environment=[Environment]::OSVersion.VersionString; scope='Hosted runner install, same-version reinstall, uninstall with synthetic marker; not clean client VM or real user data'; signed=$false; release_approved=$false; checks=[ordered]@{}}
function Save-Result { $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidencePath 'homologation.json') -Encoding utf8 }
function Invoke-Installer([string]$Path,[string]$Log,[string[]]$Extra=@()) {
    $arguments = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="' + $Log + '"')) + $Extra
    $p = Start-Process -FilePath $Path -ArgumentList $arguments -PassThru
    if (-not $p.WaitForExit(120000)) { $p.Kill(); throw 'Installer process timed out' }
    if ($p.ExitCode -ne 0) { throw "Installer process failed: $($p.ExitCode)" }
}
function Assert-Hash([string]$Path,[string]$Expected) {
    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Expected regular file' }
    if ($Expected -notmatch '^[0-9a-f]{64}$' -or (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Expected) { throw "Hash mismatch: $Path" }
}
try {
    if ((Test-Path -LiteralPath $install) -or (Test-Path -LiteralPath $data)) { throw 'Existing installation or data found: refusing to test' }
    $inventory = @(Get-Content -LiteralPath (Join-Path $evidencePath 'artifact-inventory.json') -Raw | ConvertFrom-Json)
    if ($inventory.Count -ne 2) { throw 'Expected both candidate packages' }
    $sums = @(Get-Content -LiteralPath (Join-Path $stagePath 'SHA256SUMS.txt'))
    foreach ($name in @($setupName,$portableName)) {
        $entry = @($inventory | Where-Object { $_.name -ceq $name })
        if ($entry.Count -ne 1 -or $sums -cnotcontains ($entry[0].sha256 + '  ' + $name)) { throw 'Missing or inconsistent build hash' }
        $path = Join-Path $stagePath $name
        Assert-Hash $path $entry[0].sha256
        if ((Get-Item -LiteralPath $path).Length -ne $entry[0].bytes) { throw 'Size mismatch' }
    }
    $result.checks.package_hashes = 'PASS'
    $exeHash = (Get-Content -LiteralPath (Join-Path $stagePath 'AERIS-EXE-SHA256.txt') -Raw).Trim()
    $setupArgs = @('/SP-',('/DIR="' + $install + '"'),'/TASKS=""')
    Invoke-Installer $setup (Join-Path $evidencePath 'install.log') $setupArgs
    Assert-Hash $exe $exeHash
    $result.checks.install = 'PASS'
    & (Join-Path $PSScriptRoot 'validate-windows.ps1') -AerisExe $exe -ExpectedExeSha256 $exeHash -Mode Installed -ConfirmTestVM | Set-Content -LiteralPath (Join-Path $evidencePath 'installed-self-test.json')
    $result.checks.installed_self_test = 'PASS'
    # Verify every distributed file against the independently recorded portable manifest.
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($portable)
    try {
        $entry = $archive.GetEntry('Aeris/BUNDLE-MANIFEST.json')
        if ($null -eq $entry -or $entry.Length -gt 2097152) { throw 'Invalid manifest' }
        $reader = [IO.StreamReader]::new($entry.Open())
        try { $manifest = $reader.ReadToEnd() | ConvertFrom-Json -AsHashtable } finally { $reader.Dispose() }
        $count=0
        foreach ($name in $manifest.Keys) {
            if ($name -cnotmatch '^Aeris/[A-Za-z0-9_./ -]+$' -or ($name -split '/') -contains '..') { throw 'Unexpected manifest path' }
            $file = Join-Path $install ($name.Substring(6).Replace('/','\'))
            Assert-Hash $file $manifest[$name]
            $count++
        }
        $result.checks.installed_manifest_files = $count
    } finally { $archive.Dispose() }
    if (Test-Path -LiteralPath $data) { throw 'Unexpected data created before synthetic test' }
    New-Item -ItemType Directory -Path $data | Out-Null
    $marker = Join-Path $data 'homologation-synthetic-marker.txt'
    Set-Content -LiteralPath $marker -Value 'Aeris RC1 synthetic fixture, not personal data' -Encoding ascii
    $markerHash = (Get-FileHash -LiteralPath $marker -Algorithm SHA256).Hash.ToLowerInvariant()
    Invoke-Installer $setup (Join-Path $evidencePath 'reinstall.log') $setupArgs
    Assert-Hash $marker $markerHash
    Assert-Hash $exe $exeHash
    $result.checks.same_version_reinstall = 'PASS'
    $uninstallers = @(Get-ChildItem -LiteralPath $install -File -Filter 'unins*.exe')
    if ($uninstallers.Count -ne 1 -or ($uninstallers[0].Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Expected exactly one regular uninstaller' }
    Invoke-Installer $uninstallers[0].FullName (Join-Path $evidencePath 'uninstall.log')
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    while ((Test-Path -LiteralPath $exe) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 250 }
    if (Test-Path -LiteralPath $exe) { throw 'Executable remains after uninstall' }
    Assert-Hash $marker $markerHash
    $result.checks.uninstall_preserves_synthetic_data = 'PASS'
    $result.status = 'PASS'
} catch {
    $result.status = 'FAILED'
    $result.error = $_.Exception.Message
    throw
} finally { Save-Result }
