"""Supervisor: decide qué agentes se ejecutan, en qué orden y con qué dependencias."""
from __future__ import annotations

from .agents import (
    AnalysisContext, InventoryAgent, DeepAnalysisAgent, FunctionalAnalysisAgent,
    JavaAnalysisAgent, QualityAnalysisAgent, IntegrationAnalysisAgent,
)
from .agents.context import AnalyzerAgent


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
            for dep in agent.requires:
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
                     if all(d in done or d not in names for d in a.requires)]
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
        """Ejecuta el plan. Un fallo se propaga al llamador (igual que antes del supervisor)."""
        for agent in self.plan(scope, only, available=set(context.results)):
            missing = [d for d in agent.requires if d not in context.results]
            if missing:
                raise SupervisorError(f"{agent.name} no puede ejecutarse; falta: {', '.join(missing)}")
            agent.run(context)
        return context.results


def default_supervisor() -> Supervisor:
    return Supervisor([
        InventoryAgent(), DeepAnalysisAgent(), FunctionalAnalysisAgent(),
        JavaAnalysisAgent(), QualityAnalysisAgent(), IntegrationAnalysisAgent(),
    ])
