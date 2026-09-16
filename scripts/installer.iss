#define AppName "YOLO Media Organizer"
#define Artifact "YOLO-media-organizer-" + AppVersion + "-windows-" + AppArchitecture + "-" + AppBackend
#define ExeName Artifact + ".exe"

[Setup]
AppId=electblake.YOLO-media-organizer
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=electblake
DefaultDirName={localappdata}\Programs\YOLO-media-organizer
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename={#Artifact}-Setup
UninstallDisplayIcon={app}\{#ExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Files]
Source: "..\dist\{#Artifact}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#ExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
