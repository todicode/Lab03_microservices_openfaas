param([string]$Profile = "lab03-openfaas", [string]$Stack = "stack.yml")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path -LiteralPath $Stack)) { throw "Prepare/publish a public image stack first. See docs/OPENFAAS.md." }
$gateway = "http://127.0.0.1:18080"
$encoded = kubectl --context $Profile -n openfaas get secret basic-auth -o "jsonpath={.data.basic-auth-password}"
if ($LASTEXITCODE -ne 0) { throw "Could not read Gateway credentials" }
$password = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))
$password | & .tools/faas-cli.exe login --gateway $gateway --username admin --password-stdin
if ($LASTEXITCODE -ne 0) { throw "Gateway login failed. Is port-forward running?" }
& .tools/faas-cli.exe deploy -f $Stack --gateway $gateway --read-template=false
if ($LASTEXITCODE -ne 0) { throw "Function deployment failed" }
foreach ($name in @("product-service","order-service","total-calculator")) {
    # Explicitly verify existence: faas-cli may not propagate every API error as an exit code.
    kubectl --context $Profile -n openfaas-fn get deployment $name -o name
    if ($LASTEXITCODE -ne 0) { throw "Function $name was not deployed" }
    kubectl --context $Profile -n openfaas-fn rollout status ("deployment/" + $name) --timeout=180s
    if ($LASTEXITCODE -ne 0) { throw "Function $name did not become ready" }
}
& .tools/faas-cli.exe list --gateway $gateway
