"""Supervisor: decide qué agentes se ejecutan, en qué orden y con qué dependencias."""
from __future__ import annotations

from .agents import (
    AnalysisContext, InventoryAgent, DeepAnalysisAgent, FunctionalAnalysisAgent,
    JavaAnalysisAgent, QualityAnalysisAgent, IntegrationAnalysisAgent,
    FunctionalInterpretationAgent, BugReviewAgent, ArchitectureExplanationAgent,
    EvidenceCorrelationAgent, CrossValidationAgent, GroupCrossValidationAgent,
    RepositoryReportingAgent, GroupReportingAgent,
)
from .agents.context import AnalyzerAgent
from .communication import AgentMessage, AgentSkipped, AgentStatus, SharedStore

MAX_EVIDENCE_PER_MESSAGE = 500


class SupervisorError(RuntimeError):
    pass


class Supervisor:
    def __init__(self, agents: list[AnalyzerAgent]):
        self._agents: dict[str, AnalyzerAgent] = {}
        for agent in agents:
            if agent.name in self._agents:
                raise SupervisorError(f"Agente duplicado: {agent.name}")
            self._agents[agent.name] = agent
        for agent in agents:
            for dep in (*agent.requires, *agent.after):
                if dep not in self._agents:
                    raise SupervisorError(f"{agent.name} depende de un agente desconocido: {dep}")
                if self._agents[dep].scope == "group" and agent.scope == "repository":
                    raise SupervisorError(f"{agent.name} (repository) no puede depender de {dep} (group)")
        for scope in ("repository", "group"):
            self.plan(scope)  # detecta ciclos al construir

    @property
    def agents(self) -> list[AnalyzerAgent]:
        return list(self._agents.values())

    def plan(self, scope: str = "repository", only: list[str] | None = None,
             available: set[str] | frozenset[str] = frozenset()) -> list[AnalyzerAgent]:
        """Orden de ejecución (topológico y estable según el orden de registro).

        Un agente va detrás de sus ``requires`` (dependencias) y de sus ``after`` (solo orden).
        ``only`` limita el plan a esos agentes y a sus dependencias transitivas.
        ``available`` son resultados que ya existen en el contexto y no hay que recalcular.
        """
        in_scope = [a for a in self._agents.values() if a.scope == scope]
        if only is not None:
            unknown = [n for n in only if n not in self._agents]
            if unknown:
                raise SupervisorError("Agentes desconocidos: " + ", ".join(unknown))
            wanted: set[str] = set()
            stack = list(only)
            while stack:
                name = stack.pop()
                if name in wanted or name in available:
                    continue
                wanted.add(name)
                stack.extend(self._agents[name].requires)
            in_scope = [a for a in in_scope if a.name in wanted]
        names = {a.name for a in in_scope}
        done: set[str] = set(available)
        ordered: list[AnalyzerAgent] = []
        pending = [a for a in in_scope if a.name not in done]
        while pending:
            ready = [a for a in pending
                     if all(d in done or d not in names for d in (*a.requires, *a.after))]
            if not ready:
                raise SupervisorError("Dependencias cíclicas entre: " + ", ".join(a.name for a in pending))
            nxt = ready[0]
            ordered.append(nxt)
            done.add(nxt.name)
            pending.remove(nxt)
        return ordered

    def describe_plan(self, scope: str = "repository", only: list[str] | None = None) -> list[dict]:
        return [{"step": i, "agent": a.name, "scope": a.scope, "requires": list(a.requires)}
                for i, a in enumerate(self.plan(scope, only), 1)]

    def run(self, context: AnalysisContext, scope: str = "repository",
            only: list[str] | None = None) -> dict:
        """Ejecuta el plan publicando un ``AgentMessage`` por agente en el almacén compartido.

        - Agente obligatorio que falla: se publica FAILED, el resto queda SKIPPED y la
          excepción se propaga (mismo comportamiento que antes del supervisor).
        - Agente opcional que falla o se omite: se publica FAILED/SKIPPED y se continúa;
          los agentes que dependan de él se omiten.
        """
        store = context.store if context.store is not None else SharedStore()
        context.store = store
        repository = None
        if scope == "repository":
            repository = context.repository or "repository"
            context.repository = repository
        plan = self.plan(scope, only, available=set(context.results))
        messages = {a.name: store.publish(AgentMessage(
            agent=a.name, scope=scope, repository=repository, requires=list(a.requires))) for a in plan}
        try:
            for agent in plan:
                message = messages[agent.name]
                missing = [d for d in agent.requires if d not in context.results]
                if missing:
                    reason = "Dependencias no disponibles: " + ", ".join(missing)
                    if agent.optional:
                        message.detail = reason
                        store.publish(message.transition(AgentStatus.SKIPPED))
                        continue
                    message.transition(AgentStatus.RUNNING)
                    message.add_error(reason)
                    store.publish(message.transition(AgentStatus.FAILED))
                    raise SupervisorError(f"{agent.name} no puede ejecutarse. {reason}")
                store.publish(message.transition(AgentStatus.RUNNING))
                try:
                    result = agent.run(context)
                except AgentSkipped as skipped:
                    context.results.pop(agent.name, None)
                    message.detail = str(skipped)
                    store.publish(message.transition(AgentStatus.SKIPPED))
                    if not agent.optional:
                        raise SupervisorError(f"El agente obligatorio {agent.name} se omitió: {skipped}")
                    continue
                except Exception as exc:
                    context.results.pop(agent.name, None)
                    message.add_error(exc, recoverable=agent.optional)
                    store.publish(message.transition(AgentStatus.FAILED))
                    if not agent.optional:
                        raise
                    continue
                context.results[agent.name] = result
                message.payload = result
                evidence = agent.collect_evidence(result, context)[:MAX_EVIDENCE_PER_MESSAGE]
                for item in evidence:
                    if item.get("repository") is None:
                        item["repository"] = repository
                message.evidence = evidence
                store.publish(message.transition(AgentStatus.COMPLETED))
        finally:
            for message in messages.values():
                if message.status == AgentStatus.PENDING:
                    message.detail = "No ejecutado: el análisis se interrumpió antes."
                    store.publish(message.transition(AgentStatus.SKIPPED))
        return context.results


def default_supervisor(llm_client=None) -> Supervisor:
    """Agentes estáticos (obligatorios) + LLM (opcionales, SKIPPED sin LLM) + validación cruzada + agente documental."""
    return Supervisor([
        InventoryAgent(), DeepAnalysisAgent(), FunctionalAnalysisAgent(),
        JavaAnalysisAgent(), QualityAnalysisAgent(), IntegrationAnalysisAgent(),
        FunctionalInterpretationAgent(llm_client), BugReviewAgent(llm_client),
        ArchitectureExplanationAgent(llm_client), EvidenceCorrelationAgent(llm_client),
        CrossValidationAgent(), GroupCrossValidationAgent(),
        RepositoryReportingAgent(), GroupReportingAgent(),
    ])
