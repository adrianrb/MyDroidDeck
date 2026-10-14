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
; server, waits until it answers, then opens http://127.0.0.1:56997/ in the
; browser (the root redirects to /admin/config). It also adds Start-menu
; shortcuts for Configuracao, Iniciar, Parar, Reiniciar, Conectar por USB and
; readme.txt. The admin pages have NO login; the REST API still uses device
; tokens.
;
; The wizard asks how the phone will reach the server (multiple choice): USB
; (adb reverse over the cable), Wi-Fi/LAN (visible on the network) and Bluetooth
; (listed but not available yet). See setup/README.md.
;
; Note: enabling LAN access ("Visivel na rede") also needs a Windows Firewall
; rule, which requires an elevated PowerShell once - see setup/README.md.

#define AppName "MyDroidDeck"
#define AppPublisher "MyDroidDeck"
#define AppExeName "run-server.cmd"
#define DefaultPort "56997"
#define StageDir AddBackslash(SourcePath) + "..\build\stage"
#define Version Trim(FileRead(FileOpen(AddBackslash(SourcePath) + "..\..\server\version.txt")))
; Installer/shortcut icon, matching the app's launcher icon. Regenerate it from
; the Android vector with: python3 setup/windows/make-icon.py
#define AppIcon AddBackslash(SourcePath) + "app.ico"

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
; Same icon as the app (and the shortcuts below).
SetupIconFile={#AppIcon}
UninstallDisplayIcon={app}\app.ico

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
brazilianportuguese.UninstallDataPrompt=Deseja apagar também todos os dados do MyDroidDeck?%n%nIsso remove perfis, dispositivos pareados, ações, ícones e logs (a pasta %1).%n%nEscolha "Não" para manter os dados.
english.UninstallDataPrompt=Also delete all MyDroidDeck data?%n%nThis removes profiles, paired devices, actions, icons and logs (the %1 folder).%n%nChoose "No" to keep the data.
; Connectivity choices (see setup/README.md): how the phone reaches the server.
brazilianportuguese.GroupConnectivity=Conectividade:
brazilianportuguese.TaskConnectUsb=USB (cabo): encaminhar a porta com o adb reverse
brazilianportuguese.TaskConnectWifi=Wi-Fi/rede local: liberar o servidor na rede
brazilianportuguese.TaskConnectBluetooth=Bluetooth (em breve - ainda não disponível)
brazilianportuguese.GroupStartup=Inicialização:
brazilianportuguese.TaskStartup=Iniciar o servidor no logon do Windows
brazilianportuguese.WifiFirewallNote=Para o Wi-Fi funcionar, libere a porta no Firewall do Windows (a página de Configuração explica como).
english.GroupConnectivity=Connectivity:
english.TaskConnectUsb=USB (cable): forward the port with adb reverse
english.TaskConnectWifi=Wi-Fi/LAN: make the server visible on the network
english.TaskConnectBluetooth=Bluetooth (coming soon - not available yet)
english.GroupStartup=Startup:
english.TaskStartup=Start the server at Windows logon
english.WifiFirewallNote=For Wi-Fi to work, open the port in the Windows Firewall (the Settings page explains how).

[Tasks]
; Connectivity: the phone can reach the server over the USB cable (adb reverse,
; loopback on the phone) and/or over the LAN. Bluetooth has no transport yet, so
; its item is disabled in InitializeWizard.
Name: "connect_usb"; Description: "{cm:TaskConnectUsb}"; GroupDescription: "{cm:GroupConnectivity}"; Flags: checkedonce
Name: "connect_wifi"; Description: "{cm:TaskConnectWifi}"; GroupDescription: "{cm:GroupConnectivity}"; Flags: checkedonce
Name: "connect_bluetooth"; Description: "{cm:TaskConnectBluetooth}"; GroupDescription: "{cm:GroupConnectivity}"; Flags: unchecked
Name: "startup"; Description: "{cm:TaskStartup}"; GroupDescription: "{cm:GroupStartup}"; Flags: checkedonce

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
; Server start/stop/restart/status scripts (also usable from a console).
Source: "{#SourcePath}\start.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\stop.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\restart.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\status.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\..\readme.txt"; DestDir: "{app}"; Flags: ignoreversion
; Installer/shortcut icon (also referenced by UninstallDisplayIcon).
Source: "{#AppIcon}"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"
Name: "{app}\logs"

[Icons]
; The "Configuracao" shortcut starts the server and opens the admin page in the
; owner's browser (Firefox). The server-control shortcuts are silent.
Name: "{group}\Configuracao do MyDroidDeck"; Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""{app}\tools\open-console.ps1"""; IconFilename: "{app}\app.ico"; Comment: "Iniciar o servidor e abrir a Configuracao (Firefox)"
Name: "{group}\Iniciar servidor MyDroidDeck"; Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action start"; IconFilename: "{app}\app.ico"; Comment: "Ligar o servidor"
Name: "{group}\Parar servidor MyDroidDeck"; Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action stop"; IconFilename: "{app}\app.ico"; Comment: "Desligar o servidor"
Name: "{group}\Reiniciar servidor MyDroidDeck"; Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action restart"; IconFilename: "{app}\app.ico"; Comment: "Reiniciar o servidor"
Name: "{group}\readme.txt"; Filename: "{app}\readme.txt"; IconFilename: "{app}\app.ico"; Comment: "Como usar o MyDroidDeck"
; USB cable: forwards the server port to the phone with adb (only offered when
; the USB connectivity option was chosen).
Name: "{group}\Conectar por USB"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action usb-connect"; IconFilename: "{app}\app.ico"; Comment: "Encaminhar a porta do servidor pelo cabo USB (adb reverse)"; Tasks: connect_usb
Name: "{group}\Desinstalar MyDroidDeck"; Filename: "{uninstallexe}"; IconFilename: "{app}\app.ico"

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action enable-logon"; Tasks: startup; Flags: runhidden
; Wire the cable to the server right away when USB was chosen (silent included).
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action usb-connect"; Tasks: connect_usb; Flags: runhidden
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\open-console.ps1"""; Description: "Iniciar o servidor e abrir a Configuracao"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action disable-logon"; Flags: runhidden; RunOnceId: "RemoveStartupEntry"
; Stop the server before any file/data is removed (it may hold the SQLite DB).
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\tools\control.ps1"" -Action stop"; Flags: runhidden; RunOnceId: "StopServer"

[Code]
{ The Bluetooth transport does not exist yet (the server has no RFCOMM
  listener), so its connectivity item is shown but cannot be selected. }
procedure InitializeWizard();
var
  Index: Integer;
begin
  for Index := 0 to WizardForm.TasksList.Items.Count - 1 do
    if Pos('Bluetooth', WizardForm.TasksList.Items[Index]) > 0 then
      WizardForm.TasksList.ItemEnabled[Index] := False;
end;

{ Write the initial runtime.json with the installer's choices, unless the user
  already has one (for example, reinstalling over an existing install). }
procedure WriteRuntimeConfig();
var
  DataDir, ConfigFile, StartOnLogon, VisibleOnNetwork, Json: string;
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

  { Wi-Fi/LAN: the server must listen on the network, not only on 127.0.0.1. }
  if WizardIsTaskSelected('connect_wifi') then
    VisibleOnNetwork := 'true'
  else
    VisibleOnNetwork := 'false';

  Json := '{' + #13#10 +
          '  "visible_on_network": ' + VisibleOnNetwork + ',' + #13#10 +
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

{ Remind the user about the firewall when Wi-Fi was chosen (the installer is
  not elevated, so it cannot add the rule itself). }
var
  ConnectivityNoteShown: Boolean;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and not ConnectivityNoteShown then
  begin
    ConnectivityNoteShown := True;
    if WizardIsTaskSelected('connect_wifi') then
      WizardForm.FinishedLabel.Caption :=
        WizardForm.FinishedLabel.Caption + #13#10 + #13#10 +
        ExpandConstant('{cm:WifiFirewallNote}');
  end;
end;

{ Set in InitializeUninstall when the user asks to wipe everything. }
var
  DeleteAllData: Boolean;

{ Before the uninstall starts, offer to remove the whole install folder
  (profiles, paired devices, actions, icons and logs). Silent uninstalls keep
  the data. }
function InitializeUninstall(): Boolean;
begin
  Result := True;
  DeleteAllData := False;
  if UninstallSilent then
    exit;
  if MsgBox(
       FmtMessage(CustomMessage('UninstallDataPrompt'), [ExpandConstant('{app}')]),
       mbConfirmation, MB_YESNO) = IDYES then
    DeleteAllData := True;
end;

{ After the uninstaller removed its own files, wipe whatever is left (data\,
  logs\, runtime\) when the user asked for it. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and DeleteAllData then
    DelTree(ExpandConstant('{app}'), True, True, True);
end;
