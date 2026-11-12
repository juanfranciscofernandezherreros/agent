# Roadmap de evolución

## Implementado en la versión 3.3
- Generación de código asistida por LLM en workspace separado.
- Comparación HTTP y snapshots de DB, eventos e integraciones.
- Reparación guiada por informe diferencial, limitada a archivos del manifiesto de generación.
- Copia de seguridad por archivo antes de aplicar cambios, historial de reparación y endpoint de consulta.
- Control del número máximo de archivos por ejecución; no se ejecuta código generado.

## Pendiente
1. Capturadores automáticos para PostgreSQL/MySQL/SQLite y brokers/colas.
2. Sandbox aislado para compilar, ejecutar pruebas y revalidar automáticamente cada parche.
3. Orquestación de ciclos de reparación/retest con límite total, criterios de parada y aprobación humana.
4. Proxies de observabilidad para integraciones externas, con modo sandbox/mock y redacción de secretos.
5. Workers durables, cancelación, reintentos e historial de artefactos.

La reparación actual aplica parches LLM en el workspace y queda en estado PATCHED_AWAITING_RETEST. No confirma que el arreglo funciona hasta que un sandbox ejecute build/tests y se repita la comparación. El repositorio original permanece inmutable.
