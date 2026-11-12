@echo off
setlocal
set "ROOT=%~dp0"

if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo [ERROR] No existe el entorno .venv.
  echo Ejecuta primero setup-windows.ps1.
  pause
  exit /b 1
)

echo.
echo ============================================
echo    ANALISIS BILLING WATCHER + REPORT WRITER
echo ============================================
echo.
echo Introduce las URL Git de los dos repositorios Billing.
echo El BAT iniciara el analizador, generara el HTML y lo abrira.
echo.

set /p "WATCHER_URL=URL Git de Billing Watcher: "
if not defined WATCHER_URL (
  echo [ERROR] Falta la URL de Billing Watcher.
  pause
  exit /b 1
)

set /p "WRITER_URL=URL Git de Billing Report Writer: "
if not defined WRITER_URL (
  echo [ERROR] Falta la URL de Billing Report Writer.
  pause
  exit /b 1
)

if not exist "%ROOT%.venv\Scripts\python.exe" exit /b 1

start "Billing Analyzer API" /D "%ROOT%" cmd /k ""%ROOT%.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%run-billing-report.ps1" -Root "%ROOT%" -WatcherUrl "%WATCHER_URL%" -WriterUrl "%WRITER_URL%"
if errorlevel 1 (
  echo.
  echo [ERROR] No se pudo generar el informe. Revisa la ventana Billing Analyzer API.
  pause
  exit /b 1
)
endlocal
