def java_catalog(analysis):
    lines = ["## Inventario Java detallado"]
    for repo in analysis.get("repositories", []):
        java = repo.get("java_analysis", {})
        lines += ["", "### " + repo["name"] + " — clases y métodos"]
        for cls in java.get("classes", []):
            lines.append("- **" + cls["kind"] + " " + cls["name"] + "** — " + cls["file"] + ":" + str(cls["line"]))
            for method in java.get("methods", []):
                if method["file"] == cls["file"]:
                    lines.append("  - " + method["name"] + "(" + method["parameters"] + ") — " + method["file"] + ":" + str(method["line"]) + "; llamadas: " + ", ".join(method["calls"][:12]))
        lines += ["", "### " + repo["name"] + " — API, Kafka y SQL"]
        for key, label in (("spring_endpoints", "Spring"), ("kafka_listeners", "Kafka listener"), ("kafka_producers", "Kafka producer candidato"), ("sql_statements", "SQL"), ("avro_contracts", "Contrato")):
            for item in java.get(key, []):
                detail = item.get("arguments") or item.get("expression") or item.get("excerpt") or item.get("name") or ""
                lines.append("- " + label + " " + str(detail)[:240] + " — " + item.get("file", "") + ":" + str(item.get("line", "")))
    return "\n".join(lines) + "\n"

def write_individual_reports(destination, name, inventory, deep, functional, java, member):
    from .deep_analysis import build_analysis_markdown
    import json
    report = build_analysis_markdown(name, inventory, deep)
    report += "\n## Análisis funcional\n" + json.dumps(functional.get("summary", {}), ensure_ascii=False, indent=2)
    report += "\n\n## Java / Spring\n" + json.dumps(java.get("summary", {}), ensure_ascii=False, indent=2)
    report += "\n\n" + java_catalog({"repositories": [{"name": name, "java_analysis": java}]})
    (destination / "analysis.md").write_text(report, encoding="utf-8")
    from .rich_report import build_integral_html
    single = {
        "group_name": name,
        "repositories": [{
            "name": name, "inventory": inventory, "deep_analysis": deep,
            "functional_analysis": functional, "java_analysis": java,
            "artifact_dir": str(destination)
        }],
        "integration_analysis": {"topic_candidates": [], "shared_contract_candidates": [], "limitations": []},
        "failures": [],
        "completion_status": member.get("completion_status", "STATIC_ANALYSIS_COMPLETED"),
        "runtime_validation": member.get("runtime_validation", "NOT_PERFORMED")
    }
    (destination / "analysis.html").write_text(build_integral_html(name, single), encoding="utf-8")
    bug_report = member.get("bug_report")
    links = "<nav class='doc-links'><a href='../../analysis.html'>← Informe global</a>"
    if bug_report:
        links += "<a href='../../" + __import__("html").escape(bug_report, quote=True) + "'>Informe de posibles bugs</a>"
    links += "</nav>"
    html_path = destination / "analysis.html"
    html_text = html_path.read_text(encoding="utf-8").replace("<main>", "<main>" + links, 1)
    html_text = html_text.replace("</style>", ".doc-links{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px}.doc-links a{color:#2457c5;text-decoration:none;border:1px solid #dce3ed;border-radius:7px;padding:7px 10px;font-weight:650}</style>", 1)
    html_path.write_text(html_text, encoding="utf-8")
