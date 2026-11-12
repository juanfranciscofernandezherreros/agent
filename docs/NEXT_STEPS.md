# Roadmap de evolución

## Implementado en la versión 3.1
- Generación de código asistida por LLM: planificación de archivos y generación de contenido en un workspace separado.
- Proveedores configurables: OpenAI y Ollama mediante API compatible con Chat Completions.
- Registro de ejecuciones, consulta de estado e informe de archivos.
- Protección inicial frente a rutas inseguras, archivos de secretos y prompt injection en el contexto del repositorio.
- El código generado no se ejecuta automáticamente.

## Pendiente
1. Sandbox aislado para instalar dependencias, compilar y ejecutar pruebas del código generado.
2. Comparación de bases de datos, eventos, colas e integraciones.
3. Reparación automática guiada por diferencias y con límite de iteraciones.
4. Análisis semántico y dinámico más profundo del repositorio original.
5. Workers durables, cancelación, reintentos e historial de artefactos.

No ejecutar código de repositorios o generado sin un sandbox con límites de recursos, red y filesystem.
