"""Sistema de comunicación entre agentes: contratos JSON, estados, evidencias, errores y almacén compartido."""
from .contracts import (
    CONTRACT_VERSION, AgentStatus, AgentMessage, AgentError, Evidence,
    AgentSkipped, ContractError, validate_message,
)
from .store import SharedStore

__all__ = ["CONTRACT_VERSION", "AgentStatus", "AgentMessage", "AgentError", "Evidence",
           "AgentSkipped", "ContractError", "validate_message", "SharedStore"]
