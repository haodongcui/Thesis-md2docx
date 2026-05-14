$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$VenvActivate = Join-Path $Root ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
}

$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue

if ($PythonLauncher) {
    & py -3 "md2docx.py" docx `
        "example\thesis-demo.md" `
        "example\thesis-demo.docx" `
        --profile xju-undergraduate-thesis
} else {
    & python "md2docx.py" docx `
        "example\thesis-demo.md" `
        "example\thesis-demo.docx" `
        --profile xju-undergraduate-thesis
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Generated: $Root\example\thesis-demo.docx"
