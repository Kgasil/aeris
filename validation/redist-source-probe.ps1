param([Parameter(Mandatory=$true)][string]$Output,[string]$PythonRoot=(Split-Path -Parent (Get-Command python.exe).Source))
$ErrorActionPreference='Stop'
# Read-only metadata, no files copied or uploaded. Do not search System32 or debug_nonredist.
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$roots=@()
if(Test-Path -LiteralPath $vswhere){
  $instances=@((& $vswhere -all -products '*' -format json | Out-String | ConvertFrom-Json))
  foreach($i in $instances){
    if($i.isPrerelease -or -not $i.isComplete){continue}
    $root=Join-Path $i.installationPath 'VC\Redist\MSVC'
    if(Test-Path -LiteralPath $root){$roots+=@([pscustomobject]@{root=$root;edition=$i.productId;version=$i.installationVersion})}
  }
}
function Entry($p){
  $f=Get-Item -LiteralPath $p
  if($f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Unexpected reparse point'}
  $sig=Get-AuthenticodeSignature -LiteralPath $f.FullName
  [ordered]@{name=$f.Name;version=$f.VersionInfo.FileVersion;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant();signature=[string]$sig.Status;signer=if($sig.SignerCertificate){$sig.SignerCertificate.Subject}else{$null}}
}
$rows=@(foreach($name in @('vcruntime140.dll','vcruntime140_1.dll')){
  $source=Join-Path $PythonRoot $name
  if(-not(Test-Path -LiteralPath $source -PathType Leaf)){throw "Python runtime DLL missing: $name"}
  $p=Entry $source
  $redist=@(foreach($r in $roots){
    Get-ChildItem -LiteralPath $r.root -Recurse -File -Filter $name | Where-Object {
      $_.FullName -match '\\x64\\Microsoft\.VC\d+\.CRT\\' -and $_.FullName -notmatch 'debug_nonredist|preview'
    } | ForEach-Object {
      $v=Entry $_.FullName
      [pscustomobject]@{edition=$r.edition;vs_version=$r.version;relative_path=$_.FullName.Substring($r.root.Length).TrimStart('\');file=$v;exact_match=($v.sha256 -ceq $p.sha256 -and $v.signature -eq 'Valid' -and $p.signature -eq 'Valid')}
    }
  })
  [pscustomobject]@{python=$p;redist=$redist;exact_match_count=@($redist|Where-Object exact_match).Count}
})
[ordered]@{schema='kgvision.redist-probe.v1';python_version=(& python --version);scope='Hosted runner source files only, no candidate and no legal approval';rows=$rows;owner_entitlement='REVIEW_REQUIRED';release_approved=$false}|ConvertTo-Json -Depth 9|Set-Content -LiteralPath $Output -Encoding utf8
Get-Content -LiteralPath $Output
