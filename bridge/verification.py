"""Structured NVIDIA Nemotron evidence verification for Dredge Echo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from bridge.llm_adapter import LLMAdapter

EVIDENCE_CRITIC_INSTRUCTIONS = """ROLE: Evidence Critic
You are the independent verification model inside Dredge Echo.
Do not rewrite the primary answer or answer the question independently.
For each material claim, identify supporting evidence and decide whether it actually
supports the claim. Flag weak support, contradictions, missing evidence, and excessive
certainty. Use: SUPPORTED, PARTIAL, CONFLICTED, or UNSUPPORTED. Recommend only the
smallest correction necessary. Agreement between models is not proof. Evidence
outranks model consensus.

Every claim must include evidence_ids, using only exact IDs from the supplied
sources. SUPPORTED, PARTIAL, and CONFLICTED claims require at least one source ID.
Use an empty list only for UNSUPPORTED claims when no source applies. Never invent
IDs. overall_status may be SUPPORTED only when every claim is SUPPORTED and both
conflicts and missing_evidence are empty.

Keep the response compact enough to complete reliably: evaluate at most 6 material
claims, and keep each claim, reason, and recommended correction under 120 characters.
Do not include markdown fences or any text outside the JSON object.

Return JSON only:
{"claims":[{"claim":"...","status":"SUPPORTED|PARTIAL|CONFLICTED|UNSUPPORTED",
"evidence_ids":["source-1"],"reason":"...","recommended_correction":null}],
"overall_status":"SUPPORTED|PARTIAL|CONFLICTED|UNSUPPORTED",
"conflicts":[],"missing_evidence":[]}
"""

VALID_STATUSES = {"SUPPORTED", "PARTIAL", "CONFLICTED", "UNSUPPORTED"}


class VerificationError(ValueError):
    """Raised when a verifier response violates the evidence contract."""


def _source_ids(evidence: Optional[Dict[str, Any]]) -> Set[str]:
    """Validate the evidence registry before trusting a model's references."""
    if not isinstance(evidence, dict) or not isinstance(evidence.get("sources"), list):
        raise VerificationError("Verification requires an evidence sources list")
    if not evidence["sources"]:
        raise VerificationError("Verification requires at least one evidence source")
    ids: Set[str] = set()
    for source in evidence["sources"]:
        if not isinstance(source, dict):
            raise VerificationError("Every evidence source must be an object")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip() or source_id != source_id.strip():
            raise VerificationError("Every evidence source must have a non-empty string ID")
        if source_id in ids:
            raise VerificationError("Evidence source IDs must be unique")
        if not isinstance(source.get("content"), str) or not source["content"].strip():
            raise VerificationError("Every evidence source must include non-empty content")
        ids.add(source_id)
    return ids


def parse_verification(
    raw: str, *, evidence: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Parse a claim assessment only against its actual retrieved evidence."""
    if not isinstance(raw, str):
        raise VerificationError("Nemotron verification must be JSON text")
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
    source_ids = _source_ids(evidence)
    for claim in data["claims"]:
        if (not isinstance(claim, dict) or not isinstance(claim.get("status"), str)
                or claim["status"] not in VALID_STATUSES):
            raise VerificationError("Every verified claim must have a valid evidence status")
        if not isinstance(claim.get("claim"), str) or not claim["claim"].strip():
            raise VerificationError("Every verified claim must include claim text")
        evidence_ids = claim.get("evidence_ids")
        if not isinstance(evidence_ids, list):
            raise VerificationError("Every claim must include an evidence_ids list")
        if any(not isinstance(source_id, str) or source_id not in source_ids
               for source_id in evidence_ids):
            raise VerificationError("Every evidence ID must match a retrieved source")
        if not evidence_ids and claim["status"] != "UNSUPPORTED":
            raise VerificationError("Only UNSUPPORTED claims may have no evidence IDs")
    if not isinstance(data.get("overall_status"), str) or data["overall_status"] not in VALID_STATUSES:
        raise VerificationError("Nemotron verification must include a valid overall_status")
    for field in ("conflicts", "missing_evidence"):
        if not isinstance(data.get(field), list):
            raise VerificationError(f"Nemotron verification must include a {field} list")
    if data["overall_status"] == "SUPPORTED" and (
        any(claim["status"] != "SUPPORTED" for claim in data["claims"])
        or data["conflicts"] or data["missing_evidence"]
    ):
        raise VerificationError("SUPPORTED verification cannot contain unresolved evidence limitations")
    return data


@dataclass
class NemotronVerifier:
    llm: LLMAdapter

    def verify(self, *, question: str, evidence: Dict[str, Any], proposed_answer: str) -> Dict[str, Any]:
        _source_ids(evidence)
        raw = self.llm.generate(
            "verify_material_claims",
            source="question_evidence_and_kimi_draft",
            target="structured_evidence_verification_json",
            source_value={"instructions": EVIDENCE_CRITIC_INSTRUCTIONS, "question": question,
                          "evidence": evidence, "proposed_answer": proposed_answer},
        )
        if not isinstance(raw, str) or not raw.strip():
            raise VerificationError("Nemotron returned an empty verification")
        return parse_verification(raw, evidence=evidence)


def verification_counts(verification: Dict[str, Any]) -> Dict[str, int]:
    counts = {status.lower(): 0 for status in VALID_STATUSES}
    for claim in verification["claims"]:
        counts[claim["status"].lower()] += 1
    return counts
