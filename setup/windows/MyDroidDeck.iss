; Inno Setup 6 script for the MyDroidDeck "no-login / LAN" fork (Windows).
;
; 1) Build the offline bundle first (downloads Python + wheels):
;        setup/build-offline.sh
; 2) Compile this installer with Inno Setup 6.3+ (ISCC.exe):
;        "C:\Desenv\Util\Inno Setup 7\ISCC.exe" setup\windows\MyDroidDeck.iss
;
; What it does: installs the bundled server under the user's HOME
; (%USERPROFILE%\MyDroidDeck) with NO elevation, keeps data/logs beside it, can
; add a hidden launcher to the user's Startup folder, and on finish starts the
; server, waits ~5s and opens http://127.0.0.1:56997/ in the browser (the root
; redirects to /admin/config). The admin pages have NO login; the REST API still
; uses device tokens.
;
; Note: enabling LAN access ("Visivel na rede") also needs a Windows Firewall
; rule, which requires an elevated PowerShell once - see setup/README.md.

#define AppName "MyDroidDeck"
#define AppPublisher "MyDroidDeck"
#define AppExeName "run-server.cmd"
#define DefaultPort "56997"
#define StageDir AddBackslash(SourcePath) + "..\build\stage"
#define Version Trim(FileRead(FileOpen(AddBackslash(SourcePath) + "..\..\server\version.txt")))

[Setup]
AppId={{9C1B7E5A-3F2D-4A6B-8E71-2D5C0A4F1B93}
AppName={#AppName}
AppVersion={#Version}
AppPublisher={#AppPublisher}
; Per-user install in the user's HOME - never needs administrator rights.
DefaultDirName={%USERPROFILE}\MyDroidDeck
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\build\output
OutputBaseFilename=MyDroidDeck-{#Version}-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startup"; Description: "Iniciar o servidor no logon do Windows"; GroupDescription: "Inicializacao:"; Flags: checkedonce

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Dirs]
Name: "{app}\data"
Name: "{app}\logs"

[Icons]
Name: "{group}\Iniciar servidor MyDroidDeck"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Configuracao do MyDroidDeck"; Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""{app}\tools\open-console.ps1"""; Comment: "Iniciar o servidor e abrir a Configuracao (Firefox)"
Name: "{group}\Desinstalar MyDroidDeck"; Filename: "{uninstallexe}"

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action enable-logon"; Tasks: startup; Flags: runhidden
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\open-console.ps1"""; Description: "Iniciar o servidor e abrir a Configuracao"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action disable-logon"; Flags: runhidden; RunOnceId: "RemoveStartupEntry"

[Code]
{ Write the initial runtime.json with the installer's choices, unless the user
  already has one (for example, reinstalling over an existing install). }
procedure WriteRuntimeConfig();
var
  DataDir, ConfigFile, StartOnLogon, Json: string;
begin
  DataDir := ExpandConstant('{app}\data');
  ConfigFile := DataDir + '\runtime.json';
  if FileExists(ConfigFile) then
    exit;
  if not DirExists(DataDir) then
    ForceDirectories(DataDir);

  if WizardIsTaskSelected('startup') then
    StartOnLogon := 'true'
  else
    StartOnLogon := 'false';

  Json := '{' + #13#10 +
          '  "visible_on_network": false,' + #13#10 +
          '  "port": {#DefaultPort},' + #13#10 +
          '  "start_on_logon": ' + StartOnLogon + #13#10 +
          '}' + #13#10;
  SaveStringToFile(ConfigFile, Json, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    WriteRuntimeConfig();
end;
