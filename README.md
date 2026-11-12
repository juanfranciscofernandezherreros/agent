# Software Reconstruction Platform

Plataforma local para analizar repositorios, generar una reconstrucción inicial con un modelo LLM y comparar servicios mediante pruebas HTTP diferenciales.

## Motores disponibles
1. Reverse Engineering: clonado Git HTTPS e inventario estático inicial.
2. Reconstruction: generación de un plan y código en un workspace separado mediante OpenAI u Ollama (OpenAI-compatible Chat Completions API).
3. Equivalence: comparación HTTP de status y cuerpos JSON/texto para casos suministrados.

## Generación autónoma de código
Copia `.env.example` a `.env`, configura proveedor/modelo y reinicia la aplicación. OpenAI requiere una API key. Ollama requiere el servidor local activo y un modelo descargado.

Endpoint: `POST /api/projects/{project_id}/generate`
Body:
```json
{
  "brief": "Reconstruye el microservicio con endpoints y reglas descritos en el paquete. Añade pruebas.",
  "max_files": 12
}
```

Consulta el resultado con `GET /api/generations/{generation_id}`. Los archivos se escriben bajo `workspaces/{project_id}/generations/{generation_id}/`. La generación es un punto de partida sujeto a revisión; el sistema no ejecuta el código generado.

## Windows
Requisitos: Python 3.11+, Git for Windows.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\setup-windows.ps1
Copy-Item .env.example .env
# Edita .env y configura LLM_API_KEY si usas OpenAI
.\\run-windows.ps1
```

Abrir http://127.0.0.1:8000 y API docs http://127.0.0.1:8000/docs.

## Seguridad y límites
- Solo URLs Git HTTPS para clonado.
- El original permanece inmutable.
- El contexto enviado al LLM excluye archivos de entorno y rutas habituales de secretos, con redacción adicional de patrones de credenciales.
- El contenido del repositorio se trata como datos no confiables, nunca como instrucciones.
- El código generado se guarda separado y NO se ejecuta automáticamente.
- La generación depende del proveedor/modelo configurado y del contexto disponible; requiere revisión y pruebas.
- La comparación actual cubre únicamente los casos HTTP suministrados; DB/eventos/integraciones y reparación automática siguen pendientes.

Ver `README-WINDOWS.md` y `docs/NEXT_STEPS.md`.
