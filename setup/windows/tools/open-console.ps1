<#
    MyDroidDeck "finish install" helper.

    Starts the server (hidden) and opens the Configuration page in the browser.
    The server needs a moment to boot, so we wait a few seconds before opening
    the URL — otherwise the first request can hit a 404.

    Called by the installer's post-install step; harmless to run by hand.
#>
[CmdletBinding()]
param(
    [int]$Port = 56997,
    [int]$DelaySeconds = 5
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

# Start the server unless an instance is already running.
$Running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -match 'launch\.py' }
if (-not $Running) {
    Start-Process -FilePath $Launcher -WorkingDirectory $Root -WindowStyle Hidden
    Start-Sleep -Seconds $DelaySeconds
}

# Open the Configuration page in the owner's browser. Never the Windows default
# browser (Edge): use MYDROIDDECK_BROWSER, else the local Firefox. If neither
# exists, report the URL instead of silently falling back to Edge.
$Url = "http://127.0.0.1:$Port/"
$Browser = $env:MYDROIDDECK_BROWSER
if (-not $Browser) { $Browser = 'C:\Desenv\Util\Firefox\firefox.exe' }
if (Test-Path -LiteralPath $Browser) {
    Start-Process -FilePath $Browser -ArgumentList $Url
} else {
    Write-Warning "Navegador não encontrado: $Browser — abra $Url manualmente."
    exit 1
}
