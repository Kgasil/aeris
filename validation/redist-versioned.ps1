$ErrorActionPreference='Stop'
$e=Join-Path $PWD 'redist-evidence'
New-Item -ItemType Directory -Path $e | Out-Null
$r=[ordered]@{status='INCONCLUSIVE';scope='Official signed versioned redistributable layout only; no app build or installer publication';release_approved=$false}
try {
  $tmp=Join-Path $env:RUNNER_TEMP ('vc-redist-'+[guid]::NewGuid())
  New-Item -ItemType Directory -Path $tmp | Out-Null
  $url='https://aka.ms/vs/18/release/14.51.36247/VC_redist.x64.exe'
  $exe=Join-Path $tmp 'VC_redist.x64.exe'
  $r['url']=$url
  Invoke-WebRequest -Uri $url -OutFile $exe -TimeoutSec 180
  $sig=Get-AuthenticodeSignature -LiteralPath $exe
  $f=Get-Item -LiteralPath $exe
  $r['package']=[ordered]@{sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant();version=$f.VersionInfo.FileVersion;signature=[string]$sig.Status;signer=if($sig.SignerCertificate){$sig.SignerCertificate.Subject}else{$null}}
  if($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation' -or $f.VersionInfo.FileVersion -notmatch '^14\.51\.36247(?:\.0)?$'){throw 'Unexpected Microsoft package signature/version'}
  $layout=Join-Path $tmp 'layout'
  New-Item -ItemType Directory -Path $layout | Out-Null
  # Layout only: do not install the redistributable on the host.
  $p=Start-Process -FilePath $exe -ArgumentList @('/layout',('"'+$layout+'"'),'/quiet','/norestart',('/log'),('"'+(Join-Path $e 'layout.log')+'"')) -PassThru
  if(-not $p.WaitForExit(120000)){throw 'Layout timeout'}
  if($p.ExitCode -ne 0){throw "Layout failed: $($p.ExitCode)"}
  $msis=@(Get-ChildItem -LiteralPath $layout -Recurse -File -Filter 'vc_runtimeMinimum_x64.msi')
  if($msis.Count -ne 1){throw 'Exact minimum x64 MSI not found'}
  $msi=$msis[0]
  $mSig=Get-AuthenticodeSignature -LiteralPath $msi.FullName
  if($mSig.Status -ne 'Valid' -or $mSig.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation'){throw 'Unexpected MSI signature'}
  $r['minimum_msi']=[ordered]@{sha256=(Get-FileHash -LiteralPath $msi.FullName -Algorithm SHA256).Hash.ToLowerInvariant();signature=[string]$mSig.Status}
  $extract=Join-Path $tmp 'admin-layout'
  New-Item -ItemType Directory -Path $extract | Out-Null
  $p=Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\msiexec.exe') -ArgumentList @('/a',('"'+$msi.FullName+'"'),'/qn','/norestart',('TARGETDIR="'+$extract+'"')) -PassThru
  if(-not $p.WaitForExit(120000)){throw 'Administrative layout timeout'}
  if($p.ExitCode -ne 0){throw "Administrative layout failed: $($p.ExitCode)"}
  $py=Split-Path -Parent (Get-Command python.exe).Source
  $r['rows']=@(foreach($name in @('vcruntime140.dll','vcruntime140_1.dll')){
    $source=Join-Path $py $name
    $sha=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    $matches=@(Get-ChildItem -LiteralPath $extract -Recurse -File -Filter $name | ForEach-Object {
      $s=Get-AuthenticodeSignature -LiteralPath $_.FullName
      $h=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
      [pscustomobject]@{name=$_.Name;version=$_.VersionInfo.FileVersion;sha256=$h;signature=[string]$s.Status;exact_match=($h -ceq $sha -and $s.Status -eq 'Valid' -and $s.SignerCertificate.Subject -match 'O=Microsoft Corporation')}
    })
    [pscustomobject]@{name=$name;python_sha256=$sha;matches=$matches;exact_match_count=@($matches|Where-Object exact_match).Count}
  })
  if(@($r.rows|Where-Object {$_.exact_match_count -lt 1}).Count){throw 'Exact DLL match not established'}
  $r.status='EXACT_SOURCE_MATCH'
} catch {$r['error']=$_.Exception.Message;throw}
finally {$r|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $e 'versioned-redist.json') -Encoding utf8;Get-Content -LiteralPath (Join-Path $e 'versioned-redist.json')}
