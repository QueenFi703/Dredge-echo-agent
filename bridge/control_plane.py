"""Adaptive reasoning and orchestration policy for Dredge Echo Astra.

This module is intentionally model-agnostic.  It converts observable
investigation signals into an explicit intelligence state: reasoning depth,
orchestration topology, and the next actions Dredge should instantiate.

It does not expose or store private chain-of-thought.  The outputs are compact,
auditable control decisions suitable for API traces and UI telemetry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Tuple


class ReasoningDepth(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class OrchestrationMode(str, Enum):
    DIRECT = "direct"
    GROUNDED = "grounded"
    INVESTIGATIVE = "investigative"
    ADVERSARIAL = "adversarial"
    DELIBERATIVE = "deliberative"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class InvestigationSignals:
    """Normalized signals observed while Dredge is solving a task.

    Scores are expected in the inclusive range [0.0, 1.0].  The policy clamps
    them defensively so callers can feed imperfect telemetry safely.
    """

    task_complexity: float = 0.0
    evidence_needed: bool = False
    evidence_coverage: float = 0.0
    contradiction_score: float = 0.0
    uncertainty: float = 0.0
    materiality: float = 0.5
    source_quality: float = 1.0
    tool_failure_rate: float = 0.0
    competing_hypotheses: int = 1
    user_risk_tolerance: str = "normal"


@dataclass(frozen=True)
class IntelligenceState:
    mode: OrchestrationMode
    reasoning: ReasoningDepth
    agents: Tuple[str, ...]
    rationale_codes: Tuple[str, ...]
    may_collapse: bool

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["mode"] = self.mode.value
        data["reasoning"] = self.reasoning.value
        data["agents"] = list(self.agents)
        data["rationale_codes"] = list(self.rationale_codes)
        return data


class DredgeControlPlane:
    """Select the smallest sufficient intelligence configuration.

    The policy expands when evidence conflict, uncertainty, risk, or competing
    hypotheses increase; it can also collapse once evidence converges.  This
    keeps latency and cost proportional to the actual epistemic difficulty.
    """

    def decide(self, signals: InvestigationSignals) -> IntelligenceState:
        s = self._normalize(signals)
        codes = []

        if not s.evidence_needed and s.task_complexity < 0.30 and s.uncertainty < 0.30:
            return IntelligenceState(
                mode=OrchestrationMode.DIRECT,
                reasoning=ReasoningDepth.MEDIUM,
                agents=("astra_investigator",),
                rationale_codes=("LOW_COMPLEXITY",),
                may_collapse=True,
            )

        mode = OrchestrationMode.GROUNDED
        reasoning = ReasoningDepth.MEDIUM
        agents = ["evidence_scout", "astra_investigator", "evidence_checker"]
        codes.append("EXTERNAL_EVIDENCE_REQUIRED")

        if s.task_complexity >= 0.60 or s.evidence_coverage < 0.55:
            mode = OrchestrationMode.INVESTIGATIVE
            reasoning = ReasoningDepth.HIGH
            agents.extend(("parallel_scout", "claim_mapper"))
            codes.append("EXPAND_INVESTIGATION")

        if s.contradiction_score >= 0.45:
            mode = OrchestrationMode.ADVERSARIAL
            reasoning = ReasoningDepth.HIGH
            agents.extend(("challenger", "counter_evidence_scout", "arbiter"))
            codes.append("EVIDENCE_CONFLICT")

        if s.competing_hypotheses > 1:
            mode = OrchestrationMode.DELIBERATIVE
            reasoning = ReasoningDepth.XHIGH
            agents.extend(("hypothesis_builder", "hypothesis_judge", "arbiter"))
            codes.append("COMPETING_HYPOTHESES")

        high_stakes = s.materiality >= 0.80 or s.user_risk_tolerance.lower() == "low"
        unresolved = s.uncertainty >= 0.70 or s.source_quality < 0.50 or s.tool_failure_rate >= 0.35
        if high_stakes and unresolved:
            mode = OrchestrationMode.ESCALATED
            reasoning = ReasoningDepth.XHIGH
            agents.extend(("independent_verifier", "source_quality_auditor", "arbiter"))
            codes.append("HIGH_STAKES_UNRESOLVED")

        converged = (
            s.evidence_coverage >= 0.85
            and s.contradiction_score < 0.20
            and s.uncertainty < 0.25
            and s.source_quality >= 0.70
            and s.tool_failure_rate < 0.15
        )
        if converged:
            codes.append("EVIDENCE_CONVERGED")

        return IntelligenceState(
            mode=mode,
            reasoning=reasoning,
            agents=tuple(dict.fromkeys(agents)),
            rationale_codes=tuple(codes),
            may_collapse=converged,
        )

    @staticmethod
    def _normalize(signals: InvestigationSignals) -> InvestigationSignals:
        clamp = lambda value: max(0.0, min(1.0, float(value)))
        return InvestigationSignals(
            task_complexity=clamp(signals.task_complexity),
            evidence_needed=bool(signals.evidence_needed),
            evidence_coverage=clamp(signals.evidence_coverage),
            contradiction_score=clamp(signals.contradiction_score),
            uncertainty=clamp(signals.uncertainty),
            materiality=clamp(signals.materiality),
            source_quality=clamp(signals.source_quality),
            tool_failure_rate=clamp(signals.tool_failure_rate),
            competing_hypotheses=max(1, int(signals.competing_hypotheses)),
            user_risk_tolerance=str(signals.user_risk_tolerance or "normal"),
        )
