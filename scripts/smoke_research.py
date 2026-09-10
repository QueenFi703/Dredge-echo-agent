"""Run one live Dredge Echo research cycle through Tavily and Nebius Token Factory."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

from bridge.llm_adapter import LLMAdapter
from bridge.research_agent import ResearchAgent
from bridge.search_adapter import TavilySearchAdapter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "question",
        nargs="?",
        default="What are the latest practical developments in agentic AI infrastructure?",
    )
    parser.add_argument("--max-results", type=int, default=5)
    args = parser.parse_args()

    model = os.environ["NEBIUS_MODEL"]
    started_at = datetime.now(timezone.utc).isoformat()

    agent = ResearchAgent(
        search=TavilySearchAdapter(),
        llm=LLMAdapter(backend="nebius", model=model),
    )
    result = agent.research(args.question, max_results=args.max_results)

    sources = result.evidence["sources"]
    answer = result.answer.strip()
    if not sources:
        raise RuntimeError("Live research returned no sources; grounded demo failed")
    if not answer:
        raise RuntimeError("Nebius returned an empty answer; grounded demo failed")

    print(f"Dredge Echo research started: {started_at}")
    print(f"Nebius model: {model}")
    print(f"Tavily query: {result.evidence['query']}")
    print(f"Sources: {len(sources)}")
    for index, source in enumerate(sources, start=1):
        print(f"  {index}. {source.get('title') or '(untitled)'} - {source.get('url')}")
    print("\nGrounded answer:\n")
    print(answer)
    print(f"\nDredge Echo research completed: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
