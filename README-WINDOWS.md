# Instalación y ejecución en Windows 10/11

## Requisitos
- Python 3.11 o superior: https://www.python.org/downloads/windows/
- Git for Windows: https://git-scm.com/download/win
- Un proveedor LLM: OpenAI API o Ollama local.

## Instalar
1. Clona este repositorio.
2. Abre PowerShell en la carpeta del proyecto.
3. Ejecuta `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
4. Ejecuta `.\\setup-windows.ps1`.
5. Copia el archivo de configuración: `Copy-Item .env.example .env`.
6. Edita `.env` y configura OpenAI u Ollama.

## Arrancar
`.\\run-windows.ps1`

Aplicación: http://127.0.0.1:8001  
API interactiva: http://127.0.0.1:8001/docs

