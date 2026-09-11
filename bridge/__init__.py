# Bridge package
from .adaptive_agent import AdaptiveResearchAgent, AdaptiveResearchResult, IntelligenceEvent
from .control_plane import (
    DredgeControlPlane,
    IntelligenceState,
    InvestigationSignals,
    OrchestrationMode,
    ReasoningDepth,
)
from .execution_graph import ExecutionGraph, ExecutionNode, GraphMutation, NodeStatus
from .llm_adapter import LLMAdapter, LLMBackendError
from .research_agent import ResearchAgent, ResearchResult
from .search_adapter import SearchBackendError, TavilySearchAdapter
from .verification import NemotronVerifier, VerificationError

__all__ = [
    "AdaptiveResearchAgent",
    "AdaptiveResearchResult",
    "DredgeControlPlane",
    "ExecutionGraph",
    "ExecutionNode",
    "GraphMutation",
    "IntelligenceEvent",
    "IntelligenceState",
    "InvestigationSignals",
    "LLMAdapter",
    "LLMBackendError",
    "NemotronVerifier",
    "NodeStatus",
    "OrchestrationMode",
    "PythonAdapter",
    "ReasoningDepth",
    "ResearchAgent",
    "ResearchResult",
    "SearchBackendError",
    "TavilySearchAdapter",
    "VerificationError",
]


def __getattr__(name):
    """Load the legacy Aster bridge only when a caller requests it."""
    if name == "PythonAdapter":
        from .python_adapter import PythonAdapter

        return PythonAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
