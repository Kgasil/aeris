# CI-only: upgrade an independently verified RC3 to a newly built RC4 and test rollback.
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$OldSetup,
  [Parameter(Mandatory)][string]$OldSetupSha256,
  [Parameter(Mandatory)][string]$OldExeSha256,
  [Parameter(Mandatory)][string]$NewSetup,
  [Parameter(Mandatory)][string]$NewSetupSha256,
  [Parameter(Mandatory)][string]$NewExeSha256,
  [Parameter(Mandatory)][string]$Python,
  [Parameter(Mandatory)][string]$SourceDesktop,
  [Parameter(Mandatory)][string]$Validator,
  [Parameter(Mandatory)][string]$EvidenceDirectory
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') { throw 'Disposable Windows CI only' }
if ($OldExeSha256 -eq $NewExeSha256 -or $OldSetupSha256 -eq $NewSetupSha256) { throw 'Distinct packages required' }
$dest = Join-Path $env:LOCALAPPDATA 'Programs\KGVision\Aeris'
$data = Join-Path $env:LOCALAPPDATA 'Aeris'
if ((Test-Path -LiteralPath $dest) -or (Test-Path -LiteralPath $data)) { throw 'Expected fresh synthetic profile' }
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'Expected fresh evidence directory' }
New-Item -ItemType Directory -Path $EvidenceDirectory | Out-Null
$evidence = (Resolve-Path -LiteralPath $EvidenceDirectory).Path
$installed = Join-Path $dest 'Aeris.exe'
function Check-Hash([string]$File,[string]$Expected) {
  if ($Expected -notmatch '^[0-9a-fA-F]{64}$' -or (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash -ne $Expected) { throw 'Hash mismatch' }
}
function Install-Version([string]$Setup,[string]$ExpectedHash,[string]$Label) {
  Check-Hash $Setup $ExpectedHash
  $log = Join-Path $evidence ($Label + '.log')
  $p = Start-Process -FilePath $Setup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CURRENTUSER',('/LOG="' + $log + '"')) -PassThru
  if (-not $p.WaitForExit(120000)) { $p.Kill(); throw 'Setup timed out' }
  if ($p.ExitCode -ne 0) { throw "Setup exit code $($p.ExitCode)" }
}
function Confirm-Version([string]$Version,[string]$ExpectedHash,[string]$Label) {
  Check-Hash $installed $ExpectedHash
  $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{76A8CB97-8F34-42A2-9B8D-462CAB196D85}_is1'
  $entry = Get-ItemProperty -LiteralPath $key
  if ($entry.DisplayVersion -ne $Version) { throw "Unexpected installed version: $($entry.DisplayVersion)" }
  & $Validator -AerisExe $installed -ExpectedExeSha256 $ExpectedHash -Mode Installed -ConfirmTestVM | Set-Content -LiteralPath (Join-Path $evidence ($Label + '-validation.json')) -Encoding utf8
}
function Uninstall-Version([string]$Label) {
  $uninstallers = @(Get-ChildItem -LiteralPath $dest -Filter 'unins*.exe' -File)
  if ($uninstallers.Count -ne 1) { throw 'Expected one uninstaller' }
  $log = Join-Path $evidence ($Label + '.log')
  $p = Start-Process -FilePath $uninstallers[0].FullName -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="' + $log + '"')) -PassThru
  if (-not $p.WaitForExit(120000)) { $p.Kill(); throw 'Uninstall timed out' }
  if ($p.ExitCode -ne 0 -or (Test-Path -LiteralPath $installed)) { throw 'Uninstall failed' }
}
function Profile-Manifest([string]$Root) {
  $map = [ordered]@{}
  foreach ($file in @(Get-ChildItem -LiteralPath $Root -File -Force -Recurse | Sort-Object FullName)) {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected reparse point' }
    $map[$file.FullName.Substring($Root.Length+1)] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  }
  return ($map | ConvertTo-Json -Compress)
}
function Check-Profile([string]$Expected,[string]$Label) {
  $actual = Profile-Manifest $data
  if ($actual -cne $Expected) { throw "Synthetic profile changed: $Label" }
  Set-Content -LiteralPath (Join-Path $evidence ($Label + '-profile.json')) -Value $actual -Encoding utf8
  Push-Location $SourceDesktop
  try {
    & $Python -c "from aeris.settings import Settings; s=Settings(); assert s.timeline_enabled and not s.warning"
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic settings unreadable' }
  } finally { Pop-Location }
}
Check-Hash $OldSetup $OldSetupSha256
Check-Hash $NewSetup $NewSetupSha256
Install-Version $OldSetup $OldSetupSha256 'rc3-install'
Confirm-Version '1.0.0rc3' $OldExeSha256 'rc3'
# Settings are written by the actual application storage implementation, not a hand-made schema.
Push-Location $SourceDesktop
try {
  & $Python -c "from aeris.settings import Settings; s=Settings(); s.set_module('Timeline',True); assert Settings().timeline_enabled"
  if ($LASTEXITCODE -ne 0) { throw 'Synthetic settings creation failed' }
} finally { Pop-Location }
Set-Content -LiteralPath (Join-Path $data 'ci-upgrade-marker.txt') -Value 'Aeris synthetic upgrade and recovery fixture' -Encoding ascii
$baseline = Profile-Manifest $data
$backup = Join-Path $env:RUNNER_TEMP ('aeris-synthetic-backup-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath $data -Destination $backup -Recurse
if ((Profile-Manifest $backup) -cne $baseline) { throw 'Backup verification failed' }
Check-Profile $baseline 'rc3-before'
# Verify that a rejected hash never launches the installer or modifies the current profile.
$rejected = $false
try { Install-Version $NewSetup ('0'*64) 'must-not-start' } catch { $rejected = $_.Exception.Message -eq 'Hash mismatch' }
if (-not $rejected -or (Test-Path -LiteralPath (Join-Path $evidence 'must-not-start.log'))) { throw 'Invalid hash was not rejected before execution' }
Confirm-Version '1.0.0rc3' $OldExeSha256 'rc3-after-rejected-hash'
Check-Profile $baseline 'rc3-after-rejected-hash'
Install-Version $NewSetup $NewSetupSha256 'rc4-upgrade'
Confirm-Version '1.0.0rc4' $NewExeSha256 'rc4'
Check-Profile $baseline 'rc4-upgrade'
# Test whether Inno leaves superseded runtime files behind after an in-place upgrade.
$internal = Join-Path $dest '_internal'
$leftovers = @(Get-ChildItem -LiteralPath $internal -File | Where-Object { $_.Name -match '^(api-ms-win-(core|crt)-.*|ucrtbase)\.dll$' } | ForEach-Object { [pscustomobject]@{name=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
[pscustomobject]@{scope='In-place RC3 to RC4 on disposable CI';leftover_count=$leftovers.Count;files=$leftovers;status=if($leftovers.Count -eq 0){'PASS'}else{'REQUIRES_CLEAN_REINSTALL'};release_approved=$false} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $evidence 'obsolete-runtime-files.json') -Encoding utf8
Uninstall-Version 'rc4-uninstall'
Check-Profile $baseline 'rc4-uninstall'
# Supported clean path: let the previous uninstaller remove owned files; never delete user data.
Install-Version $NewSetup $NewSetupSha256 'rc4-clean-reinstall'
Confirm-Version '1.0.0rc4' $NewExeSha256 'rc4-clean-reinstall'
Check-Profile $baseline 'rc4-clean-reinstall'
if (@(Get-ChildItem -LiteralPath (Join-Path $dest '_internal') -File | Where-Object { $_.Name -match '^(api-ms-win-(core|crt)-.*|ucrtbase)\.dll$' }).Count -ne 0) { throw 'Obsolete system copies remain after clean reinstall' }
Uninstall-Version 'rc4-clean-uninstall'
Check-Profile $baseline 'rc4-clean-uninstall'
# Controlled rollback: uninstall RC4 then reinstall exact RC3; never silently downgrade production.
Install-Version $OldSetup $OldSetupSha256 'rc3-rollback'
Confirm-Version '1.0.0rc3' $OldExeSha256 'rc3-rollback'
Check-Profile $baseline 'rc3-rollback'
# Restore a copy to a separate test directory, never overwrite the live profile.
$restore = Join-Path $env:RUNNER_TEMP ('aeris-synthetic-restore-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath $backup -Destination $restore -Recurse
if ((Profile-Manifest $restore) -cne $baseline) { throw 'Backup restoration mismatch' }
Push-Location $SourceDesktop
try {
  & $Python -c "from aeris.settings import Settings; import sys; s=Settings(sys.argv[1]); assert s.timeline_enabled and not s.warning" (Join-Path $restore 'settings.json')
  if ($LASTEXITCODE -ne 0) { throw 'Restored synthetic settings unreadable' }
} finally { Pop-Location }
Uninstall-Version 'rc3-final-uninstall'
Check-Profile $baseline 'rc3-final-uninstall'
[pscustomobject]@{scope='Server 2022 CI, synthetic settings/marker; no production rollback or DPAPI claim';old_version='1.0.0rc3';new_version='1.0.0rc4';old_setup_sha256=$OldSetupSha256;new_setup_sha256=$NewSetupSha256;old_exe_sha256=$OldExeSha256;new_exe_sha256=$NewExeSha256;upgrade='PASS';obsolete_runtime_files_remaining=$leftovers.Count;clean_reinstall='PASS';settings_preserved='PASS';rejected_hash='PASS';uninstall_preservation='PASS';rollback='PASS';backup_restore_copy='PASS';interrupted_install='NOT_TESTED';client_windows='NOT_TESTED';release_approved=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence 'upgrade-validation.json') -Encoding utf8
