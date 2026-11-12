# Software Reconstruction Platform — v3.0 MVP

Plataforma local para analizar repositorios Git, generar un paquete inicial de reconstrucción y comparar dos implementaciones mediante pruebas HTTP diferenciales.

## Motores incluidos en este MVP
1. Reverse Engineering: clonado Git HTTPS e inventario estático.
2. Reconstruction: generación de paquete de reconstrucción y tareas iniciales.
3. Equivalence: comparación HTTP de status y cuerpos JSON/texto.

> Este repositorio contiene un MVP ejecutable, no una implementación autónoma completa de reconstrucción con IA. No ejecuta el código del repositorio analizado. El análisis de negocio, los agentes LLM, los sandboxes y la comparación de DB/eventos/integraciones son siguientes fases.

## Windows
Requisitos: Python 3.11+, Git for Windows.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup-windows.ps1
.\run-windows.ps1
```

Abrir http://127.0.0.1:8000 y API docs http://127.0.0.1:8000/docs.

## Seguridad
- Solo URLs Git HTTPS.
- Original inmutable; cada proyecto se clona a su propio workspace.
- No se ejecutan scripts ni tests del código clonado.
- La API escucha en localhost.
- No introducir secretos en artefactos.
- El comparador HTTP solo prueba los casos suministrados; no demuestra equivalencia universal.

Ver `README-WINDOWS.md` y `docs/NEXT_STEPS.md`.
