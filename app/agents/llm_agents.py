"""Agentes inteligentes (Fase 4). Interpretan los resultados estáticos con un LLM.

Todos son opcionales: si el LLM no está activado se publican como SKIPPED y el análisis
estático no cambia. Su salida se marca siempre como ``llm_inferred``: es una interpretación
que la Fase 5 contrasta con la evidencia estática, nunca un hecho verificado.
"""
from __future__ import annotations

from ..codegen import _redact
from ..communication.contracts import AgentSkipped, Evidence
from ..llm import LLMClient, compact
from .context import AnalysisContext, AnalyzerAgent

VERDICTS = ("likely_bug", "false_positive", "needs_review")


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _refs(items) -> list[dict]:
    """Normaliza citas de evidencia a [{repository?, file, line}]."""
    out = []
    for x in _as_list(items):
        if isinstance(x, dict) and x.get("file"):
            line = x.get("line")
            ref = {"file": str(x["file"]), "line": int(line) if str(line).isdigit() else None}
            if x.get("repository"):
                ref["repository"] = str(x["repository"])
            out.append(ref)
    return out


class LLMAgent(AnalyzerAgent):
    optional = True
    evidence_kind = "llm_claim"

    def __init__(self, client: LLMClient | None = None):
        self._client = client

    def client(self) -> LLMClient:
        client = self._client or LLMClient.from_env()
        if client is None:
            raise AgentSkipped("Agentes LLM desactivados o sin configurar (LLM_AGENTS_ENABLED / LLM_API_KEY).")
        return client

    def finish(self, context: AnalysisContext, client: LLMClient, payload: dict) -> dict:
        payload["generated_by"] = "llm"
        payload["model"] = getattr(client, "model", "unknown")
        payload["confidence"] = "llm_inferred"
        payload["limitations"] = [
            "Interpretación generada por un LLM a partir de resultados estáticos; puede contener errores.",
            "No se ha ejecutado el código. Revisar cada afirmación contra la evidencia citada.",
        ]
        context.results[self.name] = payload
        return payload

    def cited(self, result: dict) -> list[tuple[str, dict]]:
        """Pares (texto, cita) que el agente afirma; lo usa collect_evidence y la validación cruzada."""
        return []

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        return [Evidence(source_agent=self.name, kind=self.evidence_kind, repository=ref.get("repository"),
                         file=ref.get("file"), line=ref.get("line"), excerpt=text,
                         confidence="llm_inferred").to_dict() for text, ref in self.cited(result)]


class FunctionalInterpretationAgent(LLMAgent):
    """Interpreta qué hace funcionalmente el microservicio."""
    name = "llm_functional_interpretation"
    requires = ("functional_analysis", "java_analysis")
    evidence_kind = "functional_claim"

    def run(self, context: AnalysisContext) -> dict:
        client = self.client()
        functional, java = context.results["functional_analysis"], context.results["java_analysis"]
        data = {
            "repository": context.repository,
            "summary": {"functional": functional.get("summary"), "java": java.get("summary")},
            "operations": [{k: x.get(k) for k in ("name", "file", "start_line", "evidence")}
                           for x in functional.get("operations", [])],
            "business_rules": functional.get("business_rules", []),
            "validations": functional.get("validations", []),
            "state_changes": functional.get("state_changes", []),
            "spring_endpoints": java.get("spring_endpoints", []),
            "kafka_listeners": java.get("kafka_listeners", []),
            "kafka_producers": java.get("kafka_producers", []),
            "sql_statements": [{k: x.get(k) for k in ("operation", "file", "line", "excerpt")}
                               for x in java.get("sql_statements", [])],
        }
        answer = client.complete_json(
            "Explica el propósito funcional del microservicio, sus capacidades de negocio y las reglas "
            "de negocio que se deducen. Cada capacidad y regla debe citar al menos una evidencia de la entrada.",
            '{"purpose": str, "capabilities": [{"name": str, "description": str, "evidence": [{"file": str, "line": int}]}], '
            '"business_rules": [{"rule": str, "evidence": [{"file": str, "line": int}]}], "open_questions": [str]}',
            compact(data, max_items=30, max_str=240))
        return self.finish(context, client, {
            "purpose": str(answer.get("purpose", ""))[:3000],
            "capabilities": [{"name": str(x.get("name", ""))[:200], "description": str(x.get("description", ""))[:1500],
                              "evidence": _refs(x.get("evidence"))}
                             for x in _as_list(answer.get("capabilities")) if isinstance(x, dict)][:40],
            "business_rules": [{"rule": str(x.get("rule", ""))[:1500], "evidence": _refs(x.get("evidence"))}
                               for x in _as_list(answer.get("business_rules")) if isinstance(x, dict)][:60],
            "open_questions": [str(x)[:500] for x in _as_list(answer.get("open_questions"))][:20],
        })

    def cited(self, result):
        return ([(c["name"], r) for c in result.get("capabilities", []) for r in c["evidence"]] +
                [(b["rule"], r) for b in result.get("business_rules", []) for r in b["evidence"]])


class BugReviewAgent(LLMAgent):
    """Revisa cada candidato heurístico de bug con su contexto de código."""
    name = "llm_bug_review"
    requires = ("quality_analysis",)
    evidence_kind = "bug_review"
    max_candidates = 40

    @staticmethod
    def ref(candidate: dict) -> str:
        return f"{candidate.get('code')}@{candidate.get('file')}:{candidate.get('line')}"

    def _snippet(self, context: AnalysisContext, candidate: dict, radius: int = 6) -> str:
        try:
            path = (context.root / str(candidate.get("file"))).resolve()
            if context.root.resolve() not in path.parents or path.is_symlink() or path.stat().st_size > 1_000_000:
                return ""
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except (OSError, TypeError, AttributeError):
            return ""
        line = int(candidate.get("line") or 1)
        start = max(0, line - 1 - radius)
        return _redact("\n".join(f"{n}: {text[:240]}" for n, text in enumerate(lines[start:line + radius], start + 1)))

    def run(self, context: AnalysisContext) -> dict:
        candidates = context.results["quality_analysis"].get("bug_candidates", [])
        if not candidates:
            raise AgentSkipped("No hay candidatos de bug que revisar.")
        client = self.client()
        order = {"high": 0, "medium": 1, "low": 2}
        chosen = sorted(candidates, key=lambda x: order.get(x.get("severity"), 3))[:self.max_candidates]
        data = [{"ref": self.ref(x), "code": x.get("code"), "severity": x.get("severity"), "title": x.get("title"),
                 "file": x.get("file"), "line": x.get("line"), "context": self._snippet(context, x)} for x in chosen]
        answer = client.complete_json(
            "Revisa cada candidato de bug detectado por reglas heurísticas. Para cada 'ref' decide si es un bug "
            "probable, un falso positivo o si necesita revisión humana, y justifícalo con el contexto dado. "
            "Usa exactamente los 'ref' de la entrada; no añadas otros.",
            '{"reviews": [{"ref": str, "verdict": "likely_bug|false_positive|needs_review", '
            '"rationale": str, "suggested_fix": str}]}',
            compact(data, max_items=self.max_candidates, max_str=2500), max_tokens=4000)
        reviews = []
        for x in _as_list(answer.get("reviews")):
            if not isinstance(x, dict) or not x.get("ref"):
                continue
            verdict = str(x.get("verdict", "")).strip().lower()
            reviews.append({"ref": str(x["ref"])[:400], "verdict": verdict if verdict in VERDICTS else "needs_review",
                            "rationale": str(x.get("rationale", ""))[:1500],
                            "suggested_fix": str(x.get("suggested_fix", ""))[:1500]})
        counts = {v: sum(r["verdict"] == v for r in reviews) for v in VERDICTS}
        return self.finish(context, client, {
            "reviews": reviews[:self.max_candidates * 2],
            "summary": {"candidates_total": len(candidates), "candidates_sent": len(chosen),
                        "reviewed": len(reviews), **counts}})

    def cited(self, result):
        out = []
        for r in result.get("reviews", []):
            _, _, location = r["ref"].partition("@")
            file, _, line = location.rpartition(":")
            if file:
                out.append((r["verdict"] + ": " + r["rationale"], {"file": file, "line": int(line) if line.isdigit() else None}))
        return out


class ArchitectureExplanationAgent(LLMAgent):
    """Explica la arquitectura del microservicio."""
    name = "llm_architecture_explanation"
    requires = ("inventory", "deep_analysis", "java_analysis")
    evidence_kind = "architecture_claim"

    def run(self, context: AnalysisContext) -> dict:
        client = self.client()
        inv, deep, java = (context.results[k] for k in self.requires)
        data = {
            "repository": context.repository,
            "languages": inv.get("languages"), "manifests": inv.get("manifests"), "top_level": inv.get("top_level"),
            "architecture": deep.get("architecture"), "dependencies": deep.get("dependencies"),
            "routes": deep.get("api", {}).get("route_candidates", []),
            "integrations": {k: v[:6] for k, v in deep.get("integrations", {}).items() if v},
            "data_models": deep.get("data", {}).get("model_candidates", []),
            "configuration": deep.get("configuration"),
            "java_summary": java.get("summary"),
            "classes": [{k: x.get(k) for k in ("kind", "name", "file", "line")} for x in java.get("classes", [])],
            "injections": java.get("injections", []),
            "spring_endpoints": java.get("spring_endpoints", []),
            "kafka_listeners": java.get("kafka_listeners", []),
        }
        answer = client.complete_json(
            "Explica la arquitectura del microservicio: visión general, componentes con su responsabilidad, "
            "integraciones externas (bases de datos, mensajería, APIs) y riesgos arquitectónicos. "
            "Cita evidencias de la entrada en cada componente e integración.",
            '{"overview": str, "components": [{"name": str, "responsibility": str, "evidence": [{"file": str, "line": int}]}], '
            '"integrations": [{"name": str, "type": str, "description": str, "evidence": [{"file": str, "line": int}]}], '
            '"risks": [str]}',
            compact(data, max_items=25, max_str=240))
        return self.finish(context, client, {
            "overview": str(answer.get("overview", ""))[:4000],
            "components": [{"name": str(x.get("name", ""))[:200], "responsibility": str(x.get("responsibility", ""))[:1500],
                            "evidence": _refs(x.get("evidence"))}
                           for x in _as_list(answer.get("components")) if isinstance(x, dict)][:40],
            "integrations": [{"name": str(x.get("name", ""))[:200], "type": str(x.get("type", ""))[:80],
                              "description": str(x.get("description", ""))[:1500], "evidence": _refs(x.get("evidence"))}
                             for x in _as_list(answer.get("integrations")) if isinstance(x, dict)][:40],
            "risks": [str(x)[:800] for x in _as_list(answer.get("risks"))][:20],
        })

    def cited(self, result):
        return [(x["name"], r) for key in ("components", "integrations") for x in result.get(key, []) for r in x["evidence"]]


class EvidenceCorrelationAgent(LLMAgent):
    """Correlaciona evidencias entre microservicios (ámbito grupo)."""
    name = "llm_evidence_correlation"
    requires = ("integration_analysis",)
    scope = "group"
    evidence_kind = "flow_claim"

    def run(self, context: AnalysisContext) -> dict:
        repositories = context.data.get("repositories", [])
        integration = context.results["integration_analysis"]
        if not integration.get("topic_candidates") and not integration.get("shared_contract_candidates"):
            raise AgentSkipped("No hay topics ni contratos candidatos que correlacionar.")
        client = self.client()
        data = {
            "services": [{
                "name": r.get("name"),
                "java_summary": r.get("java_analysis", {}).get("summary"),
                "purpose": (r.get("agent_insights", {}).get("llm_functional_interpretation") or {}).get("purpose"),
                "endpoints": [{k: x.get(k) for k in ("arguments", "file", "line")}
                              for x in r.get("java_analysis", {}).get("spring_endpoints", [])][:15],
            } for r in repositories],
            "topic_candidates": integration.get("topic_candidates", []),
            "shared_contract_candidates": integration.get("shared_contract_candidates", []),
        }
        answer = client.complete_json(
            "Correlaciona las evidencias entre microservicios y describe los flujos de datos probables "
            "(quién produce, quién consume y por qué canal). Cada flujo debe citar evidencias de la entrada "
            "(repositorio, archivo y línea) e indicar confianza alta, media o baja.",
            '{"flows": [{"description": str, "from": str, "to": str, "via": str, "confidence": "alta|media|baja", '
            '"evidence": [{"repository": str, "file": str, "line": int}]}], "observations": [str]}',
            compact(data, max_items=30, max_str=240), max_tokens=4000)
        return self.finish(context, client, {
            "flows": [{"description": str(x.get("description", ""))[:1500], "from": str(x.get("from", ""))[:200],
                       "to": str(x.get("to", ""))[:200], "via": str(x.get("via", ""))[:300],
                       "confidence": str(x.get("confidence", "baja"))[:20], "evidence": _refs(x.get("evidence"))}
                      for x in _as_list(answer.get("flows")) if isinstance(x, dict)][:60],
            "observations": [str(x)[:800] for x in _as_list(answer.get("observations"))][:20],
        })

    def cited(self, result):
        return [(x["description"], r) for x in result.get("flows", []) for r in x["evidence"]]
