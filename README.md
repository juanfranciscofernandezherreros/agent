# Deep Reverse Engineering & Analysis Orchestrator

Versión 5.1: plataforma de análisis estático profundo para uno o varios microservicios. Coordina inventario, análisis funcional, extracción Java/Spring, SQL, Kafka/Avro y correlación entre repositorios. No ejecuta ni modifica el código analizado.

## Capacidades
- Clonado Git HTTPS aislado por repositorio.
- Inventario, dependencias, despliegue, configuración, endpoints candidatos, seguridad, integraciones, migraciones y tests.
- Análisis funcional estático: operaciones, ramas, validaciones, errores, efectos y referencias de llamadas.
- Parser Java heurístico: clases, métodos, llamadas por nombre, inyección de dependencias, mappings Spring, listeners/productores Kafka, SQL y contratos Avro/Proto.
- Análisis coordinado de hasta 10 repositorios en una ejecución: candidatos de topics y contratos compartidos.
- Informes HTML integrales y por microservicio: resumen ejecutivo, arquitectura, flujo, integraciones, API, configuración, seguridad, persistencia, reglas/ramas inferidas, errores, inventario Java clase/método filtrable, riesgos y limitaciones. También se generan JSON y Markdown.

## Límites
El parser Java no sustituye a javac ni resuelve el grafo completo de tipos, sobrecargas, proxies Spring o dispatch dinámico. Las coincidencias de topic/contrato son candidatos, no prueba de conexión o compatibilidad. El informe HTML estructura la evidencia disponible; el mapeo de payload campo a campo, la semántica de isLast/UUID y la compatibilidad real de schemas requieren extracción/validación adicional y no se deben dar por demostrados. No se ejecutan tests, SQL, Maven/Gradle, contenedores ni servicios. No se leen valores .env. El análisis no certifica comportamiento runtime.

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
