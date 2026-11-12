$ErrorActionPreference = "Stop"
Write-Host "=== Instalador local - Software Reconstruction Platform ===" -ForegroundColor Cyan
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 --version
    py -3 -m venv .venv
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python --version
    python -m venv .venv
} else {
    Write-Host "Python 3 no está instalado. Descárgalo de https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    exit 1
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "AVISO: instala Git for Windows para clonar repositorios." -ForegroundColor Yellow
} else { git --version }
Write-Host "Instalación terminada. Ejecuta .\run-windows.ps1" -ForegroundColor Green
