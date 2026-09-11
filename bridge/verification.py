"""Structured NVIDIA Nemotron evidence verification for Dredge Echo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from bridge.llm_adapter import LLMAdapter

EVIDENCE_CRITIC_INSTRUCTIONS = """ROLE: Evidence Critic
You are the independent verification model inside Dredge Echo.
Do not rewrite the primary answer or answer the question independently.
For each material claim, identify supporting evidence and decide whether it actually
supports the claim. Flag weak support, contradictions, missing evidence, and excessive
certainty. Use: SUPPORTED, PARTIAL, CONFLICTED, or UNSUPPORTED. Recommend only the
smallest correction necessary. Agreement between models is not proof. Evidence
outranks model consensus.

Return JSON only:
{"claims":[{"claim":"...","status":"SUPPORTED|PARTIAL|CONFLICTED|UNSUPPORTED",
"evidence_ids":["source-1"],"reason":"...","recommended_correction":null}],
"overall_status":"SUPPORTED|PARTIAL|CONFLICTED|UNSUPPORTED",
"conflicts":[],"missing_evidence":[]}
"""

VALID_STATUSES = {"SUPPORTED", "PARTIAL", "CONFLICTED", "UNSUPPORTED"}


class VerificationError(ValueError):
    """Raised when a verifier response violates the evidence contract."""


def parse_verification(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1])
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VerificationError("Nemotron verification was not valid JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise VerificationError("Nemotron verification must contain a claims list")
    if not data["claims"]:
        raise VerificationError("Nemotron verification must evaluate at least one claim")
    for claim in data["claims"]:
        if not isinstance(claim, dict) or claim.get("status") not in VALID_STATUSES:
            raise VerificationError("Every verified claim must have a valid evidence status")
        if not str(claim.get("claim") or "").strip():
            raise VerificationError("Every verified claim must include claim text")
        if not isinstance(claim.get("evidence_ids", []), list):
            raise VerificationError("evidence_ids must be a list")
    if data.get("overall_status") not in VALID_STATUSES:
        raise VerificationError("Nemotron verification must include a valid overall_status")
    for field in ("conflicts", "missing_evidence"):
        if not isinstance(data.get(field), list):
            raise VerificationError(f"Nemotron verification must include a {field} list")
    return data


@dataclass
class NemotronVerifier:
    llm: LLMAdapter

    def verify(self, *, question: str, evidence: Dict[str, Any], proposed_answer: str) -> Dict[str, Any]:
        raw = self.llm.generate(
            "verify_material_claims",
            source="question_evidence_and_kimi_draft",
            target="structured_evidence_verification_json",
            source_value={"instructions": EVIDENCE_CRITIC_INSTRUCTIONS, "question": question,
                          "evidence": evidence, "proposed_answer": proposed_answer},
        )
        if not raw.strip():
            raise VerificationError("Nemotron returned an empty verification")
        return parse_verification(raw)


def verification_counts(verification: Dict[str, Any]) -> Dict[str, int]:
    counts = {status.lower(): 0 for status in VALID_STATUSES}
    for claim in verification["claims"]:
        counts[claim["status"].lower()] += 1
    return counts
