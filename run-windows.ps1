$ErrorActionPreference = "Stop"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Ejecuta primero .\setup-windows.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "Abre http://127.0.0.1:8000 en el navegador" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
