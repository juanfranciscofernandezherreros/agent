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
