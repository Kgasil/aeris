# Evidence only. Never disable protection, add exclusions, sign or publish.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Stage,[Parameter(Mandatory=$true)][string]$Evidence)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or $env:OS -ne 'Windows_NT') { throw 'Hosted Windows runner required' }
$stagePath=(Resolve-Path -LiteralPath $Stage).Path
$e=(Resolve-Path -LiteralPath $Evidence).Path
$bundle=Join-Path $stagePath 'dist\Aeris'
$exe=Join-Path $bundle 'Aeris.exe'
$setup=Join-Path $stagePath 'Aeris-1.1.0rc1-Windows-x64-Setup.exe'
$portable=Join-Path $stagePath 'Aeris-1.1.0rc1-Windows-x64-portable.zip'
$report=[ordered]@{commit=$env:GITHUB_SHA;utc=[DateTime]::UtcNow.ToString('o');scope='Hosted runner; evidence only, not certification';release_approved=$false}
function Save-Report { $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $e 'assurance.json') -Encoding utf8 }
try {
    $files=@(Get-ChildItem -LiteralPath $bundle -File -Recurse)
    if ($files.Count -lt 1 -or $files.Count -gt 1000) { throw 'Unexpected bundle inventory size' }
    $inventory=@(foreach ($f in $files) {
        if ($f.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected reparse point' }
        $entry=[ordered]@{path=[IO.Path]::GetRelativePath($bundle,$f.FullName);bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
        if ($f.Extension -in @('.exe','.dll','.pyd')) {
            $entry['file_version']=$f.VersionInfo.FileVersion
            $entry['authenticode']=(Get-AuthenticodeSignature -LiteralPath $f.FullName).Status.ToString()
        }
        [pscustomobject]$entry
    })
    $inventory | ConvertTo-Json -AsArray -Depth 5 | Set-Content -LiteralPath (Join-Path $e 'distributed-files.json') -Encoding utf8
    $notices=@($inventory | Where-Object { $_.path -like 'NOTICES\*' -or $_.path -eq 'PYTHON-LICENSE.txt' })
    if ($notices.Count -lt 13) { throw 'Incomplete collected notice inventory' }
    $notices | ConvertTo-Json -AsArray -Depth 5 | Set-Content -LiteralPath (Join-Path $e 'license-inventory.json') -Encoding utf8
    $report['inventory_files']=$files.Count
    $report['notice_files']=$notices.Count
    $report['installer_authenticode']=(Get-AuthenticodeSignature -LiteralPath $setup).Status.ToString()
    $report['license_status']='INVENTORY_ONLY_REVIEW_PENDING'
    $hashes=@{}
    foreach ($p in @($setup,$portable,$exe)) { $hashes[$p]=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
    $scan=[ordered]@{status='INCONCLUSIVE';scope='Fresh candidate bundle and packages only';runs=@()}
    try {
        $status=Get-MpComputerStatus -ErrorAction Stop
        $scan['antivirus_enabled']=[bool]$status.AntivirusEnabled
        $scan['engine_version']=$status.AMEngineVersion
        $scan['signature_version']=$status.AntivirusSignatureVersion
        $scan['signature_last_updated']=$status.AntivirusSignatureLastUpdated
        if (-not $status.AntivirusEnabled -or -not $status.AMServiceEnabled) { throw 'Defender inactive; no settings changed' }
        $platform=Join-Path $env:ProgramData 'Microsoft\Windows Defender\Platform'
        $cmd=$null
        if (Test-Path -LiteralPath $platform) {
            $cmd=Get-ChildItem -LiteralPath $platform -Directory | Sort-Object LastWriteTime -Descending | ForEach-Object { Join-Path $_.FullName 'MpCmdRun.exe' } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
        }
        if (-not $cmd) { $cmd=Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe' }
        if (-not (Test-Path -LiteralPath $cmd -PathType Leaf) -or (Get-AuthenticodeSignature -LiteralPath $cmd).Status -ne 'Valid') { throw 'Trusted Defender command unavailable' }
        $i=0
        foreach ($target in @($setup,$portable,$bundle)) {
            $i++
            $p=Start-Process -FilePath $cmd -ArgumentList @('-Scan','-ScanType','3','-File',('"' + $target + '"')) -RedirectStandardOutput (Join-Path $e "defender-$i.log") -RedirectStandardError (Join-Path $e "defender-$i-error.log") -PassThru
            if (-not $p.WaitForExit(180000)) { throw 'Defender scan timed out; no clearance' }
            $scan.runs+=@([pscustomobject]@{target=(Split-Path -Leaf $target);exit_code=$p.ExitCode})
            if ($p.ExitCode -ne 0) { throw 'Defender scan returned nonzero; review required' }
        }
        $detections=@(Get-MpThreatDetection -ErrorAction Stop | Where-Object { @($_.Resources | Where-Object { $_ -and $_.IndexOf($stagePath,[StringComparison]::OrdinalIgnoreCase) -ge 0 }).Count -gt 0 })
        $scan['matched_detection_count']=$detections.Count
        if ($detections.Count -gt 0) { $scan.status='DETECTIONS_FOUND' }
        else { $scan.status='COMPLETED_NO_MATCHED_DETECTIONS' }
    } catch { $scan['error']=$_.Exception.Message }
    $report['defender']=$scan
    foreach ($p in $hashes.Keys) {
        if (-not (Test-Path -LiteralPath $p -PathType Leaf) -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $hashes[$p]) { throw 'Package or executable changed during scan' }
    }
    if ($scan.status -eq 'DETECTIONS_FOUND') { throw 'Candidate detection requires review' }
    # Measure existing packaged smoke test, not end-user startup or AI latency.
    $measurements=@()
    foreach ($i in 1..3) {
        $timer=[Diagnostics.Stopwatch]::StartNew()
        $p=Start-Process -FilePath $exe -ArgumentList '--self-test-full' -WorkingDirectory $bundle -PassThru
        if (-not $p.WaitForExit(90000)) { $p.Kill(); throw 'Timed packaged smoke test timed out' }
        $timer.Stop()
        $measurements+=@([pscustomobject]@{round=$i;elapsed_ms=$timer.ElapsedMilliseconds;exit_code=$p.ExitCode})
        $report['packaged_smoke_measurements']=$measurements
        if ($p.ExitCode -ne 0) { throw 'Timed packaged smoke test failed' }
    }
    $report['status']='EVIDENCE_COLLECTED'
} catch { $report['status']='FAILED';$report['error']=$_.Exception.Message;throw }
finally { Save-Report }
