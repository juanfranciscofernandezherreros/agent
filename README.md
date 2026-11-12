# Software Reconstruction Platform

Plataforma local para analizar repositorios, generar una reconstrucción inicial con un modelo LLM y comparar comportamiento HTTP y snapshots de estado.

## Motores disponibles
1. Reverse Engineering: clonado Git HTTPS e inventario estático inicial.
2. Reconstruction: generación de código en un workspace separado mediante OpenAI u Ollama.
3. Equivalence: comparación HTTP diferencial y snapshots de DB, eventos e integraciones.
4. Auto-Repair: reparación LLM acotada por un informe diferencial persistido.

## Generación de código
Configura `.env` con el proveedor/modelo. Endpoint: `POST /api/projects/{project_id}/generate`; consulta `GET /api/generations/{generation_id}`. Los archivos se escriben bajo `workspaces/{project_id}/generations/{generation_id}/`.

## Comparación de estado
Endpoint: `POST /api/equivalence/compare-state`. Envía `original` y `reconstructed` snapshots con `database.schema`, `database.tables`, `events` e `integrations`. La respuesta informa MATCH/MISMATCH por dimensión y se conserva en `GET /api/equivalence/{run_id}`.

## Reparación guiada
1. Genera el servicio y ejecútalo solo en un sandbox aislado cuando el entorno de pruebas esté configurado.
2. Ejecuta los mismos casos contra original y reconstruido. Guarda el resultado mediante los endpoints de equivalencia HTTP o de snapshots.
3. Solicita reparación:
   `POST /api/generations/{generation_id}/repair`
   ```json
   {"equivalence_run_id": "ID_DEL_INFORME", "max_files": 5}
   ```
4. Consulta `GET /api/repairs/{repair_id}`. Si termina en `PATCHED_AWAITING_RETEST`, los archivos cambiaron y se guardó una copia previa bajo `repairs/{repair_id}/backup/`.
5. Vuelve a compilar y ejecutar las pruebas en sandbox, compara de nuevo y repite con el nuevo informe si siguen existiendo diferencias.

La reparación solo modifica archivos que figuran en el manifiesto de la generación, limita el número de archivos por ejecución y rechaza rutas no permitidas y contenido con apariencia de secretos. No toca el repositorio original, no ejecuta código ni despliega cambios. Cada parche requiere build/test y nueva comparación. El límite es por ejecución (1-10 archivos); el operador controla el número total de ciclos.

## Seguridad y límites
- Usa entornos aislados y mocks para evitar enviar pagos, correos u otros efectos externos reales.
- La reparación aplica parches al workspace generado; revisa el diff antes de aceptarla.
- No se normalizan UUID/timestamps automáticamente. Define reglas explícitas.
- MATCH solo valida los casos/snapshots recibidos, no demuestra equivalencia universal.

## Windows
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\setup-windows.ps1
Copy-Item .env.example .env
.\\run-windows.ps1
```
Abrir http://127.0.0.1:8000 y API docs http://127.0.0.1:8000/docs.
