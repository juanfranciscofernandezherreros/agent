# Deep Reverse Engineering & Analysis Orchestrator

**Versión 5.4** · Plataforma de análisis estático de arquitectura, comportamiento y calidad para uno o varios microservicios. Permite analizar repositorios individuales, una lista de repositorios o descubrir automáticamente todos los proyectos de un grupo GitLab y sus subgrupos.

El resultado principal es un informe HTML integral, con una vista conjunta del sistema y fichas detalladas por microservicio. La herramienta inspecciona el código y sus artefactos, pero **no ejecuta ni modifica los proyectos analizados**.

## Qué hace

### Descubrimiento y análisis de repositorios
- Clona repositorios Git mediante HTTPS, incluidos repositorios privados.
- Descubre proyectos de un grupo GitLab y de sus subgrupos, excluyendo proyectos archivados.
- Analiza hasta 10.000 proyectos descubiertos desde GitLab por ejecución; las listas manuales admiten hasta 100 repositorios.
- Genera inventario de tecnologías, estructura, dependencias, configuración, despliegue, endpoints candidatos, persistencia, migraciones, seguridad, integraciones y tests detectados.
- Conserva resultados individuales y consolidados para poder revisar cada microservicio y el conjunto completo.

### Análisis técnico y funcional
- Extrae información de Java y Spring: clases, métodos, llamadas, inyección de dependencias, mappings, listeners y productores Kafka.
- Identifica operaciones, ramas, validaciones, manejo de errores, efectos y referencias de llamadas mediante análisis funcional estático.
- Inspecciona SQL, migraciones y contratos Avro/Protocol Buffers.
- Correlaciona indicios de configuración Kafka con consumidores y productores encontrados en el código.
- Identifica posibles topics y contratos compartidos entre repositorios, mostrando las evidencias que sustentan cada correlación.

### Calidad y posibles bugs
- Calcula una **puntuación heurística de calidad de 0 a 100 para cada microservicio** y presenta una visión global del conjunto.
- Explica los factores de puntuación: hallazgos estáticos de prioridad alta/media, tests no detectados, incidencias de parseo e indicadores estáticos de seguridad.
- Busca patrones que podrían indicar bugs, entre ellos excepciones ignoradas, comparaciones sospechosas con valores nulos, marcadores TODO/FIXME/XXX/HACK, uso de assert, comparaciones sospechosas con `is` en Python y credenciales literales.
- Para cada candidato muestra prioridad, microservicio, código del patrón, archivo, línea, fragmento de evidencia y explicación.
- Construye al principio del informe un resumen de las puntuaciones de todos los microservicios, ordenadas de menor a mayor para facilitar la identificación de los que requieren más atención.
- Añade un **plan de tareas priorizado** con los posibles bugs detectados, ordenado por severidad, para facilitar su revisión y seguimiento.

Las puntuaciones y los posibles bugs son señales de priorización basadas en análisis estático. **No son una certificación de calidad ni defectos confirmados**: deben revisarse con el contexto del código y, cuando proceda, reproducirse mediante pruebas.

## Informe HTML

El informe utiliza un título genérico de arquitectura y calidad; el nombre del grupo o análisis aparece como contexto, no como título fijo de producto o proyecto.

Incluye:
- Resumen ejecutivo y puntuación por microservicio.
- Plan de tareas priorizado de posibles bugs, con prioridad y referencias a la evidencia.
- Métricas agregadas y comparación entre repositorios.
- Alcance, metodología, cobertura y limitaciones del análisis.
- Mapa del conjunto de servicios y sus relaciones candidatas.
- Correlaciones Kafka y contratos compartidos con evidencias.
- Riesgos y agenda de validación recomendada.
- Fichas por microservicio con arquitectura, dependencias, endpoints, configuración, persistencia, seguridad, integraciones, comportamiento funcional, tests e incidencias de análisis.
- Catálogo Java filtrable por clase, método, archivo y llamadas.

El diseño es responsive para facilitar la consulta desde escritorio, tablet y móvil.

## Límites y consideraciones

- El análisis es estático: no ejecuta la aplicación, tests, SQL, Maven/Gradle, contenedores ni servicios.
- No modifica los repositorios clonados.
- No lee valores de archivos `.env` ni certifica la configuración efectiva en ejecución.
- La detección de bugs y la puntuación son heurísticas y pueden producir falsos positivos y falsos negativos.
- El parser Java no sustituye al compilador: algunas asociaciones se basan en nombres y proximidad textual, no en resolución semántica completa.
- La presencia de configuración Kafka, consumidores y productores constituye evidencia de posibles relaciones; no demuestra una conexión activa en runtime ni compatibilidad real de payload.
- Los contratos se agrupan por nombre, pero no se realiza una validación formal de compatibilidad ni una comparación completa campo a campo.
- La trazabilidad completa de payloads y la verificación de semánticas de negocio (por ejemplo, UUID o `isLast`) requieren análisis adicional y pruebas específicas.

## Requisitos y configuración

La API se sirve en **`http://127.0.0.1:8001`**. La documentación interactiva está disponible en `http://127.0.0.1:8001/docs`.

En Windows:

```powershell
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run-windows.ps1
```

Para el acceso a GitLab, configura las variables en un archivo local `.env` (no debe subirse al repositorio):

```dotenv
GITLAB_BASE_URL=https://gitlab.six-group.net
GITLAB_TOKEN=<token_personal_de_gitlab>
```

El token debe tener permisos de lectura de API y repositorios (por ejemplo, `read_api` y `read_repository`). No incluyas el token en URLs, peticiones JSON, scripts versionados ni commits. El clonado utiliza autenticación temporal en el entorno del proceso.

Si modificas `.env` mientras la API está levantada, reinicia el proceso para que cargue las nuevas variables.

## Analizar un repositorio

Envía un repositorio a:

```http
POST /api/projects
Content-Type: application/json
```

Ejemplo de cuerpo:

```json
{
  "name": "service-example",
  "git_url": "https://github.com/org/service-example.git"
}
```

Consultar el análisis y los informes:

- `GET /api/projects/{project_id}/analysis`
- `GET /api/projects/{project_id}/report`
- `GET /api/projects/{project_id}/report.html`

## Analizar un grupo GitLab completo

El endpoint descubre automáticamente los proyectos del grupo y sus subgrupos, omite los archivados y lanza el análisis conjunto. No es necesario enumerar manualmente los repositorios.

```http
POST /api/gitlab/groups/{group_id}/analysis
Content-Type: application/json
```

Ejemplo para el grupo 212:

```bash
curl.exe --fail --silent --show-error -X POST "http://127.0.0.1:8001/api/gitlab/groups/212/analysis" -H "Content-Type: application/json" -d "{\"name\":\"platform-analysis\"}"
```

La respuesta incluye `analysis_group_id`. Usa ese identificador para consultar el estado y descargar el informe:

- `GET /api/analysis-groups/{analysis_group_id}`
- `GET /api/analysis-groups/{analysis_group_id}/analysis`
- `GET /api/analysis-groups/{analysis_group_id}/report`
- `GET /api/analysis-groups/{analysis_group_id}/report.html`

## Analizar varios microservicios mediante una lista

También puedes indicar explícitamente los repositorios:

```http
POST /api/analysis-groups
Content-Type: application/json
```

Ejemplo:

```json
{
  "name": "platform-analysis",
  "repositories": [
    {
      "name": "service-one",
      "git_url": "https://github.com/org/service-one.git"
    },
    {
      "name": "service-two",
      "git_url": "https://github.com/org/service-two.git"
    }
  ]
}
```

La lista admite hasta 100 repositorios. Para grupos GitLab, utiliza el endpoint de descubrimiento automático descrito arriba.

## Acceso desde la interfaz

La API interactiva está disponible en `/docs`. Desde ahí puedes consultar los endpoints y lanzar peticiones. No se requiere una API key de LLM.

## Script de conveniencia para Windows

El repositorio incluye `run-billing.bat`, un script de conveniencia preparado para el grupo GitLab 212. Arranca la API en el puerto 8001 si es necesario, solicita el análisis, espera a que termine, descarga el HTML y lo abre en el navegador.

Antes de ejecutarlo:
1. Configura `.env` con `GITLAB_BASE_URL` y `GITLAB_TOKEN`.
2. Asegúrate de que Git y el entorno Python del proyecto están instalados.
3. Ejecuta `run-billing.bat`.

El script conserva el nombre histórico Billing, pero el informe HTML generado tiene un título genérico y utiliza el nombre del análisis como contexto. Para otros grupos o proyectos, utiliza directamente el endpoint de GitLab o la API de grupos.
