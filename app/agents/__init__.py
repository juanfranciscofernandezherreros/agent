"""Adaptadores de los analizadores existentes a una interfaz común."""
from .context import AnalysisContext
from .inventory import InventoryAgent
from .deep import DeepAnalysisAgent
from .functional import FunctionalAnalysisAgent
from .java import JavaAnalysisAgent
from .quality import QualityAnalysisAgent
from .integration import IntegrationAnalysisAgent
from .llm_agents import (
    FunctionalInterpretationAgent, BugReviewAgent, ArchitectureExplanationAgent,
    EvidenceCorrelationAgent,
)
from .validation import CrossValidationAgent, GroupCrossValidationAgent
from .reporting import RepositoryReportingAgent, GroupReportingAgent

__all__ = [
    "AnalysisContext", "InventoryAgent", "DeepAnalysisAgent",
    "FunctionalAnalysisAgent", "JavaAnalysisAgent", "QualityAnalysisAgent",
    "IntegrationAnalysisAgent", "FunctionalInterpretationAgent", "BugReviewAgent",
    "ArchitectureExplanationAgent", "EvidenceCorrelationAgent",
    "CrossValidationAgent", "GroupCrossValidationAgent",
    "RepositoryReportingAgent", "GroupReportingAgent",
]
