param([string]$Profile = "lab03-openfaas")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force -Path .openfaas | Out-Null
function Ensure-Forward([string]$Name,[string]$Namespace,[string]$Service,[int]$Port,[string]$Probe) {
    try {
        $response = Invoke-WebRequest -Uri ("http://127.0.0.1:" + $Port + $Probe) -TimeoutSec 2
        if ($response.StatusCode -eq 200) { Write-Output "$Name already available on $Port"; return }
    } catch {}
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) { throw "Port $Port is occupied but does not respond. Close its old port-forward and retry." }
    $process = Start-Process -FilePath kubectl -ArgumentList @("--context",$Profile,"-n",$Namespace,"port-forward","--address=127.0.0.1",("svc/" + $Service),("$Port" + ":8080")) -WindowStyle Hidden -PassThru -RedirectStandardOutput (".openfaas/" + $Name + "-forward.log") -RedirectStandardError (".openfaas/" + $Name + "-forward-error.log")
    for ($attempt=0; $attempt -lt 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri ("http://127.0.0.1:" + $Port + $Probe) -TimeoutSec 2
            if ($response.StatusCode -eq 200) { Write-Output "$Name ready on $Port (PID $($process.Id))"; return }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    throw "$Name port-forward did not become ready. See .openfaas logs."
}
Ensure-Forward "gateway" "openfaas" "gateway" 18080 "/healthz"
Ensure-Forward "web" "lab03-web" "frontend" 8084 "/"
Write-Output "OpenFaaS web: http://127.0.0.1:8084"
Write-Output "Gateway: http://127.0.0.1:18080"
