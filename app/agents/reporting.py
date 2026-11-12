"""Agente documental (Fase 6): genera los informes individuales por microservicio y los globales.

Conserva los informes existentes (analysis.json/md/html, expedientes de bugs, índices) y añade
el informe multiagente (agents.md / agents.html) con el estado de los agentes, la interpretación
LLM y la validación cruzada.
"""
from __future__ import annotations

import json

from ..agent_report import STATUS_LABEL, build_sections, group_activity_sections, to_html, to_markdown
from ..bug_report import build_bug_report_html, build_bug_reports_index
from ..communication.contracts import AgentSkipped
from ..documentation import build_documentation_index
from ..group_report import markdown, slug
from ..report_details import java_catalog, write_individual_reports
from ..rich_report import build_integral_html
from .context import AnalysisContext, AnalyzerAgent
from .validation import LLM_REPOSITORY, STATIC

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
        insights = {k: v for k, v in context.results.items() if k not in STATIC and k != self.name}
        service = slug(name)
        dest = folder / "repositories" / service
        dest.mkdir(parents=True, exist_ok=True)
        files = []

        report_file = None
        candidates = quality.get("bug_candidates") or []
        if candidates:
            bug_dir = folder / "bug-reports"
            bug_dir.mkdir(parents=True, exist_ok=True)
            report_file = str(len(bug_reports) + 1).zfill(3) + "-" + service + ".html"
            (bug_dir / report_file).write_text(build_bug_report_html(name, group_name, quality, service), encoding="utf-8")
            bug_reports.append({"repository": name, "file": report_file, "count": len(candidates)})
            files.append("bug-reports/" + report_file)
        bug_report = ("bug-reports/" + report_file) if report_file else None

        member = {"project_name": name, "inventory": inv, "deep_analysis": deep,
                  "functional_analysis": functional, "java_analysis": java, "quality_analysis": quality,
                  "bug_report": bug_report, "agent_insights": insights,
                  "completion_status": "STATIC_ANALYSIS_COMPLETED", "runtime_validation": "NOT_PERFORMED"}
        (dest / "analysis.json").write_text(json.dumps(member, indent=2, ensure_ascii=False), encoding="utf-8")
        write_individual_reports(dest, name, inv, deep, functional, java, member)

        sections = build_sections(insights, _runs(context, name, "repository", self.name), "repository")
        title = "Informe multiagente: " + str(name)
        (dest / "agents.md").write_text(to_markdown(title, SUBTITLE, sections), encoding="utf-8")
        links = [("← Ficha técnica", "analysis.html"), ("Informe multiagente global", "../../agents.html"),
                 ("Índice de documentación", "../../index.html")]
        if bug_report:
            links.append(("Posibles bugs", "../../" + bug_report))
        (dest / "agents.html").write_text(to_html(title, SUBTITLE, sections, links), encoding="utf-8")

        artifact_dir = str(dest.relative_to(folder))
        files += [artifact_dir + "/" + f for f in ("analysis.json", "analysis.md", "analysis.html", "agents.md", "agents.html")]
        entry = {"name": name, "inventory": inv, "deep_analysis": deep, "functional_analysis": functional,
                 "java_analysis": java, "quality_analysis": quality, "artifact_dir": artifact_dir,
                 "bug_report": bug_report, "agent_insights": insights}
        context.outputs["repository_entry"] = entry  # no se publica: ya está en analysis.json
        return {"artifact_dir": artifact_dir, "bug_report": bug_report, "files": files}


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
        (bug_dir / "index.html").write_text(build_bug_reports_index(name, bug_reports), encoding="utf-8")

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

        activity_files = []
        if insights.get("group_activity"):
            a_title = "Histórico de actividad: " + str(name)
            a_sub = f"Últimos {insights['group_activity']['window_days']} días · datos de la API de GitLab"
            a_sections = group_activity_sections(insights["group_activity"])
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
