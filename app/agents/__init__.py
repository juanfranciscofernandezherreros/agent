"""Adaptadores de los analizadores existentes a una interfaz común."""
from .context import AnalysisContext
from .inventory import InventoryAgent
from .deep import DeepAnalysisAgent
from .functional import FunctionalAnalysisAgent
from .java import JavaAnalysisAgent
from .quality import QualityAnalysisAgent

__all__ = [
    "AnalysisContext", "InventoryAgent", "DeepAnalysisAgent",
    "FunctionalAnalysisAgent", "JavaAnalysisAgent", "QualityAnalysisAgent",
]
