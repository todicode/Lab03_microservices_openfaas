$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force -Path .tools | Out-Null
$faasVersion = "0.18.17"
$helmVersion = "3.19.0"
Invoke-WebRequest -Uri "https://github.com/openfaas/faas-cli/releases/download/$faasVersion/faas-cli.exe" -OutFile .tools/faas-cli.exe
Invoke-WebRequest -Uri "https://get.helm.sh/helm-v$helmVersion-windows-amd64.zip" -OutFile .tools/helm.zip
Invoke-WebRequest -Uri "https://get.helm.sh/helm-v$helmVersion-windows-amd64.zip.sha256sum" -OutFile .tools/helm.sha256sum
$expected = ((Get-Content .tools/helm.sha256sum -Raw).Trim() -split "\s+")[0]
$actual = (Get-FileHash .tools/helm.zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "Helm checksum mismatch" }
Expand-Archive -LiteralPath .tools/helm.zip -DestinationPath .tools/helm -Force
Copy-Item -LiteralPath .tools/helm/windows-amd64/helm.exe -Destination .tools/helm.exe
& .tools/faas-cli.exe version
& .tools/helm.exe version --short
