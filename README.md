---
title: Dredge Echo
emoji: 🔎
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
license: mit
---

# Dredge Echo

> **Ask the live web. Hear the evidence answer back.**

Dredge Echo is a grounded, multi-model research agent built for people who need more than a fluent answer. It retrieves current evidence, drafts a source-grounded response, challenges the material claims, and shows the trace behind the result.

**It does not just answer. It shows what it knows, how it knows it, and where the evidence ends.**

## The signal path

```text
Question
  ↓
Tavily — Scout
  ↓
Kimi on Nebius Token Factory — Architect
  ↓
NVIDIA Nemotron — Challenger
  ↓
Dredge Echo — Arbiter
  ↓
Grounded answer + sources + evidence status + trace
```

Each model has one job:

| Layer | Role | Responsibility |
|---|---|---|
| **Tavily** | Scout | Retrieves current, relevant web evidence at runtime. |
| **Kimi** | Architect | Produces the first grounded synthesis from the retrieved evidence. |
| **NVIDIA Nemotron** | Challenger | Checks material claims for support, contradiction, missing context, and excess certainty. |
| **Dredge Echo** | Arbiter | Reconciles the critique with the evidence and returns the final answer. |

Nemotron is intentionally not used as a second answer generator. Its independent role is to pressure-test Kimi's draft. When it recommends corrections, Dredge Echo invokes Kimi again to arbitrate the disputed claims against the source packet.

## Why Dredge Echo exists

Search tools can find fresh information. Language models can explain it beautifully. The dangerous gap lives between those two moments: a polished answer may still overreach beyond its evidence.

Dredge Echo turns that gap into a visible part of the product. A user can inspect:

- the final grounded answer;
- the retrieved sources;
- verification counts for supported, unsupported, and contradicted claims;
- whether arbitration revised the answer;
- stage-level latency and model identity;
- a clear **“Insufficient evidence”** result when retrieval cannot support an answer.

That is the echo: the answer returns with the shape of its evidence still audible.

## What makes it different

- **Separation of duties:** retrieval, synthesis, verification, and arbitration are distinct stages.
- **Evidence before eloquence:** no evidence means no manufactured certainty.
- **Challenge, not duplication:** Nemotron evaluates claims instead of merely rewriting the draft.
- **Inspectable reasoning path:** the UI exposes a compact per-stage trace without leaking credentials or raw provider errors.
- **Graceful failure:** missing configuration and provider failures become safe, understandable states.
- **Model flexibility:** OpenAI-compatible adapters keep the orchestration portable while the demo runs through Nebius Token Factory.

## Built for the Nebius x NVIDIA Global AI Hackathon

Dredge Echo uses **Nebius Token Factory** as the inference gateway and **NVIDIA Nemotron 3 Nano 30B A3B** as its evidence critic.

The Nano variant fits the critic role: verification calls should be fast and economical enough to run after every synthesis, while still being capable of structured claim-level review. Kimi remains the primary synthesizer; Nemotron adds an independent adversarial pass.

Tavily is a functional runtime component, not a decorative integration. Every live research request begins with a Tavily retrieval call whose normalized evidence is passed downstream to both synthesis and verification.

## Run the demo

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Configure

Set the following as secrets in your local environment or deployment platform:

```bash
export TAVILY_API_KEY="your-tavily-key"
export NEBIUS_API_KEY="your-nebius-key"
```

Set the model and endpoint configuration:

```bash
export TAVILY_PROJECT="dredge-echo-agent"
export NEBIUS_BASE_URL="https://api.tokenfactory.nebius.com/v1"
export NEBIUS_MODEL="moonshotai/Kimi-K3"
export NVIDIA_MODEL="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
```

Never commit API keys. In Hugging Face Spaces, add the keys under **Secrets** and the non-sensitive configuration under **Variables**.

### 3. Launch

```bash
python app.py
```

Open the local Gradio URL printed in the terminal, enter a current research question, and select **Run grounded research**.

A strong demo question is:

> What are the most important recent developments in open-source AI agents, and which claims are strongly supported by current sources?

## Use the research agent in Python

```python
from bridge.research_agent import ResearchAgent
from bridge.search_adapter import TavilySearchAdapter
from bridge.llm_adapter import LLMAdapter
from bridge.nemotron_verifier import NemotronVerifier

search = TavilySearchAdapter()
kimi = LLMAdapter(backend="nebius")
critic = LLMAdapter(backend="nebius", model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")

agent = ResearchAgent(
    search=search,
    llm=kimi,
    verifier=NemotronVerifier(critic),
    arbitrator=kimi,
)

result = agent.research("What changed, and what evidence supports it?")
print(result["answer"])
print(result["sources"])
print(result["trace"])
```

## Verification contract

Nemotron evaluates each material claim using structured statuses:

- `supported` — the evidence directly backs the claim;
- `unsupported` — the retrieved packet does not establish the claim;
- `contradicted` — the evidence conflicts with the claim.

Dredge Echo records the counts, preserves the source trail, and routes corrections through arbitration. This makes verification an executable stage of the system rather than a sentence in the prompt.

## Test and verify

Run the automated test suite:

```bash
pytest -q
```

Run the local research smoke test:

```bash
python scripts/smoke_research.py
```

The GitHub Actions workflow `Dredge Echo Research Demo` exercises the live path:

```text
Tavily retrieval → Kimi synthesis → Nemotron verification → arbitration → grounded answer → trace
```

Launch it from `.github/workflows/dredge-echo-research.yml`. Required credentials stay in GitHub Actions secrets; the workflow prints only non-secret execution evidence.

## Project map

| Path | Purpose |
|---|---|
| `app.py` | Gradio research interface |
| `bridge/search_adapter.py` | Tavily retrieval and evidence normalization |
| `bridge/llm_adapter.py` | Nebius Token Factory / OpenAI-compatible model access |
| `bridge/nemotron_verifier.py` | Nemotron claim assessment |
| `bridge/research_agent.py` | Dredge Echo orchestration and arbitration |
| `scripts/smoke_research.py` | End-to-end research smoke test |
| `tests/test_research_agent.py` | Pipeline and failure-boundary tests |
| `docs/TAVILY_RESEARCH.md` | Deeper architecture and configuration notes |

## What changed during the hackathon

This repository began with a reusable **Fractal Operational Coherence** foundation: patterns for systems that preserve structure, observability, and graceful failure under pressure.

During the hackathon, that foundation became Dredge Echo through a substantial new product layer:

- Nebius Token Factory model integration;
- live Tavily retrieval and evidence normalization;
- Kimi grounded synthesis;
- NVIDIA Nemotron claim verification;
- arbitration when the critic recommends correction;
- a Gradio/Hugging Face demo surface;
- evidence status, source display, and stage tracing;
- unit tests, live smoke tests, and GitHub Actions verification.

The inherited coherence pattern is still present, but now it serves the agent: **Scout → Architect → Challenger → Arbiter** is the product cadence.

## Known limitations

- Source quality still depends on what retrieval can find and normalize.
- Verification is evidence-bounded; it does not prove truth beyond the retrieved packet.
- The current demo uses one critic pass rather than an open-ended debate.
- Provider availability and rate limits can affect live latency.
- The trace explains orchestration state and evidence status; it is not private model chain-of-thought.

## Vision

Dredge Echo is a step toward research agents that earn trust through structure.

Not a black box that sounds certain.  
A living instrument that retrieves, reasons, challenges, reconciles—and knows when silence is more honest than invention.

## License

Released under the [MIT License](LICENSE).
