# Deep Reverse Engineering & Analysis Orchestrator

Herramienta de **análisis estático de repositorios y grupos de microservicios**. Descubre repositorios desde GitLab, los clona, ejecuta analizadores especializados sobre el código fuente y genera resultados individuales y un informe HTML consolidado.

La aplicación utiliza un **orquestador con módulos analizadores especializados**. No es actualmente un sistema multiagente autónomo: los analizadores no mantienen conversaciones entre sí ni toman decisiones independientes.

## Flujo de funcionamiento

1. **Descubrimiento:** consulta la API de GitLab para listar los proyectos de un grupo, incluyendo subgrupos y excluyendo proyectos archivados.
2. **Clonado:** clona los repositorios HTTPS, incluidos los privados. La autenticación se realiza con un token local y no se incorpora a las URLs, argumentos de Git ni informes.
3. **Análisis individual:** inspecciona cada repositorio con analizadores de inventario, dependencias, análisis funcional, Java/Spring, SQL, contratos y calidad.
4. **Correlación entre repositorios:** consolida resultados y busca relaciones candidatas entre servicios, especialmente en configuración Kafka, productores, consumidores y contratos compartidos.
5. **Calidad:** calcula una puntuación heurística por repositorio y extrae candidatos a posibles bugs con evidencias.
6. **Informe:** genera datos estructurados, un informe Markdown y un HTML conjunto con resumen, puntuaciones, tareas priorizadas y fichas por servicio.

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

El lanzador invoca run-analysis.ps1, que:
1. Lee la configuración local de .env.
2. Comprueba dependencias y prepara el entorno virtual si hace falta.
3. Arranca la API local en el puerto 8001 si no está disponible.
4. Envía el ID configurado a GitLab para descubrir el grupo y sus subgrupos.
5. Espera a que termine el análisis.
6. Descarga el informe HTML en la carpeta configurada, con nombre y marca temporal.
7. Abre el informe en el navegador predeterminado.

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
- app/analysis_orchestrator.py: coordinación del análisis de repositorios.
- app/engines.py: clonado e inventario base.
- app/deep_analysis.py: análisis técnico profundo.
- app/functional_analysis.py: análisis funcional estático.
- app/java_analysis.py: extracción Java/Spring, Kafka, SQL y contratos.
- app/quality_analysis.py: puntuación y candidatos a bugs.
- app/rich_report.py: generación del informe HTML consolidado.
- run-analysis.bat y run-analysis.ps1: ejecución integral de un clic en Windows.
- setup-windows.ps1: preparación manual del entorno.
- run-windows.ps1: arranque manual de la API.

## Desarrollo y pruebas

Instalación:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Ejecución de pruebas:

    .\.venv\Scripts\python.exe -m pytest

La ejecución de pruebas debe realizarse en el entorno de desarrollo; el lanzador de análisis no ejecuta los tests de los microservicios que inspecciona.
