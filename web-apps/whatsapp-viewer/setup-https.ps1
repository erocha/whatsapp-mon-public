$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$certDir = Join-Path $root 'certs'
New-Item -ItemType Directory -Force -Path $certDir | Out-Null
$mkcert = Get-Command mkcert -ErrorAction SilentlyContinue
if (-not $mkcert) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'Instale o mkcert e execute novamente: https://github.com/FiloSottile/mkcert' }
    & $winget.Source install --id FiloSottile.mkcert --exact --accept-package-agreements --accept-source-agreements
    $mkcert = Get-Command mkcert -ErrorAction SilentlyContinue
    if (-not $mkcert) {
        $candidate = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter 'mkcert.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($candidate) { $mkcert = $candidate }
    }
}
if (-not $mkcert) { throw 'mkcert instalado, mas ainda não está no PATH. Feche e reabra o PowerShell.' }
$mkcertPath = if ($mkcert -is [System.Management.Automation.CommandInfo]) { $mkcert.Source } else { $mkcert.FullName }
if (-not $mkcertPath) { $mkcertPath = [string]$mkcert }
$caroot = & $mkcertPath -CAROOT
$rootCa = Join-Path $caroot 'rootCA.pem'
if (Test-Path -LiteralPath $rootCa) {
    & certutil.exe -user -addstore Root $rootCa | Out-Null
} else {
    & $mkcertPath -install
}
$addresses = @('localhost','127.0.0.1',"$env:COMPUTERNAME", "$env:COMPUTERNAME.local")
$addresses += Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Select-Object -ExpandProperty IPAddress
$addresses = $addresses | Sort-Object -Unique
& $mkcertPath -cert-file (Join-Path $certDir 'viewer.pem') -key-file (Join-Path $certDir 'viewer-key.pem') @addresses
Copy-Item -LiteralPath (Join-Path $caroot 'rootCA.pem') -Destination (Join-Path $certDir 'rootCA-for-android.pem') -Force
Write-Host 'HTTPS configurado.' -ForegroundColor Green
Write-Host ('Nomes/IPs do certificado: ' + ($addresses -join ', '))
Write-Host ('CA para instalar no Android: ' + (Join-Path $certDir 'rootCA-for-android.pem'))
