"""HTML fragments shared by every report that shows a finding (classes styled in report.css)."""
from __future__ import annotations

import html

VERDICT_LABEL = {"confirmed": "Confirmado por el agente", "false_positive": "Falso positivo según el agente",
                 "needs_review": "Requiere revisión humana"}
STEP_LABEL = {"source": "Entrada", "propagation": "Propagación", "sanitizer": "Saneamiento", "sink": "Uso peligroso"}


def _e(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def classification_html(finding: dict) -> str:
    badges = []
    cwe = finding.get("cwe") or {}
    owasp = finding.get("owasp") or {}
    if cwe.get("id"):
        badges.append("<a class='tag' href='" + _e(cwe.get("url", "")) + "' title='" + _e(cwe.get("name", "")) + "'>"
                      + _e(cwe["id"]) + "</a>")
    if owasp.get("id"):
        badges.append("<a class='tag' href='" + _e(owasp.get("url", "")) + "'>OWASP " + _e(owasp["id"]) + " · "
                      + _e(owasp.get("name", "")) + "</a>")
    if finding.get("confidence_level"):
        level = {"high": "alta", "medium": "media", "low": "baja"}.get(finding["confidence_level"], finding["confidence_level"])
        badges.append("<span class='tag'>Confianza " + _e(level) + "</span>")
    return "<p class='finding-tags'>" + "".join(badges) + "</p>" if badges else ""


def dataflow_html(finding: dict) -> str:
    steps = finding.get("trace") or []
    if not steps:
        return ""
    items = "".join(
        "<li class='flow-" + _e(step.get("kind")) + "'><span class='flow-kind'>" + _e(STEP_LABEL.get(step.get("kind"), step.get("kind")))
        + "</span> <code>" + _e(step.get("file")) + ":" + _e(step.get("line")) + "</code>"
        + (" <span class='muted'>" + _e(step.get("note")) + "</span>" if step.get("note") else "")
        + "<pre>" + _e(step.get("code")) + "</pre></li>" for step in steps)
    return "<h3>Flujo de datos (fuente → uso peligroso)</h3><ol class='dataflow'>" + items + "</ol>"


def triage_html(finding: dict) -> str:
    triage = finding.get("triage") or {}
    if not triage:
        return ""
    verdict = triage.get("verdict", "needs_review")
    parts = ["<div class='triage triage-" + _e(verdict) + "'><p><b>" + _e(VERDICT_LABEL.get(verdict, verdict)) + "</b></p>"]
    if triage.get("reason"):
        parts.append("<p>" + _e(triage["reason"]) + "</p>")
    if triage.get("exploit_scenario"):
        parts.append("<p><b>Escenario:</b> " + _e(triage["exploit_scenario"]) + "</p>")
    if triage.get("fix"):
        parts.append("<p><b>Corrección propuesta:</b> " + _e(triage["fix"]) + "</p>")
    if triage.get("evidence"):
        parts.append("<p class='muted'>Evidencias: " + ", ".join(
            "<code>" + _e(item.get("file")) + ":" + _e(item.get("line")) + "</code>" for item in triage["evidence"]) + "</p>")
    parts.append("</div>")
    return "".join(parts)


def references_html(finding: dict) -> str:
    refs = finding.get("references") or []
    if not refs or not finding.get("cwe"):
        return ""
    return "<p class='muted'>Referencias: " + " · ".join(
        "<a href='" + _e(url) + "'>" + _e(url.rsplit("/", 1)[-1].replace(".html", "").replace("_", " ") or url) + "</a>"
        for url in refs[:4]) + "</p>"


def finding_details_html(finding: dict) -> str:
    return classification_html(finding) + dataflow_html(finding) + triage_html(finding)
