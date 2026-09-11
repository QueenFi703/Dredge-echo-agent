# Dredge Echo Grounded Research

Dredge Echo separates retrieval, synthesis, verification, and arbitration:

```text
question
  -> TavilySearchAdapter
  -> normalized live web evidence
  -> Kimi synthesis (NEBIUS_MODEL)
  -> NVIDIA Nemotron evidence challenge (NVIDIA_MODEL)
  -> Dredge Echo arbitration
  -> grounded answer, evidence status, citations, and trace
```

## Why this shape

Tavily is used as a retrieval/tool layer rather than an LLM backend. The existing `LLMAdapter` remains responsible for model inference, while `TavilySearchAdapter` supplies current external evidence. This keeps the architecture composable and makes the live demo easy to trace.

## Install

```bash
pip install -e ".[agent]"
cp .env.example .env
```

Configure:

```text
NEBIUS_API_KEY=...
NEBIUS_MODEL=...
NVIDIA_MODEL=...
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
TAVILY_API_KEY=...
TAVILY_PROJECT=dredge-echo-agent
```

Do not commit real credentials.

## Run the demo smoke path

```bash
python scripts/smoke_research.py \
  "What are the latest practical developments in agentic AI infrastructure?"
```

The command prints both model identifiers, Tavily sources, the grounded answer, claim-status counts, stage latencies, revisions, and evidence confidence.

## Implementation targets

- `bridge/search_adapter.py` — live Tavily retrieval and evidence normalization.
- `bridge/research_agent.py` — retrieval, synthesis, verification, and arbitration.
- `bridge/verification.py` — strict Nemotron evidence-critic contract and validation.
- `scripts/smoke_research.py` — one-command live integration demo.
- `tests/test_search_adapter.py` — search adapter contract tests without network calls.
- `tests/test_research_agent.py` — verifies evidence is passed into model reasoning.

## Demo acceptance criteria

A submission-ready run should demonstrate all of the following in one execution:

1. Tavily returns current web evidence.
2. Dredge Echo normalizes and passes that evidence to the reasoning layer.
3. Kimi produces a non-empty primary synthesis.
4. Nemotron evaluates at least one material claim using structured evidence statuses.
5. Dredge Echo preserves supported claims and applies necessary corrections.
6. The console shows source URLs and a safe, inspectable execution trace.
7. Both Token Factory requests can be located in Nebius observability.

The core narrative is: **Tavily finds the evidence. Kimi reasons over it. Nemotron challenges it. Dredge Echo decides what survives. Evidence outranks model consensus.**
