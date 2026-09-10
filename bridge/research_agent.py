"""Grounded Dredge Echo research flow: Tavily evidence -> Nebius reasoning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from bridge.llm_adapter import LLMAdapter
from bridge.search_adapter import TavilySearchAdapter


@dataclass
class ResearchResult:
    question: str
    evidence: Dict[str, Any]
    answer: str


class ResearchAgent:
    """Compose live retrieval with the existing model-agnostic LLM bridge."""

    def __init__(
        self,
        *,
        search: Optional[TavilySearchAdapter] = None,
        llm: Optional[LLMAdapter] = None,
    ) -> None:
        self.search = search or TavilySearchAdapter()
        self.llm = llm or LLMAdapter(backend="nebius")

    def research(self, question: str, *, max_results: int = 5) -> ResearchResult:
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        evidence = self.search.search(question, max_results=max_results)
        answer = self.llm.generate(
            "research_and_reason",
            source="tavily_web_evidence",
            target="grounded_answer",
            source_value={
                "question": question,
                "instructions": (
                    "Answer using the supplied evidence. Distinguish evidence from inference, "
                    "do not invent sources, and include source URLs for material claims."
                ),
                "evidence": evidence,
            },
        )
        return ResearchResult(question=question, evidence=evidence, answer=answer)
