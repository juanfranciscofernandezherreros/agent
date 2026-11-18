"""CLI for analysing a local source tree without cloning or modifying it."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .agents import AnalysisContext
from .communication import SharedStore
from .supervisor import default_supervisor
from .deep_analysis import build_analysis_markdown
from .functional_analysis import build_analysis_html


def analyze_local(source: Path, output: Path, name: str) -> dict:
    source = source.expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"LocalPath no es un directorio: {source}")
    output.mkdir(parents=True, exist_ok=True)
    run_id = re.sub(r"[^A-Za-z0-9_-]", "-", name)[:80] or "local-analysis"
    context = AnalysisContext(root=source, repository=name, store=SharedStore(output / "agent-runs", run_id=run_id))
    default_supervisor().run(context, only=[
        "inventory", "deep_analysis", "functional_analysis", "java_analysis",
        "quality_analysis", "llm_bug_hunter", "llm_bug_review",
        "llm_functional_interpretation", "llm_architecture_explanation",
    ])
    inventory = context.results["inventory"]
    deep = context.results["deep_analysis"]
    functional = context.results["functional_analysis"]
    java = context.results["java_analysis"]
    quality = context.results.get("quality_analysis", {})
    analysis = {
        "analysis_version": "6.5",
        "functional_analysis": functional,
        "project_name": name,
        "source_path": str(source),
        "repository_inventory": inventory,
        "deep_analysis": deep,
        "java_analysis": java,
        "quality_analysis": quality,
        "agent_insights": {k: v for k, v in context.results.items() if k not in (
            "inventory", "deep_analysis", "functional_analysis", "java_analysis", "quality_analysis")},
        "completion_status": "STATIC_ANALYSIS_COMPLETED",
        "runtime_validation": "NOT_PERFORMED",
    }
    # Unifica todas las señales sin perder la procedencia de cada detector.
    production_candidates = quality.get("bug_candidates", [])
    test_candidates = quality.get("test_bug_candidates", [])
    llm_findings = context.results.get("llm_bug_hunter", {}).get("findings", [])
    unified_candidates = []
    for candidate in production_candidates:
        unified_candidates.append({"source": candidate.get("source", "static_quality"), "scope": "production", **candidate})
    for candidate in test_candidates:
        unified_candidates.append({"source": "static_quality", "scope": "test", **candidate})
    for candidate in llm_findings:
        unified_candidates.append({"source": "llm_bug_hunter", "scope": "production", **candidate})

    # Exportación completa de candidatos detectados por análisis estático y agentes LLM.
    bug_export = {
        "schema_version": "1.0",
        "project_name": name,
        "source_path": str(source),
        "completion_status": analysis["completion_status"],
        "runtime_validation": analysis["runtime_validation"],
        "summary": {
            **quality.get("summary", {}),
            "production_candidates": len(production_candidates) + len(llm_findings),
            "test_candidates": len(test_candidates),
            "total_candidates": len(unified_candidates),
        },
        "candidates": unified_candidates,
        "production_candidates": production_candidates,
        "test_candidates": test_candidates,
        "llm_bug_hunter": context.results.get("llm_bug_hunter", {}),
        "llm_bug_review": context.results.get("llm_bug_review", {}),
        "limitations": [
            "Son candidatos detectados estáticamente, no defectos confirmados.",
            "No se ejecutó el repositorio ni sus pruebas.",
            "Los resultados del LLM son inferencias y pueden contener falsos positivos.",
        ],
    }
    from datetime import datetime
    export_datetime = datetime.now().astimezone()
    export_timestamp = export_datetime.strftime("%Y%m%d-%H%M%S")
    bug_export["generated_at"] = export_datetime.isoformat(timespec="seconds")
    timestamped_name = f"possible-bugs-{export_timestamp}.json"
    serialized_bugs = json.dumps(bug_export, indent=2, ensure_ascii=False)
    (output / timestamped_name).write_text(serialized_bugs, encoding="utf-8")
    # Alias estable para compatibilidad con scripts existentes.
    (output / "possible-bugs.json").write_text(serialized_bugs, encoding="utf-8")
    analysis["possible_bugs_export"] = timestamped_name
    analysis["possible_bugs_export_latest"] = "possible-bugs.json"
    (output / "analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    report = build_analysis_markdown(name, inventory, deep)
    report += "\n\n## Análisis funcional\n" + json.dumps(functional.get("summary", {}), ensure_ascii=False, indent=2)
    report += "\n\n## Análisis Java / Spring\n" + json.dumps(java.get("summary", {}), ensure_ascii=False, indent=2)
    report += "\n\n## Posibles bugs\n"
    for finding in quality.get("bug_candidates", []):
        report += f"- **{finding.get('severity', 'low').upper()} · {finding.get('title', 'Posible bug')}** — {finding.get('file', 'N/D')}:{finding.get('line', 'N/D')}\n  {finding.get('description', '')}\n"
    (output / "analysis.md").write_text(report, encoding="utf-8")
    (output / "analysis.html").write_text(build_analysis_html(name, analysis), encoding="utf-8")
    return analysis


def main() -> int:
    parser = argparse.ArgumentParser(description="Static analysis of a local repository.")
    parser.add_argument("--local-path", required=True, help="Path to source repository; it is read-only.")
    parser.add_argument("--output", required=True, help="Directory where reports are written.")
    parser.add_argument("--name", default="", help="Repository label (optional)")
    args = parser.parse_args()
    source = Path(args.local_path)
    label = args.name.strip() or source.resolve().name
    result = analyze_local(source, Path(args.output), label)
    print(f"Análisis terminado: {result['completion_status']}")
    print(f"Informes: {Path(args.output).resolve()}")
    print(f"HTML: {Path(args.output, 'analysis.html').resolve()}")
    print(f"JSON de posibles bugs: {Path(args.output, 'possible-bugs.json').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
