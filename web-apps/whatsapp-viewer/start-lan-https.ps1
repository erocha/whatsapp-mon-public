$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$cert = Join-Path $root 'certs\viewer.pem'; $key = Join-Path $root 'certs\viewer-key.pem'
if (-not (Test-Path $python)) { throw 'Execute .\setup-local.ps1 primeiro.' }
if (-not (Test-Path $cert)) { throw 'Execute .\setup-https.ps1 primeiro.' }
$ruleName = 'WhatsApp Viewer HTTPS (Private LAN)'
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    try { New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765 -Profile Private -RemoteAddress LocalSubnet | Out-Null }
    catch { Write-Warning 'Não foi possível criar a regra do firewall. Reabra o PowerShell como Administrador e execute novamente.'; throw }
}
$ips = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Select-Object -ExpandProperty IPAddress
Write-Host 'Acesso HTTPS na rede privada:' -ForegroundColor Green
$ips | ForEach-Object { Write-Host "  https://${_}:8765/" }
Push-Location $root
try { & $python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --ssl-certfile $cert --ssl-keyfile $key --proxy-headers } finally { Pop-Location }
