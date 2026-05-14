$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$VenvActivate = Join-Path $Root ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
}

$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$PdfBackend = if ($env:THESIS_DOCX2PDF_BACKEND) { $env:THESIS_DOCX2PDF_BACKEND } else { "auto" }
$PreviewDpi = if ($env:THESIS_PDF_PREVIEW_DPI) { $env:THESIS_PDF_PREVIEW_DPI } else { "120" }
$OutputDir = Join-Path $Root "example\output"

if ($PythonLauncher) {
    & py -3 "md2docx.py" `
        "example\thesis-demo.md" `
        --pdf `
        --pages `
        --out "example\output" `
        --profile xju-undergraduate-thesis `
        --backend $PdfBackend `
        --dpi $PreviewDpi
} else {
    & python "md2docx.py" `
        "example\thesis-demo.md" `
        --pdf `
        --pages `
        --out "example\output" `
        --profile xju-undergraduate-thesis `
        --backend $PdfBackend `
        --dpi $PreviewDpi
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Generated: $Root\example\output\thesis-demo.docx"
Write-Host "Generated: $Root\example\output\thesis-demo.pdf"
Write-Host "Generated PDF pages: $Root\example\output\pages\page-*.png"
