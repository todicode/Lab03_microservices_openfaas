param([switch]$Push)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
# Images contain code/dependencies only. Actual database passwords are mounted at runtime.
# Without -Push this script prepares a reviewable plan and does not upload anything.
$prefix = "lab03-" + [guid]::NewGuid().ToString("N")
$content = Get-Content -LiteralPath stack.yml -Raw
$images = @()
foreach ($name in @("product-service","order-service","total-calculator")) {
    $local = "localhost:5000/lab03/" + $name + ":1.0.0"
    $remote = "ttl.sh/" + $prefix + "-" + $name + ":24h"
    $content = $content.Replace($local, $remote)
    $images += @{ Local = $local; Remote = $remote }
}
New-Item -ItemType Directory -Force -Path .generated | Out-Null
[IO.File]::WriteAllText((Join-Path (Get-Location) ".generated/stack-public.yml"), $content, [Text.UTF8Encoding]::new($false))
$images | ForEach-Object { Write-Output ($_.Local + " -> " + $_.Remote) }
if (-not $Push) {
    Write-Output "Plan only. To explicitly publish public images for 24 hours, run with -Push."
    exit 0
}
foreach ($image in $images) {
    docker tag $image.Local $image.Remote
    if ($LASTEXITCODE -ne 0) { throw "Image tag failed" }
    docker push $image.Remote
    if ($LASTEXITCODE -ne 0) { throw "Image push failed" }
}
Write-Output "Published. Deploy using .generated/stack-public.yml."
