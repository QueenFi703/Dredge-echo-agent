"""Run one live Dredge Echo research cycle through Tavily and Nebius Token Factory."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

from bridge.llm_adapter import LLMAdapter
from bridge.research_agent import ResearchAgent
from bridge.search_adapter import TavilySearchAdapter
from bridge.verification import NemotronVerifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "question",
        nargs="?",
        default="What are the latest practical developments in agentic AI infrastructure?",
    )
    parser.add_argument("--max-results", type=int, default=5)
    args = parser.parse_args()

    model = os.environ["NEBIUS_MODEL"].strip()
    nvidia_model = os.environ["NVIDIA_MODEL"].strip()
    started_at = datetime.now(timezone.utc).isoformat()

    agent = ResearchAgent(
        search=TavilySearchAdapter(),
        llm=LLMAdapter(backend="nebius", model=model),
        verifier=NemotronVerifier(LLMAdapter(backend="nebius", model=nvidia_model)),
        arbitrator=LLMAdapter(backend="nebius", model=model),
        kimi_model=model,
        nemotron_model=nvidia_model,
    )
    result = agent.research(args.question, max_results=args.max_results)

    sources = result.evidence["sources"]
    answer = result.answer.strip()
    if not sources:
        raise RuntimeError("Live research returned no sources; grounded demo failed")
    if not answer:
        raise RuntimeError("Nebius returned an empty answer; grounded demo failed")

    print(f"Dredge Echo research started: {started_at}")
    print(f"Kimi synthesis model: {model}")
    print(f"NVIDIA verification model: {nvidia_model}")
    print(f"Tavily query: {result.evidence['query']}")
    print(f"Sources: {len(sources)}")
    for index, source in enumerate(sources, start=1):
        print(f"  {index}. {source.get('title') or '(untitled)'} - {source.get('url')}")
    print("\nGrounded answer:\n")
    print(answer)
    trace = result.trace
    verify = trace["verification"]
    print("\nDREDGE ECHO TRACE")
    print(f"Retrieval\n  Tavily ................. {trace['retrieval']['source_count']} sources")
    print(f"  Retrieval latency ...... {trace['retrieval']['latency_ms']} ms")
    print(f"Synthesis\n  Kimi ................... {trace['synthesis']['status']}")
    print(f"  Model .................. {trace['synthesis']['model']}")
    print(f"  Kimi latency ........... {trace['synthesis']['latency_ms']} ms")
    print(f"Verification\n  NVIDIA Nemotron ........ {verify['status']}")
    print(f"  Model .................. {verify['model']}")
    print(f"  Claims evaluated ....... {verify['claims_evaluated']}")
    for status in ("supported", "partial", "conflicted", "unsupported"):
        print(f"  {status.title():<23} {verify[status]}")
    print(f"Arbitration\n  Claims revised ......... {trace['arbitration']['claims_revised']}")
    print(f"  Evidence confidence .... {trace['arbitration']['evidence_confidence']}")
    print(f"Total research latency ... {trace['total_latency_ms']} ms")
    print(f"\nDredge Echo research completed: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
