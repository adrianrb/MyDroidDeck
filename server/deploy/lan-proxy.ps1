# Expose the WSL2 MyDroidDeck server to the LAN (so an Android device can reach it).
#
# Run in an ELEVATED PowerShell (right-click the file > "Executar com o PowerShell"
# as administrator, or from an admin terminal:  powershell -ExecutionPolicy Bypass -File .\lan-proxy.ps1).
#
# Why: the server listens inside WSL2, whose 172.x NAT address is only reachable
# from Windows. This adds a netsh portproxy from the Windows LAN to the current
# WSL2 IP, plus the inbound firewall rule. Re-run it after a Windows reboot or a
# `wsl --shutdown`, because the WSL2 IP changes.

$Port = 8000
$Rule = "MyDroidDeck $Port"

$WslIp = (wsl.exe hostname -I).Trim().Split()[0]
if (-not $WslIp) {
    Write-Error "Não foi possível detectar o IP do WSL2. O WSL está em execução?"
    exit 1
}
Write-Host "IP atual do WSL2: $WslIp"

# Replace any previous rule for this port so the target follows the WSL2 IP.
netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=0.0.0.0 2>$null | Out-Null
netsh interface portproxy add v4tov4 listenport=$Port listenaddress=0.0.0.0 connectport=$Port connectaddress=$WslIp

if (-not (Get-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $Rule -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
    Write-Host "Regra de firewall criada: $Rule"
}
else {
    Write-Host "Regra de firewall já existe: $Rule"
}

Write-Host ""
Write-Host "Proxy ativo — aparelhos na LAN alcançam o servidor pelo IP do Windows:"
netsh interface portproxy show v4tov4
Write-Host ""
Write-Host "No app, use:  https://<ip-lan-do-windows>:$Port/"
