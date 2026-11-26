"""Informe multiagente (Markdown y HTML): estado de los agentes, interpretación LLM y validación cruzada."""
from __future__ import annotations

import html
from .report_theme import stylesheet_link

STATUS_LABEL = {"CONSISTENT": "Coherente", "WARNINGS": "Con avisos", "CONTRADICTIONS": "Con contradicciones"}
CHECK_LABEL = {"consistent": "coherente", "warning": "aviso", "contradiction": "contradicción", "not_applicable": "no aplica"}
VERDICT_LABEL = {"likely_bug": "bug probable", "false_positive": "falso positivo", "needs_review": "requiere revisión"}
AGENT_LABEL = {
    "inventory": "Inventario", "deep_analysis": "Análisis profundo", "functional_analysis": "Análisis funcional",
    "java_analysis": "Análisis Java", "quality_analysis": "Calidad y bugs", "integration_analysis": "Correlación estática",
    "llm_functional_interpretation": "Interpretación funcional (LLM)", "llm_bug_review": "Revisión de bugs (LLM)",
    "llm_architecture_explanation": "Explicación arquitectónica (LLM)", "llm_evidence_correlation": "Correlación de evidencias (LLM)",
    "cross_validation": "Validación cruzada", "group_cross_validation": "Validación cruzada global",
    "activity_analysis": "Histórico de actividad", "group_activity": "Ranking de actividad",
    "repository_report": "Agente documental", "group_report": "Agente documental global",
}


def _e(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def _cites(refs):
    return ", ".join((r.get("repository") + "/" if r.get("repository") else "") + str(r.get("file")) +
                     (":" + str(r["line"]) if r.get("line") else "") for r in refs or [])


def _item(item: dict) -> str:
    return "; ".join(f"{k}: {v}" for k, v in item.items() if v not in (None, "", []))


def build_sections(insights: dict, runs: list[dict], scope: str) -> list[dict]:
    """Estructura neutra del informe: lista de secciones {title, paragraphs, table, bullets, note}."""
    sections = []
    rows = [[AGENT_LABEL.get(m["agent"], m["agent"]), m["status"],
             "" if m.get("duration_ms") is None else str(m["duration_ms"]) + " ms",
             str(m.get("evidence_count", len(m.get("evidence", [])))),
             m.get("detail") or "; ".join(e["message"] for e in m.get("errors", []))] for m in runs]
    sections.append({"title": "Ejecución de agentes", "table": (["Agente", "Estado", "Duración", "Evidencias", "Detalle"], rows)})

    llm_ran = any(k.startswith("llm_") for k in insights)
    if not llm_ran:
        reasons = sorted({m.get("detail") or "; ".join(e["message"] for e in m.get("errors", []))
                          for m in runs if m["agent"].startswith("llm_")} - {"", None})
        sections.append({"title": "Agentes inteligentes (LLM)",
                         "note": "No se ejecutó ningún agente LLM. " + " ".join(reasons) +
                                 " Este informe contiene únicamente resultados estáticos y su validación cruzada."})

    f = insights.get("llm_functional_interpretation")
    if f:
        sections.append({"title": "Interpretación funcional (LLM)", "paragraphs": [f.get("purpose", "")],
                         "table": (["Capacidad", "Descripción", "Evidencia"],
                                   [[c["name"], c["description"], _cites(c["evidence"])] for c in f.get("capabilities", [])])})
        if f.get("business_rules"):
            sections.append({"title": "Reglas de negocio interpretadas (LLM)",
                             "table": (["Regla", "Evidencia"], [[b["rule"], _cites(b["evidence"])] for b in f["business_rules"]])})
        if f.get("open_questions"):
            sections.append({"title": "Preguntas abiertas", "bullets": f["open_questions"]})
    a = insights.get("llm_architecture_explanation")
    if a:
        sections.append({"title": "Explicación arquitectónica (LLM)", "paragraphs": [a.get("overview", "")],
                         "table": (["Componente", "Responsabilidad", "Evidencia"],
                                   [[c["name"], c["responsibility"], _cites(c["evidence"])] for c in a.get("components", [])])})
        if a.get("integrations"):
            sections.append({"title": "Integraciones (LLM)",
                             "table": (["Integración", "Tipo", "Descripción", "Evidencia"],
                                       [[i["name"], i["type"], i["description"], _cites(i["evidence"])] for i in a["integrations"]])})
        if a.get("risks"):
            sections.append({"title": "Riesgos arquitectónicos (LLM)", "bullets": a["risks"]})
    b = insights.get("llm_bug_review")
    if b:
        s = b.get("summary", {})
        sections.append({"title": "Revisión de bugs (LLM)",
                         "paragraphs": [f"Candidatos: {s.get('candidates_total', 0)} · enviados: {s.get('candidates_sent', 0)} · "
                                        f"bug probable: {s.get('likely_bug', 0)} · falso positivo: {s.get('false_positive', 0)} · "
                                        f"requiere revisión: {s.get('needs_review', 0)}"],
                         "table": (["Candidato", "Veredicto", "Justificación", "Corrección sugerida"],
                                   [[r["ref"], VERDICT_LABEL.get(r["verdict"], r["verdict"]), r["rationale"], r["suggested_fix"]]
                                    for r in b.get("reviews", [])])})
    c = insights.get("llm_evidence_correlation")
    if c:
        sections.append({"title": "Flujos entre microservicios (LLM)",
                         "table": (["Flujo", "Origen", "Destino", "Canal", "Confianza", "Evidencia"],
                                   [[x["description"], x["from"], x["to"], x["via"], x["confidence"], _cites(x["evidence"])]
                                    for x in c.get("flows", [])])})
        if c.get("observations"):
            sections.append({"title": "Observaciones de correlación (LLM)", "bullets": c["observations"]})
    if llm_ran:
        used = sorted({str(v.get("provider", "?")) + " · " + str(v.get("model", "?"))
                       for k, v in insights.items() if k.startswith("llm_") and isinstance(v, dict)})
        sections.append({"title": "Cómo leer las secciones LLM",
                         "note": "Modelo utilizado: " + ", ".join(used) + ". Son interpretaciones generadas por un modelo a partir de resultados estáticos, no hechos verificados. "
                                 "La validación cruzada comprueba sus citas contra el repositorio."})

    if insights.get("group_activity"):
        sections += group_activity_sections(insights["group_activity"])

    v = insights.get("group_cross_validation" if scope == "group" else "cross_validation")
    if v:
        n = v.get("summary", {})
        sections.append({"title": "Validación cruzada: " + STATUS_LABEL.get(v.get("status"), str(v.get("status"))),
                         "paragraphs": [f"Coherentes: {n.get('consistent', 0)} · avisos: {n.get('warning', 0)} · "
                                        f"contradicciones: {n.get('contradiction', 0)} · no aplicables: {n.get('not_applicable', 0)}. "
                                        "Agentes revisados: " + ", ".join(AGENT_LABEL.get(x, x) for x in v.get("reviewed_agents", []))],
                         "table": (["Comprobación", "Resultado", "Agentes", "Detalle"],
                                   [[c["title"], CHECK_LABEL.get(c["status"], c["status"]),
                                     ", ".join(AGENT_LABEL.get(x, x) for x in c["agents"]),
                                     c["detail"] + ("".join("\n• " + _item(i) for i in c["items"][:10]))]
                                    for c in v.get("checks", [])]), "bullets": v.get("limitations", [])})
    else:
        sections.append({"title": "Validación cruzada", "note": "La validación cruzada no se ejecutó o falló; consulta la tabla de agentes."})
    return sections


def _day(value) -> str:
    return str(value)[:10] if value else "—"


def _cut(flag) -> str:
    return " (truncado: hay más)" if flag else ""


def repository_activity_sections(a: dict) -> list[dict]:
    b, c, p = a["branches"], a["commits"], a["pushes"]
    top = p.get("top_user") or {}
    out = [{"title": f"Histórico de actividad (últimos {a['window_days']} días)",
            "paragraphs": [f"Ramas recientes: {b['recent']} de {b['total']}{_cut(b['truncated'])} · commits: {c['total']}{_cut(c['truncated'])} "
                           f"de {c['authors']} autores · pushes: {p['total']}{_cut(p['truncated'])} de {p['users']} usuarios · "
                           f"último commit: {_day(c.get('last_commit_at'))}.",
                           ("Usuario con más pushes: " + str(top.get("display_name")) + " (" + str(top.get("user")) + "), " +
                            str(top.get("count")) + " pushes.") if top else "Sin pushes registrados en el periodo."],
            "bullets": a.get("errors", [])}]
    out.append({"title": "Ramas con actividad reciente",
                "table": (["Rama", "Último commit", "Autor", "Fusionada"],
                          [[x["name"] + (" (principal)" if x["default"] else ""), _day(x["last_commit_at"]), x.get("last_author") or "",
                            "Sí" if x["merged"] else "No"] for x in b["recent_branches"]])})
    out.append({"title": "Pushes por usuario",
                "table": (["Usuario", "Nombre", "Pushes", "Commits empujados"],
                          [[x["user"], x.get("display_name", ""), str(x["count"]), str(x.get("commits_pushed", 0))] for x in p["by_user"]])})
    out.append({"title": "Commits por autor",
                "table": (["Autor", "Commits"], [[x["name"], str(x["count"])] for x in c["by_author"]]),
                "bullets": a.get("limitations", [])})
    return out


def group_activity_sections(g: dict) -> list[dict]:
    t, top = g["totals"], g.get("top_pusher") or {}
    repo_row = lambda r: [r["repository"], str(r["recent_branches"]), str(r["total_branches"]), str(r["commits"]),
                          str(r["pushes"]), (str(r["top_pusher"]) + " (" + str(r["top_pusher_pushes"]) + ")") if r.get("top_pusher") else "—",
                          _day(r.get("last_commit_at"))]
    head = ["Repositorio", "Ramas recientes", "Ramas totales", "Commits", "Pushes", "Quien más empuja", "Último commit"]
    out = [{"title": f"Resumen de actividad (últimos {g['window_days']} días)",
            "paragraphs": [f"Repositorios con datos: {g['repositories_with_data']} · ramas recientes: {t['recent_branches']} · "
                           f"commits: {t['commits']} · pushes: {t['pushes']}.",
                           ("Usuario con más pushes: " + str(top.get("display_name")) + " (" + str(top.get("user")) + "), " +
                            str(top.get("count")) + " pushes en " + str(top.get("repositories")) + " repositorios.") if top
                           else "Sin pushes registrados en el periodo."]},
           {"title": "Repositorios con más ramas recientes", "table": (head, [repo_row(r) for r in g["by_recent_branches"]])},
           {"title": "Repositorios con más commits", "table": (head, [repo_row(r) for r in g["by_commits"]])},
           {"title": "Usuarios con más pushes",
            "table": (["Usuario", "Nombre", "Pushes", "Repositorios"],
                      [[x["user"], x.get("display_name", ""), str(x["count"]), str(x.get("repositories", ""))] for x in g["top_pushers"]])},
           {"title": "Autores con más commits",
            "table": (["Autor", "Commits"], [[x["name"], str(x["count"])] for x in g["top_committers"]]),
            "bullets": g.get("limitations", [])}]
    if g.get("repositories_without_data"):
        out.append({"title": "Repositorios sin datos de actividad", "bullets": g["repositories_without_data"][:100]})
    return out


def to_markdown(title: str, subtitle: str, sections: list[dict]) -> str:
    out = ["# " + title, "", "> " + subtitle, ""]
    for s in sections:
        out += ["## " + s["title"], ""]
        for p in s.get("paragraphs", []):
            if p:
                out += [p, ""]
        if s.get("note"):
            out += ["> " + s["note"], ""]
        if s.get("table"):
            head, rows = s["table"]
            if rows:
                cell = lambda x: str(x).replace("|", "\\|").replace("\n", "<br>")
                out += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
                out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows] + [""]
            else:
                out += ["_Sin elementos._", ""]
        for b in s.get("bullets", []):
            out.append("- " + str(b))
        if s.get("bullets"):
            out.append("")
    return "\n".join(out)


def to_html(title: str, subtitle: str, sections: list[dict], links: list[tuple[str, str]],
            kicker: str = "INFORME MULTIAGENTE") -> str:
    body = []
    for s in sections:
        body.append("<section><h2>" + _e(s["title"]) + "</h2>")
        body += ["<p>" + _e(p) + "</p>" for p in s.get("paragraphs", []) if p]
        if s.get("note"):
            body.append("<p class='note'>" + _e(s["note"]) + "</p>")
        if s.get("table"):
            head, rows = s["table"]
            if rows:
                body.append("<div class='scroll'><table><thead><tr>" + "".join("<th>" + _e(h) + "</th>" for h in head) + "</tr></thead><tbody>")
                for r in rows:
                    body.append("<tr>" + "".join("<td class='" + _e(_css(c)) + "'>" + _e(c).replace("\n", "<br>") + "</td>" for c in r) + "</tr>")
                body.append("</tbody></table></div>")
            else:
                body.append("<p class='muted'>Sin elementos.</p>")
        if s.get("bullets"):
            body.append("<ul>" + "".join("<li>" + _e(b) + "</li>" for b in s["bullets"]) + "</ul>")
        body.append("</section>")
    nav = "".join("<a href='" + _e(href) + "'>" + _e(label) + "</a>" for label, href in links)
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>""" + _e(title) + """</title>""" + stylesheet_link() + """</head><body><header><p>""" + _e(kicker) + """</p><h1>""" + _e(title) + """</h1><p>""" + _e(subtitle) + """</p></header><main><nav>""" + nav + """</nav>""" + "".join(body) + """</main></body></html>"""


def _css(cell) -> str:
    value = str(cell)
    if value in ("COMPLETED", "coherente", "bug probable"):
        return "ok"
    if value in ("aviso", "requiere revisión"):
        return "warn"
    if value in ("FAILED", "contradicción"):
        return "bad"
    if value in ("SKIPPED", "no aplica", "falso positivo"):
        return "off"
    return ""
