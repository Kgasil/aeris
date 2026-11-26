# Read-only scanner on a disposable hosted runner. No protection changes or binary uploads.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Stage,[Parameter(Mandatory=$true)][string]$Evidence)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or $env:OS -ne 'Windows_NT') { throw 'Hosted Windows runner required' }
$stagePath=(Resolve-Path -LiteralPath $Stage).Path
$e=(Resolve-Path -LiteralPath $Evidence).Path
$bundle=Join-Path $stagePath 'dist\Aeris'
$setup=Join-Path $stagePath 'Aeris-1.1.0rc1-Windows-x64-Setup.exe'
$portable=Join-Path $stagePath 'Aeris-1.1.0rc1-Windows-x64-portable.zip'
$report=[ordered]@{commit=$env:GITHUB_SHA;utc=[DateTime]::UtcNow.ToString('o');status='INCONCLUSIVE';release_approved=$false;scanner_version='1.5.5';scanner_archive_sha256='90169f5e551010bfbd0208b50d9b2fa8988ef396cccbd46b0cc8cae03e22a4a4';targets=@();scope='Exact candidate installer, portable archive and build bundle; not certification'}
function Save-Report { $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $e 'clamav-assurance.json') -Encoding utf8 }
function Get-Inventory {
    $files=@(Get-Item -LiteralPath $setup,$portable)+@(Get-ChildItem -LiteralPath $bundle -File -Recurse)
    if ($files.Count -lt 3 -or $files.Count -gt 1000) { throw 'Unexpected candidate inventory' }
    $entries=[ordered]@{}
    foreach ($f in ($files | Sort-Object FullName)) {
        if ($f.PSIsContainer -or ($f.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unexpected candidate file' }
        $entries[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    return $entries
}
function Invoke-Recorded([string]$Program,[string[]]$Arguments,[string]$Log) {
    $PSNativeCommandUseErrorActionPreference=$false
    & $Program @Arguments 2>&1 | ForEach-Object { "$_" } | Set-Content -LiteralPath $Log -Encoding utf8
    return $LASTEXITCODE
}
$before=$null
try {
    $before=Get-Inventory
    $expected=Get-Content -LiteralPath (Join-Path $e 'artifact-inventory.json') -Raw | ConvertFrom-Json
    foreach ($target in @($setup,$portable)) {
        $entry=@($expected | Where-Object { $_.name -ceq (Split-Path -Leaf $target) })
        if ($entry.Count -ne 1 -or $before[$target] -cne $entry[0].sha256) { $report.status='INTEGRITY_FAILURE';throw 'Package hash differs from build inventory' }
    }
    $report['candidate_package_hashes']=[ordered]@{setup=$before[$setup];portable=$before[$portable]}
    $temp=Join-Path $env:RUNNER_TEMP ('clamav-aeris-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temp | Out-Null
    $zip=Join-Path $temp 'clamav.zip'
    $url='https://github.com/Cisco-Talos/clamav/releases/download/clamav-1.5.5/clamav-1.5.5.win.x64.zip'
    Invoke-WebRequest -Uri $url -OutFile $zip -TimeoutSec 300
    if ((Get-Item -LiteralPath $zip).Length -ne 225800047 -or (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -cne $report.scanner_archive_sha256) { throw 'Official scanner archive digest/length mismatch' }
    $report['scanner_archive_verified']=$true
    Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $temp 'engine')
    $scanners=@(Get-ChildItem -LiteralPath (Join-Path $temp 'engine') -Recurse -File -Filter clamscan.exe)
    if ($scanners.Count -ne 1) { throw 'Expected one scanner executable' }
    $engine=$scanners[0].DirectoryName
    $scan=$scanners[0].FullName
    $fresh=Join-Path $engine 'freshclam.exe'
    $sig=Join-Path $engine 'sigtool.exe'
    $db=Join-Path $temp 'database'
    New-Item -ItemType Directory -Path $db | Out-Null
    $conf=Join-Path $temp 'freshclam.conf'
    @(('DatabaseDirectory "'+$db+'"'),'DatabaseMirror database.clamav.net','Checks 1') | Set-Content -LiteralPath $conf -Encoding ascii
    if ((Invoke-Recorded $fresh @("--config-file=$conf",'--stdout') (Join-Path $e 'clamav-freshclam.log')) -ne 0) { throw 'Signature update failed; scan not approved' }
    $daily=@(Get-ChildItem -LiteralPath $db -File | Where-Object { $_.Name -in @('daily.cvd','daily.cld') })
    if ($daily.Count -ne 1) { throw 'Daily signature database missing or ambiguous' }
    $infoLog=Join-Path $e 'clamav-daily-info.txt'
    if ((Invoke-Recorded $sig @('--info',$daily[0].FullName) $infoLog) -ne 0) { throw 'Signature inspection failed' }
    $info=Get-Content -LiteralPath $infoLog -Raw
    if ($info -notmatch '(?m)^Verification OK\.?\s*$' -or $info -notmatch '(?m)^Build time:\s*(.+)$') { throw 'Signature verification or timestamp missing' }
    $raw=$Matches[1].Trim() -replace '([+-]\d{2})(\d{2})$','$1:$2'
    $date=[DateTimeOffset]::ParseExact($raw,'dd MMM yyyy HH:mm zzz',[Globalization.CultureInfo]::InvariantCulture)
    $age=([DateTimeOffset]::UtcNow-$date).TotalSeconds
    $report['definition_build_utc']=$date.ToUniversalTime().ToString('o')
    $report['definition_age_seconds']=[math]::Round($age)
    if ($age -lt 0 -or $age -gt 86400) { throw 'Definitions not within 24 hours; scan blocked' }
    $report['definitions_fresh']=$true
    if ((Invoke-Recorded $scan @("--database=$db",'--version') (Join-Path $e 'clamav-version.txt')) -ne 0) { throw 'Scanner version check failed' }
    $i=0
    foreach ($target in @($setup,$portable,$bundle)) {
        $i++
        $log=Join-Path $e "clamav-scan-$i.log"
        $exit=Invoke-Recorded $scan @("--database=$db",'--recursive=yes','--scan-archive=yes','--alert-exceeds-max=yes','--max-filesize=100M','--max-scansize=400M','--max-files=20000','--max-recursion=30',$target) $log
        $out=Get-Content -LiteralPath $log -Raw
        $result='INCONCLUSIVE'
        if ($exit -eq 1 -or $out -match '(?m)\sFOUND\s*$') { $result='DETECTION_OR_LIMIT_ALERT' }
        elseif ($exit -eq 0 -and $out -match '(?m)^Infected files:\s*0\s*$' -and $out -match '(?m)^Scanned files:\s*[1-9]\d*\s*$' -and $out -notmatch '(?im)\b(?:ERROR|WARNING|skipped|excluded)\b') { $result='COMPLETED_NO_THREATS_REPORTED' }
        $report.targets+=@([pscustomobject]@{target=(Split-Path -Leaf $target);exit_code=$exit;outcome=$result})
        if ($result -eq 'DETECTION_OR_LIMIT_ALERT') { $report.status='REVIEW_REQUIRED';throw 'Detection or scanner limit alert; review required' }
    }
    if ($report.targets.Count -eq 3 -and @($report.targets | Where-Object { $_.outcome -ne 'COMPLETED_NO_THREATS_REPORTED' }).Count -eq 0) { $report.status='COMPLETED_NO_THREATS_REPORTED' }
} catch {
    $report['error']=$_.Exception.Message
    if ($report.status -in @('REVIEW_REQUIRED','INTEGRITY_FAILURE')) { throw }
} finally {
    try {
        if ($null -ne $before) {
            $after=Get-Inventory
            if (($before | ConvertTo-Json -Compress) -cne ($after | ConvertTo-Json -Compress)) { $report.status='INTEGRITY_FAILURE';throw 'Candidate changed during scan' }
            $report['post_scan_integrity']='PASS'
        }
    } finally { Save-Report }
}
