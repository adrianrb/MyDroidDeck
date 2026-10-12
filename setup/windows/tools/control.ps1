<#
    MyDroidDeck control helper — called by the server's /admin/config page.

    Actions:
      enable-logon    add a hidden launcher to the user's Startup folder
      disable-logon   remove it
      restart         stop the running server and start it again

    Everything is per-user: no administrator rights, no console window.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('enable-logon', 'disable-logon', 'restart')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'

# tools\ sits next to run-server.cmd, i.e. one level below the install root.
$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $Root 'run-server.cmd'
$Startup = [Environment]::GetFolderPath('Startup')
$Entry = Join-Path $Startup 'MyDroidDeck.vbs'

function Set-LogonEntry {
    # A .vbs wrapper keeps the server running in the background (no console).
    $body = @(
        "' MyDroidDeck - inicia o servidor em segundo plano no logon.",
        'Set sh = CreateObject("WScript.Shell")',
        'sh.Run """' + $Launcher + '""", 0, False'
    ) -join "`r`n"
    Set-Content -Path $Entry -Value $body -Encoding ASCII
}

switch ($Action) {
    'enable-logon' {
        Set-LogonEntry
        Write-Host "Inicializacao no logon habilitada: $Entry"
    }
    'disable-logon' {
        if (Test-Path -LiteralPath $Entry) { Remove-Item -LiteralPath $Entry -Force }
        Write-Host "Inicializacao no logon removida: $Entry"
    }
    'restart' {
        Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -and $_.CommandLine -match 'launch\.py' } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Milliseconds 500
        Start-Process -FilePath $Launcher -WindowStyle Hidden
        Write-Host 'Servidor reiniciado.'
    }
}
