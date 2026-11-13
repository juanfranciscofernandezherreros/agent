$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "=== Preparación del entorno - Analizador de arquitectura y calidad de microservicios ===" -ForegroundColor Cyan
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
if ($LASTEXITCODE -ne 0) { Write-Host "No se pudieron instalar las dependencias." -ForegroundColor Red; exit 1 }
Set-Content -LiteralPath ".\.venv\requirements.sha256" -Value (Get-FileHash -LiteralPath ".\requirements.txt" -Algorithm SHA256).Hash -Encoding ASCII
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "AVISO: instala Git for Windows para clonar repositorios." -ForegroundColor Yellow
} else { git --version }
Write-Host "Instalación terminada. Para analizar un grupo, haz doble clic en run-analysis.bat" -ForegroundColor Green
