from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AnalysisContext:
    """Contexto compartido de ejecución para los adaptadores de análisis.

    - ``root``: carpeta del repositorio clonado (None en agentes de ámbito grupo).
    - ``results``: resultados ya producidos, indexados por ``AnalyzerAgent.name``.
    - ``data``: datos de entrada adicionales (p. ej. la lista de repositorios del grupo).
    """
    root: Path | None = None
    results: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)


class AnalyzerAgent:
    """Interfaz común de todos los analizadores.

    Cada agente declara:
    - ``name``: clave única bajo la que publica su resultado en ``context.results``.
    - ``requires``: nombres de los resultados que necesita antes de ejecutarse.
    - ``scope``: ``"repository"`` (se ejecuta por microservicio) o ``"group"``.
    """
    name: str = "unnamed"
    requires: tuple[str, ...] = ()
    scope: str = "repository"

    def run(self, context: AnalysisContext) -> dict:
        raise NotImplementedError
