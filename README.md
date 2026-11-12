# Deep Reverse Engineering & Analysis Orchestrator

Versión 5.3: plataforma de análisis estático profundo para uno o varios microservicios. Coordina inventario, análisis funcional, extracción Java/Spring, SQL, Kafka/Avro y correlación entre repositorios. No ejecuta ni modifica el código analizado.

## Capacidades
- Clonado Git HTTPS aislado por repositorio, con autenticación privada GitLab sin incrustar tokens en URLs, argumentos ni informes.
- Descubrimiento automático de todos los proyectos no archivados de un grupo GitLab, incluidos subgrupos, con paginación de API (hasta 10.000 repositorios por ejecución).
- Inventario, dependencias, despliegue, configuración, endpoints candidatos, seguridad, integraciones, migraciones y tests.
- Análisis funcional estático: operaciones, ramas, validaciones, errores, efectos y referencias de llamadas.
- Parser Java heurístico: clases, métodos, llamadas por nombre, inyección de dependencias, mappings Spring, listeners/productores Kafka, SQL y contratos Avro/Proto.
- Análisis coordinado de hasta 10 repositorios en una ejecución: candidatos de topics y contratos compartidos.
- Informes HTML integrales y por microservicio con diseño editorial, índice navegable, métricas, mapa de servicios, cobertura y límites, integración Kafka/contratos con evidencias, riesgos y agenda de validación.
- Fichas detalladas por microservicio: arquitectura, dependencias, endpoints, configuración, persistencia, seguridad, integraciones, comportamiento funcional, tests, incidencias del parser y catálogo Java filtrable por clase/método/archivo/llamadas.
- Correlación Kafka enriquecida con evidencias de configuración, listeners consumidores y expresiones productoras. La presencia de ambos roles se marca como candidato, nunca como conexión runtime demostrada.

## Límites
El parser Java sigue siendo heurístico: las llamadas se asocian por nombre y la asociación método-clase usa la declaración de clase anterior más cercana, no resolución semántica del compilador. La correlación Kafka ahora separa indicios de configuración, consumidores y productores, pero no demuestra conexión activa ni compatibilidad de payload. Los contratos se agrupan por nombre, sin comparación formal campo a campo. El informe documenta la evidencia disponible y diferencia hallazgos, inferencias y pendientes; la trazabilidad completa de payloads, la semántica de isLast/UUID y la validación de schemas requieren extracción y pruebas adicionales. No se ejecutan tests, SQL, Maven/Gradle, contenedores ni servicios. No se leen valores .env ni se certifica comportamiento runtime.

## Windows
    git pull origin main
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\run-windows.ps1

## Analizar un repositorio
POST /api/projects

    {"name":"billing-watcher","git_url":"https://github.com/org/billing-watcher.git"}

Consultar:
- GET /api/projects/{project_id}/analysis
- GET /api/projects/{project_id}/report
- GET /api/projects/{project_id}/report.html

## Analizar un grupo completo de GitLab (descubrimiento automático)
Configura una sola vez las variables locales `GITLAB_BASE_URL` y `GITLAB_TOKEN` en `.env` (el archivo está ignorado por Git):

    GITLAB_BASE_URL=https://gitlab.six-group.net
    GITLAB_TOKEN=\u003ctoken_personal_de_gitlab\u003e

El token debe tener permiso de lectura de API y repositorios (`read_api` y `read_repository`). No lo incluyas en JSON, BAT, URL ni commits. El endpoint descubre automáticamente los proyectos del grupo y sus subgrupos, omite archivados y clona cada repositorio privado con autenticación temporal en el entorno del proceso:

    curl.exe --fail --silent --show-error -X POST "http://127.0.0.1:8001/api/gitlab/groups/212/analysis" -H "Content-Type: application/json" -d "{\"name\":\"billing-platform\"}"

La respuesta incluye `analysis_group_id`. Consulta el estado con `GET /api/analysis-groups/{analysis_group_id}` y descarga el informe con `GET /api/analysis-groups/{analysis_group_id}/report.html`. También se puede lanzar desde `/docs`. El límite por ejecución es de 100 repositorios para listas manuales y 10.000 para descubrimiento GitLab.

## Analizar varios microservicios conjuntamente
POST /api/analysis-groups

    {
      "name":"billing-platform",
      "repositories":[
        {"name":"billing-watcher","git_url":"https://github.com/org/billing-watcher.git"},
        {"name":"billing-report-writer","git_url":"https://github.com/org/billing-report-writer.git"}
      ]
    }

Consultar:
- GET /api/analysis-groups/{analysis_group_id}
- GET /api/analysis-groups/{analysis_group_id}/analysis
- GET /api/analysis-groups/{analysis_group_id}/report
- GET /api/analysis-groups/{analysis_group_id}/report.html

La API interactiva está en /docs. No requiere API key de LLM.


## Generar y abrir el informe integral de Billing en Windows
Ejecuta únicamente `run-billing.bat` con doble clic: si falta el entorno Python, el propio BAT ejecuta la instalación; después comprueba si la API está activa y, si no lo está, la arranca en el puerto 8001. Cuando la API responde, envía `billing-platform-full-analysis.json` mediante `curl` a `POST /api/analysis-groups`, espera a que termine el análisis, descarga el informe HTML y lo abre. El JSON utiliza los dos repositorios privados de GitLab SIX; el equipo debe tener acceso y credenciales GitLab configuradas para clonarlos.
