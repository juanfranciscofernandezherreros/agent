from __future__ import annotations

import html
import json
import re
from collections import Counter


def _e(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def _slug(value):
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip()).strip("-_").lower()
    return value[:70] or "section"


def _pretty(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value if value is not None else "")


def _table(items, columns, empty="No se han encontrado evidencias estáticas para este apartado."):
    if not items:
        return "<p class='empty'>" + _e(empty) + "</p>"
    head = "".join("<th>" + _e(label) + "</th>" for _, label in columns)
    rows = []
    for item in items:
        cells = []
        for key, _ in columns:
            value = item.get(key, "")
            cells.append("<td>" + _e(_pretty(value)) + "</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<div class='table-wrap'><table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"


def _evidence_table(items):
    return _table(items, [("kind", "Tipo"), ("file", "Archivo"), ("line", "Línea"), ("excerpt", "Fragmento / evidencia")])


def _metric(value, label, hint=""):
    return "<div class='metric'><strong>" + _e(value) + "</strong><span>" + _e(label) + "</span>" + ("<small>" + _e(hint) + "</small>" if hint else "") + "</div>"


def _list(items, empty="No identificado"):
    if not items:
        return "<p class='empty'>" + _e(empty) + "</p>"
    return "<ul class='compact'>" + "".join("<li>" + _e(x) + "</li>" for x in items) + "</ul>"


def _service_section(repo, index):
    name = repo.get("name", "Microservicio")
    anchor = "svc-" + str(index) + "-" + _slug(name)
    inv = repo.get("inventory", {})
    deep = repo.get("deep_analysis", {})
    func = repo.get("functional_analysis", {})
    java = repo.get("java_analysis", {})
    stats = deep.get("scan_stats", {})
    js = java.get("summary", {})
    fs = func.get("summary", {})
    arch = deep.get("architecture", {})
    deps = deep.get("dependencies", {})
    cfg = deep.get("configuration", {})
    integration = deep.get("integrations", {})
    security = deep.get("security", {})
    data = deep.get("data", {})
    tests = deep.get("tests", {})
    quality = repo.get("quality_analysis", {})
    quality_summary = quality.get("summary", {})
    bug_candidates = quality.get("bug_candidates", [])
    metrics = [
        _metric(stats.get("files_seen", inv.get("file_count_scanned", 0)), "Archivos inspeccionados"),
        _metric(js.get("classes", 0), "Clases Java"),
        _metric(js.get("methods", 0), "Métodos Java"),
        _metric(fs.get("operations", 0), "Operaciones detectadas"),
        _metric(fs.get("business_rules", 0), "Reglas / ramas"),
        _metric(js.get("sql_statements", 0), "Sentencias SQL"),
        _metric(js.get("kafka_listeners", 0), "Listeners Kafka"),
        _metric(stats.get("test_files", len(tests.get("files", []))), "Ficheros de test"),
    ]
    parts = [
        "<section class='service' id='" + _e(anchor) + "'>",
        "<div class='section-kicker'>MICROSERVICIO " + str(index + 1).zfill(2) + "</div>",
        "<h2>" + _e(name) + "</h2>",
        "<p class='lead'>Ficha técnica consolidada a partir del repositorio y del commit inspeccionado. Las detecciones están enlazadas a su ubicación de origen cuando el parser dispone de ella.</p>",
        ("<nav class='doc-links' aria-label='Documentación relacionada'><a href='../../analysis.html'>← Volver al informe global</a>" + ("<a href='../../" + _e(repo.get("bug_report")) + "'>Informe de posibles bugs</a>" if repo.get("bug_report") else "") + "</nav>" if repo.get("standalone_document") else ""),
        "<div class='quality-banner'><div><span class='quality-score'>" + _e(quality.get("score", "N/D")) + "<small>/100</small></span><b>Calidad estática: " + _e(quality.get("rating", "Sin datos")) + "</b><p>Indicador heurístico; no es probabilidad de bugs.</p></div><div class='quality-counts'><span>" + str(quality_summary.get("bug_candidates", 0)) + " candidatos</span><span>" + str(quality_summary.get("high", 0)) + " prioridad alta</span><span>" + str(quality_summary.get("medium", 0)) + " prioridad media</span></div></div>",
        "<h3>Posibles bugs detectados (requieren revisión)</h3>" + _table(bug_candidates, [("severity", "Prioridad"), ("code", "Código"), ("title", "Detección"), ("file", "Archivo"), ("line", "Línea"), ("excerpt", "Fragmento"), ("description", "Por qué revisarlo")]),
        "<p class='note'>Los candidatos se obtienen mediante patrones estáticos y pueden ser falsos positivos. No se consideran defectos confirmados. La puntuación parte de 100 y descuenta hasta 45 puntos por patrones de prioridad alta/media, 10 por ausencia de tests detectados, hasta 10 por incidencias de parseo y hasta 15 por indicadores estáticos de seguridad. El resultado se limita a 0–100.</p>",
        "<div class='metrics'>" + "".join(metrics) + "</div>",
        "<div class='subgrid'><article class='panel'><h3>Identidad de la fuente</h3><dl class='facts'>",
        "<dt>Commit analizado</dt><dd><code>" + _e(inv.get("commit_sha", "No disponible")) + "</code></dd>",
        "<dt>Lenguajes</dt><dd>" + _e(_pretty(inv.get("languages", {}))) + "</dd>",
        "<dt>Ruta de evidencias</dt><dd><code>" + _e(repo.get("artifact_dir", "No disponible")) + "</code></dd>",
        "<dt>Estado</dt><dd>" + _e(repo.get("completion_status", "STATIC_ANALYSIS_COMPLETED")) + "</dd>",
        "</dl></article><article class='panel'><h3>Arquitectura y empaquetado</h3>",
        "<h4>Directorios principales</h4>" + _list(arch.get("top_level_directories", [])),
        "<h4>Puntos de entrada candidatos</h4>" + _list(arch.get("entrypoints", [])),
        "<h4>Despliegue</h4>" + _list(arch.get("deployment_files", [])),
        "</article></div>",
        "<h3>Dependencias y construcción</h3>",
        "<p><b>Manifiestos encontrados:</b></p>" + _list(deps.get("manifests", [])),
        _table(deps.get("package_json_dependencies", []), [("name", "Dependencia"), ("version", "Versión declarada"), ("group", "Grupo"), ("file", "Manifiesto")]),
        "<h3>API y puntos de entrada HTTP</h3>",
        _table(deep.get("api", {}).get("route_candidates", []), [("framework", "Framework"), ("method", "Método"), ("path", "Ruta"), ("file", "Archivo"), ("line", "Línea")]),
        "<h3>Configuración y parámetros de entorno</h3>",
        "<div class='subgrid'><article class='panel'><h4>Ficheros de configuración</h4>" + _list(cfg.get("files", [])) + "</article><article class='panel'><h4>Nombres de variables detectadas</h4>" + _list(cfg.get("environment_variable_names", [])) + "</article></div>",
        "<p class='note'>Se muestran nombres de configuración, no valores secretos. La ausencia de una variable en este inventario no demuestra que no exista configuración externa.</p>",
        "<h3>Persistencia, modelos y migraciones</h3>",
        "<p><b>Ficheros de migración:</b></p>" + _list(data.get("migration_files", [])),
        _evidence_table(data.get("model_candidates", [])),
        "<h3>Seguridad: señales y evidencias</h3>",
    ]
    for key, values in security.items():
        parts.append("<details class='evidence-group'><summary>" + _e(key.replace("_", " ").title()) + " · " + str(len(values)) + " indicios</summary>" + _evidence_table(values) + "</details>")
    parts.append("<h3>Integraciones externas detectadas</h3>")
    for key, values in integration.items():
        parts.append("<details class='evidence-group'><summary>" + _e(key.replace("_", " ").title()) + " · " + str(len(values)) + " indicios</summary>" + _evidence_table(values) + "</details>")
    parts.append("<h3>Comportamiento funcional inferido</h3>")
    for key, label in [
        ("operations", "Operaciones y funciones"),
        ("business_rules", "Reglas y ramas condicionales"),
        ("validations", "Validaciones"),
        ("error_handling", "Gestión de errores"),
        ("state_changes", "Efectos y cambios de estado"),
    ]:
        items = func.get(key, [])
        cols = [("name", "Elemento"), ("operation", "Operación"), ("description", "Descripción"), ("file", "Archivo"), ("start_line", "Inicio"), ("line", "Línea"), ("end_line", "Fin"), ("confidence", "Confianza"), ("evidence", "Evidencia")]
        parts.append("<details class='evidence-group' " + ("open" if key == "operations" else "") + "><summary>" + label + " · " + str(len(items)) + "</summary>" + _table(items, cols) + "</details>")
    parts.append("<h3>Java / Spring: catálogo completo de clases y métodos</h3>")
    classes = java.get("classes", [])
    methods = java.get("methods", [])
    methods_by_class = {}
    methods_by_file = {}
    classes_per_file = {}
    for cls in classes:
        classes_per_file[cls.get("file")] = classes_per_file.get(cls.get("file"), 0) + 1
    for method in methods:
        methods_by_class.setdefault((method.get("class_name"), method.get("file")), []).append(method)
        methods_by_file.setdefault(method.get("file"), []).append(method)
    parts.append("<div class='catalog-tools'><input class='class-search' data-target='" + _e(anchor) + "' placeholder='Filtrar por clase, método, archivo o llamada...' aria-label='Filtrar catálogo Java'><span>" + str(len(classes)) + " clases · " + str(len(methods)) + " métodos</span></div>")
    cards = []
    for cls in classes:
        class_methods = methods_by_class.get((cls.get("name"), cls.get("file")), [])
        if not class_methods and classes_per_file.get(cls.get("file")) == 1:
            class_methods = methods_by_file.get(cls.get("file"), [])
        method_html = []
        for method in class_methods:
            method_html.append("<li><div><code>" + _e(method.get("name")) + "(" + _e(method.get("parameters")) + ")</code> <span class='line-ref'>" + _e(method.get("file")) + ":" + _e(method.get("line")) + "–" + _e(method.get("end_line")) + "</span></div><p><b>Llamadas candidatas:</b> " + _e(", ".join(method.get("calls", [])[:30]) + ("…" if len(method.get("calls", [])) > 30 else "")) + "</p><p><b>Ramas / errores:</b> " + _e(_pretty(method.get("branches_and_errors", []))) + "</p><p><b>Efectos posibles:</b> " + _e(", ".join(method.get("possible_effects", [])) or "No detectados") + " · <b>Confianza:</b> " + _e(method.get("confidence", "inferred")) + "</p></li>")
        search_text = (cls.get("name", "") + " " + cls.get("file", "") + " " + " ".join(m.get("name", "") + " " + " ".join(m.get("calls", [])) for m in class_methods)).lower()
        cards.append("<article class='class-card' data-search='" + _e(search_text) + "'><div class='meta'>" + _e(cls.get("kind")) + " · " + _e(cls.get("file")) + ":" + _e(cls.get("line")) + "</div><h4>" + _e(cls.get("name")) + "</h4><details><summary>" + str(len(class_methods)) + " métodos detectados</summary><ol>" + ("".join(method_html) if method_html else "<li>No hay métodos asociados por el parser.</li>") + "</ol></details></article>")
    parts.append("<div class='class-grid'>" + ("".join(cards) if cards else "<p class='empty'>No se detectaron clases Java.</p>") + "</div>")
    parts.append("<h3>Relaciones de llamadas detectadas (candidatas)</h3><p class='note'>Las llamadas se reconocen por nombre de método; pueden existir falsos positivos por sobrecargas, librerías o métodos homónimos. No equivalen a un grafo resuelto por compilador.</p>")
    parts.append(_table(java.get("call_references", []), [("caller", "Método llamante"), ("callee", "Nombre invocado"), ("file", "Archivo"), ("line", "Línea"), ("confidence", "Confianza")]))
    for key, label, cols in [
        ("injections", "Inyección de dependencias", [("type", "Tipo declarado"), ("field", "Campo"), ("file", "Archivo"), ("line", "Línea")]),
        ("spring_endpoints", "Anotaciones Spring / endpoints", [("annotation", "Anotación"), ("arguments", "Argumentos"), ("file", "Archivo"), ("line", "Línea")]),
        ("kafka_listeners", "Consumidores Kafka", [("arguments", "Topic / expresión"), ("file", "Archivo"), ("line", "Línea")]),
        ("kafka_producers", "Productores Kafka candidatos", [("expression", "Expresión detectada"), ("file", "Archivo"), ("line", "Línea")]),
        ("configuration_keys", "Claves de configuración relevantes", [("kind", "Tipo"), ("value", "Valor detectado"), ("file", "Archivo"), ("line", "Línea")]),
        ("sql_statements", "SQL: consultas y modificaciones", [("operation", "Operación"), ("excerpt", "Fragmento SQL"), ("file", "Archivo"), ("line", "Línea")]),
        ("avro_contracts", "Contratos Avro / Proto", [("name", "Tipo / mensaje"), ("format", "Formato"), ("file", "Archivo"), ("line", "Línea")]),
    ]:
        parts.append("<h3>" + label + "</h3>" + _table(java.get(key, []), cols))
    parts.append("<h3>Pruebas y calidad estática</h3><p><b>Ficheros de test detectados:</b> " + str(len(tests.get("files", []))) + "</p>" + _list(tests.get("files", []), "No se identificaron ficheros de test mediante los patrones actuales. Esto no demuestra que no existan pruebas."))
    parse_issues = deep.get("parse_issues", [])
    parts.append("<h3>Incidencias del análisis</h3>" + _table(parse_issues, [("file", "Archivo"), ("line", "Línea"), ("message", "Incidencia")]))
    limitations = list(dict.fromkeys((deep.get("limitations", []) or []) + (func.get("limitations", []) or []) + (java.get("limitations", []) or [])))
    parts.append("<h3>Alcance y limitaciones específicas</h3><ul class='compact'>" + "".join("<li>" + _e(x) + "</li>" for x in limitations) + "</ul>")
    parts.append("</section>")
    return "".join(parts), anchor


def build_integral_html(name, analysis, index_href="index.html"):
    repos = analysis.get("repositories", [])
    integration = analysis.get("integration_analysis", {})
    failures = analysis.get("failures", [])
    total_classes = sum(r.get("java_analysis", {}).get("summary", {}).get("classes", 0) for r in repos)
    total_methods = sum(r.get("java_analysis", {}).get("summary", {}).get("methods", 0) for r in repos)
    total_rules = sum(r.get("functional_analysis", {}).get("summary", {}).get("business_rules", 0) for r in repos)
    total_ops = sum(r.get("functional_analysis", {}).get("summary", {}).get("operations", 0) for r in repos)
    total_sql = sum(r.get("java_analysis", {}).get("summary", {}).get("sql_statements", 0) for r in repos)
    total_tests = sum(r.get("deep_analysis", {}).get("scan_stats", {}).get("test_files", 0) for r in repos)
    average_quality = round(sum(r.get("quality_analysis", {}).get("score", 0) for r in repos) / len(repos)) if repos else 0
    total_bug_candidates = sum(r.get("quality_analysis", {}).get("summary", {}).get("bug_candidates", 0) for r in repos)
    high_bug_candidates = sum(r.get("quality_analysis", {}).get("summary", {}).get("high", 0) for r in repos)
    service_scores = sorted(repos, key=lambda r: r.get("quality_analysis", {}).get("score", -1))
    score_cards = "".join(
        "<article class='score-card'><div class='score-card-head'><h3>" + _e(repo.get("name", "Microservicio")) +
        "</h3><strong>" + _e(repo.get("quality_analysis", {}).get("score", "N/D")) +
        "<small>/100</small></strong></div><div class='score-track'><span style='width:" +
        str(max(0, min(100, int(repo.get("quality_analysis", {}).get("score", 0))))) +
        "%'></span></div><p>" + _e(repo.get("quality_analysis", {}).get("rating", "Sin datos")) +
        " · " + str(repo.get("quality_analysis", {}).get("summary", {}).get("bug_candidates", 0)) +
        " posibles bugs</p></article>" for repo in service_scores
    )
    priority_order = {"high": 0, "medium": 1, "low": 2}
    task_titles = {
        "BUG001": "Revisar la excepción ignorada y decidir cómo registrar, propagar o tratar el error.",
        "BUG002": "Revisar la comparación con None/null y comprobar los casos de valor nulo.",
        "BUG003": "Resolver o documentar el TODO/FIXME y añadir una prueba que cubra el comportamiento esperado.",
        "BUG004": "Sustituir assert por una validación explícita cuando proteja una condición de negocio o entrada.",
        "BUG005": "Corregir la comparación de identidad si se pretendía comparar valores.",
        "BUG006": "Eliminar la credencial del código, rotarla si es real y cargarla desde un gestor seguro."
    }
    tasks = []
    for repo in repos:
        for finding in repo.get("quality_analysis", {}).get("bug_candidates", []):
            tasks.append({
                "priority": finding.get("severity", "low"),
                "service": repo.get("name", "Microservicio"),
                "task": task_titles.get(finding.get("code"), "Revisar el hallazgo y añadir una prueba de regresión."),
                "finding": finding.get("title", finding.get("code", "Posible bug")),
                "file": finding.get("file", ""),
                "line": finding.get("line", ""),
                "code": finding.get("code", ""),
                "excerpt": finding.get("excerpt", "")
            })
    tasks.sort(key=lambda item: (priority_order.get(item["priority"], 3), item["service"], item["file"], str(item["line"])))
    for index, task in enumerate(tasks, 1):
        task["order"] = index
    task_rows = _table(tasks, [("order", "Orden"), ("priority", "Prioridad"), ("service", "Microservicio"), ("task", "Tarea recomendada"), ("finding", "Hallazgo"), ("file", "Archivo"), ("line", "Línea"), ("excerpt", "Evidencia")], "No se han detectado candidatos de bug con los patrones actuales.")
    topics = integration.get("topic_candidates", [])
    contracts = integration.get("shared_contract_candidates", [])
    service_sections = []
    nav_links = []
    for i, repo in enumerate(repos):
        section, anchor = _service_section(repo, i)
        service_sections.append(section)
        nav_links.append("<a href='#" + _e(anchor) + "'>" + _e(repo.get("name", "Microservicio")) + "</a>")
        artifact_dir = str(repo.get("artifact_dir", ""))
        if artifact_dir and not repo.get("standalone_document"):
            service_path = artifact_dir.replace("\\", "/").strip("/") + "/analysis.html"
            nav_links.append("<a href='" + _e(service_path) + "'>↗ Ficha HTML: " + _e(repo.get("name", "Microservicio")) + "</a>")
            if repo.get("bug_report"):
                nav_links.append("<a href='" + _e(repo.get("bug_report")) + "'>↗ Posibles bugs: " + _e(repo.get("name", "Microservicio")) + "</a>")
    topic_rows = _table(topics, [("topic", "Topic candidato"), ("repositories", "Repositorios"), ("roles_detected", "Roles detectados"), ("producer_and_consumer_candidates", "Productor y consumidor candidatos"), ("cross_service_candidate", "Coincidencia"), ("evidence", "Evidencias por repositorio")])
    contract_rows = _table(contracts, [("contract", "Contrato candidato"), ("repositories", "Repositorios"), ("cross_service_candidate", "Coincidencia"), ("evidence", "Evidencias por repositorio")])
    risk_items = [
        ("Integración Kafka", "Comprobar productor, consumidor, configuración efectiva y despliegue. La coincidencia de un nombre no prueba que el flujo esté conectado."),
        ("Compatibilidad de mensajes", "Comparar schemas completos, tipos, nullability, defaults, subject/version y política de compatibilidad del Schema Registry."),
        ("Trazabilidad de datos", "Reconstruir identificadores, campos, transformaciones y persistencia desde el origen hasta el artefacto final con evidencia en ambos extremos."),
        ("Semántica de lote", "Verificar isLast, UUID, agrupación, orden, concurrencia, duplicados y mensajes tardíos en código y pruebas."),
        ("Resiliencia", "Revisar reintentos, DLQ, backoff, idempotencia, timeouts, circuit breakers y recuperación tras reinicio."),
        ("Seguridad", "Validar autenticación/autorización efectiva, secretos, cifrado, permisos de topics, base de datos y exposición de endpoints."),
        ("Operación", "Contrastar métricas, logs, alertas, lag, volumen, tiempos por etapa y capacidad de recuperación.")
    ]
    risks_html = "".join("<article class='risk-card'><span class='risk-index'>" + str(i + 1).zfill(2) + "</span><div><h4>" + _e(title) + "</h4><p>" + _e(desc) + "</p></div></article>" for i, (title, desc) in enumerate(risk_items))
    limits = [
        "El análisis es estático: no ejecuta microservicios, tests, SQL, Maven/Gradle, brokers Kafka ni infraestructura.",
        "Las llamadas Java se correlacionan por nombre; no se resuelven tipos, sobrecargas, proxies Spring, reflexión ni dispatch dinámico.",
        "Las coincidencias de topics y contratos son candidatos sustentados por fragmentos, no prueba de conexión activa ni compatibilidad.",
        "No se realiza todavía trazabilidad campo a campo ni validación formal de schemas Avro/Proto contra Schema Registry.",
        "No se pueden confirmar garantías runtime de orden, entrega, atomicidad, idempotencia o concurrencia solo con el análisis estático.",
        "La ausencia de una detección no demuestra que la funcionalidad no exista: puede estar en configuración externa, código generado o dependencias."
    ] + integration.get("limitations", [])
    nav = ["<a href='" + html.escape(index_href, quote=True) + "'>Índice de documentación</a>", "<a href='#executive'>Resumen ejecutivo</a>", "<a href='#scope'>Alcance y método</a>", "<a href='#landscape'>Mapa de servicios</a>", "<a href='#integration'>Integración y contratos</a>", "<a href='#risks'>Riesgos y validaciones</a>"] + nav_links
    failure_section = ""
    if failures:
        failure_section = "<section id='failures'><div class='section-kicker'>COBERTURA</div><h2>Repositorios con análisis incompleto</h2><p>Estos repositorios no pudieron analizarse completamente. Sus ausencias no deben interpretarse como ausencia de funcionalidad.</p>" + _table(failures, [("repository", "Repositorio"), ("error", "Error registrado")]) + "</section>"
    completion = analysis.get("completion_status", "STATIC_ANALYSIS_COMPLETED")
    status_label = "Completo (estático)" if completion == "STATIC_ANALYSIS_COMPLETED" and not failures else "Parcial" if failures or completion == "PARTIAL_ANALYSIS_COMPLETED" else str(completion)
    flow_nodes = "".join("<article class='service-node'><span class='node-number'>" + str(i + 1).zfill(2) + "</span><div><h3>" + _e(repo.get("name")) + "</h3><p>" + str(repo.get("java_analysis", {}).get("summary", {}).get("classes", 0)) + " clases · " + str(repo.get("java_analysis", {}).get("summary", {}).get("methods", 0)) + " métodos</p><small>Commit " + _e((repo.get("inventory", {}).get("commit_sha") or "no disponible")[:12]) + "</small></div></article>" for i, repo in enumerate(repos))
    return """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>Informe técnico de arquitectura y calidad de microservicios</title>
<style>
/* AGENT unified report theme v2 */
:root{color-scheme:dark;--bg:#080b12;--surface:#101722;--surface2:#151f2d;--surface3:#1b293a;--line:#26364b;--text:#e7edf7;--muted:#91a2b9;--accent:#64d8c5;--blue:#83adff;--danger:#ff7385;--warning:#f4c56a;--success:#65d6a5}
*{box-sizing:border-box}
html{scroll-behavior:smooth;background:var(--bg)}
body{background:radial-gradient(ellipse at 12% 0%,rgba(39,87,125,.18),transparent 35%),var(--bg)!important;color:var(--text)!important;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;line-height:1.58}
header{background:linear-gradient(125deg,#101b2b 0%,#142b40 58%,#123a3b 100%)!important;color:var(--text)!important;border:1px solid var(--line);border-radius:0 0 22px 22px;padding:30px clamp(18px,4vw,48px)!important;box-shadow:0 20px 55px rgba(0,0,0,.22)}
header h1,h1{letter-spacing:-.04em;line-height:1.12;font-weight:780}
header p:first-child,.section-kicker{color:var(--accent)!important;font-size:.75rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase}
main{max-width:1280px!important;margin:28px auto!important;padding:0 20px!important}
section,article,.panel,.metric,.score-card,.finding,.task,.notice,.service-node,.class-card,.quality-banner,.selection,.evidence-group{background:linear-gradient(180deg,var(--surface),#0e1520)!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:16px!important;box-shadow:0 10px 30px rgba(0,0,0,.16)!important}
section,article{padding:clamp(16px,2.5vw,26px)!important;margin:16px 0!important}
h2{color:#f0f5ff!important;letter-spacing:-.025em;font-weight:750}
h3,h4{color:#dce8f8!important}
.metric,.kpi,.score-card{background:linear-gradient(145deg,var(--surface2),var(--surface3))!important;border-color:#30445c!important}
.metric strong,.kpi strong,.score-card strong{color:var(--accent)!important}
nav{gap:9px!important}
nav a,.actions a,button{background:#152235!important;color:#cfe0f6!important;border:1px solid #2b405b!important;border-radius:10px!important;padding:8px 12px!important;text-decoration:none!important;transition:all .15s ease}
nav a:hover,.actions a:hover,button:hover{background:#1d314a!important;border-color:#4d7994!important;color:#fff!important}
a{color:var(--blue)!important}a:hover{color:var(--accent)!important}
.muted,small,.note,footer,dt{color:var(--muted)!important}
.note{background:#132233!important;border-left:3px solid var(--accent)!important;border-radius:10px!important;padding:12px 15px!important}
table{border-collapse:separate!important;border-spacing:0!important;width:100%}
table th{background:#172436!important;color:#aebed3!important;font-size:.76rem!important;letter-spacing:.07em;text-transform:uppercase}
td,th{border-color:var(--line)!important;padding:11px 12px!important}
tbody tr:hover td{background:rgba(102,157,204,.055)!important}
pre,code{background:#080e17!important;color:#d7e6ff!important;border:1px solid #26364b!important;border-radius:9px!important}
input,select,textarea{background:#0b1320!important;color:var(--text)!important;border:1px solid #2b3b50!important;border-radius:9px!important}
.bad,.badge-danger{color:var(--danger)!important}.warn,.warning{color:var(--warning)!important}.ok,.success{color:var(--success)!important}
hr{border-color:var(--line)!important}
@media(max-width:700px){main{padding:0 12px!important;margin:18px auto!important}header{padding:22px 18px!important;border-radius:0 0 16px 16px}section,article{padding:15px!important}table{min-width:620px}nav a,.actions a{font-size:.88rem}}
</style></head><body>
<header class='hero'><div class='hero-inner'><div class='eyebrow'>Arquitectura y calidad de software · Informe técnico</div>
<h1>Informe de arquitectura y calidad de microservicios</h1>
<p class='report-context'>Conjunto analizado: <strong>""" + _e(name) + """</strong></p>
<p>Documento integral de arquitectura, comportamiento, integraciones y evidencias de código. El objetivo es explicar qué contiene cada servicio, cómo se relacionan las piezas y qué aspectos necesitan validación adicional, separando los hallazgos de las hipótesis.</p>
<div class='hero-meta'><span>""" + str(len(repos)) + """ repositorios incluidos</span><span>""" + str(total_classes) + """ clases Java</span><span>""" + str(total_methods) + """ métodos</span><span>""" + str(total_sql) + """ sentencias SQL</span><span>Estado: """ + _e(status_label) + """</span><span>Validación runtime: no realizada</span></div></div></header>
<div class='shell'><aside class='sidebar'><strong>Índice del informe</strong>""" + "".join(nav) + """</aside><main>
<section class='report-section' id='executive'><div class='section-kicker'>01 · VISIÓN EJECUTIVA</div><h2>Calidad global de los microservicios</h2>
<p class='task-intro'>Puntuación estática individual de cada repositorio. Los servicios aparecen ordenados de menor a mayor puntuación para facilitar la priorización.</p>
<div class='score-grid'>""" + score_cards + """</div>
<h3>Plan de tareas priorizado: posibles bugs</h3>
<p class='task-intro'>Lista de revisión ordenada por prioridad (alta, media y baja), con servicio, ubicación y acción recomendada. Cada tarea debe confirmarse manualmente antes de modificar código.</p>
<div class='task-table'>""" + task_rows + """</div>
<h2>Resumen ejecutivo del análisis</h2>
<p>Este documento consolida el análisis de """ + str(len(repos)) + """ repositorios. Las cifras describen elementos detectados por los analizadores; no equivalen a cobertura funcional ni a validación de ejecución.</p>
<div class='metrics'>""" + _metric(len(repos), "Repositorios") + _metric(total_classes, "Clases Java") + _metric(total_methods, "Métodos Java") + _metric(total_ops, "Operaciones detectadas") + _metric(total_rules, "Reglas / ramas") + _metric(total_sql, "Sentencias SQL") + _metric(len(topics), "Topics candidatos") + _metric(len(contracts), "Contratos candidatos") + _metric(total_tests, "Ficheros de test") + _metric(average_quality, "Puntuación media /100", "Heurística estática") + _metric(total_bug_candidates, "Posibles bugs", str(high_bug_candidates) + " prioridad alta") + """</div>
<div class='two-col'><article class='panel'><h3>Resultado del proceso</h3><p><span class='status """ + ("partial" if failures else "") + """'>""" + _e(status_label) + """</span></p><p>Repositorios procesados: """ + str(len(repos)) + """ de """ + str(len(repos) + len(failures)) + """. Fallos: """ + str(len(failures)) + """</p><p>El análisis es estático. No se ha ejecutado el software ni se han lanzado sus pruebas.</p></article>
<article class='panel'><h3>Cómo leer las conclusiones</h3><p><b>Hallazgo:</b> elemento localizado en el código con archivo y línea.</p><p><b>Inferencia:</b> interpretación derivada de patrones o nombres, sujeta a revisión.</p><p><b>Pendiente:</b> aspecto que requiere configuración efectiva, contrato completo, test o ejecución.</p></article></div>
<h3>Repositorios y revisiones analizadas</h3>""" + _table([{"name": x.get("name"), "commit": x.get("inventory", {}).get("commit_sha"), "languages": x.get("inventory", {}).get("languages", {}), "files": x.get("deep_analysis", {}).get("scan_stats", {}).get("files_seen", 0), "classes": x.get("java_analysis", {}).get("summary", {}).get("classes", 0), "methods": x.get("java_analysis", {}).get("summary", {}).get("methods", 0)} for x in repos], [("name", "Servicio"), ("commit", "Commit inspeccionado"), ("languages", "Lenguajes"), ("files", "Archivos"), ("classes", "Clases"), ("methods", "Métodos")]) + """<h3>Calidad y posibles bugs por microservicio</h3>""" + _table([{"name": x.get("name"), "score": x.get("quality_analysis", {}).get("score", "N/D"), "rating": x.get("quality_analysis", {}).get("rating", "Sin datos"), "bugs": x.get("quality_analysis", {}).get("summary", {}).get("bug_candidates", 0), "high": x.get("quality_analysis", {}).get("summary", {}).get("high", 0), "medium": x.get("quality_analysis", {}).get("summary", {}).get("medium", 0)} for x in repos], [("name", "Microservicio"), ("score", "Puntuación /100"), ("rating", "Valoración"), ("bugs", "Candidatos"), ("high", "Alta"), ("medium", "Media")]) + """</section>
<section class='report-section' id='scope'><div class='section-kicker'>02 · MÉTODO Y COBERTURA</div><h2>Alcance, método y cobertura del análisis</h2>
<div class='two-col'><article class='panel'><h3>Qué se inspecciona</h3><ul class='compact'><li>Estructura de directorios, manifiestos y artefactos de despliegue.</li><li>Clases, métodos, anotaciones Spring, inyección y llamadas candidatas.</li><li>SQL, listeners/productores Kafka y definiciones Avro / Proto.</li><li>Operaciones, ramas, validaciones, errores y mutaciones inferidas.</li><li>Configuración, integraciones, señales de seguridad y tests detectados.</li><li>Coincidencias de topics y contratos entre repositorios incluidos.</li></ul></article>
<article class='panel'><h3>Qué no se puede afirmar</h3><ul class='compact'><li>Que una ruta o listener esté activo en el despliegue.</li><li>Que dos servicios intercambien mensajes solo por compartir un nombre.</li><li>Que los payloads sean compatibles sin comparar schemas y mappings.</li><li>Que un método se invoque realmente por encontrar una llamada homónima.</li><li>Que los tests pasen o que el comportamiento runtime sea correcto.</li><li>Que la ausencia de una detección signifique ausencia de funcionalidad.</li></ul></article></div>
<h3>Estado de validación</h3>""" + _table([{"dimension": "Código fuente", "status": "Inspección estática", "detail": "Archivos y patrones del repositorio clonado."}, {"dimension": "Grafo de llamadas", "status": "Parcial / heurístico", "detail": "Referencias por nombre; sin resolución semántica completa."}, {"dimension": "Integración entre servicios", "status": "Candidatos", "detail": "Correlación de topics y nombres de contratos con evidencias."}, {"dimension": "Schemas y payloads", "status": "No validados", "detail": "Sin comparación formal de campos ni compatibilidad del registry."}, {"dimension": "Ejecución y pruebas", "status": "No realizadas", "detail": "No se ejecutaron procesos, tests, consultas ni infraestructura."}], [("dimension", "Dimensión"), ("status", "Nivel de validación"), ("detail", "Interpretación")]) + """</section>
<section class='report-section' id='landscape'><div class='section-kicker'>03 · ARQUITECTURA GLOBAL</div><h2>Mapa de servicios y límites de responsabilidad</h2>
<p>La vista siguiente identifica los repositorios que forman parte del análisis. No dibuja flechas de comunicación cuando no existe evidencia suficiente de productor, consumidor y contrato asociado.</p><div class='service-map'>""" + flow_nodes + """</div>
<p class='note'>Para convertir este inventario en un diagrama de arquitectura confirmado hay que resolver las relaciones entre productores y consumidores con sus configuraciones efectivas, contratos, transformaciones y despliegues.</p>
<h3>Visión consolidada de componentes</h3>""" + _table([{"service": x.get("name"), "entrypoints": x.get("deep_analysis", {}).get("architecture", {}).get("entrypoints", []), "http_routes": len(x.get("deep_analysis", {}).get("api", {}).get("route_candidates", [])), "kafka_listeners": x.get("java_analysis", {}).get("summary", {}).get("kafka_listeners", 0), "kafka_producers": x.get("java_analysis", {}).get("summary", {}).get("kafka_producers", 0), "contracts": x.get("java_analysis", {}).get("summary", {}).get("avro_contracts", 0), "sql": x.get("java_analysis", {}).get("summary", {}).get("sql_statements", 0)} for x in repos], [("service", "Servicio"), ("entrypoints", "Puntos de entrada"), ("http_routes", "Rutas HTTP"), ("kafka_listeners", "Listeners Kafka"), ("kafka_producers", "Productores candidatos"), ("contracts", "Contratos"), ("sql", "Sentencias SQL")]) + """</section>
<section class='report-section' id='integration'><div class='section-kicker'>04 · COMUNICACIÓN ENTRE SERVICIOS</div><h2>Integración, mensajería y contratos</h2>
<p>Se muestran las coincidencias encontradas y las evidencias que las originan. La coincidencia de nombres no se presenta como conexión probada.</p>
<h3>Topics Kafka candidatos</h3>""" + topic_rows + """
<h3>Expresiones productoras Kafka detectadas</h3>""" + _table(integration.get("producer_candidates", []), [("repository", "Servicio"), ("expression", "Expresión productora"), ("file", "Archivo"), ("line", "Línea")]) + """<h3>Contratos Avro / Proto candidatos</h3>""" + contract_rows + """
<div class='two-col'><article class='panel'><h3>Validaciones necesarias para Kafka</h3><ul class='compact'><li>Resolver el topic final tras placeholders, perfiles y configuración externa.</li><li>Identificar el método productor y el método consumidor.</li><li>Seguir el tipo real del mensaje y sus conversiones.</li><li>Verificar grupo consumidor, particiones, offsets, retries y DLQ.</li><li>Confirmar ACLs, serializers y configuración de despliegue.</li></ul></article><article class='panel'><h3>Validaciones necesarias para contratos</h3><ul class='compact'><li>Comparar nombres fully-qualified y namespaces.</li><li>Comparar todos los campos, tipos, defaults y nullability.</li><li>Revisar evolución, compatibilidad y versiones publicadas.</li><li>Seguir el mapping desde DTO/entidad hasta mensaje publicado.</li><li>Validar el contrato consumido y el tratamiento de campos desconocidos.</li></ul></article></div>
</section>
<section class='report-section' id='risks'><div class='section-kicker'>05 · CALIDAD Y DECISIONES</div><h2>Riesgos técnicos y plan de validación</h2><p>Los siguientes puntos son una agenda de validación derivada de los límites del análisis; no son defectos confirmados.</p><div class='risk-list'>""" + risks_html + """</div>
<h3>Limitaciones y advertencias de interpretación</h3><ul class='compact'>""" + "".join("<li>" + _e(x) + "</li>" for x in dict.fromkeys(limits)) + """</ul>
</section>
""" + "".join(service_sections) + failure_section + """
<div class='footer'>Fin del informe · Generado por Analizador de arquitectura y calidad de microservicios · Evidencia estática; validación runtime no realizada.</div>
</main></div>
<script>
(function(){
  document.querySelectorAll('.class-search').forEach(function(input){
    input.addEventListener('input',function(){
      var section=document.getElementById(input.getAttribute('data-target'));
      if(!section)return;
      var q=input.value.trim().toLowerCase();
      section.querySelectorAll('.class-card').forEach(function(card){
        card.hidden=q!=='' && !(card.getAttribute('data-search')||'').includes(q);
      });
    });
  });
})();
</script></body></html>"""


