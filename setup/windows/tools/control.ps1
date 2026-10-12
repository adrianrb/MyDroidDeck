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

    Everything is per-user: no administrator rights, no console window.

    NOTE: keep this file pure ASCII (Windows PowerShell 5.1 reads .ps1 files
    without a BOM using the system ANSI codepage).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'enable-logon', 'disable-logon')]
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

switch ($Action) {
    'start' { Start-MyServer }
    'stop' { Stop-MyServer }
    'restart' { Stop-MyServer; Start-Sleep -Milliseconds 500; Start-MyServer }
    'status' { Show-Status }
    'enable-logon' {
        Set-LogonEntry
        Write-Host "Inicializacao no logon habilitada: $Entry"
    }
    'disable-logon' {
        Remove-LogonEntry
        Write-Host "Inicializacao no logon removida: $Entry"
    }
}
