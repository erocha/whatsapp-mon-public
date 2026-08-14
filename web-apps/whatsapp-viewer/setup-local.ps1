$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = (Get-Command python -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath (Join-Path $root '.venv\Scripts\python.exe'))) { & $python -m venv (Join-Path $root '.venv') }
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root 'requirements.txt')
if (-not (Test-Path -LiteralPath (Join-Path $root 'config.toml'))) { Copy-Item (Join-Path $root 'config.toml.example') (Join-Path $root 'config.toml') }
New-Item -ItemType Directory -Force -Path (Join-Path $root 'data'), (Join-Path $root 'certs') | Out-Null
Write-Host 'Ambiente local preparado.' -ForegroundColor Green
Write-Host 'Próximo passo: .\setup-https.ps1'
