<#
    MyDroidDeck firewall rule - scoped to the bundled Python so any port serves.

    Actions:
      add      (re)create the inbound rule (needs an elevated PowerShell)
      remove   delete it

    Run by the installer (which is elevated); can also be run by hand after
    changing something:  powershell -ExecutionPolicy Bypass -File firewall.ps1 -Action add
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('add', 'remove')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Rule = 'MyDroidDeck'
$Python = Join-Path $Root 'runtime\python.exe'

if ($Action -eq 'add') {
    Remove-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $Rule -Direction Inbound -Action Allow `
        -Program $Python -Profile Any -Description 'MyDroidDeck server (LAN access)' | Out-Null
    Write-Host "Regra de firewall criada: $Rule"
}
else {
    Remove-NetFirewallRule -DisplayName $Rule -ErrorAction SilentlyContinue
    Write-Host "Regra de firewall removida: $Rule"
}
