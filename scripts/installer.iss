#define AppName "YOLO Media Organizer"
#define Artifact "YOLO-media-organizer-" + AppVersion + "-windows-amd64"

[Setup]
AppId=electblake.YOLO-media-organizer
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=electblake
DefaultDirName={localappdata}\Programs\YOLO-media-organizer
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
OutputDir=..\dist
OutputBaseFilename={#Artifact}-Setup
UninstallDisplayIcon={app}\runtime\venv\Scripts\pythonw.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
SetupLogging=yes

[Types]
Name: "cpu"; Description: "CPU"
Name: "gpu"; Description: "NVIDIA GPU (CUDA 13.0; requires a compatible NVIDIA driver)"

[Components]
Name: "cpu"; Description: "CPU dependencies"; Types: cpu; Flags: exclusive
Name: "gpu"; Description: "NVIDIA CUDA 13.0 dependencies"; Types: gpu; Flags: exclusive

[Files]
Source: "..\build\bootstrap\uv\uv.exe"; DestDir: "{app}\tools"; Hash: "b1645e948603c12dd741987d0c072471195e18dd299b42334477ceac694f0af8"; Flags: ignoreversion
Source: "..\build\bootstrap\LICENSE-*"; DestDir: "{app}\tools\licenses"; Flags: ignoreversion
Source: "..\app\*.py"; DestDir: "{app}\app\app"; Flags: ignoreversion
Source: "..\pyproject.toml"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\uv.lock"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "install-runtime.cmd"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\runtime\venv\Scripts\pythonw.exe"; Parameters: "-I -m app"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\runtime\venv\Scripts\pythonw.exe"; Parameters: "-I -m app"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\runtime\venv\Scripts\pythonw.exe"; Parameters: "-I -m app"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent; Check: DependenciesInstalled

[UninstallDelete]
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\app\yolo_media_organizer.egg-info"
Type: filesandordirs; Name: "{app}\app\build"

[Code]
var
  DependencyExitCode: Integer;
  DependencyLog: TNewMemo;

procedure InitializeWizard;
begin
  WizardForm.SelectComponentsLabel.Caption :=
    'Choose CPU or NVIDIA GPU. Setup downloads Python and the selected dependencies. Internet access is required.';
  DependencyLog := TNewMemo.Create(WizardForm);
  DependencyLog.Parent := WizardForm.InstallingPage;
  DependencyLog.SetBounds(0, ScaleY(100), WizardForm.InstallingPage.Width,
    WizardForm.InstallingPage.Height - ScaleY(100));
  DependencyLog.ReadOnly := True;
  DependencyLog.ScrollBars := ssVertical;
end;

procedure DependencyOutput(const S: String; const Error, FirstLine: Boolean);
begin
  Log(S);
  DependencyLog.Lines.Add(S);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Backend: String;
begin
  if CurStep = ssPostInstall then begin
    Backend := WizardSelectedComponents(False);
    WizardForm.StatusLabel.Caption := 'Downloading and installing Python and ' + Backend + ' dependencies...';
    ExecAndLogOutput(ExpandConstant('{cmd}'),
      '/D /C ""' + ExpandConstant('{app}\install-runtime.cmd') + '" ' + Backend + '"',
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, DependencyExitCode, @DependencyOutput);
    Log('Dependency setup exit code: ' + IntToStr(DependencyExitCode));
  end;
end;

function DependenciesInstalled: Boolean;
begin
  Result := DependencyExitCode = 0;
end;

function GetCustomSetupExitCode: Integer;
begin
  Result := DependencyExitCode;
end;
