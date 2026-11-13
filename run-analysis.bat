@echo off
rem Lanzador unico: prepara el entorno, arranca la API, analiza el grupo GitLab y abre la documentacion.
rem Uso:  run-analysis.bat            (usa GITLAB_GROUP_ID de .env o lo pregunta)
rem       run-analysis.bat 1118       (analiza el grupo 1118)
rem       run-analysis.bat 1118 -Llm claude -Model claude-sonnet-5-5   (activa los agentes LLM con ese proveedor y modelo)
rem       run-analysis.bat -ListModels                                  (lista los modelos del proveedor configurado)
setlocal
cd /d "%~dp0"
chcp 65001 >nul
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-analysis.ps1" %*
set "RESULT=%errorlevel%"
echo.
if not "%RESULT%"=="0" echo El proceso no pudo completarse. Revisa el mensaje anterior.
echo Pulsa una tecla para cerrar esta ventana.
pause >nul
endlocal & exit /b %RESULT%
