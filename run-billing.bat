@echo off
setlocal EnableExtensions

REM Arranque local de Billing Watcher y Billing Report Writer.
REM Por defecto, ambos proyectos deben estar junto a este BAT.
REM Se pueden sobrescribir las rutas con BILLING_WATCHER_DIR y BILLING_WRITER_DIR.

if not defined BILLING_WATCHER_DIR set "BILLING_WATCHER_DIR=%~dp0rft-billing-watcher"
if not defined BILLING_WRITER_DIR set "BILLING_WRITER_DIR=%~dp0rft-billing-report-writer"

echo.
echo ============================================
echo       ARRANQUE DE BILLING MICROSERVICES
echo ============================================
echo.

call :check_project "%BILLING_WATCHER_DIR%" "Billing Watcher"
if errorlevel 1 exit /b 1

call :check_project "%BILLING_WRITER_DIR%" "Billing Report Writer"
if errorlevel 1 exit /b 1

call :launch "%BILLING_WATCHER_DIR%" "Billing Watcher"
if errorlevel 1 exit /b 1

call :launch "%BILLING_WRITER_DIR%" "Billing Report Writer"
if errorlevel 1 exit /b 1

echo.
echo Se han abierto ventanas independientes para ambos microservicios.
echo Para detenerlos, cierra sus respectivas ventanas o pulsa Ctrl+C en ellas.
echo.
exit /b 0

:check_project
if not exist "%~1\pom.xml" if not exist "%~1\mvnw.cmd" (
    echo [ERROR] No encuentro el proyecto %~2 en:
    echo         %~1
    echo.
    echo Ajusta BILLING_WATCHER_DIR y BILLING_WRITER_DIR en el entorno
    echo o edita las rutas por defecto al principio de este BAT.
    exit /b 1
)
exit /b 0

:launch
set "PROJECT_DIR=%~1"
set "SERVICE_NAME=%~2"
if exist "%PROJECT_DIR%\mvnw.cmd" (
    echo [OK] Lanzando %SERVICE_NAME% con Maven Wrapper...
    start "%SERVICE_NAME%" cmd /k "cd /d ""%PROJECT_DIR%"" && mvnw.cmd spring-boot:run"
) else (
    where mvn >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] No hay mvnw.cmd ni Maven (mvn) disponible para %SERVICE_NAME%.
        exit /b 1
    )
    echo [OK] Lanzando %SERVICE_NAME% con Maven...
    start "%SERVICE_NAME%" cmd /k "cd /d ""%PROJECT_DIR%"" && mvn spring-boot:run"
)
exit /b 0
