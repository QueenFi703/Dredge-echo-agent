"""GPT-6 Astra evidence-challenger role for adaptive Dredge investigations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from bridge.llm_adapter import LLMAdapter
from bridge.verification import VerificationError, parse_verification


ASTRA_CRITIC_INSTRUCTIONS = """ROLE: Dredge Evidence Challenger
Independently test the proposed answer against the retrieved evidence.
Do not reward agreement or rewrite the answer. Identify material claims, weak
support, contradictions, missing context, and excessive certainty. Evidence
outranks model consensus. Use SUPPORTED, PARTIAL, CONFLICTED, or UNSUPPORTED.

Return JSON only:
{"claims":[{"claim":"...","status":"SUPPORTED|PARTIAL|CONFLICTED|UNSUPPORTED",
"evidence_ids":["source-1"],"reason":"...","recommended_correction":null}],
"overall_status":"SUPPORTED|PARTIAL|CONFLICTED|UNSUPPORTED",
"conflicts":[],"missing_evidence":[]}
"""


@dataclass
class AstraEvidenceCritic:
    """Run an independent Astra call as Dredge's evidence challenger."""

    llm: LLMAdapter
    reasoning_effort: str = "high"

    def __call__(
        self, question: str, evidence: Dict[str, Any], draft: str
    ) -> Dict[str, Any]:
        raw = self.llm.generate(
            "challenge_material_claims",
            source="question_evidence_and_astra_draft",
            target="structured_evidence_verification_json",
            source_value={
                "instructions": ASTRA_CRITIC_INSTRUCTIONS,
                "question": question,
                "evidence": evidence,
                "proposed_answer": draft,
            },
            reasoning_effort=self.reasoning_effort,
        )
        if not raw.strip():
            raise VerificationError("Astra returned an empty evidence challenge")
        return parse_verification(raw)
