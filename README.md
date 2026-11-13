# Deep Reverse Engineering & Analysis Orchestrator

Herramienta de **análisis estático de repositorios y grupos de microservicios**. Descubre repositorios desde GitLab, los clona, ejecuta analizadores especializados sobre el código fuente y genera resultados individuales y un informe HTML consolidado.

La aplicación es un **sistema multiagente coordinado por un supervisor**. Cada analizador es un agente con una interfaz común; el supervisor decide qué agentes ejecutar y en qué orden según sus dependencias, y todos se comunican mediante mensajes JSON publicados en un almacén compartido. Los agentes estáticos son deterministas; los agentes LLM son opcionales y sus conclusiones se contrastan con la evidencia estática mediante validación cruzada.

## Arquitectura multiagente

| Capa | Agentes | Módulo |
|---|---|---|
| Análisis estático (obligatorio) | `inventory`, `deep_analysis`, `functional_analysis`, `java_analysis`, `quality_analysis`, `integration_analysis` (grupo) | `app/agents/` (adaptadores sobre los analizadores originales, sin cambiar su lógica) |
| Agentes inteligentes (opcional, LLM) | `llm_functional_interpretation`, `llm_bug_review`, `llm_architecture_explanation`, `llm_evidence_correlation` (grupo) | `app/agents/llm_agents.py`, `app/llm.py` |
| Validación cruzada | `cross_validation`, `group_cross_validation` (grupo) | `app/agents/validation.py` |
| Histórico de actividad (GitLab) | `activity_analysis`, `group_activity` (grupo) | `app/agents/activity.py`, `app/activity_analysis.py` |
| Documentación | `repository_report`, `group_report` (grupo) | `app/agents/reporting.py`, `app/agent_report.py` |

- **Supervisor** (`app/supervisor.py`): ordena los agentes topológicamente a partir de `requires` (dependencias) y `after` (solo orden), admite ejecutar un subconjunto (`only`) y rechaza ciclos o dependencias desconocidas. Si falla un agente obligatorio, el repositorio se marca como fallido; si falla o se omite uno opcional, el análisis continúa y los agentes que dependían de él se omiten.
- **Comunicación** (`app/communication/`): cada ejecución produce un `AgentMessage` (contrato `1.0`) con estado (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`), duración, payload, evidencias (`repositorio`, `archivo`, `línea`, `confianza`) y errores. El `SharedStore` los guarda en memoria y en `workspaces/<id>/agent-runs/` (`manifest.json` y un JSON por agente y repositorio).
- **Agentes LLM**: desactivados por defecto. Se activan con `LLM_AGENTS_ENABLED=true` y la configuración `LLM_*`. Envían al proveedor resultados del análisis y fragmentos de código con secretos redactados; el contenido del repositorio se trata como dato no confiable. Su salida se marca siempre como `llm_inferred`.
- **Validación cruzada**: compara los analizadores estáticos entre sí (por ejemplo, Kafka o endpoints que ve el analizador Java y no el análisis profundo) y verifica las afirmaciones LLM: citas a archivos o líneas inexistentes, revisiones de bugs que no corresponden a ningún candidato, discrepancias en prioridad alta, integraciones sin respaldo estático y flujos entre servicios no respaldados.
- **Histórico de actividad**: para grupos GitLab, consulta la API (solo lectura) y resume por repositorio las ramas con actividad reciente, los commits por autor y los pushes por usuario; `activity.html` ordena los repositorios por ramas recientes y commits y muestra quién hace más pushes. La ventana es de 90 días (`ACTIVITY_DAYS`).
- **Informe multiagente**: `agents.html` / `agents.md` global y por microservicio, enlazados desde el índice de documentación.

Para añadir un agente: crea una clase que herede de `AnalyzerAgent` (`name`, `requires`, `scope`, `run`) y regístrala en `default_supervisor()`.

## Flujo de funcionamiento

1. **Descubrimiento:** consulta la API de GitLab para listar los proyectos de un grupo, incluyendo subgrupos y excluyendo proyectos archivados.
2. **Clonado:** clona los repositorios HTTPS, incluidos los privados. La autenticación se realiza con un token local y no se incorpora a las URLs, argumentos de Git ni informes.
3. **Análisis individual:** inspecciona cada repositorio con analizadores de inventario, dependencias, análisis funcional, Java/Spring, SQL, contratos y calidad.
4. **Correlación entre repositorios:** consolida resultados y busca relaciones candidatas entre servicios, especialmente en configuración Kafka, productores, consumidores y contratos compartidos.
5. **Calidad:** calcula una puntuación heurística por repositorio y extrae candidatos a posibles bugs con evidencias.
6. **Interpretación LLM (opcional):** interpretación funcional, revisión de candidatos a bugs, explicación arquitectónica y correlación de evidencias entre servicios.
7. **Validación cruzada:** los resultados de unos agentes se contrastan con los de otros y se señalan contradicciones.
8. **Documentación enlazada:** genera un índice HTML navegable, un informe global, fichas HTML por microservicio y expedientes HTML de posibles bugs. Los documentos incluyen enlaces de ida y vuelta y conservan una estructura de carpetas común para poder consultarlos sin conexión.

El análisis no ejecuta ni modifica los repositorios inspeccionados.

## Capacidades

### Descubrimiento y clonado
- Análisis de un repositorio individual mediante URL Git.
- Análisis de una lista explícita de hasta 100 repositorios.
- Descubrimiento automático de proyectos de un grupo GitLab y sus subgrupos mediante include_subgroups.
- Exclusión de proyectos archivados.
- Paginación de GitLab con un límite de seguridad de 10.000 proyectos por ejecución.
- Soporte para GitLab autogestionado o GitLab.com mediante GITLAB_BASE_URL.
- Autenticación de lectura mediante GITLAB_TOKEN.

### Análisis de código y arquitectura
- Inventario de lenguajes, estructura, dependencias, configuración, despliegue y artefactos.
- Detección de endpoints candidatos, persistencia, migraciones, integraciones, indicadores de seguridad y tests detectables.
- Análisis funcional estático de operaciones, ramas, validaciones, errores, efectos y referencias de llamadas.
- Extracción heurística de Java y Spring: clases, métodos, llamadas, inyección de dependencias y mappings.
- Detección de listeners y productores Kafka, configuración relacionada y posibles topics compartidos.
- Inspección de SQL y migraciones.
- Inventario de contratos Avro y Protocol Buffers y agrupación de contratos por nombre.
- Correlación entre repositorios basada en evidencias estáticas.

### Calidad y candidatos a bugs
- Puntuación heurística de 0 a 100 por microservicio.
- Factores de puntuación: hallazgos estáticos de prioridad alta/media, tests no detectados, incidencias de parseo e indicadores estáticos de seguridad.
- Patrones candidatos: excepciones ignoradas, comparaciones sospechosas con valores nulos, marcadores TODO/FIXME/XXX/HACK, uso de assert, comparaciones sospechosas con is en Python y posibles credenciales literales.
- Evidencia de cada candidato: identificador de patrón, prioridad, archivo, línea, fragmento y explicación.
- Resumen de puntuaciones al principio del informe, ordenado de menor a mayor.
- Plan de tareas derivado de los candidatos detectados, ordenado por prioridad.
- Un HTML técnico independiente por cada microservicio analizado, enlazado con el informe global.
- Un HTML de posibles bugs por cada microservicio con candidatos, enlazado con su ficha técnica y el informe global.
- Un índice HTML de documentación que conecta todos los documentos y permite navegar el conjunto sin conexión.

La puntuación no es una certificación ni una probabilidad de defectos. Los candidatos son indicios heurísticos y necesitan revisión humana.

## Informe generado

El informe HTML consolidado incluye:
- Resumen ejecutivo y puntuaciones por microservicio.
- Plan de tareas priorizado de posibles bugs.
- Métricas y comparación entre repositorios.
- Alcance, metodología, cobertura y limitaciones.
- Mapa de servicios y relaciones candidatas.
- Evidencias de correlaciones Kafka y contratos compartidos.
- Riesgos y agenda de validación.
- Fichas detalladas por microservicio: arquitectura, dependencias, endpoints, configuración, persistencia, seguridad, integraciones, comportamiento funcional, tests e incidencias del análisis.
- Catálogo Java filtrable por clase, método, archivo y llamadas.
- Informes individuales de posibles bugs en `workspaces/{analysis_group_id}/bug-reports/`; solo se genera un informe de servicio si hay candidatos.

El diseño HTML es adaptable a escritorio, tablet y móvil. El nombre del grupo o análisis se muestra como contexto del informe; no se utiliza un nombre de proyecto fijo.

## Límites conocidos

- Es análisis estático. No ejecuta la aplicación, pruebas, SQL, Maven, Gradle, contenedores ni servicios.
- No demuestra el comportamiento real en runtime.
- La detección de bugs y la puntuación pueden producir falsos positivos y falsos negativos.
- El parser Java es heurístico y no sustituye al compilador ni a un análisis semántico completo.
- Una coincidencia entre configuración Kafka, productor y consumidor es una relación candidata; no demuestra que estén conectados en ejecución ni que sus payloads sean compatibles.
- Los contratos se agrupan por nombre, pero no se realiza una comparación formal campo a campo ni una validación completa de compatibilidad.
- No se certifican semánticas de negocio ni trazabilidad completa de payloads.
- No se leen los valores de ficheros .env de los repositorios analizados.

## Requisitos

- Windows PowerShell 5.1 o PowerShell 7.
- Python 3.
- Git for Windows.
- Acceso HTTPS a la instancia GitLab.
- Un token GitLab con permisos de lectura de API y repositorios, por ejemplo read_api y read_repository.

La API local escucha en http://127.0.0.1:8001 y publica su documentación interactiva en http://127.0.0.1:8001/docs.

## Configuración

Crea el fichero local .env a partir de .env.example y establece al menos:

    GITLAB_BASE_URL=https://gitlab.com
    GITLAB_TOKEN=<token_de_lectura>
    GITLAB_GROUP_ID=<id_numerico_del_grupo>

Para una instancia autogestionada, sustituye GITLAB_BASE_URL por su URL HTTPS. El identificador del grupo se obtiene de GitLab. Actualmente el endpoint de grupo recibe un identificador compatible con la ruta de la API; se recomienda el ID numérico.

Opcionales:

    ANALYSIS_NAME=
    REPORT_DIR=reports

Si ANALYSIS_NAME está vacío, el lanzador genera un nombre contextual automáticamente. REPORT_DIR define dónde guardar los informes descargados.

No guardes el token en el repositorio, en scripts, URLs, peticiones JSON ni informes. El fichero .env está excluido de Git.

## Ejecución completa con un clic en Windows

La forma recomendada de ejecutar el flujo completo es hacer doble clic en:

    run-analysis.bat

También admite el identificador del grupo como argumento, que tiene prioridad sobre `.env`:

    run-analysis.bat 1118

Es el único lanzador necesario. En la primera ejecución crea `.env` desde la plantilla y lo abre para que pongas el token, prepara el entorno Python e instala las dependencias; después las actualiza solo si cambia `requirements.txt`. Si no hay grupo configurado, lo pregunta. Si encuentra una API arrancada con código anterior a la última actualización, la reinicia.

El lanzador invoca run-analysis.ps1, que:
1. Lee la configuración local de .env.
2. Comprueba dependencias y prepara el entorno virtual si hace falta.
3. Arranca la API local en el puerto 8001 si no está disponible.
4. Envía el ID configurado a GitLab para descubrir el grupo y sus subgrupos.
5. Espera a que termine el análisis.
6. Descarga el informe HTML principal en la carpeta configurada.
7. Descarga un paquete autocontenido con el informe global, todas las fichas de microservicio, los informes de posibles bugs y un índice HTML que enlaza todos los documentos.
8. Abre el índice de documentación en el navegador predeterminado.

Durante el análisis el lanzador muestra una barra de progreso y una línea por repositorio terminado, y descarga los HTML de cada microservicio en cuanto están listos.

**Reanudación:** el análisis y los informes de cada repositorio se guardan en `workspaces/_cache`. En la siguiente ejecución, los repositorios cuyo último commit no ha cambiado se marcan como REUTILIZADO: no se clonan ni se analizan, y su ficha técnica, su informe multiagente y su expediente de bugs se copian tal cual, sin regenerarlos. Lo único que se genera de nuevo es el histórico de Git (`activity.html` de cada repositorio y del grupo) y los documentos globales, incluido el índice con el ranking de microservicios más trabajados. Si un análisis se interrumpe, al relanzarlo continúa a partir de lo ya hecho. Para rehacer todo desde cero, pon `ANALYSIS_CACHE=false` en `.env` o borra `workspaces/_cache`.

**Índice general:** al terminar, el lanzador crea `reports/index.html`, que enlaza todos los análisis descargados (el más reciente primero) y, dentro de cada uno, el índice, el informe global, el histórico de Git, los bugs y los documentos de cada microservicio. Se puede regenerar a mano con `python -m app.reports_index reports`.

No es necesario editar scripts para cambiar de grupo: modifica GITLAB_GROUP_ID en .env. Si ANALYSIS_NAME está vacío, el nombre se genera automáticamente a partir del grupo y la fecha/hora.

Para preparar manualmente el entorno:

    .\setup-windows.ps1

Para arrancar únicamente la API (sin iniciar un análisis):

    .\run-windows.ps1

## API: endpoints principales

### Análisis individual

POST /api/projects

Cuerpo JSON:

    {
      "name": "service-example",
      "git_url": "https://gitlab.com/group/service-example.git"
    }

Consulta:
- GET /api/projects/{project_id}
- GET /api/projects/{project_id}/analysis
- GET /api/projects/{project_id}/report
- GET /api/projects/{project_id}/report.html

### Análisis de un grupo GitLab

POST /api/gitlab/groups/{group_id}/analysis

El cuerpo admite un nombre contextual opcional:

    {
      "name": "optional-analysis-label"
    }

La respuesta contiene analysis_group_id y el número de repositorios descubiertos. Consulta:
- GET /api/analysis-groups/{analysis_group_id}
- GET /api/analysis-groups/{analysis_group_id}/analysis
- GET /api/analysis-groups/{analysis_group_id}/report
- GET /api/analysis-groups/{analysis_group_id}/report.html
- GET /api/analysis-groups/{analysis_group_id}/documentation/index.html
- GET /api/analysis-groups/{analysis_group_id}/repositories/{repository_slug}/report.html

### Lista manual de repositorios

POST /api/analysis-groups

    {
      "name": "optional-analysis-label",
      "repositories": [
        {
          "name": "service-one",
          "git_url": "https://gitlab.com/group/service-one.git"
        },
        {
          "name": "service-two",
          "git_url": "https://gitlab.com/group/service-two.git"
        }
      ]
    }

La lista manual admite hasta 100 repositorios.

## Estructura principal del proyecto

- app/main.py: API, persistencia de trabajos y endpoints de análisis.
- app/gitlab.py: descubrimiento paginado de proyectos GitLab.
- app/analysis_orchestrator.py: prepara el entorno (clonado, almacén compartido) y delega en el supervisor.
- app/supervisor.py: planificación y ejecución de agentes.
- app/agents/: agentes (estáticos, LLM, validación cruzada y documental) con interfaz común.
- app/communication/: contratos JSON, estados, evidencias, errores y almacén compartido.
- app/llm.py: cliente LLM de los agentes inteligentes.
- app/agent_report.py: informe multiagente (Markdown y HTML).
- app/engines.py: clonado e inventario base.
- app/deep_analysis.py: análisis técnico profundo.
- app/functional_analysis.py: análisis funcional estático.
- app/java_analysis.py: extracción Java/Spring, Kafka, SQL y contratos.
- app/quality_analysis.py: puntuación y candidatos a bugs.
- app/rich_report.py: generación del informe HTML consolidado.
- run-analysis.bat y run-analysis.ps1: ejecución integral de un clic en Windows.
- setup-windows.ps1: preparación manual del entorno.
- start-windows.bat y run-windows.ps1: arranque de la API sola (desarrollo); no lanza ningún análisis.

## Desarrollo y pruebas

Instalación:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Ejecución de pruebas:

    .\.venv\Scripts\python.exe -m pytest

La ejecución de pruebas debe realizarse en el entorno de desarrollo; el lanzador de análisis no ejecuta los tests de los microservicios que inspecciona.
