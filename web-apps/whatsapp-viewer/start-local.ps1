$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$cert = Join-Path $root 'certs\viewer.pem'; $key = Join-Path $root 'certs\viewer-key.pem'
if (-not (Test-Path $python)) { throw 'Execute .\setup-local.ps1 primeiro.' }
if (-not (Test-Path $cert)) { throw 'Execute .\setup-https.ps1 primeiro.' }
Push-Location $root
try { & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --ssl-certfile $cert --ssl-keyfile $key } finally { Pop-Location }
