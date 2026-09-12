"""Grounded multi-model Dredge Echo research and arbitration flow."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, Optional

from bridge.llm_adapter import LLMAdapter
from bridge.search_adapter import TavilySearchAdapter
from bridge.verification import NemotronVerifier, verification_counts


@dataclass
class ResearchResult:
    question: str
    evidence: Dict[str, Any]
    answer: str
    draft: str
    verification: Dict[str, Any]
    trace: Dict[str, Any]


class ResearchAgent:
    """Compose live retrieval with the existing model-agnostic LLM bridge."""

    def __init__(
        self,
        *,
        search: Optional[TavilySearchAdapter] = None,
        llm: Optional[LLMAdapter] = None,
        verifier: Optional[NemotronVerifier] = None,
        arbitrator: Optional[LLMAdapter] = None,
        kimi_model: Optional[str] = None,
        nemotron_model: Optional[str] = None,
    ) -> None:
        self.search = search or TavilySearchAdapter()
        self.llm = llm or LLMAdapter(backend="nebius")
        self.verifier = verifier
        self.arbitrator = arbitrator
        self.kimi_model = kimi_model
        self.nemotron_model = nemotron_model

    def research(self, question: str, *, max_results: int = 5) -> ResearchResult:
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        cycle_started = perf_counter()
        started = perf_counter()
        evidence = self.search.search(question, max_results=max_results)
        retrieval_ms = round((perf_counter() - started) * 1000)
        if not evidence.get("sources"):
            raise RuntimeError("Tavily returned no sources; grounded research cannot continue")

        started = perf_counter()
        draft = self.llm.generate(
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
        kimi_ms = round((perf_counter() - started) * 1000)
        if not draft.strip():
            raise RuntimeError("Kimi returned an empty synthesis")
        if self.verifier is None:
            raise RuntimeError("Nemotron verifier is required for grounded research")

        started = perf_counter()
        verification = self.verifier.verify(
            question=question, evidence=evidence, proposed_answer=draft
        )
        nemotron_ms = round((perf_counter() - started) * 1000)

        corrections = [
            claim for claim in verification["claims"]
            if claim["status"] != "SUPPORTED" and claim.get("recommended_correction")
        ]
        answer = draft
        if corrections:
            if self.arbitrator is None:
                raise RuntimeError("An arbitrator is required when verification finds revisions")
            answer = self.arbitrator.generate(
                "arbitrate_evidence_critique",
                source="kimi_draft_and_nemotron_verification",
                target="final_grounded_answer",
                source_value={
                    "question": question,
                    "evidence": evidence,
                    "draft": draft,
                    "verification": verification,
                    "instructions": (
                        "Apply only evidence-supported corrections. Preserve supported claims, "
                        "citations, and useful wording. Evidence outranks model consensus."
                    ),
                },
            )
        if not answer.strip():
            raise RuntimeError("Dredge Echo arbitration returned an empty final answer")

        counts = verification_counts(verification)
        retrieval_trace = {
            "provider": evidence.get("provider") or "Tavily",
            "source_count": len(evidence["sources"]),
            "latency_ms": retrieval_ms,
        }
        if evidence.get("tool"):
            retrieval_trace["tool"] = evidence["tool"]
        if evidence.get("execution_id"):
            retrieval_trace["execution_id"] = evidence["execution_id"]
        trace = {
            "retrieval": retrieval_trace,
            "synthesis": {"provider": "Kimi", "model": self.kimi_model, "status": "COMPLETE", "latency_ms": kimi_ms},
            "verification": {"provider": "NVIDIA Nemotron", "model": self.nemotron_model, "status": "COMPLETE", "latency_ms": nemotron_ms, "claims_evaluated": len(verification["claims"]), **counts},
            "arbitration": {"claims_revised": len(corrections), "evidence_confidence": _confidence(verification)},
            "total_latency_ms": round((perf_counter() - cycle_started) * 1000),
        }
        return ResearchResult(question, evidence, answer, draft, verification, trace)


def _confidence(verification: Dict[str, Any]) -> str:
    counts = verification_counts(verification)
    total = len(verification["claims"])
    if counts["unsupported"] or counts["conflicted"]:
        return "LOW"
    if counts["partial"]:
        return "MEDIUM"
    return "HIGH" if total else "LOW"
