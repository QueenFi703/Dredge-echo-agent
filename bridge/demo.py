"""Presentation helpers for the public Dredge Echo demo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from bridge.research_agent import ResearchResult


@dataclass(frozen=True)
class DemoOutput:
    answer: str
    sources_markdown: str
    evidence_status: str
    verification_json: str
    trace_json: str


def present_result(result: ResearchResult) -> DemoOutput:
    """Convert an internal result into safe, readable public output."""
    sources: list[dict[str, Any]] = result.evidence.get("sources") or []
    source_lines = []
    for index, source in enumerate(sources, start=1):
        title = str(source.get("title") or f"Source {index}").replace("[", "").replace("]", "")
        url = str(source.get("url") or "")
        if urlparse(url).scheme in {"http", "https"}:
            source_lines.append(f"{index}. [{title}]({url})")

    public_verification = {
        "overall_status": result.verification.get("overall_status"),
        "claims": result.verification.get("claims", []),
        "conflicts": result.verification.get("conflicts", []),
        "missing_evidence": result.verification.get("missing_evidence", []),
    }
    status = result.trace.get("arbitration", {}).get("evidence_confidence", "UNKNOWN")
    return DemoOutput(
        answer=result.answer,
        sources_markdown="\n".join(source_lines) or "Insufficient evidence: no usable source URLs were returned.",
        evidence_status=f"Evidence confidence: **{status}**",
        verification_json=json.dumps(public_verification, indent=2),
        trace_json=json.dumps(result.trace, indent=2),
    )
