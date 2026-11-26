# Measure exact verified portable RC5 in a disposable Windows CI runner.
# No personal files, inference, microphone, or external service.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$AerisExe,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ExpectedSha256,
    [Parameter(Mandatory)][string]$EvidencePath
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') { throw 'Disposable Windows CI only' }
if (Test-Path -LiteralPath $EvidencePath) { throw 'Refusing to overwrite evidence' }
$exe = (Get-Item -LiteralPath $AerisExe).FullName
if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -ne $ExpectedSha256) { throw 'Executable hash mismatch' }
if (Get-Process -Name Aeris -ErrorAction SilentlyContinue) { throw 'Unexpected existing Aeris process' }
$profile = Join-Path $env:RUNNER_TEMP ('aeris-perf-profile-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $profile | Out-Null
$original = $env:LOCALAPPDATA
$rows = @()
try {
    $env:LOCALAPPDATA = $profile
    for ($i=1; $i -le 3; $i++) {
        $clock = [Diagnostics.Stopwatch]::StartNew()
        $p = Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -PassThru
        try {
            do {
                Start-Sleep -Milliseconds 100
                $p.Refresh()
                if ($p.HasExited) { throw 'Aeris exited before window appeared' }
                if ($clock.Elapsed.TotalSeconds -gt 30) { throw 'Window not ready within 30 seconds' }
            } until ($p.MainWindowHandle -ne 0 -and $p.Responding)
            $startup = $clock.Elapsed.TotalSeconds
            Start-Sleep -Seconds 2
            $p.Refresh()
            $cpuBefore = $p.TotalProcessorTime.TotalSeconds
            $idle = [Diagnostics.Stopwatch]::StartNew()
            $rss = @()
            for ($j=0; $j -lt 5; $j++) {
                Start-Sleep -Seconds 1
                $p.Refresh()
                if ($p.HasExited -or -not $p.Responding) { throw 'Aeris not responsive while idle' }
                $rss += $p.WorkingSet64
            }
            $cpu = 100 * ($p.TotalProcessorTime.TotalSeconds - $cpuBefore) / $idle.Elapsed.TotalSeconds
            $memory = ($rss | Measure-Object -Maximum).Maximum
            $closing = [Diagnostics.Stopwatch]::StartNew()
            if (-not $p.CloseMainWindow() -or -not $p.WaitForExit(10000)) { throw 'Normal window close failed' }
            if ($p.ExitCode -ne 0) { throw "Aeris exited with code $($p.ExitCode)" }
            $shutdown = $closing.Elapsed.TotalSeconds
            $rows += [pscustomobject]@{
                trial=$i; startup_seconds=[Math]::Round($startup,3)
                idle_cpu_percent_one_core=[Math]::Round($cpu,3)
                peak_sampled_working_set_bytes=[long]$memory
                shutdown_seconds=[Math]::Round($shutdown,3)
                budget_met=($startup -le 10 -and $cpu -le 5 -and $memory -le 200MB -and $shutdown -le 5)
            }
        } finally {
            if (-not $p.HasExited) { $p.Kill(); $p.WaitForExit(10000) | Out-Null }
            $p.Dispose()
        }
    }
} finally { $env:LOCALAPPDATA = $original }
$os=Get-CimInstance Win32_OperatingSystem
$machine=Get-CimInstance Win32_ComputerSystem
$result=[ordered]@{
    scope='Exact portable RC5 on Windows Server 2022; fresh process launches, not cold OS-cache starts; window handle/responding proxy, not full interactive readiness'
    exe_sha256=$ExpectedSha256.ToLowerInvariant()
    os=$os.Caption; build=$os.BuildNumber
    logical_processors=$machine.NumberOfLogicalProcessors; ram_bytes=$machine.TotalPhysicalMemory
    limits=@{startup_seconds=10;idle_cpu_percent_one_core=5;peak_sampled_working_set_bytes=200MB;shutdown_seconds=5}
    samples=$rows
    status=if (@($rows | Where-Object {-not $_.budget_met}).Count -eq 0) {'PASS'} else {'FAIL'}
    client_windows='NOT_TESTED'; release_approved=$false
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $EvidencePath -Encoding utf8
if ($result.status -ne 'PASS') { throw 'One or more trials exceeded provisional CI budget' }
