@echo off
setlocal EnableExtensions

REM Envia el JSON de Billing a la API local, espera el analisis y abre el HTML.
set "ROOT=%~dp0"
set "API=http://127.0.0.1:8001"
set "JSON=%ROOT%billing-platform-full-analysis.json"
set "RESPONSE=%TEMP%\billing-analysis-response.json"
set "STATUSFILE=%TEMP%\billing-analysis-status.json"

if not exist "%JSON%" (
  echo [ERROR] No existe: %JSON%
  pause
  exit /b 1
)

where curl.exe >nul 2>nul
if errorlevel 1 (
  echo [ERROR] curl no esta disponible en PATH.
  pause
  exit /b 1
)

echo Enviando el JSON de Billing con curl...
curl.exe --fail --silent --show-error -X POST "%API%/api/analysis-groups" -H "Content-Type: application/json" --data-binary "@%JSON%" -o "%RESPONSE%"
if errorlevel 1 (
  echo [ERROR] No se pudo enviar el JSON. Comprueba que la API esta levantada en %API%.
  pause
  exit /b 1
)

for /f "usebackq delims=" %%I in (`powershell.exe -NoProfile -Command "(Get-Content -Raw '%RESPONSE%' | ConvertFrom-Json).analysis_group_id"`) do set "GROUP_ID=%%I"
if not defined GROUP_ID (
  echo [ERROR] La API no devolvio analysis_group_id:
  type "%RESPONSE%"
  pause
  exit /b 1
)

echo Analisis iniciado: %GROUP_ID%
echo Esperando a que termine...
:WAIT
curl.exe --fail --silent --show-error "%API%/api/analysis-groups/%GROUP_ID%" -o "%STATUSFILE%"
if errorlevel 1 (
  echo [ERROR] No se puede consultar el estado del analisis.
  pause
  exit /b 1
)
for /f "usebackq delims=" %%S in (`powershell.exe -NoProfile -Command "(Get-Content -Raw '%STATUSFILE%' | ConvertFrom-Json).status"`) do set "ANALYSIS_STATUS=%%S"

if "%ANALYSIS_STATUS%"=="ANALYSIS_COMPLETED" goto DOWNLOAD
if "%ANALYSIS_STATUS%"=="PARTIAL_ANALYSIS_COMPLETED" goto DOWNLOAD
if "%ANALYSIS_STATUS%"=="FAILED" (
  echo [ERROR] El analisis ha fallado:
  type "%STATUSFILE%"
  pause
  exit /b 1
)
timeout /t 5 /nobreak >nul
goto WAIT

:DOWNLOAD
set "REPORT=%ROOT%billing-platform-full-analysis.html"
echo Descargando informe HTML...
curl.exe --fail --silent --show-error "%API%/api/analysis-groups/%GROUP_ID%/report.html" -o "%REPORT%"
if errorlevel 1 (
  echo [ERROR] No se pudo descargar el informe HTML.
  pause
  exit /b 1
)
echo Informe generado: %REPORT%
start "" "%REPORT%"
endlocal
