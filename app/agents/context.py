from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AnalysisContext:
    """Contexto compartido de ejecución para los adaptadores de análisis."""
    root: Path
    results: dict[str, Any] = field(default_factory=dict)


class AnalyzerAgent:
    """Interfaz común mínima para los analizadores estáticos existentes."""
    name = "unnamed"

    def run(self, context: AnalysisContext) -> dict:
        raise NotImplementedError
