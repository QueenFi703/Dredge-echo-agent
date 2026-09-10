# Dredge Echo Grounded Research

Dredge Echo now separates **retrieval** from **reasoning**:

```text
question
  -> TavilySearchAdapter
  -> normalized live web evidence
  -> ResearchAgent
  -> LLMAdapter(backend="nebius")
  -> Nebius Token Factory model
  -> grounded synthesis with source URLs
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

The command prints the Token Factory model, Tavily query, retrieved source URLs, and the final grounded synthesis.

## Implementation targets

- `bridge/search_adapter.py` — live Tavily retrieval and evidence normalization.
- `bridge/research_agent.py` — retrieval-to-reasoning orchestration.
- `scripts/smoke_research.py` — one-command live integration demo.
- `tests/test_search_adapter.py` — search adapter contract tests without network calls.
- `tests/test_research_agent.py` — verifies evidence is passed into model reasoning.

## Demo acceptance criteria

A submission-ready run should demonstrate all of the following in one execution:

1. Tavily returns current web evidence.
2. Dredge Echo normalizes and passes that evidence to the reasoning layer.
3. The configured Nebius Token Factory model produces a non-empty answer.
4. The console shows the source URLs used for grounding.
5. The corresponding Token Factory request can be located in Nebius observability.

The core narrative is: **Dredge Echo perceives current information through Tavily, reasons through Nebius Token Factory, and leaves an inspectable trail from evidence to answer.**
