<#
    MyDroidDeck "finish install" helper.

    Starts the server (hidden) and opens the Configuration page in the owner's
    browser. It waits until the server actually answers /health before opening
    the URL, so the first request never hits a 404 or "connection refused".

    Called by the installer's post-install step; harmless to run by hand.

    NOTE: keep this file pure ASCII. Windows PowerShell 5.1 reads .ps1 files
    without a BOM using the system ANSI codepage, so an em dash or an accented
    character inside a string can be mis-decoded and break parsing entirely.
#>
[CmdletBinding()]
param(
    [int]$Port = 56997,
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = 'Stop'

# tools\ sits one level below the install root.
$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $Root 'run-server.cmd'

# Honor the port chosen on the Configuration page (defaults to 56997).
$Config = Join-Path $Root 'data\runtime.json'
if (Test-Path -LiteralPath $Config) {
    try {
        $Saved = (Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json).port
        if ($Saved) { $Port = [int]$Saved }
    } catch {
        # A corrupt file is not fatal: keep the default port.
    }
}

$Url = "http://127.0.0.1:$Port/"

# Start the server unless an instance is already running.
$Running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -match 'launch\.py' }
if (-not $Running) {
    Start-Process -FilePath $Launcher -WorkingDirectory $Root -WindowStyle Hidden
}

# Wait until the server is actually serving before opening the browser. A cold
# first boot can take a few seconds, and opening too early is what produced the
# "404 / server did not start?" report.
$Ready = $false
$Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $Deadline) {
    try {
        Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri ($Url + 'health') -ErrorAction Stop | Out-Null
        $Ready = $true
        break
    } catch {
        Start-Sleep -Milliseconds 500
    }
}
if (-not $Ready) {
    Write-Warning "Servidor MyDroidDeck nao respondeu em $TimeoutSeconds s: $Url"
    exit 1
}

# Open the Configuration page in the owner's browser. Never the Windows default
# browser (Edge): use MYDROIDDECK_BROWSER, else the local Firefox. If neither
# exists, report the URL instead of silently falling back to Edge.
$Browser = $env:MYDROIDDECK_BROWSER
if (-not $Browser) { $Browser = 'C:\Desenv\Util\Firefox\firefox.exe' }
if (Test-Path -LiteralPath $Browser) {
    Start-Process -FilePath $Browser -ArgumentList $Url
} else {
    Write-Warning "Navegador nao encontrado: $Browser - abra $Url manualmente."
    exit 1
}
