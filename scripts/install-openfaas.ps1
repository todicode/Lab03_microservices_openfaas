param([string]$Profile = "lab03-openfaas")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
function Check { if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" } }
minikube -p $Profile start --driver=docker --container-runtime=docker --cpus=2 --memory=4096 --kubernetes-version=v1.35.0 --keep-context
Check
kubectl --context $Profile apply -f infra/namespaces.yml
Check
foreach ($ns in @("lab03-data","lab03-web")) {
    kubectl --context $Profile create namespace $ns --dry-run=client -o yaml | kubectl --context $Profile apply -f -
    Check
}
& .tools/helm.exe repo add openfaas https://openfaas.github.io/faas-netes/
Check
& .tools/helm.exe repo update openfaas
Check
& .tools/helm.exe upgrade --install openfaas openfaas/openfaas --version 15.0.14 --namespace openfaas --kube-context $Profile -f infra/openfaas-values.yml --wait --timeout 5m
Check
python scripts/fetch_template.py
Check
python scripts/setup_env.py
Check
python scripts/k8s_secrets.py --profile $Profile
Check
kubectl --context $Profile -n lab03-data create configmap postgres-init --from-file=01-init.sh=infra/postgres/init.sh --from-file=products.sql=infra/postgres/products.sql --from-file=orders.sql=infra/postgres/orders.sql --dry-run=client -o yaml | kubectl --context $Profile apply -f -
Check
kubectl --context $Profile apply -f infra/kubernetes/postgres.yml
Check
kubectl --context $Profile -n lab03-web create configmap frontend-assets --from-file=frontend/index.html --from-file=frontend/styles.css --from-file=frontend/app.js --dry-run=client -o yaml | kubectl --context $Profile apply -f -
Check
kubectl --context $Profile -n lab03-web create configmap frontend-nginx --from-file=default.conf=infra/nginx/kubernetes.conf --dry-run=client -o yaml | kubectl --context $Profile apply -f -
Check
kubectl --context $Profile apply -f infra/kubernetes/frontend.yml
Check
kubectl --context $Profile -n lab03-data rollout status statefulset/postgres --timeout=180s
Check
kubectl --context $Profile -n lab03-web rollout status deployment/frontend --timeout=180s
Check
Write-Output "OpenFaaS infrastructure installed. Function deployment requires public images for CE."
