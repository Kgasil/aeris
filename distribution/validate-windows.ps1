# Run only on a clean Windows x64 test VM with a trusted, locally built Aeris bundle.
# Does not install/uninstall software or modify execution policy, personal data or antivirus settings.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$AerisExe,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Fa-f0-9]{64}$')][string]$ExpectedExeSha256,
    [Parameter(Mandatory=$true)][ValidateSet('Portable','Installed')][string]$Mode,
    [Parameter(Mandatory=$true)][switch]$ConfirmTestVM
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $ConfirmTestVM) { throw 'Use a disposable test VM with fictitious data.' }
if ($env:OS -ne 'Windows_NT' -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Windows x64 required.' }
$exe = Get-Item -LiteralPath $AerisExe
if ($exe.PSIsContainer -or $exe.Name -ne 'Aeris.exe' -or ($exe.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Expected regular Aeris.exe.' }
$hash = (Get-FileHash -LiteralPath $exe.FullName -Algorithm SHA256).Hash
if ($hash -ne $ExpectedExeSha256) { throw 'Executable hash mismatch.' }
# The expected hash must originate from the trusted build, not from this same untrusted copy.
# The hash covers the EXE only: verify the complete portable archive separately before extraction.
$runtime = Join-Path $exe.DirectoryName '_internal\python314.dll'
if (-not (Test-Path -LiteralPath $runtime -PathType Leaf)) { throw 'Bundled Python runtime missing.' }
$catalog = Join-Path $exe.DirectoryName '_internal\aeris\catalog.json'
if (-not (Test-Path -LiteralPath $catalog -PathType Leaf)) { throw 'Bundled catalog missing.' }
$process = Start-Process -FilePath $exe.FullName -WorkingDirectory $exe.DirectoryName -ArgumentList '--self-test-full' -PassThru
if (-not $process.WaitForExit(90000)) { $process.Kill(); throw 'Full packaged UI self-test timed out.' }
if ($process.ExitCode -ne 0) { throw "Full packaged UI self-test failed: $($process.ExitCode)" }
[pscustomobject]@{
    mode = $Mode
    utc = [DateTime]::UtcNow.ToString('o')
    windows = [Environment]::OSVersion.VersionString
    architecture = $env:PROCESSOR_ARCHITECTURE
    exe_sha256 = $hash.ToLowerInvariant()
    self_test_full = 'PASS'
    authenticode = (Get-AuthenticodeSignature -LiteralPath $exe.FullName).Status.ToString()
    scope = 'Catalog and window construction only; not installation, DPAPI roundtrip, audio, AI or performance validation.'
} | ConvertTo-Json
