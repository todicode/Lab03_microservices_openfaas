param([string]$Document = "reports/Bao_cao_Lab03_OpenFaaS.docx")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$source = (Resolve-Path -LiteralPath $Document).Path
$destination = [IO.Path]::ChangeExtension($source,"pdf")
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($source,$false,$true)
    $doc.ExportAsFixedFormat($destination,17)
    Write-Output "Exported PDF for layout verification"
} finally {
    if ($doc) { $doc.Close(0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc) }
    if ($word) { $word.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
}
