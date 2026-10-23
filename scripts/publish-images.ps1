param([switch]$Push)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$images = @()
foreach ($name in @("product-service","order-service","total-calculator")) {
    $local = "localhost:5000/lab03/" + $name + ":1.0.0"
    $remote = "docker.io/giabaonguyentran/lab03-" + $name + ":1.0.0"
    $images += @{ Local = $local; Remote = $remote }
}
$images | ForEach-Object { Write-Output ($_.Local + " -> " + $_.Remote) }
if (-not $Push) {
    Write-Output "Plan only. Run with -Push to publish these images to public Docker Hub repositories."
    exit 0
}
foreach ($image in $images) {
    docker tag $image.Local $image.Remote
    if ($LASTEXITCODE -ne 0) { throw "Image tag failed" }
    docker push $image.Remote
    if ($LASTEXITCODE -ne 0) { throw "Image push failed" }
}
Write-Output "Published all three images. Deploy with stack.yml."
