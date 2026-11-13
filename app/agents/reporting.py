"""Agente documental (Fase 6): genera los informes individuales por microservicio y los globales.

Conserva los informes existentes (analysis.json/md/html, expedientes de bugs, índices) y añade
el informe multiagente (agents.md / agents.html) con el estado de los agentes, la interpretación
LLM y la validación cruzada.
"""
from __future__ import annotations

import hashlib
import json
import shutil

from ..agent_report import STATUS_LABEL, build_sections, group_activity_sections, repository_activity_sections, to_html, to_markdown
from ..bug_report import build_bug_report_html, build_bug_reports_index
from ..communication.contracts import AgentSkipped
from ..documentation import build_documentation_index
from ..group_report import markdown, slug
from ..report_details import java_catalog, write_individual_reports
from ..rich_report import build_integral_html
from .context import AnalysisContext, AnalyzerAgent
from .validation import LLM_REPOSITORY, STATIC

STATIC_REPORT_FILES = ("analysis.json", "analysis.md", "analysis.html", "agents.md", "agents.html")
SUBTITLE = "Análisis estático; no se ejecutó el código. Las secciones LLM son interpretaciones, no hechos verificados."


def _runs(context: AnalysisContext, repository: str | None, scope: str, exclude: str) -> list[dict]:
    return [m.to_dict(include_payload=False) for m in context.store.messages(repository, scope) if m.agent != exclude] \
        if context.store is not None else []


class RepositoryReportingAgent(AnalyzerAgent):
    """Informes individuales de un microservicio."""
    name = "repository_report"
    requires = STATIC
    after = (*LLM_REPOSITORY, "cross_validation", "activity_analysis")
    optional = True  # se omite si no hay carpeta de salida; el orquestador exige su resultado

    def run(self, context: AnalysisContext) -> dict:
        folder = context.data.get("output_dir")
        if folder is None:
            raise AgentSkipped("Sin carpeta de salida (output_dir): no se generan informes.")
        name, group_name = context.repository, context.data.get("group_name", context.repository)
        bug_reports = context.data.setdefault("bug_reports", [])
        inv, deep, functional, java, quality = (context.results[k] for k in STATIC)
        activity = context.results.get("activity_analysis")
        # Los informes estáticos no incluyen el histórico de Git: así no cambian mientras no cambie el código.
        insights = {k: v for k, v in context.results.items() if k not in STATIC and k not in (self.name, "activity_analysis")}
        service = slug(name)
        dest = folder / "repositories" / service
        dest.mkdir(parents=True, exist_ok=True)
        artifact_dir = str(dest.relative_to(folder))
        candidates = quality.get("bug_candidates") or []
        # Nombre estable por repositorio: los enlaces siguen siendo válidos entre ejecuciones.
        identity = (context.data.get("repository_input") or {}).get("git_url") or str(name)
        report_file = (service + "-" + hashlib.sha1(identity.encode("utf-8")).hexdigest()[:6] + ".html") if candidates else None
        bug_report = ("bug-reports/" + report_file) if report_file else None
        static_files = [artifact_dir + "/" + f for f in STATIC_REPORT_FILES] + ([bug_report] if bug_report else [])

        cached = context.data.get("cached_reports")
        if cached is not None:
            # Informes ya generados para este mismo commit: se copian tal cual, sin regenerarlos.
            for rel in static_files:
                target = folder / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cached / rel.replace("\\", "/").split("/")[-1], target)
        else:
            if report_file:
                (folder / "bug-reports").mkdir(parents=True, exist_ok=True)
                (folder / bug_report).write_text(build_bug_report_html(name, group_name, quality, service, context.data.get("group_id"), report_file), encoding="utf-8")
            member = {"project_name": name, "inventory": inv, "deep_analysis": deep,
                      "functional_analysis": functional, "java_analysis": java, "quality_analysis": quality,
                      "bug_report": bug_report, "agent_insights": insights,
                      "completion_status": "STATIC_ANALYSIS_COMPLETED", "runtime_validation": "NOT_PERFORMED"}
            (dest / "analysis.json").write_text(json.dumps(member, indent=2, ensure_ascii=False), encoding="utf-8")
            write_individual_reports(dest, name, inv, deep, functional, java, member)
            runs = [m for m in _runs(context, name, "repository", self.name) if m["agent"] != "activity_analysis"]
            sections = build_sections(insights, runs, "repository")
            title = "Informe multiagente: " + str(name)
            (dest / "agents.md").write_text(to_markdown(title, SUBTITLE, sections), encoding="utf-8")
            links = [("← Ficha técnica", "analysis.html"), ("Histórico de Git", "activity.html"),
                     ("Informe multiagente global", "../../agents.html"), ("Índice de documentación", "../../index.html")]
            if bug_report:
                links.append(("Posibles bugs", "../../" + bug_report))
            (dest / "agents.html").write_text(to_html(title, SUBTITLE, sections, links), encoding="utf-8")
        if candidates:
            bug_reports.append({"repository": name, "file": report_file, "count": len(candidates)})

        # Informe de Git del repositorio: se genera siempre, porque la actividad cambia aunque el código no.
        a_title = "Histórico de Git: " + str(name)
        if activity:
            a_sections = repository_activity_sections(activity)
            a_sub = f"Últimos {activity['window_days']} días · datos de la API de GitLab"
        else:
            message = context.store.get("activity_analysis", name) if context.store is not None else None
            reason = (message.detail or "; ".join(e["message"] for e in message.errors)) if message else ""
            a_sections = [{"title": "Sin histórico disponible", "note": reason or "No se pudo obtener el histórico de Git de este repositorio."}]
            a_sub = "Datos de la API de GitLab"
        (dest / "activity.md").write_text(to_markdown(a_title, a_sub, a_sections), encoding="utf-8")
        (dest / "activity.html").write_text(to_html(a_title, a_sub, a_sections, [
            ("← Índice de documentación", "../../index.html"), ("Ficha técnica", "analysis.html"),
            ("Histórico del grupo", "../../activity.html")], kicker="HISTÓRICO DE GIT"), encoding="utf-8")
        (dest / "activity.json").write_text(json.dumps(activity, indent=2, ensure_ascii=False), encoding="utf-8")

        entry = {"name": name, "inventory": inv, "deep_analysis": deep, "functional_analysis": functional,
                 "java_analysis": java, "quality_analysis": quality, "artifact_dir": artifact_dir,
                 "bug_report": bug_report,
                 "agent_insights": {**insights, **({"activity_analysis": activity} if activity else {})}}
        context.outputs["repository_entry"] = entry  # no se publica: ya está en analysis.json
        context.outputs["static_report_files"] = static_files
        return {"artifact_dir": artifact_dir, "bug_report": bug_report, "reused": cached is not None,
                "files": static_files + [artifact_dir + "/" + f for f in ("activity.md", "activity.html", "activity.json")]}


class GroupReportingAgent(AnalyzerAgent):
    """Informes globales del conjunto de microservicios."""
    name = "group_report"
    requires = ("integration_analysis",)
    after = ("llm_evidence_correlation", "group_cross_validation", "group_activity")
    scope = "group"
    optional = True

    def run(self, context: AnalysisContext) -> dict:
        folder = context.data.get("output_dir")
        if folder is None:
            raise AgentSkipped("Sin carpeta de salida (output_dir): no se generan informes.")
        name = context.data.get("group_name", "analysis")
        repositories = context.data.get("repositories", [])
        failures = context.data.get("failures", [])
        bug_reports = context.data.get("bug_reports", [])
        insights = {k: v for k, v in context.results.items() if k not in ("integration_analysis", self.name)}
        result = {"analysis_version": "5.0", "group_name": name, "repositories": repositories,
                  "integration_analysis": context.results["integration_analysis"],
                  "agent_insights": insights, "failures": failures,
                  "completion_status": "STATIC_ANALYSIS_COMPLETED" if not failures else "PARTIAL_ANALYSIS_COMPLETED",
                  "runtime_validation": "NOT_PERFORMED"}
        (folder / "analysis.md").write_text(markdown(name, result) + "\n" + java_catalog(result), encoding="utf-8")
        result["bug_reports"] = bug_reports
        (folder / "analysis.html").write_text(build_integral_html(name, result), encoding="utf-8")
        bug_dir = folder / "bug-reports"
        bug_dir.mkdir(parents=True, exist_ok=True)
        (bug_dir / "index.html").write_text(build_bug_reports_index(name, bug_reports, repositories, context.data.get("group_id")), encoding="utf-8")

        sections = build_sections(insights, _runs(context, None, "group", self.name), "group")
        rows = []
        for repo in repositories:
            ins = repo.get("agent_insights", {})
            validation = ins.get("cross_validation") or {}
            counts = validation.get("summary", {})
            review = (ins.get("llm_bug_review") or {}).get("summary", {})
            rows.append([repo["name"], STATUS_LABEL.get(validation.get("status"), "No ejecutada"),
                         str(counts.get("contradiction", 0)), str(counts.get("warning", 0)),
                         "Sí" if any(k.startswith("llm_") for k in ins) else "No",
                         str(review.get("likely_bug", "—")), repo["artifact_dir"].replace("\\", "/") + "/agents.html"])
        sections.insert(1, {"title": "Resumen por microservicio",
                            "table": (["Microservicio", "Validación cruzada", "Contradicciones", "Avisos", "LLM",
                                       "Bugs probables (LLM)", "Informe individual"], rows)})
        if failures:
            sections.append({"title": "Repositorios no analizados",
                             "bullets": [f["repository"] + ": " + f["error"] for f in failures]})
        title = "Informe multiagente: " + str(name)
        (folder / "agents.md").write_text(to_markdown(title, SUBTITLE, sections), encoding="utf-8")
        links = [("← Índice de documentación", "index.html"), ("Informe global", "analysis.html"),
                 ("Posibles bugs", "bug-reports/index.html")] + \
                [(r["name"], r["artifact_dir"].replace("\\", "/") + "/agents.html") for r in repositories[:40]]
        (folder / "agents.html").write_text(to_html(title, SUBTITLE, sections, links), encoding="utf-8")

        # Histórico de Git del grupo: se genera siempre para que los enlaces de cada microservicio sean válidos.
        a_title = "Histórico de actividad: " + str(name)
        if insights.get("group_activity"):
            a_sub = f"Últimos {insights['group_activity']['window_days']} días · datos de la API de GitLab"
            a_sections = group_activity_sections(insights["group_activity"])
        else:
            message = context.store.get("group_activity") if context.store is not None else None
            reason = (message.detail or "; ".join(e["message"] for e in message.errors)) if message else ""
            a_sub = "Datos de la API de GitLab"
            a_sections = [{"title": "Sin histórico disponible",
                           "note": reason or "No se pudo obtener el histórico de Git de ningún repositorio."}]
        (folder / "activity.md").write_text(to_markdown(a_title, a_sub, a_sections), encoding="utf-8")
        (folder / "activity.html").write_text(to_html(a_title, a_sub, a_sections, [
            ("← Índice de documentación", "index.html"), ("Informe global", "analysis.html"),
            ("Informe multiagente", "agents.html")], kicker="HISTÓRICO DE ACTIVIDAD"), encoding="utf-8")
        activity_files = ["activity.md", "activity.html"]
        (folder / "index.html").write_text(build_documentation_index(name, result), encoding="utf-8")
        (folder / "analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        context.outputs["group_analysis"] = result  # no se publica: ya está en analysis.json
        return {"completion_status": result["completion_status"], "files": ["analysis.json", "analysis.md", "analysis.html", "agents.md", "agents.html",
                                              "index.html", "bug-reports/index.html"] + activity_files}
