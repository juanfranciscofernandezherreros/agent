$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Preparando el entorno por primera vez..." -ForegroundColor Yellow
    & .\setup-windows.ps1
    if (-not (Test-Path ".\.venv\Scripts\python.exe")) { exit 1 }
}
Write-Host "API en http://127.0.0.1:8001/docs (solo arranca la API; para un análisis completo usa run-analysis.bat)" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
