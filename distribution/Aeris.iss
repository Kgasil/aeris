; Inno Setup 6.3+ / Windows 10 and 11 x64. Preview, not code-signed.
; Overlay for the verified Fix 1 source archive. Keep AppId, paths and data policy.
#ifndef AppVersion
  #error AppVersion must be supplied by build.ps1
#endif
#ifndef BundleDir
  #error BundleDir must be supplied by build.ps1
#endif
[Setup]
AppId={{76A8CB97-8F34-42A2-9B8D-462CAB196D85}
AppName=Project Aeris
AppVersion={#AppVersion}
AppPublisher=K&G Vision
AppPublisherURL=https://kgasil.github.io/aeris/
DefaultDirName={localappdata}\Programs\KGVision\Aeris
DefaultGroupName=Project Aeris
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0
AppMutex=Local\KGVision.Aeris.Desktop
CloseApplications=no
RestartApplications=no
UninstallDisplayIcon={app}\Aeris.exe
SetupIconFile=aeris.ico
OutputBaseFilename=Aeris-{#AppVersion}-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
InfoBeforeFile=PREVIEW.txt
LicenseFile=TERMS-REVIEW.txt
ShowLanguageDialog=auto
DisableWelcomePage=yes
DisableReadyPage=yes
UsePreviousTasks=yes
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[CustomMessages]
brazilianportuguese.LaunchAeris=Abrir o Project Aeris
english.LaunchAeris=Open Project Aeris
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"
[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Project Aeris"; Filename: "{app}\Aeris.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Project Aeris"; Filename: "{app}\Aeris.exe"; WorkingDir: "{app}"; Tasks: desktopicon
[Run]
Filename: "{app}\Aeris.exe"; Description: "{cm:LaunchAeris}"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent unchecked runasoriginaluser
[Code]
function InitializeSetup(): Boolean;
begin
  { Silent deployment requires explicit acceptance of this revision. }
  Result := not WizardSilent or (ExpandConstant('{param:ACCEPTTERMS|}') = 'RC1-1.1-TERMS1');
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  { Preserve the preview disclosure; the tasks page is the final confirmation. }
  if CurPageID = wpSelectTasks then
    WizardForm.NextButton.Caption := SetupMessage(msgButtonInstall)
  else if CurPageID = wpFinished then
    WizardForm.NextButton.Caption := SetupMessage(msgButtonFinish)
  else if CurPageID = wpReady then
    WizardForm.NextButton.Caption := SetupMessage(msgButtonInstall)
  else
    WizardForm.NextButton.Caption := SetupMessage(msgButtonNext);
end;
{ No autorun, updater, file associations, forced restart or user-data deletion. }
