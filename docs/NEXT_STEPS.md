# Roadmap de evolución

## Implementado en la versión 3.2
- Generación de código asistida por LLM en workspace separado; proveedores OpenAI/Ollama.
- Comparación HTTP diferencial de status y cuerpos.
- Comparación de snapshots de base de datos: esquema, tablas, filas y multiplicidad.
- Comparación ordenada de eventos emitidos y trazas de integraciones (provider, operation, request, response).
- Informe persistido por ejecución con estados VERIFIED/MISMATCH por dimensión y diferencias detalladas.

## Pendiente
1. Capturadores automáticos para PostgreSQL/MySQL/SQLite y brokers/colas.
2. Proxies de observabilidad para integraciones externas, con modo sandbox/mock y redacción de secretos.
3. Sandbox aislado para instalar dependencias, compilar y ejecutar pruebas del código generado.
4. Reparación automática guiada por diferencias y con límite de iteraciones.
5. Workers durables, cancelación, reintentos e historial de artefactos.

La comparación de estado actual consume snapshots JSON exportados: no se conecta todavía a las bases de datos, colas o APIs por sí misma. Ejecuta ambos sistemas con el mismo escenario y usa entornos aislados. No ejecutar código de repositorios o generado sin un sandbox con límites de recursos, red y filesystem.
