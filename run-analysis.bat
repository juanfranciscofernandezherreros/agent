@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-analysis.ps1"
if errorlevel 1 (
  echo.
  echo El proceso no pudo completarse. Revisa el mensaje anterior.
  pause
)
endlocal
