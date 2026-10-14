<#
    MyDroidDeck server control helper - used by the Start-menu shortcuts and by
    the server's /admin/config page.

    Actions:
      start          start the server (hidden) if it is not already running
      stop           stop the running server
      restart        stop, then start
      status         report whether the server is running and its version
      enable-logon   add a hidden launcher to the user's Startup folder
      disable-logon  remove it
      usb-connect    forward the server port over the USB cable (adb reverse)
      usb-disconnect undo the USB port forwarding

    Everything is per-user: no administrator rights, no console window.

    NOTE: keep this file pure ASCII (Windows PowerShell 5.1 reads .ps1 files
    without a BOM using the system ANSI codepage).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'enable-logon', 'disable-logon',
        'usb-connect', 'usb-disconnect')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'

# tools\ sits next to run-server.cmd, i.e. one level below the install root.
$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $Root 'run-server.cmd'
$Startup = [Environment]::GetFolderPath('Startup')
$Entry = Join-Path $Startup 'MyDroidDeck.vbs'

# Honor the port chosen on the Configuration page (defaults to 56997).
$Port = 56997
$Config = Join-Path $Root 'data\runtime.json'
if (Test-Path -LiteralPath $Config) {
    try {
        $Saved = (Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json).port
        if ($Saved) { $Port = [int]$Saved }
    } catch {
        # A corrupt file is not fatal: keep the default port.
    }
}

function Get-ServerProcess {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -match 'launch\.py' }
}

function Start-MyServer {
    if (Get-ServerProcess) {
        Write-Host 'Servidor MyDroidDeck ja esta em execucao.'
        return
    }
    Start-Process -FilePath $Launcher -WorkingDirectory $Root -WindowStyle Hidden
    # Wait until it is actually serving (a cold boot takes a few seconds).
    $Deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $Deadline) {
        try {
            Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri "http://127.0.0.1:$Port/health" -ErrorAction Stop | Out-Null
            break
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    Write-Host 'Servidor MyDroidDeck iniciado.'
}

function Stop-MyServer {
    $Procs = @(Get-ServerProcess)
    if ($Procs.Count -eq 0) {
        Write-Host 'Servidor MyDroidDeck nao esta em execucao.'
        return
    }
    foreach ($p in $Procs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host 'Servidor MyDroidDeck parado.'
}

function Show-Status {
    if (Get-ServerProcess) {
        $Health = '(sem resposta)'
        try {
            $Health = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri "http://127.0.0.1:$Port/health" -ErrorAction Stop).Content
        } catch { }
        Write-Host "Servidor MyDroidDeck em execucao na porta $Port. /health: $Health"
    } else {
        Write-Host 'Servidor MyDroidDeck parado.'
    }
}

function Set-LogonEntry {
    # A .vbs wrapper keeps the server running in the background (no console).
    $body = @(
        "' MyDroidDeck - inicia o servidor em segundo plano no logon.",
        'Set sh = CreateObject("WScript.Shell")',
        'sh.Run """' + $Launcher + '""", 0, False'
    ) -join "`r`n"
    Set-Content -Path $Entry -Value $body -Encoding ASCII
}

function Remove-LogonEntry {
    if (Test-Path -LiteralPath $Entry) { Remove-Item -LiteralPath $Entry -Force }
}

function Resolve-Adb {
    # adb ships with the Android SDK platform-tools; check the usual locations
    # (the SDK paths are not on PATH on most Windows machines).
    $Candidates = @()
    foreach ($Var in 'ANDROID_HOME', 'ANDROID_SDK_ROOT') {
        $Value = [Environment]::GetEnvironmentVariable($Var)
        if ($Value) { $Candidates += (Join-Path $Value 'platform-tools\adb.exe') }
    }
    if ($env:LOCALAPPDATA) {
        $Candidates += (Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe')
    }
    $Candidates += 'C:\Desenv\Android\Sdk\platform-tools\adb.exe'
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate) { return $Candidate }
    }
    $OnPath = Get-Command 'adb.exe' -ErrorAction SilentlyContinue
    if ($OnPath) { return $OnPath.Source }
    return $null
}

# USB cable: forward the server port from the phone to this PC, so the app talks
# to the server over the cable (http://127.0.0.1:<port>/) without any network.
function Connect-UsbReverse {
    $Adb = Resolve-Adb
    if (-not $Adb) {
        Write-Host 'adb nao encontrado. Instale o Android SDK platform-tools e tente de novo.'
        return
    }
    if (-not (Get-ServerProcess)) { Start-MyServer }
    $Result = & $Adb reverse "tcp:$Port" "tcp:$Port" 2>&1
    Write-Host "adb reverse tcp:$Port tcp:$Port -> $Result"
    Write-Host "No app, use o endereco: http://127.0.0.1:$Port/"
}

function Disconnect-UsbReverse {
    $Adb = Resolve-Adb
    if (-not $Adb) {
        Write-Host 'adb nao encontrado.'
        return
    }
    $Result = & $Adb reverse --remove "tcp:$Port" 2>&1
    Write-Host "adb reverse --remove tcp:$Port -> $Result"
}

switch ($Action) {
    'start' { Start-MyServer }
    'stop' { Stop-MyServer }
    'restart' { Stop-MyServer; Start-Sleep -Milliseconds 500; Start-MyServer }
    'status' { Show-Status }
    'usb-connect' { Connect-UsbReverse }
    'usb-disconnect' { Disconnect-UsbReverse }
    'enable-logon' {
        Set-LogonEntry
        Write-Host "Inicializacao no logon habilitada: $Entry"
    }
    'disable-logon' {
        Remove-LogonEntry
        Write-Host "Inicializacao no logon removida: $Entry"
    }
}
