# Analizador de arquitectura y calidad de microservicios

Herramienta local que analiza todos los repositorios de un grupo de GitLab y genera documentación HTML navegable: arquitectura de cada servicio, relaciones entre servicios, posibles bugs y actividad reciente en Git.

Se lanza con un doble clic, trabaja en tu máquina y solo lee los repositorios: no ejecuta su código, no los modifica y no sube nada a ningún sitio, salvo que actives expresamente los agentes LLM.

```
run-analysis.bat 1118
```

## Qué obtienes

Al terminar se abre un índice desde el que se llega a todo:

| Documento | Contenido |
|---|---|
| Índice del análisis | Ranking de los microservicios más trabajados, enlaces a todos los documentos y lista seleccionable de posibles bugs |
| Informe global | Visión de conjunto: servicios, tecnologías, relaciones candidatas entre servicios y puntuaciones de calidad |
| Ficha técnica (una por servicio) | Lenguajes, estructura, dependencias, endpoints, configuración, persistencia, integraciones y catálogo de clases Java |
| Posibles bugs (uno por servicio) | Cada candidato con su prioridad, archivo, línea, fragmento de código y explicación |
| Histórico de Git (global y por servicio) | Ramas con actividad reciente, commits por autor y pushes por usuario |
| Informe multiagente (global y por servicio) | Qué análisis se ejecutaron, contradicciones detectadas entre ellos y, si están activos, las interpretaciones del LLM |

Todos los documentos son HTML estático con enlaces relativos: la carpeta `reports` se puede copiar o compartir y sigue funcionando sin conexión. `reports/index.html` enlaza todos los análisis que hayas hecho, el más reciente primero.

## Puesta en marcha

Requisitos: Windows con PowerShell 5.1 o superior, Python 3.10 o superior, Git for Windows y un token de GitLab con permisos `read_api` y `read_repository`.

1. Clona este repositorio.
2. Haz doble clic en `run-analysis.bat`.
3. La primera vez se crea `.env` y se abre en el Bloc de notas: pon tu `GITLAB_TOKEN` (y `GITLAB_BASE_URL` si tu GitLab no es gitlab.com), guarda y cierra.
4. Si no has indicado `GITLAB_GROUP_ID`, elige un grupo de la lista que Agent obtiene de GitLab.
5. Elige todos los repositorios/microservicios del grupo o selecciona algunos por número.

El lanzador se encarga del resto: prepara el entorno Python, instala dependencias, arranca la API local, permite seleccionar grupo y repositorios/microservicios y abre la documentación.

```
run-analysis.bat                 muestra los grupos GitLab y permite seleccionar repositorios
run-analysis.bat 1118            usa el grupo 1118 y permite elegir sus repositorios
run-analysis.bat 1118 -Llm claude -Model claude-sonnet-5-5     con agentes LLM
run-analysis.bat -ListModels     lista los modelos del proveedor LLM configurado
```

Durante el análisis se ve una barra de progreso y una línea por repositorio terminado. Los informes de cada servicio se descargan en cuanto están listos.

## Configuración (`.env`)

| Variable | Para qué sirve | Por defecto |
|---|---|---|
| `GITLAB_BASE_URL` | URL de tu GitLab | `https://gitlab.com` |
| `GITLAB_TOKEN` | Token de lectura. Obligatorio | |
| `GITLAB_GROUP_ID` | Grupo que se analiza si no se pasa como argumento | |
| `REPORT_DIR` | Carpeta donde se guardan los informes | `reports` |
| `ANALYSIS_NAME` | Nombre del análisis; si se deja vacío se genera con el grupo y la fecha | |
| `ANALYSIS_CACHE` | Reutilizar el análisis de los repositorios que no han cambiado | `true` |
| `ACTIVITY_DAYS` | Días que se consideran "actividad reciente" en Git | `90` |
| `LLM_AGENTS_ENABLED` | Activar los agentes LLM | `false` |

El token se lee de `.env` en cada ejecución. No se guarda en la base de datos, ni en las URLs o argumentos de Git, ni en los informes. `.env` está excluido de Git.

## Ejecuciones repetidas

El análisis de cada repositorio se guarda en `workspaces/_cache`. En la siguiente ejecución, los repositorios cuyo último commit no ha cambiado aparecen como `REUTILIZADO`: no se clonan ni se analizan, y su ficha, su informe multiagente y su expediente de bugs se copian tal cual.

Lo que se genera siempre de nuevo es el histórico de Git y los documentos globales, incluido el índice con el ranking, porque la actividad cambia aunque el código no lo haga.

Si un análisis se interrumpe, al relanzarlo continúa a partir de lo que ya estaba hecho. Para forzar un análisis completo, pon `ANALYSIS_CACHE=false` o borra `workspaces/_cache`. La caché también se descarta al actualizar la herramienta o al cambiar de proveedor o modelo LLM.

## Qué se analiza

**Por repositorio**

- Inventario: lenguajes, estructura, manifiestos de dependencias, configuración y despliegue.
- Arquitectura: endpoints candidatos, modelos de datos, migraciones, integraciones (bases de datos, mensajería, APIs externas), indicadores de seguridad y tests detectables.
- Comportamiento: operaciones, ramas, validaciones, errores y cambios de estado que se deducen del código.
- Java y Spring: clases, métodos, llamadas, inyección de dependencias, endpoints, listeners y productores Kafka, sentencias SQL y contratos Avro o Protocol Buffers.
- Calidad: puntuación de 0 a 100 y candidatos a bug, entre ellos excepciones ignoradas, comparaciones sospechosas con nulos, marcadores `TODO`/`FIXME`, uso de `assert` y posibles credenciales literales.
- Actividad en Git, consultando la API de GitLab: ramas con commits recientes, commits por autor y pushes por usuario.

**Entre repositorios**

- Topics de Kafka con sus productores y consumidores candidatos.
- Contratos que aparecen en más de un servicio.
- Ranking de servicios por commits, ramas recientes y pushes, y usuarios más activos.

**Validación cruzada**

Los resultados de unos análisis se comparan con los de otros y las discrepancias se muestran en el informe multiagente. Por ejemplo: Kafka o endpoints que detecta el analizador Java y no el de arquitectura, o hallazgos que apuntan a archivos que no están en el inventario. Si los agentes LLM están activos, también se comprueba que cada archivo y línea que citan existe de verdad.

## Agentes LLM (opcional)

Están desactivados por defecto y la herramienta es plenamente útil sin ellos. Al activarlos se añaden cuatro interpretaciones: qué hace funcionalmente cada servicio, una revisión de cada candidato a bug (bug probable, falso positivo o requiere revisión), una explicación de la arquitectura y los flujos de datos probables entre servicios.

Funcionan sobre LangChain, así que el proveedor y el modelo se eligen en `.env` sin tocar código:

```
LLM_AGENTS_ENABLED=true
LLM_PROVIDER=claude
LLM_MODEL=claude-sonnet-5-5
```

| Proveedor | `LLM_PROVIDER` | Clave en `.env` |
|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Claude (Anthropic) | `claude` | `ANTHROPIC_API_KEY` |
| Gemini (Google) | `gemini` | `GOOGLE_API_KEY` |
| Ollama (local) | `ollama` | No necesita. El modelo debe estar descargado con `ollama pull` |

Se pueden dejar varias claves puestas y cambiar solo `LLM_PROVIDER` y `LLM_MODEL`, o elegirlos al lanzar con `-Llm` y `-Model`. Si falta la clave específica se usa `LLM_API_KEY`.

`LLM_MODEL` es obligatorio y no tiene valor por defecto, porque los identificadores de modelo cambian con frecuencia. `run-analysis.bat -ListModels` muestra los que ofrece tu cuenta. Para comprobar la conexión con una llamada mínima:

```
.\.venv\Scripts\python.exe -m app.llm --test
```

Otras opciones: `OLLAMA_BASE_URL` (por defecto `http://127.0.0.1:11434`), `LLM_BASE_URL` para servicios compatibles con la API de OpenAI, `LLM_MAX_TOKENS` (8000), `LLM_TIMEOUT_SECONDS` (120) y `LLM_TEMPERATURE`.

**Privacidad.** Con los agentes LLM activos se envían al proveedor elegido resultados del análisis y fragmentos de código. Antes de enviarlos se redactan contraseñas, claves y tokens reconocibles, pero el resto del código viaja tal cual. Si eso no es aceptable para tu código, usa Ollama, que se ejecuta en local, o deja los agentes desactivados.

**Fiabilidad.** Lo que escribe el LLM es una interpretación, no un hecho comprobado, y así se etiqueta en los informes. Si un agente LLM falla, el resto del análisis termina igualmente y el error queda registrado.

## Cómo funciona por dentro

Cada análisis es un *agente*: un módulo con una única responsabilidad que declara de qué otros depende. Un supervisor calcula el orden de ejecución a partir de esas dependencias. Los agentes no se llaman entre sí: publican su resultado como un mensaje JSON con estado, evidencias y errores en un almacén compartido, que queda en `workspaces/<id>/agent-runs/`.

| Grupo | Agentes | Usa IA |
|---|---|---|
| Análisis estático | `inventory`, `deep_analysis`, `functional_analysis`, `java_analysis`, `quality_analysis`, `integration_analysis` | No |
| Actividad en Git | `activity_analysis`, `group_activity` | No |
| Validación cruzada | `cross_validation`, `group_cross_validation` | No |
| Interpretación | `llm_functional_interpretation`, `llm_bug_review`, `llm_architecture_explanation`, `llm_evidence_correlation` | Sí, opcional |
| Documentación | `repository_report`, `group_report` | No |

Conviene no sobreentender el término: salvo los cuatro de interpretación, los agentes son código determinista. El supervisor sigue un plan fijo y los agentes no dialogan entre ellos.

Si falla un agente obligatorio, ese repositorio se marca como fallido y el análisis continúa con los demás. Si falla o se omite uno opcional (LLM, actividad, validación), el repositorio se completa sin esa parte.

Para añadir un análisis nuevo, crea una clase que herede de `AnalyzerAgent` en `app/agents/` con su `name`, sus `requires` y su método `run`, y regístrala en `default_supervisor()` (`app/supervisor.py`).

## Límites

- **Es análisis estático.** No se ejecuta la aplicación, ni sus tests, ni SQL, ni compilaciones. Nada de lo que aparece en los informes está comprobado en ejecución.
- **Los posibles bugs son indicios.** Se detectan por patrones y habrá falsos positivos y falsos negativos. Requieren revisión de una persona.
- **La puntuación de calidad es orientativa.** Sirve para comparar servicios entre sí; no es una certificación ni una probabilidad de fallo.
- **El análisis de Java es heurístico.** No sustituye al compilador y puede perder o malinterpretar construcciones complejas.
- **Las relaciones entre servicios son candidatas.** Que un servicio produzca en un topic y otro consuma de uno con el mismo nombre no demuestra que estén conectados ni que sus mensajes sean compatibles.
- **El histórico de Git solo existe para grupos GitLab** y cubre la ventana configurada. Los pushes salen de los eventos de GitLab, que se conservan durante un tiempo limitado. Commits y pushes identifican a las personas de forma distinta (nombre en Git frente a cuenta de GitLab).
- **Solo se analiza la rama por defecto** de cada repositorio, en su último commit.
- **El botón "Enviar" de la selección de bugs todavía no hace nada.** La lista y la selección funcionan; el envío está pendiente (ver `docs/NEXT_STEPS.md`).
- **El lanzador es para Windows.** En otros sistemas la API funciona, pero hay que arrancarla y usarla a mano.

## Uso de la API

El lanzador usa una API local en `http://127.0.0.1:8001`, con documentación interactiva en `/docs`. Se puede usar directamente, por ejemplo para analizar repositorios que no están en GitLab:

```
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

| Operación | Endpoint |
|---|---|
| Listar grupos visibles de GitLab | `GET /api/gitlab/groups` |
| Listar repositorios de un grupo | `GET /api/gitlab/groups/{group_id}/projects` |
| Analizar todos o proyectos seleccionados de un grupo | `POST /api/gitlab/groups/{group_id}/analysis` (`project_ids` opcional) |
| Analizar una lista de hasta 100 repositorios (`name`, `git_url` HTTPS) | `POST /api/analysis-groups` |
| Analizar un único repositorio | `POST /api/projects` |
| Progreso de un análisis | `GET /api/analysis-groups/{id}/progress` |
| Resultado completo en JSON | `GET /api/analysis-groups/{id}/analysis` |
| Estado de cada agente | `GET /api/analysis-groups/{id}/agent-runs` |
| Índice de documentación | `GET /api/analysis-groups/{id}/documentation/index.html` |
| Configuración LLM activa, sin claves | `GET /api/llm` |
| Modelos del proveedor | `GET /api/llm/models` |

Con una lista manual de repositorios no hay histórico de Git, porque esos datos salen de la API de GitLab.

## Estructura del proyecto

```
run-analysis.bat            único punto de entrada
run-analysis.ps1            flujo del lanzador
setup-windows.ps1           preparación del entorno Python
app/
  main.py                   API y gestión de trabajos
  gitlab.py                 descubrimiento de proyectos del grupo
  analysis_orchestrator.py  clonado, caché, progreso y llamada al supervisor
  supervisor.py             planificación y ejecución de agentes
  agents/                   agentes: estáticos, actividad, LLM, validación y documentación
  communication/            mensajes entre agentes y almacén compartido
  llm.py                    cliente LLM sobre LangChain
  *_analysis.py             lógica de cada analizador
  rich_report.py, documentation.py, agent_report.py, bug_report.py, reports_index.py   generación de HTML
tests/                      pruebas automáticas
workspaces/                 clones, resultados y caché (no se versiona)
reports/                    documentación descargada (no se versiona)
```

## Desarrollo

```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
.\.venv\Scripts\python.exe -m pytest
```

Las pruebas no necesitan red, ni GitLab, ni claves de ningún proveedor: usan repositorios de ejemplo y respuestas simuladas. Eso significa que la integración con un GitLab real y con cada proveedor LLM depende de tu entorno; la forma de comprobarla es ejecutar un análisis y, para el LLM, `python -m app.llm --test`.

Si algo falla al lanzar, el mensaje aparece en la ventana y el detalle de la API queda en `logs/api.stderr.log`.
