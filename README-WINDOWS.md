# Instalación y ejecución en Windows 10/11

## Requisitos
- Python 3.11 o superior: https://www.python.org/downloads/windows/
- Git for Windows: https://git-scm.com/download/win
- Internet durante la instalación de paquetes.

Al instalar Python, activa **Add Python to PATH**.

## Instalar
1. Clona o descomprime este repositorio.
2. Abre PowerShell en la carpeta del proyecto.
3. Si PowerShell bloquea scripts: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
4. Ejecuta ` .\setup-windows.ps1 `

## Arrancar
Ejecuta ` .\run-windows.ps1 `.

Aplicación: http://127.0.0.1:8000  
API interactiva: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/health

Detén con Ctrl+C.

## Límites
El análisis es inventario estático inicial; no ejecuta el código clonado. La reconstrucción genera paquete y tareas, no código autónomamente. El comparador actual solo evalúa status y body HTTP, no DB, eventos, integraciones ni rendimiento. No expongas el servidor a Internet.
