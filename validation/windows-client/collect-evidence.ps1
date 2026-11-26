# Read-only checkpoints for the interactive client Windows validation.
# Writes only a new JSON evidence file. Never installs, launches, changes settings or bypasses protection.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Before','Installed','Reinstalled','Uninstalled')][string]$Phase,
    [Parameter(Mandatory)][string]$SetupPath,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ExpectedSetupSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-fA-F]{64}$')][string]$ExpectedExeSha256,
    [Parameter(Mandatory)][string]$OutputFile,
    [ValidateSet('Selected','NotSelected')][string]$DesktopShortcut = 'Selected'
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows required' }
if (Test-Path -LiteralPath $OutputFile) { throw 'Refusing to overwrite evidence' }
$os = Get-CimInstance Win32_OperatingSystem
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$adminSid = 'S-1-5-32-544'
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) -or @($identity.Groups | Where-Object { $_.Value -eq $adminSid }).Count -gt 0
$build = [int]$os.BuildNumber
$family = if ($os.ProductType -eq 1 -and $build -ge 22000) { 'Windows 11' } elseif ($os.ProductType -eq 1 -and $build -ge 10240 -and $build -lt 22000) { 'Windows 10' } else { 'Not client Windows' }
$hash = (Get-FileHash -LiteralPath $SetupPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne $ExpectedSetupSha256.ToLowerInvariant()) { throw 'Setup hash mismatch' }
$dest = Join-Path $env:LOCALAPPDATA 'Programs\KGVision\Aeris'
$exe = Join-Path $dest 'Aeris.exe'
$start = Join-Path ([Environment]::GetFolderPath('Programs')) 'Project Aeris.lnk'
$desktop = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'Project Aeris.lnk'
$pythonCommands = @(Get-Command -Name python.exe,python3.exe,py.exe -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch '\\Microsoft\\WindowsApps\\' } | Select-Object -ExpandProperty Name -Unique)
$pythonRegistry = @('HKCU:\Software\Python\PythonCore','HKLM:\Software\Python\PythonCore','HKLM:\Software\WOW6432Node\Python\PythonCore') | Where-Object { Test-Path -LiteralPath $_ }
$marker = Join-Path $env:LOCALAPPDATA 'Aeris\ci-client-synthetic-preserve.txt'
$actualExe = if (Test-Path -LiteralPath $exe -PathType Leaf) { (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
$markerHash = if (Test-Path -LiteralPath $marker -PathType Leaf) { (Get-FileHash -LiteralPath $marker -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
$startExists = Test-Path -LiteralPath $start -PathType Leaf
$desktopExists = Test-Path -LiteralPath $desktop -PathType Leaf
$targetsMatch = $true
if ($startExists -or $desktopExists) {
    $shell = New-Object -ComObject WScript.Shell
    foreach ($link in @($start,$desktop)) {
        if (Test-Path -LiteralPath $link -PathType Leaf) {
            if ($shell.CreateShortcut($link).TargetPath -ne $exe) { $targetsMatch = $false }
        }
    }
}
$protection = $null
try {
    $protection = Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureVersion,AntivirusSignatureLastUpdated
} catch { Write-Warning 'Defender status unavailable; manual review required.' }
$baseline = $family -ne 'Not client Windows' -and [Environment]::Is64BitOperatingSystem -and -not $isAdmin -and $pythonCommands.Count -eq 0 -and @($pythonRegistry).Count -eq 0
$checks = [ordered]@{
    client_x64_nonadmin_no_detected_python = $baseline
    setup_sha256_matches = $true
    shortcut_targets_match = $targetsMatch
}
if ($Phase -eq 'Before') {
    $checks.clean_install_path = -not (Test-Path -LiteralPath $dest)
    $checks.clean_shortcuts = -not ($startExists -or $desktopExists)
    $checks.clean_synthetic_marker = -not $markerHash
} elseif ($Phase -in @('Installed','Reinstalled')) {
    $checks.installed_exe_matches = $actualExe -eq $ExpectedExeSha256.ToLowerInvariant()
    $checks.start_menu_present = $startExists
    $checks.desktop_choice_matches = $desktopExists -eq ($DesktopShortcut -eq 'Selected')
    if ($Phase -eq 'Reinstalled') { $checks.synthetic_marker_present = [bool]$markerHash }
} else {
    $checks.app_removed = -not (Test-Path -LiteralPath $dest)
    $checks.shortcuts_removed = -not ($startExists -or $desktopExists)
    $checks.synthetic_marker_present = [bool]$markerHash
}
$report = [ordered]@{
    schema = 1
    utc = [DateTime]::UtcNow.ToString('o')
    phase = $Phase
    os_family = $family
    os_build = $build
    os_version = $os.Version
    os_caption = $os.Caption
    architecture = $os.OSArchitecture
    admin_membership_detected = $isAdmin
    python_commands_detected = $pythonCommands
    python_registry_detected = @($pythonRegistry).Count
    python_detection_scope = 'Common launchers and registry only; confirm clean snapshot manually.'
    setup_sha256 = $hash
    expected_exe_sha256 = $ExpectedExeSha256.ToLowerInvariant()
    installed_exe_sha256 = $actualExe
    synthetic_marker_sha256 = $markerHash
    desktop_choice = $DesktopShortcut
    defender_status = $protection
    observed_checks = $checks
    status = if (@($checks.Values | Where-Object { $_ -ne $true }).Count -eq 0) { 'OBSERVATIONS_MATCH_REVIEW_REQUIRED' } else { 'BLOCKED_OR_MISMATCH' }
    manual_interactive_validation = 'NOT_TESTED_BY_SCRIPT'
    release_approved = $false
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputFile -Encoding utf8
if ($report.status -ne 'OBSERVATIONS_MATCH_REVIEW_REQUIRED') { throw 'One or more observations failed; review JSON evidence.' }
