# Software Reconstruction Platform — Analysis Edition

La aplicación se centra exclusivamente en descargar y analizar en profundidad un microservicio. La versión 4.1 añade análisis funcional estático y exportación HTML.

## Qué hace

1. Clona un repositorio Git mediante HTTPS en un workspace separado.
2. Inventaría archivos, tamaños, lenguajes y manifiestos.
3. Detecta candidatos de arquitectura, puntos de entrada, rutas HTTP, modelos de datos, migraciones, dependencias, configuración, variables de entorno, tests, seguridad e integraciones.
4. Genera cuatro artefactos:
   - workspaces/<project_id>/analysis.json: análisis estructurado con evidencias.
   - workspaces/<project_id>/analysis.md: informe legible.\n   - workspaces/<project_id>/analysis.html: informe HTML autocontenido, apto para abrir en navegador o cargar en otra herramienta.\n   - El análisis funcional identifica operaciones, ramas condicionales, validaciones, errores, posibles efectos sobre estado y referencias de llamadas, con fichero, línea y confianza.
5. Conserva el estado del análisis en SQLite para consultarlo mediante API.

## Lo que NO hace

- No genera ni modifica código del microservicio.
- No ejecuta el código descargado.
- No realiza pruebas dinámicas ni confirma comportamiento en runtime.
- No reconstruye ni compara una nueva implementación.
- No necesita una API key de OpenAI para el análisis estático.

Las detecciones de endpoints, seguridad, modelos, integraciones y comportamiento funcional son inferencias estáticas respaldadas por referencias a fichero y línea. La confianza se indica por detección; no debe interpretarse como una especificación funcional validada. Deben revisarse; los patrones estáticos no descubren necesariamente código dinámico, configuración externa o comportamiento oculto.

## Windows

    git pull origin main
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\run-windows.ps1

No es necesario configurar .env ni una API key para este modo.

## Uso

Comprueba el estado:

GET http://127.0.0.1:8000/health

Crea un análisis enviando POST a:

http://127.0.0.1:8000/api/projects

Body JSON:

    {
      "name": "mi-microservicio",
      "git_url": "https://github.com/usuario/repositorio.git"
    }

La respuesta devuelve project_id. Consulta el estado con:

GET /api/projects/{project_id}

Consulta el análisis estructurado:

GET /api/projects/{project_id}/analysis

Obtén el informe Markdown:

GET /api/projects/{project_id}/report

La documentación interactiva de la API está en http://127.0.0.1:8000/docs.
