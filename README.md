# Software Reconstruction Platform

Plataforma local para analizar repositorios, generar una reconstrucción inicial con un modelo LLM y comparar comportamiento HTTP y snapshots de estado.

## Motores disponibles
1. Reverse Engineering: clonado Git HTTPS e inventario estático inicial.
2. Reconstruction: generación de un plan y código en un workspace separado mediante OpenAI u Ollama.
3. Equivalence: comparación HTTP diferencial y comparación de snapshots de DB, eventos e integraciones.

## Generación autónoma de código
Configura `.env` con el proveedor/modelo. Endpoint: `POST /api/projects/{project_id}/generate`; consulta `GET /api/generations/{generation_id}`. Los archivos se escriben bajo `workspaces/{project_id}/generations/{generation_id}/`. El código no se ejecuta automáticamente.

## Comparación de estado (DB, eventos e integraciones)
Endpoint: `POST /api/equivalence/compare-state`.

Envía dos snapshots con la misma estructura:
```json
{
  "original": {
    "database": {"schema": {"users": ["id", "email"]}, "tables": {"users": [{"id": 1, "email": "a@example.com"}]}},
    "events": [{"name": "user.created", "payload": {"user_id": 1}}],
    "integrations": [{"provider": "mail", "operation": "send", "request": {"to": "a@example.com"}, "response": {"status": 202}}]
  },
  "reconstructed": {
    "database": {"schema": {"users": ["id", "email"]}, "tables": {"users": [{"id": 1, "email": "a@example.com"}]}},
    "events": [{"name": "user.created", "payload": {"user_id": 1}}],
    "integrations": [{"provider": "mail", "operation": "send", "request": {"to": "a@example.com"}, "response": {"status": 202}}]
  }
}
```

- DB: compara esquema, tablas, filas y multiplicidad; ignora el orden de las filas.
- Eventos: compara cantidad, orden, nombre y payload.
- Integraciones: compara secuencia, proveedor, operación, request y response.
- Respuesta: `MATCH` o `MISMATCH`, estado por dimensión y diferencias con rutas y valores original/reconstruido. Cada ejecución queda consultable en `GET /api/equivalence/{run_id}`.

**Importante:** este MVP compara snapshots exportados; todavía no se conecta automáticamente a PostgreSQL/MySQL, brokers o APIs externas para capturarlos. Debes capturar ambos snapshots ejecutando el mismo escenario en entornos aislados equivalentes. No se normalizan UUID/timestamps automáticamente: define reglas de normalización explícitas para evitar ocultar diferencias semánticas. `MATCH` solo valida los snapshots recibidos, no demuestra equivalencia universal.

## Windows
Requisitos: Python 3.11+, Git for Windows.
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\setup-windows.ps1
Copy-Item .env.example .env
.\\run-windows.ps1
```
Abrir http://127.0.0.1:8000 y API docs http://127.0.0.1:8000/docs.

## Seguridad y límites
- El original permanece inmutable; el código generado no se ejecuta automáticamente.
- Las llamadas externas deben probarse contra mocks/proxies o entornos de prueba para evitar duplicar pagos, correos u otros efectos reales.
- El sistema no declara equivalencia si falta evidencia.
