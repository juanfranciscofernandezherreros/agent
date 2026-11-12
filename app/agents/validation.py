"""Validación cruzada (Fase 5): unos agentes revisan los resultados de otros.

Las comprobaciones son deterministas. Contrastan (a) los analizadores estáticos entre sí y
(b) las afirmaciones de los agentes LLM contra la evidencia estática, para detectar
contradicciones, citas inexistentes y huecos de cobertura.

Estado de cada comprobación:
- consistent      los agentes coinciden
- warning         discrepancia o hueco que conviene revisar
- contradiction   dos agentes afirman cosas incompatibles, o un LLM cita algo que no existe
- not_applicable  no hay datos para comparar
"""
from __future__ import annotations

import re

from ..communication.contracts import Evidence
from .context import AnalysisContext, AnalyzerAgent
from .llm_agents import BugReviewAgent

STATIC = ("inventory", "deep_analysis", "functional_analysis", "java_analysis", "quality_analysis")
LLM_REPOSITORY = ("llm_functional_interpretation", "llm_bug_review", "llm_architecture_explanation")
MAX_ITEMS = 50


def _check(cid, title, agents, status, detail, items=None):
    return {"id": cid, "title": title, "agents": list(agents), "status": status,
            "detail": detail, "items": (items or [])[:MAX_ITEMS]}


def _summarise(checks, reviewed):
    counts = {s: sum(c["status"] == s for c in checks)
              for s in ("consistent", "warning", "contradiction", "not_applicable")}
    status = "CONTRADICTIONS" if counts["contradiction"] else "WARNINGS" if counts["warning"] else "CONSISTENT"
    return {
        "status": status, "summary": counts, "checks": checks, "reviewed_agents": sorted(reviewed),
        "limitations": [
            "La validación cruzada compara resultados entre agentes; no ejecuta el código ni confirma comportamiento.",
            "Que dos analizadores heurísticos coincidan no demuestra que ambos acierten.",
        ],
    }


def _inventory_index(inventory: dict) -> tuple[set[str], bool]:
    files = {x.get("path") for x in inventory.get("file_inventory", [])}
    return files, len(files) >= 30000  # el inventario se trunca a 30000 archivos


def _line_count(root, rel: str) -> int | None:
    try:
        path = (root / rel).resolve()
        if root.resolve() not in path.parents or path.stat().st_size > 2_000_000:
            return None
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except (OSError, AttributeError, TypeError):
        return None


def check_citations(agent: str, claims, files: set[str], truncated: bool, root=None) -> dict:
    """Comprueba que cada cita (archivo, línea) de un agente LLM existe en el repositorio."""
    bad, uncited, total = [], 0, 0
    for text, refs in claims:
        if not refs:
            uncited += 1
        for ref in refs:
            total += 1
            file, line = ref.get("file"), ref.get("line")
            if file not in files:
                if not truncated:
                    bad.append({"claim": str(text)[:200], "file": file, "line": line, "problem": "archivo inexistente"})
                continue
            count = _line_count(root, file) if root is not None and line else None
            if count is not None and line > count:
                bad.append({"claim": str(text)[:200], "file": file, "line": line,
                            "problem": f"línea fuera de rango (el archivo tiene {count})"})
    title = f"Citas de {agent} contra el inventario"
    agents = (agent, "inventory")
    if not claims:
        return _check("llm_citations:" + agent, title, agents, "not_applicable", "El agente no hizo afirmaciones.")
    if bad:
        return _check("llm_citations:" + agent, title, agents, "contradiction",
                      f"{len(bad)} de {total} citas no se corresponden con el repositorio.", bad)
    if uncited:
        return _check("llm_citations:" + agent, title, agents, "warning",
                      f"{uncited} afirmaciones no citan ninguna evidencia; el resto ({total} citas) es correcto.")
    return _check("llm_citations:" + agent, title, agents, "consistent", f"Las {total} citas existen en el repositorio.")


class CrossValidationAgent(AnalyzerAgent):
    """Revisa por microservicio los resultados de los agentes estáticos y LLM."""
    name = "cross_validation"
    requires = STATIC
    after = LLM_REPOSITORY
    optional = True

    def run(self, context: AnalysisContext) -> dict:
        r = context.results
        inv, deep, functional, java, quality = (r[k] for k in STATIC)
        files, truncated = _inventory_index(inv)
        js = java.get("summary", {})
        checks = []

        # 1. Inventario ↔ analizador Java
        java_files = inv.get("languages", {}).get("Java", 0)
        if java_files and not js.get("classes"):
            checks.append(_check("inventory_vs_java", "Archivos Java frente a clases detectadas", ("inventory", "java_analysis"),
                                 "contradiction", f"El inventario cuenta {java_files} archivos Java pero el analizador Java no detecta ninguna clase."))
        elif js.get("classes") and not java_files:
            checks.append(_check("inventory_vs_java", "Archivos Java frente a clases detectadas", ("inventory", "java_analysis"),
                                 "contradiction", f"El analizador Java detecta {js.get('classes')} clases pero el inventario no cuenta archivos Java."))
        else:
            checks.append(_check("inventory_vs_java", "Archivos Java frente a clases detectadas", ("inventory", "java_analysis"),
                                 "consistent" if java_files else "not_applicable",
                                 f"{java_files} archivos Java, {js.get('classes', 0)} clases."))

        # 2. Tests: análisis profundo ↔ calidad
        deep_tests = len(deep.get("tests", {}).get("files", []))
        quality_tests = quality.get("score_factors", {}).get("test_files_detected")
        checks.append(_check("tests_deep_vs_quality", "Número de tests usado en la puntuación", ("deep_analysis", "quality_analysis"),
                             "consistent" if deep_tests == quality_tests else "contradiction",
                             f"Análisis profundo: {deep_tests}; calidad: {quality_tests}."))

        # 3. Mensajería: Java ↔ análisis profundo
        kafka = js.get("kafka_listeners", 0) + js.get("kafka_producers", 0)
        messaging = len(deep.get("integrations", {}).get("messaging", []))
        if kafka and not messaging:
            checks.append(_check("messaging_java_vs_deep", "Mensajería detectada", ("java_analysis", "deep_analysis"), "warning",
                                 f"El analizador Java encuentra {kafka} usos de Kafka pero el análisis profundo no registra integración de mensajería.",
                                 [{"file": x.get("file"), "line": x.get("line")} for x in java.get("kafka_listeners", []) + java.get("kafka_producers", [])]))
        else:
            checks.append(_check("messaging_java_vs_deep", "Mensajería detectada", ("java_analysis", "deep_analysis"),
                                 "consistent" if kafka else "not_applicable", f"Java: {kafka}; análisis profundo: {messaging}."))

        # 4. API: endpoints Spring ↔ rutas del análisis profundo
        endpoints = js.get("spring_endpoints", 0)
        routes = len(deep.get("api", {}).get("route_candidates", []))
        if endpoints and not routes:
            checks.append(_check("api_java_vs_deep", "Superficie de API", ("java_analysis", "deep_analysis"), "warning",
                                 f"Hay {endpoints} endpoints Spring que el análisis profundo no lista como rutas (su sección de API está incompleta).",
                                 [{"file": x.get("file"), "line": x.get("line")} for x in java.get("spring_endpoints", [])]))
        else:
            checks.append(_check("api_java_vs_deep", "Superficie de API", ("java_analysis", "deep_analysis"),
                                 "consistent" if endpoints or routes else "not_applicable",
                                 f"Endpoints Spring: {endpoints}; rutas: {routes}."))

        # 5. Los hallazgos apuntan a archivos inventariados
        for cid, agent, items in (("quality_files", "quality_analysis", quality.get("bug_candidates", [])),
                                  ("functional_files", "functional_analysis", functional.get("operations", []))):
            missing = sorted({x.get("file") for x in items if x.get("file") not in files})
            if truncated or not items:
                status, detail = "not_applicable", "Sin hallazgos o inventario truncado."
            elif missing:
                status, detail = "contradiction", f"{len(missing)} archivos citados no están en el inventario."
            else:
                status, detail = "consistent", f"Los {len(items)} hallazgos apuntan a archivos inventariados."
            checks.append(_check(cid, f"Archivos citados por {agent}", (agent, "inventory"), status, detail,
                                 [{"file": f} for f in missing]))

        # 6. Revisión LLM de bugs ↔ candidatos heurísticos
        review = r.get("llm_bug_review")
        if review:
            by_ref = {BugReviewAgent.ref(x): x for x in quality.get("bug_candidates", [])}
            reviews = review.get("reviews", [])
            unknown = [{"ref": x["ref"], "problem": "el LLM revisa un candidato que no existe"} for x in reviews if x["ref"] not in by_ref]
            checks.append(_check("bug_review_refs", "Candidatos revisados por el LLM", ("llm_bug_review", "quality_analysis"),
                                 "contradiction" if unknown else "consistent",
                                 f"{len(unknown)} revisiones no corresponden a ningún candidato." if unknown
                                 else f"Las {len(reviews)} revisiones corresponden a candidatos reales.", unknown))
            sent = review.get("summary", {}).get("candidates_sent", 0)
            seen = {x["ref"] for x in reviews if x["ref"] in by_ref}
            if sent and len(seen) < sent:
                checks.append(_check("bug_review_coverage", "Cobertura de la revisión LLM", ("llm_bug_review", "quality_analysis"), "warning",
                                     f"Se enviaron {sent} candidatos y solo {len(seen)} recibieron veredicto."))
            disagreements = [{"ref": x["ref"], "severity": by_ref[x["ref"]].get("severity"), "verdict": x["verdict"],
                              "rationale": x["rationale"][:300], "file": by_ref[x["ref"]].get("file"), "line": by_ref[x["ref"]].get("line")}
                             for x in reviews if x["ref"] in by_ref and x["verdict"] == "false_positive"
                             and by_ref[x["ref"]].get("severity") == "high"]
            confirmed = sum(1 for x in reviews if x["ref"] in by_ref and x["verdict"] == "likely_bug")
            checks.append(_check("bug_review_disagreement", "Acuerdo entre heurística y LLM en prioridad alta",
                                 ("llm_bug_review", "quality_analysis"),
                                 "contradiction" if disagreements else "consistent",
                                 (f"{len(disagreements)} candidatos de prioridad alta son falsos positivos según el LLM: requieren decisión humana."
                                  if disagreements else f"Sin discrepancias en prioridad alta; {confirmed} candidatos corroborados como bug probable."),
                                 disagreements))

        # 7. Citas de los agentes LLM ↔ inventario
        functional_llm = r.get("llm_functional_interpretation")
        if functional_llm:
            claims = ([(c["name"], c["evidence"]) for c in functional_llm.get("capabilities", [])] +
                      [(b["rule"], b["evidence"]) for b in functional_llm.get("business_rules", [])])
            checks.append(check_citations("llm_functional_interpretation", claims, files, truncated, context.root))
        architecture = r.get("llm_architecture_explanation")
        if architecture:
            claims = [(x["name"], x["evidence"]) for key in ("components", "integrations") for x in architecture.get(key, [])]
            checks.append(check_citations("llm_architecture_explanation", claims, files, truncated, context.root))
            # 8. Integraciones que afirma el LLM ↔ evidencia estática
            text = " ".join((x["name"] + " " + x["type"]).lower() for x in architecture.get("integrations", []))
            unsupported = []
            if re.search(r"\bkafka\b", text) and not kafka and not messaging:
                unsupported.append({"claim": "Kafka", "problem": "ningún analizador estático detecta Kafka"})
            if re.search(r"\b(sql|jdbc|jpa|postgres\w*|mysql|oracle|base de datos|database)\b", text) and not js.get("sql_statements") \
                    and not deep.get("integrations", {}).get("database") and not deep.get("data", {}).get("model_candidates"):
                unsupported.append({"claim": "Base de datos", "problem": "ningún analizador estático detecta acceso a datos"})
            checks.append(_check("architecture_integrations", "Integraciones descritas por el LLM",
                                 ("llm_architecture_explanation", "java_analysis", "deep_analysis"),
                                 "contradiction" if unsupported else "consistent" if text.strip() else "not_applicable",
                                 f"{len(unsupported)} integraciones no tienen respaldo estático." if unsupported
                                 else "Las integraciones descritas tienen respaldo estático." if text.strip() else "El LLM no describe integraciones.",
                                 unsupported))

        return _summarise(checks, set(STATIC) | {k for k in LLM_REPOSITORY if k in r})

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        return _problems_as_evidence(self.name, result)


class GroupCrossValidationAgent(AnalyzerAgent):
    """Revisa la correlación entre microservicios (estática y LLM)."""
    name = "group_cross_validation"
    requires = ("integration_analysis",)
    after = ("llm_evidence_correlation",)
    scope = "group"
    optional = True

    def run(self, context: AnalysisContext) -> dict:
        repositories = context.data.get("repositories", [])
        integration = context.results["integration_analysis"]
        names = {r.get("name") for r in repositories}
        checks = []

        # 1. Topics con un solo extremo
        topics = integration.get("topic_candidates", [])
        orphans = []
        for t in topics:
            roles = set(t.get("roles_detected", []))
            if "consumer_candidate" in roles and "producer_candidate" not in roles:
                orphans.append({"topic": t["topic"], "problem": "consumidor sin productor detectado", "repositories": t.get("repositories")})
            elif "producer_candidate" in roles and "consumer_candidate" not in roles:
                orphans.append({"topic": t["topic"], "problem": "productor sin consumidor detectado", "repositories": t.get("repositories")})
        checks.append(_check("topic_endpoints", "Topics con productor y consumidor", ("integration_analysis", "java_analysis"),
                             "warning" if orphans else "consistent" if topics else "not_applicable",
                             (f"{len(orphans)} de {len(topics)} topics solo tienen un extremo dentro del conjunto analizado "
                              "(el otro puede estar fuera del conjunto o no haberse detectado)." if orphans
                              else f"{len(topics)} topics candidatos."), orphans))

        # 2. Resumen de las validaciones individuales
        flagged = [{"repository": r.get("name"), "status": (r.get("agent_insights", {}).get("cross_validation") or {}).get("status")}
                   for r in repositories]
        bad = [x for x in flagged if x["status"] == "CONTRADICTIONS"]
        checks.append(_check("repository_validations", "Validaciones por microservicio", ("cross_validation",),
                             "warning" if bad else "consistent",
                             f"{len(bad)} de {len(flagged)} microservicios tienen contradicciones entre agentes.", bad))

        # 3. Flujos descritos por el LLM ↔ correlación estática e inventarios
        correlation = context.results.get("llm_evidence_correlation")
        if correlation:
            known = {t["topic"].lower() for t in topics} | {c["contract"].lower() for c in integration.get("shared_contract_candidates", [])}
            inventories = {r.get("name"): _inventory_index(r.get("inventory", {})) for r in repositories}
            problems, claims_ok = [], 0
            for flow in correlation.get("flows", []):
                label = flow["description"][:160]
                for side in ("from", "to"):
                    if flow[side] and flow[side] not in names:
                        problems.append({"flow": label, "problem": f"'{side}' no es un microservicio analizado: {flow[side]}"})
                if flow["via"] and not any(k in flow["via"].lower() for k in known):
                    problems.append({"flow": label, "problem": f"el canal '{flow['via']}' no es un topic ni contrato detectado"})
                if not flow["evidence"]:
                    problems.append({"flow": label, "problem": "sin evidencia citada"})
                for ref in flow["evidence"]:
                    files, truncated = inventories.get(ref.get("repository"), (None, False))
                    if files is None:
                        problems.append({"flow": label, "problem": f"cita un repositorio desconocido: {ref.get('repository')}"})
                    elif ref["file"] not in files and not truncated:
                        problems.append({"flow": label, "problem": f"cita un archivo inexistente: {ref.get('repository')}/{ref['file']}"})
                    else:
                        claims_ok += 1
            checks.append(_check("llm_flows", "Flujos descritos por el LLM", ("llm_evidence_correlation", "integration_analysis", "inventory"),
                                 "contradiction" if problems else "consistent" if correlation.get("flows") else "not_applicable",
                                 f"{len(problems)} problemas en los flujos descritos." if problems
                                 else f"{len(correlation.get('flows', []))} flujos respaldados por {claims_ok} citas válidas.", problems))

        reviewed = {"integration_analysis"} | ({"llm_evidence_correlation"} if correlation else set())
        return _summarise(checks, reviewed)

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        return _problems_as_evidence(self.name, result)


def _problems_as_evidence(agent: str, result: dict) -> list[dict]:
    out = []
    for check in result.get("checks", []):
        if check["status"] not in ("contradiction", "warning"):
            continue
        items = check["items"] or [{}]
        for item in items:
            line = item.get("line")
            out.append(Evidence(
                source_agent=agent, kind=check["status"], repository=item.get("repository") if isinstance(item.get("repository"), str) else None,
                file=item.get("file"), line=line if isinstance(line, int) else None,
                excerpt=check["detail"] + (" — " + str(item.get("problem")) if item.get("problem") else ""),
                confidence="observed_static", ref=check["id"]).to_dict())
    return out
