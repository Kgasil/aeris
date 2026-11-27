# Run on Windows x64, with CPython 3.14 x64 and Inno Setup 6.3+ installed.
[CmdletBinding()]
param([string]$Iscc = '', [switch]$PortableOnly)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT' -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Windows x64 required.' }
$root = Split-Path -Parent $PSScriptRoot
$desktop = Join-Path $root 'desktop'
# Resolve and validate Inno Setup before any build work; portable needs no ISCC.
if (-not $PortableOnly) {
    if (-not $Iscc) {
        $candidates = @()
        if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe') }
        if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe') }
        $Iscc = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    }
    if (-not $Iscc -or -not (Test-Path -LiteralPath $Iscc -PathType Leaf)) { throw 'Inno Setup ISCC.exe not found; use -Iscc or -PortableOnly.' }
    $Iscc = (Resolve-Path -LiteralPath $Iscc).Path
    if ((Get-AuthenticodeSignature -LiteralPath $Iscc).Status -ne 'Valid') { throw 'Inno Setup compiler signature not valid; review source.' }
    $innoLicense = Join-Path (Split-Path -Parent $Iscc) 'LICENSE.TXT'
    if (-not (Test-Path -LiteralPath $innoLicense -PathType Leaf)) { throw 'Inno Setup license missing.' }
}
$out = Join-Path $PSScriptRoot 'out'
# Unique staging path: no recursive deletion of a user-selected directory.
$stage = Join-Path $out ([guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage -Force | Out-Null
function Invoke-Checked([string]$File, [string[]]$Arguments) {
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Failed: $File (exit $LASTEXITCODE)" }
}
Invoke-Checked 'py' @('-3.14-64','-c','import sys, tkinter; assert sys.version_info[:2] == (3,14) and sys.maxsize > 2**32')
$venv = Join-Path $stage 'venv'
Invoke-Checked 'py' @('-3.14-64','-m','venv',$venv)
$python = Join-Path $venv 'Scripts\python.exe'
Invoke-Checked $python @('-m','pip','--disable-pip-version-check','install','-r',(Join-Path $PSScriptRoot 'requirements-build.txt'))
Push-Location $desktop
try {
    Invoke-Checked $python @('-m','compileall','-q','aeris','tests','main.py')
    Invoke-Checked $python @('-m','unittest','discover','-v')
    Invoke-Checked $python @('main.py','--self-test-full')
    $version = & $python -c 'from aeris import __version__; print(__version__)'
    if ($LASTEXITCODE -ne 0 -or $version -notmatch '^\d+\.\d+\.\d+(a|rc)\d+$') { throw 'Invalid build version' }
    $dist = Join-Path $stage 'dist'
    Invoke-Checked $python @('-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--noupx','--name','Aeris','--icon',(Join-Path $PSScriptRoot 'aeris.ico'),'--add-data',((Join-Path $desktop 'aeris/catalog.json') + ':aeris'),'--add-data',((Join-Path $PSScriptRoot 'aeris.ico') + ':aeris'),'--exclude-module','argostranslate','--distpath',$dist,'--workpath',(Join-Path $stage 'work'),'--specpath',$stage,'main.py')
    $bundle = Join-Path $dist 'Aeris'
    $internal = Join-Path $bundle '_internal'
    $osFiles = @(Get-ChildItem -LiteralPath $internal -File | Where-Object { $_.Name -match '^(api-ms-win-(core|crt)-.*|ucrtbase)\.dll$' })
    if ($osFiles.Count -ne 44) { throw 'Expected 44 Windows system runtime copies; review inventory' }
    $removed = @()
    foreach ($file in $osFiles) {
        if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected reparse point' }
        if ((Get-AuthenticodeSignature -LiteralPath $file.FullName).Status -ne 'Valid') { throw 'Unexpected system DLL signature' }
        $removed += [pscustomobject]@{name=$file.Name;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
        Remove-Item -LiteralPath $file.FullName -Force
    }
    $basePython = & $python -c 'import sys; print(sys.base_prefix)'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot identify Python runtime source' }
    $vc = @()
    foreach ($name in @('VCRUNTIME140.dll','VCRUNTIME140_1.dll')) {
        $bundled = Join-Path $internal $name
        $source = Join-Path $basePython $name
        if (-not (Test-Path -LiteralPath $bundled -PathType Leaf)) { throw 'Missing VC runtime' }
        $sha = (Get-FileHash -LiteralPath $bundled -Algorithm SHA256).Hash.ToLowerInvariant()
        $sourceHash = if(Test-Path -LiteralPath $source -PathType Leaf){(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null}
        $vc += [pscustomobject]@{name=$name;sha256=$sha;python_source_sha256=$sourceHash;exact_python_match=($sha -eq $sourceHash)}
    }
    [pscustomobject]@{scope='Generated staging only; experimental reliance on OS UCRT; not a redistribution approval';removed=$removed;remaining_vcruntime=$vc;release_approved=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stage 'runtime-reduction.json') -Encoding utf8
    $exe = Join-Path $bundle 'Aeris.exe'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'Missing executable' }
    $process = Start-Process -FilePath $exe -ArgumentList '--self-test-full' -PassThru
    if (-not $process.WaitForExit(90000)) { $process.Kill(); throw 'Packaged self-test timed out' }
    if ($process.ExitCode -ne 0) { throw "Packaged self-test failed: $($process.ExitCode)" }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'PREVIEW.txt') -Destination $bundle
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'TERMS-REVIEW.txt') -Destination $bundle
    # Collect third-party notices supplied with the Python environment; build-only dependencies are not shipped wholesale.
    $base = & $python -c 'import sys; print(sys.base_prefix)'
    if ($LASTEXITCODE -ne 0) { throw 'Unable to identify Python installation' }
    $license = Join-Path $base 'LICENSE.txt'
    if (-not (Test-Path -LiteralPath $license)) { throw 'Python license missing' }
    Copy-Item -LiteralPath $license -Destination (Join-Path $bundle 'PYTHON-LICENSE.txt')
    $notices = Join-Path $bundle 'NOTICES'
    New-Item -ItemType Directory -Path $notices | Out-Null
    $i = 0
    Get-ChildItem -LiteralPath (Join-Path $base 'tcl') -Recurse -File | Where-Object { $_.Name -match '^(license|license\.terms|license\.txt)$' } | ForEach-Object {
        $i++; Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $notices "tcl-tk-$i-$($_.Name)")
    }
    # Retain build tool versions and supplied package notices for review.
    Invoke-Checked $python @((Join-Path $PSScriptRoot 'collect-notices.py'),$notices)
    $reviewNotices = Join-Path $PSScriptRoot 'third-party-notices'
    $expectedNotices = @('OpenSSL-3.5.9.txt','bzip2-1.0.8.txt','libffi-3.4.4.txt','XZ-5.2.5.txt','XZ-5.2.5-COPYING.LGPLv2.1.txt','Zstandard-1.5.7.txt','zlib-ng-2.2.4.txt','zlib-1.3.2.txt','mpdecimal-4.0.0.txt','libexpat.txt','libtommath-tcl-9.0.4.txt','Unicode-16.0.0.txt')
    foreach ($name in $expectedNotices) {
        $notice = Join-Path $reviewNotices $name
        if (-not (Test-Path -LiteralPath $notice -PathType Leaf)) { throw "Missing reviewed upstream notice: $name" }
        Copy-Item -LiteralPath $notice -Destination $notices
    }
    if (-not $PortableOnly) {
        Copy-Item -LiteralPath $innoLicense -Destination (Join-Path $notices 'InnoSetup-LICENSE.txt')
    }
    & $python -m pip freeze --all | Set-Content -LiteralPath (Join-Path $stage 'build-dependencies.txt') -Encoding ascii
    if ($LASTEXITCODE -ne 0) { throw 'Failed to record build dependencies' }
    $zip = Join-Path $stage "Aeris-$version-Windows-x64-portable.zip"
    Invoke-Checked $python @('-m','aeris.release_check','pack',$bundle,$zip)
    $artifacts = @($zip)
    if (-not $PortableOnly) {
        Invoke-Checked $Iscc @("/DAppVersion=$version","/DBundleDir=$bundle","/O$stage",(Join-Path $PSScriptRoot 'Aeris.iss'))
        $setup = Join-Path $stage "Aeris-$version-Windows-x64-Setup.exe"
        if (-not (Test-Path -LiteralPath $setup -PathType Leaf)) { throw 'Missing installer' }
        $artifacts += $setup
    }
    $hashes = foreach ($path in $artifacts) { $h = Get-FileHash -LiteralPath $path -Algorithm SHA256; "$($h.Hash.ToLowerInvariant())  $(Split-Path -Leaf $path)" }
    $hashes | Set-Content -LiteralPath (Join-Path $stage 'SHA256SUMS.txt') -Encoding ascii
    $verifyArgs = @('-m','aeris.release_check','verify',$stage,$version)
    if ($PortableOnly) { $verifyArgs += '--portable-only' }
    Invoke-Checked $python $verifyArgs
    (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() | Set-Content -LiteralPath (Join-Path $stage 'AERIS-EXE-SHA256.txt') -Encoding ascii
    $buildInfo = [pscustomobject]@{version=$version; python_version=(& $python --version); portable_only=[bool]$PortableOnly; signed=$false; release_approved=$false}
    $buildInfo | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stage 'build-info.json') -Encoding utf8
    Write-Host "Build outputs (unsigned preview): $stage"
} finally { Pop-Location }
