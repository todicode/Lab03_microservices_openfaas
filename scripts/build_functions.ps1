param([string]$Profile = "lab03-openfaas")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
function Check { if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" } }
python scripts/prepare_functions.py
Check
# Linux CLI avoids faas-cli 0.18.17 interpreting Windows drive letters as URLs.
docker run --rm --mount "type=bind,source=$((Get-Location).Path),target=/workspace" --workdir /workspace ghcr.io/openfaas/faas-cli:0.18.17 build -f stack.yml --shrinkwrap
Check
foreach ($name in @("product-service","order-service","total-calculator")) {
    $image = "localhost:5000/lab03/" + $name + ":1.0.0"
    docker build --build-arg PYTHON_VERSION=3.12 --tag $image ("build/" + $name)
    Check
}
