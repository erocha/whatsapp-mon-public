$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Execute .\setup-local.ps1 primeiro.' }
Push-Location $PSScriptRoot
try { & $python -m app.indexer @args } finally { Pop-Location }
