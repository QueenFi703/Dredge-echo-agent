"""Self-reconfiguring Dredge Echo research flow for GPT-6 Astra.

The adaptive agent is deliberately separate from the Nebius submission path.
It uses the Dredge control plane to choose reasoning effort and orchestration
shape at multiple checkpoints during one investigation.

The trace records observable control decisions, not private chain-of-thought.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional

from bridge.control_plane import (
    DredgeControlPlane,
    IntelligenceState,
    InvestigationSignals,
    OrchestrationMode,
)
from bridge.llm_adapter import LLMAdapter
from bridge.search_adapter import TavilySearchAdapter


Critic = Callable[[str, Dict[str, Any], str], Dict[str, Any]]


@dataclass(frozen=True)
class IntelligenceEvent:
    phase: str
    event: str
    state: Dict[str, Any]
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdaptiveResearchResult:
    question: str
    answer: str
    draft: str
    evidence: Dict[str, Any]
    verification: Dict[str, Any]
    intelligence_state: Dict[str, Any]
    events: List[Dict[str, Any]]
    trace: Dict[str, Any]


class AdaptiveResearchAgent:
    """Run an investigation whose topology can expand and collapse in-flight."""

    def __init__(
        self,
        *,
        search: Optional[TavilySearchAdapter] = None,
        llm: Optional[LLMAdapter] = None,
        control_plane: Optional[DredgeControlPlane] = None,
        critic: Optional[Critic] = None,
        arbitrator: Optional[LLMAdapter] = None,
        model: str = "gpt-6-astra",
    ) -> None:
        self.search = search or TavilySearchAdapter()
        self.llm = llm or LLMAdapter(backend="openai", model=model)
        self.control_plane = control_plane or DredgeControlPlane()
        self.critic = critic
        self.arbitrator = arbitrator or self.llm
        self.model = model

    def research(
        self,
        question: str,
        *,
        max_results: int = 6,
        materiality: float = 0.5,
        risk_tolerance: str = "normal",
    ) -> AdaptiveResearchResult:
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        cycle_started = perf_counter()
        events: List[IntelligenceEvent] = []

        # Checkpoint 1: decide how much machinery the question initially merits.
        signals = InvestigationSignals(
            task_complexity=_estimate_complexity(question),
            evidence_needed=True,
            evidence_coverage=0.0,
            uncertainty=0.65,
            materiality=materiality,
            user_risk_tolerance=risk_tolerance,
        )
        state = self.control_plane.decide(signals)
        _record(events, "planning", "INTELLIGENCE_CONFIGURED", state, {
            "question_complexity": round(signals.task_complexity, 3),
        })

        started = perf_counter()
        evidence = self.search.search(question, max_results=max_results)
        retrieval_ms = round((perf_counter() - started) * 1000)
        sources = evidence.get("sources") or []
        if not sources:
            raise RuntimeError("No evidence sources returned; adaptive research cannot continue")

        # Checkpoint 2: evidence arrival can shrink or expand the topology before synthesis.
        coverage = min(1.0, len(sources) / max(1, max_results))
        signals = InvestigationSignals(
            task_complexity=signals.task_complexity,
            evidence_needed=True,
            evidence_coverage=coverage,
            uncertainty=max(0.2, 0.7 - 0.45 * coverage),
            materiality=materiality,
            source_quality=_estimate_source_quality(sources),
            user_risk_tolerance=risk_tolerance,
        )
        next_state = self.control_plane.decide(signals)
        _transition(events, "evidence", state, next_state, {
            "source_count": len(sources),
            "evidence_coverage": round(coverage, 3),
        })
        state = next_state

        started = perf_counter()
        draft = self.llm.generate(
            "investigate_with_evidence",
            source="evidence_graph_seed",
            target="material_claims_and_grounded_conclusion",
            source_value={
                "question": question,
                "evidence": evidence,
                "instructions": (
                    "Build material claims from evidence. Separate fact from inference, "
                    "identify uncertainty, and cite supporting source URLs."
                ),
            },
            reasoning_effort=state.reasoning.value,
        )
        synthesis_ms = round((perf_counter() - started) * 1000)
        if not draft.strip():
            raise RuntimeError("Astra returned an empty investigation draft")

        verification: Dict[str, Any] = {"claims": []}
        if self.critic is not None:
            started = perf_counter()
            verification = self.critic(question, evidence, draft)
            critic_ms = round((perf_counter() - started) * 1000)
        else:
            critic_ms = 0

        metrics = _verification_metrics(verification)

        # Checkpoint 3: criticism can spawn adversarial or deliberative machinery.
        signals = InvestigationSignals(
            task_complexity=signals.task_complexity,
            evidence_needed=True,
            evidence_coverage=coverage,
            contradiction_score=metrics["contradiction_score"],
            uncertainty=metrics["uncertainty"],
            materiality=materiality,
            source_quality=signals.source_quality,
            competing_hypotheses=metrics["competing_hypotheses"],
            user_risk_tolerance=risk_tolerance,
        )
        next_state = self.control_plane.decide(signals)
        _transition(events, "challenge", state, next_state, metrics)
        state = next_state

        answer = draft
        arbitration_ms = 0
        needs_arbitration = state.mode in {
            OrchestrationMode.ADVERSARIAL,
            OrchestrationMode.DELIBERATIVE,
            OrchestrationMode.ESCALATED,
        }
        if needs_arbitration:
            started = perf_counter()
            answer = self.arbitrator.generate(
                "dredge_arbitrate",
                source="draft_evidence_and_challenge",
                target="verified_intelligence_response",
                source_value={
                    "question": question,
                    "evidence": evidence,
                    "draft": draft,
                    "verification": verification,
                    "control_state": state.to_dict(),
                    "instructions": (
                        "Resolve only what the evidence supports. Preserve unresolved uncertainty. "
                        "Do not manufacture consensus. Return the strongest conclusion that survives scrutiny."
                    ),
                },
                reasoning_effort=state.reasoning.value,
            )
            arbitration_ms = round((perf_counter() - started) * 1000)
            _record(events, "arbitration", "ARBITRATION_COMPLETE", state, {
                "reasoning_effort": state.reasoning.value,
            })

        if not answer.strip():
            raise RuntimeError("Dredge Echo returned an empty final answer")

        trace = {
            "model": self.model,
            "retrieval_ms": retrieval_ms,
            "synthesis_ms": synthesis_ms,
            "critic_ms": critic_ms,
            "arbitration_ms": arbitration_ms,
            "source_count": len(sources),
            "control_transitions": max(0, len([e for e in events if e.event == "TOPOLOGY_CHANGED"])),
            "total_latency_ms": round((perf_counter() - cycle_started) * 1000),
        }

        return AdaptiveResearchResult(
            question=question,
            answer=answer,
            draft=draft,
            evidence=evidence,
            verification=verification,
            intelligence_state=state.to_dict(),
            events=[event.to_dict() for event in events],
            trace=trace,
        )


def _record(
    events: List[IntelligenceEvent],
    phase: str,
    event: str,
    state: IntelligenceState,
    details: Dict[str, Any],
) -> None:
    events.append(IntelligenceEvent(phase, event, state.to_dict(), details))


def _transition(
    events: List[IntelligenceEvent],
    phase: str,
    previous: IntelligenceState,
    current: IntelligenceState,
    details: Dict[str, Any],
) -> None:
    changed = previous.mode != current.mode or previous.reasoning != current.reasoning
    payload = {
        **details,
        "from_mode": previous.mode.value,
        "to_mode": current.mode.value,
        "from_reasoning": previous.reasoning.value,
        "to_reasoning": current.reasoning.value,
        "spawned_agents": sorted(set(current.agents) - set(previous.agents)),
        "retired_agents": sorted(set(previous.agents) - set(current.agents)),
    }
    _record(
        events,
        phase,
        "TOPOLOGY_CHANGED" if changed else "TOPOLOGY_RETAINED",
        current,
        payload,
    )


def _estimate_complexity(question: str) -> float:
    words = len(question.split())
    connective_bonus = sum(
        token in question.lower()
        for token in (" compare ", " versus ", " why ", " impact ", " should ", " likely ")
    )
    return min(1.0, 0.18 + words / 80.0 + connective_bonus * 0.08)


def _estimate_source_quality(sources: List[Dict[str, Any]]) -> float:
    if not sources:
        return 0.0
    with_url = sum(bool(source.get("url")) for source in sources)
    with_content = sum(bool(source.get("content") or source.get("snippet")) for source in sources)
    return min(1.0, (with_url + with_content) / (2.0 * len(sources)))


def _verification_metrics(verification: Dict[str, Any]) -> Dict[str, Any]:
    claims = verification.get("claims") or []
    if not claims:
        return {
            "claims_evaluated": 0,
            "contradiction_score": 0.0,
            "uncertainty": 0.35,
            "competing_hypotheses": 1,
        }

    statuses = [str(claim.get("status", "")).upper() for claim in claims]
    conflicted = sum(status in {"CONFLICTED", "CONTRADICTED"} for status in statuses)
    unsupported = sum(status == "UNSUPPORTED" for status in statuses)
    partial = sum(status == "PARTIAL" for status in statuses)
    supported = sum(status == "SUPPORTED" for status in statuses)
    total = len(statuses)

    contradiction_score = min(1.0, (conflicted + 0.5 * unsupported) / total)
    uncertainty = min(1.0, 1.0 - supported / total + 0.15 * partial)
    competing = 2 if conflicted else 1
    return {
        "claims_evaluated": total,
        "supported": supported,
        "partial": partial,
        "unsupported": unsupported,
        "conflicted": conflicted,
        "contradiction_score": round(contradiction_score, 3),
        "uncertainty": round(uncertainty, 3),
        "competing_hypotheses": competing,
    }
