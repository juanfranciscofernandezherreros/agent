from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import PurePosixPath


def _e(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def _loc(item):
    file = item.get("file") or item.get("path") or ""
    line = item.get("line") or item.get("start_line")
    return file + (":" + str(line) if line else "")


def _table(items, columns, empty="No se han encontrado evidencias estáticas para este apartado."):
    if not items:
        return '<p class="muted">' + _e(empty) + '</p>'
    head = "".join("<th>" + _e(label) + "</th>" for _, label in columns)
    rows = []
    for item in items:
        cells = []
        for key, _ in columns:
            value = item.get(key, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2)
            cells.append("<td>" + _e(value) + "</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<div class='table-wrap'><table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"


def _evidence_table(items):
    return _table(items, [("kind", "Tipo"), ("file", "Archivo"), ("line", "Línea"), ("excerpt", "Evidencia")])


def _service_section(repo):
    name = repo.get("name", "Microservicio")
    inv = repo.get("inventory", {})
    deep = repo.get("deep_analysis", {})
    func = repo.get("functional_analysis", {})
    java = repo.get("java_analysis", {})
    stats = deep.get("scan_stats", {})
    js = java.get("summary", {})
    fs = func.get("summary", {})
    metrics = [
        ("Archivos", stats.get("files_seen", inv.get("file_count_scanned", 0))),
        ("Clases Java", js.get("classes", 0)),
        ("Métodos Java", js.get("methods", 0)),
        ("Reglas/ramas", fs.get("business_rules", 0)),
        ("SQL", js.get("sql_statements", 0)),
        ("Listeners Kafka", js.get("kafka_listeners", 0)),
    ]
    cards = "".join("<div class='metric'><b>" + _e(v) + "</b><span>" + _e(k) + "</span></div>" for k, v in metrics)
    arch = deep.get("architecture", {})
    deps = deep.get("dependencies", {})
    cfg = deep.get("configuration", {})
    integration = deep.get("integrations", {})
    security = deep.get("security", {})
    parts = ["<section id='svc-" + _e(name) + "'><h2>Microservicio: " + _e(name) + "</h2>",
             "<div class='metrics'>" + cards + "</div>",
             "<h3>Arquitectura y estructura</h3>",
             "<p><b>Directorios:</b> " + _e(", ".join(arch.get("top_level_directories", [])) or "No identificados") + "</p>",
             "<p><b>Puntos de entrada:</b> " + _e(", ".join(arch.get("entrypoints", [])) or "No identificados") + "</p>",
             "<p><b>Artefactos de despliegue:</b> " + _e(", ".join(arch.get("deployment_files", [])) or "No identificados") + "</p>",
             "<p><b>Manifiestos:</b> " + _e(", ".join(deps.get("manifests", [])) or "No identificados") + "</p>",
             "<p><b>Commit:</b> <code>" + _e(inv.get("commit_sha", "no disponible")) + "</code></p>",
             "<h3>API y endpoints candidatos</h3>",
             _table(deep.get("api", {}).get("route_candidates", []), [("framework", "Framework"), ("method", "Método"), ("path", "Ruta"), ("file", "Archivo"), ("line", "Línea")]),
             "<h3>Configuración</h3>",
             "<p><b>Archivos:</b> " + _e(", ".join(cfg.get("files", [])) or "No identificados") + "</p>",
             "<p><b>Nombres de variables:</b> " + _e(", ".join(cfg.get("environment_variable_names", [])) or "No identificados") + "</p>",
             "<h3>Dependencias declaradas</h3>",
             _table(deps.get("package_json_dependencies", []), [("name", "Dependencia"), ("version", "Versión"), ("group", "Grupo"), ("file", "Manifiesto")]),
             "<h3>Persistencia, modelos y migraciones</h3>",
             "<p><b>Migraciones:</b> " + _e(", ".join(deep.get("data", {}).get("migration_files", [])) or "No identificadas") + "</p>",
             _evidence_table(deep.get("data", {}).get("model_candidates", [])),
             "<h3>Seguridad: indicios encontrados</h3>"]
    for key, values in security.items():
        parts.append("<h4>" + _e(key.replace("_", " ").title()) + " (" + str(len(values)) + ")</h4>" + _evidence_table(values[:100]))
    parts.append("<h3>Integraciones externas</h3>")
    for key, values in integration.items():
        parts.append("<h4>" + _e(key.replace("_", " ").title()) + " (" + str(len(values)) + ")</h4>" + _evidence_table(values[:100]))
    parts.append("<h3>Comportamiento funcional inferido</h3>")
    for key, label in [("operations", "Operaciones"), ("business_rules", "Reglas y ramas"), ("validations", "Validaciones"),
                       ("error_handling", "Gestión de errores"), ("state_changes", "Efectos y cambios de estado")]:
        items = func.get(key, [])
        parts.append("<h4>" + label + " (" + str(len(items)) + ")</h4>" +
                     _table(items[:300], [("name", "Operación"), ("operation", "Contexto"), ("description", "Descripción"),
                                          ("file", "Archivo"), ("line", "Línea"), ("confidence", "Confianza"), ("evidence", "Evidencia")]))
    parts.append("<h3>Java / Spring: catálogo de clases y métodos</h3>")
    classes = java.get("classes", [])
    methods_by_file = {}
    for method in java.get("methods", []):
        methods_by_file.setdefault(method.get("file"), []).append(method)
    cards = []
    for cls in classes:
        methods = methods_by_file.get(cls.get("file"), [])
        method_html = "".join("<li><code>" + _e(m.get("name")) + "(" + _e(m.get("parameters")) + ")</code> · líneas " +
                              _e(m.get("line")) + "–" + _e(m.get("end_line")) + "<br><small>Llamadas: " +
                              _e(", ".join(m.get("calls", [])[:15])) + " · Efectos posibles: " +
                              _e(", ".join(m.get("possible_effects", []))) + "</small></li>" for m in methods)
        cards.append("<article class='class-card' data-search='" + _e((cls.get("name", "") + " " + cls.get("file", "") + " " + " ".join(m.get("name", "") for m in methods)).lower()) +
                     "'><div class='meta'>" + _e(cls.get("kind")) + " · " + _e(cls.get("file")) + ":" + _e(cls.get("line")) +
                     "</div><h4>" + _e(cls.get("name")) + "</h4><details><summary>" + str(len(methods)) +
                     " métodos detectados</summary><ul>" + (method_html or "<li>Sin métodos detectados por el parser.</li>") + "</ul></details></article>")
    parts.append("<input class='class-search' placeholder='Filtrar clases, métodos o rutas...' oninput='filterClasses(this)'><div class='class-grid'>" +
                 "".join(cards) + "</div>")
    for key, label, cols in [
        ("spring_endpoints", "Anotaciones Spring / endpoints", [("annotation", "Anotación"), ("arguments", "Argumentos"), ("file", "Archivo"), ("line", "Línea")]),
        ("kafka_listeners", "Kafka listeners", [("arguments", "Topic / expresión"), ("file", "Archivo"), ("line", "Línea")]),
        ("kafka_producers", "Productores Kafka candidatos", [("expression", "Expresión"), ("file", "Archivo"), ("line", "Línea")]),
        ("sql_statements", "Operaciones SQL", [("operation", "Operación"), ("excerpt", "SQL / fragmento"), ("file", "Archivo"), ("line", "Línea")]),
        ("avro_contracts", "Contratos Avro / Proto", [("name", "Tipo"), ("format", "Formato"), ("file", "Archivo"), ("line", "Línea")]),
    ]:
        parts.append("<h3>" + label + "</h3>" + _table(java.get(key, []), cols))
    parts.append("</section>")
    return "".join(parts)


def build_integral_html(name, analysis):
    repos = analysis.get("repositories", [])
    integration = analysis.get("integration_analysis", {})
    total_classes = sum(r.get("java_analysis", {}).get("summary", {}).get("classes", 0) for r in repos)
    total_methods = sum(r.get("java_analysis", {}).get("summary", {}).get("methods", 0) for r in repos)
    total_rules = sum(r.get("functional_analysis", {}).get("summary", {}).get("business_rules", 0) for r in repos)
    total_sql = sum(r.get("java_analysis", {}).get("summary", {}).get("sql_statements", 0) for r in repos)
    topics = integration.get("topic_candidates", [])
    contracts = integration.get("shared_contract_candidates", [])
    flow_nodes = "".join("<div class='flow-node'><b>" + _e(r.get("name")) + "</b><span>Clases " +
                         str(r.get("java_analysis", {}).get("summary", {}).get("classes", 0)) + " · Métodos " +
                         str(r.get("java_analysis", {}).get("summary", {}).get("methods", 0)) + "</span></div>" for r in repos)
    topic_rows = _table(topics, [("topic", "Topic candidato"), ("repositories", "Repositorios implicados"), ("cross_service_candidate", "Coincidencia entre servicios")])
    contract_rows = _table(contracts, [("contract", "Contrato candidato"), ("repositories", "Repositorios implicados"), ("cross_service_candidate", "Coincidencia entre servicios")])
    risks = []
    if not topics:
        risks.append(("Integración Kafka no demostrada", "No se han correlacionado topics de forma estática. Revisar configuración externa, constantes y bindings."))
    else:
        risks.append(("Compatibilidad Kafka pendiente", "La coincidencia de nombres de topics no demuestra que productores y consumidores compartan el mismo contrato ni que el flujo esté activo."))
    if not contracts:
        risks.append(("Contratos de mensajes no correlacionados", "No se detectaron contratos Avro/Proto compartidos. Verificar schemas externos, Schema Registry y dependencias generadas."))
    else:
        risks.append(("Compatibilidad de schemas pendiente", "Los nombres coincidentes no sustituyen una comparación campo a campo ni una comprobación de compatibilidad del registry."))
    risks += [
        ("Consistencia y reintentos", "Verificar confirmación de publicación, idempotencia, reentrega, duplicados y recuperación tras reinicio."),
        ("Cierre de lote / cuenta", "Comprobar semántica de isLast, orden de mensajes, concurrencia y tratamiento de mensajes tardíos."),
        ("Trazabilidad", "Validar propagación de identificadores de correlación/UUID desde el origen hasta el artefacto final."),
        ("Operación", "Medir lag, tiempos por etapa, volumen de lotes, errores y capacidad de recuperación.")
    ]
    risk_html = "".join("<article class='risk'><h4>" + _e(title) + "</h4><p>" + _e(desc) + "</p></article>" for title, desc in risks)
    nav = ["resumen", "flujo", "integracion", "riesgos", "limitaciones"] + ["svc-" + r.get("name", "") for r in repos]
    nav_html = "".join("<a href='#" + _e(x) + "'>" + _e(" ".join(x.replace("svc-", "").replace("-", " ").split()).title()) + "</a>" for x in nav)
    services_html = "".join(_service_section(r) for r in repos)
    failures = analysis.get("failures", [])
    failure_html = _table(failures, [("repository", "Repositorio"), ("error", "Error")])
    limits = [
        "Análisis estático: no se ejecuta el código, los tests, SQL, Maven/Gradle, brokers Kafka ni servicios.",
        "Las reglas de negocio y los efectos se infieren de patrones de código; deben confirmarse con los responsables y pruebas.",
        "El parser Java es heurístico y no resuelve completamente tipos, sobrecargas, proxies Spring ni dispatch dinámico.",
        "Los topics correlacionados por nombre son candidatos, no prueba de conexión activa.",
        "No se realiza aún mapeo de payload campo a campo ni validación de compatibilidad Avro/Schema Registry.",
        "No se infieren garantías runtime de orden, entrega, atomicidad o idempotencia."
    ] + integration.get("limitations", [])
    return """<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Informe integral · """ + _e(name) + """</title><style>
:root{--ink:#17243a;--muted:#64748b;--line:#dce4ef;--blue:#214d91;--bg:#f3f6fb}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 Inter,system-ui,Segoe UI,sans-serif}
.hero{padding:48px max(24px,calc((100% - 1280px)/2));background:linear-gradient(120deg,#10254c,#214d91 60%,#087e83);color:white}
.hero .eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:.75rem;opacity:.8}.hero h1{font-size:clamp(2rem,4vw,3.1rem);line-height:1.1;margin:12px 0}.hero p{max-width:900px;color:#e4ecf8}
.chips{display:flex;gap:8px;flex-wrap:wrap}.chips span{border:1px solid #ffffff55;border-radius:99px;padding:4px 11px;font-size:.82rem}
.layout{max-width:1500px;margin:auto;display:grid;grid-template-columns:235px minmax(0,1fr);gap:26px;padding:26px 22px 70px}
nav{position:sticky;top:15px;align-self:start;max-height:calc(100vh - 30px);overflow:auto;background:white;border:1px solid var(--line);border-radius:13px;padding:16px}
nav b{display:block;margin-bottom:10px}nav a{display:block;padding:6px 0;color:var(--blue);text-decoration:none;font-size:.88rem}
main{min-width:0}section{background:white;border:1px solid var(--line);border-radius:14px;padding:25px;margin-bottom:20px;box-shadow:0 3px 14px #1b36500a}
h2{font-size:1.55rem;margin:0 0 18px;border-bottom:1px solid var(--line);padding-bottom:12px}h3{margin:25px 0 10px;color:#24477e}h4{margin:17px 0 7px}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:10px;margin:16px 0}.metric{background:#f1f5fb;border:1px solid var(--line);border-radius:10px;padding:13px}.metric b{display:block;font-size:1.65rem;color:var(--blue)}.metric span{font-size:.82rem;color:var(--muted)}
.flow{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.flow-node{background:#eef4fc;border:1px solid #cbd9ed;border-radius:10px;padding:14px;min-width:180px}.flow-node span{display:block;font-size:.8rem;color:var(--muted)}
.table-wrap{overflow:auto;margin:10px 0 20px}table{width:100%;border-collapse:collapse;font-size:.86rem}th,td{border:1px solid var(--line);padding:9px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#edf2f8;color:#243b5b}tbody tr:nth-child(even){background:#fafbfd}
.class-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:10px;margin-top:12px}.class-card,.risk{border:1px solid var(--line);border-radius:10px;padding:13px;background:#fff}.class-card h4{margin:5px 0}.class-card .meta{font-size:.76rem;color:var(--muted);overflow-wrap:anywhere}.class-card ul{padding-left:18px}.class-card li{margin:8px 0}.class-card small{color:var(--muted)}.class-search{width:min(100%,520px);padding:10px;border:1px solid #cbd5e1;border-radius:8px}
.risks{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}.risk{border-left:4px solid #d18a25}.muted{color:var(--muted)}code{overflow-wrap:anywhere}
footer{text-align:center;color:var(--muted);padding:25px;border-top:1px solid var(--line)}
@media(max-width:900px){.layout{grid-template-columns:1fr}nav{position:relative;max-height:none;display:flex;gap:10px;flex-wrap:wrap}nav b{width:100%}}
@media print{body{background:white}.layout{display:block}nav,.class-search{display:none}section{box-shadow:none;break-inside:avoid}.hero{print-color-adjust:exact}}
</style></head><body>
<header class='hero'><div class='eyebrow'>Reverse engineering · Análisis arquitectónico end-to-end</div><h1>""" + _e(name) + """</h1>
<p>Informe técnico integral de los repositorios analizados. Incluye inventario, comportamiento inferido, puntos de integración, evidencia estática, riesgos y cuestiones pendientes de validar.</p>
<div class='chips'><span>""" + str(len(repos)) + """ microservicios</span><span>""" + str(total_classes) + """ clases Java</span><span>""" + str(total_methods) + """ métodos Java</span><span>""" + str(total_sql) + """ sentencias SQL</span><span>Análisis estático</span></div></header>
<div class='layout'><nav><b>Contenido del informe</b>""" + nav_html + """</nav><main>
<section id='resumen'><h2>1. Resumen ejecutivo</h2><div class='metrics'>
<div class='metric'><b>""" + str(len(repos)) + """</b><span>Repositorios analizados</span></div>
<div class='metric'><b>""" + str(total_classes) + """</b><span>Clases Java</span></div>
<div class='metric'><b>""" + str(total_methods) + """</b><span>Métodos Java</span></div>
<div class='metric'><b>""" + str(total_rules) + """</b><span>Reglas/ramas detectadas</span></div>
<div class='metric'><b>""" + str(total_sql) + """</b><span>Operaciones SQL</span></div>
<div class='metric'><b>""" + str(len(topics)) + """</b><span>Topics candidatos</span></div></div>
<p>El informe consolida la evidencia extraída de cada repositorio y las coincidencias estáticas entre ellos. Los contadores representan detecciones del analizador, no cobertura funcional certificada.</p>
<h3>Estado del análisis</h3><p><b>Resultado:</b> """ + _e(analysis.get("completion_status")) + " · <b>Validación runtime:</b> " + _e(analysis.get("runtime_validation")) + """</p>
<h3>Repositorios</h3>""" + _table([{"name":r.get("name"),"artifact_dir":r.get("artifact_dir"),"commit":r.get("inventory",{}).get("commit_sha")} for r in repos], [("name","Microservicio"),("artifact_dir","Carpeta de evidencias"),("commit","Commit analizado")]) + """</section>
<section id='flujo'><h2>2. Vista conjunta y flujo entre componentes</h2>
<p>La siguiente vista representa los repositorios incluidos en el análisis. Las flechas de integración solo deben considerarse confirmadas cuando exista evidencia de productor, consumidor y contrato compatibles.</p>
<div class='flow'>""" + flow_nodes + """</div>
<p class='muted'>El flujo funcional end-to-end no se inventa cuando el código no permite demostrarlo. Consulta las secciones Kafka, contratos y limitaciones para ver la evidencia disponible.</p></section>
<section id='integracion'><h2>3. Contratos e integración entre microservicios</h2>
<h3>Topics Kafka candidatos</h3>""" + topic_rows + """
<h3>Contratos Avro / Proto candidatos</h3>""" + contract_rows + """
<h3>Lectura técnica</h3><p>Una coincidencia de topic o nombre de contrato es una pista para investigar, no una prueba de que ambos servicios estén conectados ni de que sus payloads sean compatibles. Este informe aún no certifica mapeo de campos, evolución de schemas, orden, entrega ni semántica de cierre.</p></section>
<section id='riesgos'><h2>4. Riesgos y verificaciones prioritarias</h2><div class='risks'>""" + risk_html + """</div>
<h3>Repositorios con análisis parcial o fallido</h3>""" + failure_html + """</section>
""" + services_html + """
<section id='limitaciones'><h2>Limitaciones y alcance</h2><ul>""" + "".join("<li>" + _e(x) + "</li>" for x in limits) + """</ul>
<p>Para elevar este documento al nivel de una ingeniería inversa funcional completa, la siguiente fase debe resolver el grafo real de llamadas, extraer propiedades y configuración efectiva, comparar schemas campo a campo, reconstruir secuencias de negocio y contrastar los hallazgos con pruebas de integración o trazas autorizadas.</p></section>
</main></div><footer>Informe generado por Deep Reverse Engineering &amp; Analysis Orchestrator · Evidencias estáticas, no validación runtime</footer>
<script>function filterClasses(input){const q=input.value.toLowerCase();const root=input.nextElementSibling;root.querySelectorAll('.class-card').forEach(c=>c.style.display=c.dataset.search.includes(q)?'':'none')}</script>
</body></html>"""
