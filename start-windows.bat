@echo off
rem Arranca solo la API local (modo desarrollo). Para el analisis completo usa run-analysis.bat
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-windows.ps1"
if errorlevel 1 pause
