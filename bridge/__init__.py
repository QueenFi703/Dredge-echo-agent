# Bridge package
from .llm_adapter import LLMAdapter, LLMBackendError
from .research_agent import ResearchAgent, ResearchResult
from .search_adapter import SearchBackendError, TavilySearchAdapter
from .verification import NemotronVerifier, VerificationError

__all__ = [
    "LLMAdapter",
    "LLMBackendError",
    "NemotronVerifier",
    "PythonAdapter",
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
