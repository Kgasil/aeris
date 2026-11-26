# Scan an independently downloaded, hash-verified Windows candidate on a disposable VM.
# Does not launch Aeris, alter Defender configuration, add exclusions or publish files.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$SetupPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$SetupSha256,
    [Parameter(Mandatory)][string]$PortablePath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$PortableSha256,
    [Parameter(Mandatory)][string]$EvidenceDirectory
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows required' }
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'Choose a new evidence directory' }
$setup = (Get-Item -LiteralPath $SetupPath).FullName
$portable = (Get-Item -LiteralPath $PortablePath).FullName
if ((Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash -ne $SetupSha256 -or (Get-FileHash -LiteralPath $portable -Algorithm SHA256).Hash -ne $PortableSha256) { throw 'Artifact hash mismatch' }
New-Item -ItemType Directory -Path $EvidenceDirectory | Out-Null
$evidence = (Get-Item -LiteralPath $EvidenceDirectory).FullName
$report = [ordered]@{
    setup_sha256 = $SetupSha256.ToLowerInvariant()
    portable_sha256 = $PortableSha256.ToLowerInvariant()
    utc = [DateTime]::UtcNow.ToString('o')
    status = 'NOT_TESTED'
    release_approved = $false
}
try {
    $status = Get-MpComputerStatus
    $status | Select-Object AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureVersion,AntivirusSignatureLastUpdated,AMProductVersion,AMEngineVersion | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'defender-status.json') -Encoding utf8
    if (-not $status.AntivirusEnabled -or -not $status.RealTimeProtectionEnabled) { throw 'Active Defender protection required' }
    if (-not $status.AntivirusSignatureLastUpdated -or $status.AntivirusSignatureLastUpdated -lt (Get-Date).AddDays(-1)) { throw 'Definitions older than 24 hours; update Defender normally and retry' }
    $platform = Join-Path $env:ProgramData 'Microsoft\Windows Defender\Platform'
    $cmd = Get-ChildItem -LiteralPath $platform -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | ForEach-Object { Join-Path $_.FullName 'MpCmdRun.exe' } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (-not $cmd) { $cmd = Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe' }
    if (-not (Test-Path -LiteralPath $cmd -PathType Leaf)) { throw 'Defender command-line scanner not available' }
    if ((Get-AuthenticodeSignature -LiteralPath $cmd).Status -ne 'Valid') { throw 'Cannot verify scanner signature' }
    $started = Get-Date
    # Scan the installer and archive directly; no executable launch or bypass.
    foreach ($target in @(@{name='setup';path=$setup},@{name='portable';path=$portable})) {
        $log = Join-Path $evidence ($target.name + '-scan.log')
        & $cmd -Scan -ScanType 3 -File $target.path 2>&1 | Out-File -LiteralPath $log -Encoding utf8
        $code = $LASTEXITCODE
        $report[$target.name + '_exit_code'] = $code
        if ($code -ne 0) { throw "Scanner returned $code for $($target.name)" }
    }
    # Code 0 can include remediated detections. Preserve events and verify exact bytes again.
    $detections = @(Get-MpThreatDetection | Where-Object { $_.InitialDetectionTime -ge $started.AddMinutes(-2) })
    ConvertTo-Json -InputObject $detections -Depth 6 | Set-Content -LiteralPath (Join-Path $evidence 'recent-detections.json') -Encoding utf8
    if ($detections.Count -gt 0) { throw 'Recent detection found; review evidence and block release' }
    if ((Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash -ne $SetupSha256 -or (Get-FileHash -LiteralPath $portable -Algorithm SHA256).Hash -ne $PortableSha256) { throw 'Artifact changed or was removed during scan' }
    $report.status = 'ARCHIVE_SCAN_COMPLETED_REVIEW_REQUIRED'
    $report.remaining = 'Review scan logs, exclusions, and separately scan verified extracted bundle contents. No release approval.'
} catch {
    $report.status = 'BLOCKED_OR_INCOMPLETE'
    $report.error = $_.Exception.Message
    throw
} finally {
    $report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidence 'scan-status.json') -Encoding utf8
}
