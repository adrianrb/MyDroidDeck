@echo off
rem MyDroidDeck server launcher (installed copy, per-user).
rem Starts the bundled Python server, honoring data\runtime.json (network/port).
rem Everything lives under the install dir (the user's %USERPROFILE%), so no
rem administrator rights are needed.
setlocal
set "ROOT=%~dp0"
set "DATA=%ROOT%data"
set "LOGS=%ROOT%logs"

if not exist "%DATA%" mkdir "%DATA%" >nul 2>&1
if not exist "%LOGS%" mkdir "%LOGS%" >nul 2>&1

rem Forward slashes keep the SQLite URL valid.
set "DATA_URL=%DATA:\=/%"
set "MYDROIDDECK_DATABASE_URL=sqlite:///%DATA_URL%/mydroiddeck.db"
set "MYDROIDDECK_RUNTIME_CONFIG_FILE=%DATA%\runtime.json"
set "MYDROIDDECK_ICON_CACHE_DIR=%DATA%\icons"
rem No-login fork: the admin pages are open; the REST API still uses tokens.
set "MYDROIDDECK_ADMIN_AUTH_ENABLED=false"
set "MYDROIDDECK_CONTROL_HELPER=%ROOT%tools\control.ps1"

cd /d "%ROOT%server"
"%ROOT%runtime\python.exe" launch.py 1>>"%LOGS%\server.log" 2>&1
