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
        repairer: Optional[LLMAdapter] = None,
        arbitrator: Optional[LLMAdapter] = None,
        architect_model: Optional[str] = None,
        arbitrator_model: Optional[str] = None,
        kimi_model: Optional[str] = None,
        nemotron_model: Optional[str] = None,
    ) -> None:
        self.search = search or TavilySearchAdapter()
        self.llm = llm or LLMAdapter(backend="nebius")
        self.verifier = verifier
        self.repairer = repairer or self.llm
        self.arbitrator = arbitrator
        self.architect_model = architect_model or kimi_model
        self.arbitrator_model = arbitrator_model or kimi_model
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
        architect_ms = round((perf_counter() - started) * 1000)
        if not draft.strip():
            raise RuntimeError("The Architect returned an empty synthesis")
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
        arbitration_route = "SKIPPED"
        arbitration_ms = 0
        if corrections:
            requires_kimi = any(
                claim["status"] in {"CONFLICTED", "UNSUPPORTED"}
                for claim in verification["claims"]
            )
            selected_arbitrator = self.arbitrator if requires_kimi else self.repairer
            if selected_arbitrator is None:
                raise RuntimeError("An arbitrator is required when verification finds revisions")
            arbitration_route = "KIMI_ESCALATION" if requires_kimi else "ARCHITECT_REPAIR"
            started = perf_counter()
            answer = selected_arbitrator.generate(
                "arbitrate_evidence_critique",
                source="architect_draft_and_nemotron_verification",
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
            arbitration_ms = round((perf_counter() - started) * 1000)
        if not answer.strip():
            raise RuntimeError("Dredge Echo arbitration returned an empty final answer")

        counts = verification_counts(verification)
        trace = {
            "retrieval": {"provider": "Tavily", "source_count": len(evidence["sources"]), "latency_ms": retrieval_ms},
            "synthesis": {"provider": "Z.ai", "role": "Architect", "model": self.architect_model, "status": "COMPLETE", "latency_ms": architect_ms},
            "verification": {"provider": "NVIDIA Nemotron", "model": self.nemotron_model, "status": "COMPLETE", "latency_ms": nemotron_ms, "claims_evaluated": len(verification["claims"]), **counts},
            "arbitration": {"route": arbitration_route, "provider": "Moonshot AI Kimi" if arbitration_route == "KIMI_ESCALATION" else "Z.ai" if arbitration_route == "ARCHITECT_REPAIR" else None, "model": self.arbitrator_model if arbitration_route == "KIMI_ESCALATION" else self.architect_model if arbitration_route == "ARCHITECT_REPAIR" else None, "claims_revised": len(corrections), "evidence_confidence": _confidence(verification), "latency_ms": arbitration_ms},
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
