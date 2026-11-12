@echo off
setlocal EnableExtensions

REM Arranca la API si no esta activa, envia el JSON, espera el analisis y abre el HTML.
set "ROOT=%~dp0"
set "API=http://127.0.0.1:8001"
set "JSON=%ROOT%billing-platform-full-analysis.json"
set "RESPONSE=%TEMP%\billing-analysis-response.json"
set "STATUSFILE=%TEMP%\billing-analysis-status.json"
set "REPORT=%ROOT%billing-platform-full-analysis.html"

if not exist "%JSON%" goto MISSING_JSON
where curl.exe >nul 2>nul
if errorlevel 1 goto MISSING_CURL

REM Comprueba si la API ya esta disponible.
curl.exe --fail --silent "%API%/openapi.json" -o nul
if not errorlevel 1 goto API_READY

echo La API no esta levantada. Iniciando el analizador en el puerto 8001...
if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo Preparando entorno Python automaticamente...
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%ROOT%'; & '.\setup-windows.ps1'"
  if errorlevel 1 goto SETUP_FAILED
  if not exist "%ROOT%.venv\Scripts\python.exe" goto SETUP_FAILED
)
start "Billing Analyzer API" powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%ROOT%'; & '.\run-windows.ps1'"
echo Esperando a que arranque la API...
set /a ATTEMPTS=0

:WAIT_API
curl.exe --fail --silent "%API%/openapi.json" -o nul
if not errorlevel 1 goto API_READY
set /a ATTEMPTS+=1
if %ATTEMPTS% GEQ 60 goto API_TIMEOUT
timeout /t 2 /nobreak >nul
goto WAIT_API

:API_READY
echo API disponible en %API%.
echo Enviando el JSON de Billing con curl...
curl.exe --fail --silent --show-error -X POST "%API%/api/analysis-groups" -H "Content-Type: application/json" --data-binary "@%JSON%" -o "%RESPONSE%"
if errorlevel 1 goto POST_FAILED

for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -Command "(Get-Content -Raw '%RESPONSE%' | ConvertFrom-Json).analysis_group_id"`) do set "GROUP_ID=%%I"
if not defined GROUP_ID goto MISSING_GROUP_ID

echo Analisis iniciado: %GROUP_ID%
echo Esperando a que termine...

:WAIT_ANALYSIS
curl.exe --fail --silent --show-error "%API%/api/analysis-groups/%GROUP_ID%" -o "%STATUSFILE%"
if errorlevel 1 goto STATUS_FAILED
for /f "usebackq delims=" %%S in (`powershell.exe -NoProfile -Command "(Get-Content -Raw '%STATUSFILE%' | ConvertFrom-Json).status"`) do set "ANALYSIS_STATUS=%%S"

if "%ANALYSIS_STATUS%"=="ANALYSIS_COMPLETED" goto DOWNLOAD
if "%ANALYSIS_STATUS%"=="PARTIAL_ANALYSIS_COMPLETED" goto DOWNLOAD
if "%ANALYSIS_STATUS%"=="FAILED" goto ANALYSIS_FAILED
timeout /t 5 /nobreak >nul
goto WAIT_ANALYSIS

:DOWNLOAD
echo Descargando informe HTML...
curl.exe --fail --silent --show-error "%API%/api/analysis-groups/%GROUP_ID%/report.html" -o "%REPORT%"
if errorlevel 1 goto DOWNLOAD_FAILED
echo Informe generado: %REPORT%
start "" "%REPORT%"
endlocal
exit /b 0

:MISSING_JSON
echo [ERROR] No existe: %JSON%
goto FAIL
:MISSING_CURL
echo [ERROR] curl no esta disponible en PATH.
goto FAIL
:SETUP_FAILED
echo [ERROR] No se pudo preparar el entorno Python automaticamente.
goto FAIL
:API_TIMEOUT
echo [ERROR] La API no ha arrancado en 120 segundos. Revisa la ventana Billing Analyzer API.
goto FAIL
:POST_FAILED
echo [ERROR] No se pudo enviar el JSON a la API.
goto FAIL
:MISSING_GROUP_ID
echo [ERROR] La API no devolvio analysis_group_id:
type "%RESPONSE%"
goto FAIL
:STATUS_FAILED
echo [ERROR] No se puede consultar el estado del analisis.
goto FAIL
:ANALYSIS_FAILED
echo [ERROR] El analisis ha fallado:
type "%STATUSFILE%"
goto FAIL
:DOWNLOAD_FAILED
echo [ERROR] No se pudo descargar el informe HTML.
:FAIL
pause
exit /b 1
