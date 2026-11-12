from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AnalysisContext:
    """Contexto compartido de ejecución para los adaptadores de análisis.

    - ``root``: carpeta del repositorio clonado (None en agentes de ámbito grupo).
    - ``results``: resultados ya producidos, indexados por ``AnalyzerAgent.name``.
    - ``repository``: nombre del microservicio analizado.
    - ``store``: almacén compartido donde el supervisor publica los mensajes.
    - ``data``: datos de entrada adicionales (p. ej. la lista de repositorios del grupo).
    """
    root: Path | None = None
    repository: str | None = None
    store: Any = None  # SharedStore: almacén compartido de mensajes (Fase 3)
    results: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)


class AnalyzerAgent:
    """Interfaz común de todos los analizadores.

    Cada agente declara:
    - ``name``: clave única bajo la que publica su resultado en ``context.results``.
    - ``requires``: nombres de los resultados que necesita antes de ejecutarse.
    - ``after``: agentes tras los que debe ejecutarse si están en el plan (orden, no dependencia).
    - ``scope``: ``"repository"`` (se ejecuta por microservicio) o ``"group"``.
    - ``optional``: si es True, su fallo u omisión no aborta el análisis.

    ``run`` devuelve el payload. Puede lanzar ``AgentSkipped`` si no procede ejecutarse.
    ``collect_evidence`` extrae del payload evidencias trazables (contrato ``Evidence``).
    """
    name: str = "unnamed"
    requires: tuple[str, ...] = ()
    after: tuple[str, ...] = ()
    scope: str = "repository"
    optional: bool = False

    def collect_evidence(self, result: dict, context: AnalysisContext) -> list[dict]:
        return []

    def run(self, context: AnalysisContext) -> dict:
        raise NotImplementedError
