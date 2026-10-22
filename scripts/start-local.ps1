$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python scripts/setup_env.py
if ($LASTEXITCODE -ne 0) { throw "Could not prepare .env" }
docker compose up -d --build --wait --wait-timeout 120
if ($LASTEXITCODE -ne 0) { throw "Local startup failed" }
Write-Output "Local development demo: http://127.0.0.1:8082"
