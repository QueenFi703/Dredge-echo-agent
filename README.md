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

Architected by **Fi (QueenFi703)**, Dredge Echo is the research-agent expression of the larger Dredge vision: intelligence should be organized around the problem, evidence should outrank model agreement, and deeper reasoning should be invoked only when it earns its cost.

**Project surfaces:** [Live demo](https://huggingface.co/spaces/QueenFi/Dredge-Echo) · [Devpost submission](https://devpost.com/software/dredge-echo) · [Demo video](https://youtu.be/ZG9Eg4mGg6w)

## The signal path

```text
Question
  ↓
Tavily — Scout
  ↓
Configured GLM on Nebius Token Factory — Architect
  ↓
NVIDIA Nemotron — Challenger
  ↓
Dredge Echo — Router + Arbiter (Kimi on serious disputes)
  ↓
Grounded answer + sources + evidence status + trace
```

Each model has one job:

| Layer | Role | Responsibility |
|---|---|---|
| **Tavily** | Scout | Retrieves current, relevant web evidence at runtime. |
| **GLM-5.3** | Architect | Produces the fast, low-cost grounded synthesis from the retrieved evidence. The benchmark and current public Space use this verified route. |
| **NVIDIA Nemotron** | Challenger | Checks material claims for support, contradiction, missing context, and excess certainty. |
| **Dredge Echo** | Router | Skips arbitration for supported answers, sends partial claims back to GLM, and escalates serious disputes. |
| **Kimi K3** | Escalation Arbiter | Reconciles only conflicted or unsupported claims against the source packet. |

Nemotron is intentionally not used as a second answer generator. Its independent role is to pressure-test the Architect's draft. Supported answers stop immediately, partial claims get an economical GLM repair, and only conflicted or unsupported claims trigger the more expensive Kimi arbitration path.

## Why Dredge Echo exists

Search tools can find fresh information. Language models can explain it beautifully. The dangerous gap lives between those two moments: a polished answer may still overreach beyond its evidence.

Dredge Echo turns that gap into a visible part of the product. A user can inspect:

- the final grounded answer;
- the retrieved sources;
- verification counts for supported, partial, conflicted, and unsupported claims;
- whether arbitration revised the answer;
- stage-level latency and model identity;
- a clear **“Insufficient evidence”** result when retrieval returns no usable sources.

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

The Nano variant fits the critic role: verification calls should be fast and economical enough to run after every synthesis, while still being capable of structured claim-level review. GLM-5.3 handles routine synthesis, Nemotron adds an independent adversarial pass, and Kimi is reserved for the cases where its higher-cost reasoning adds the most value. The completed benchmark and current public Space use the same verified GLM-5.3 route.

Tavily is a functional runtime component, not a decorative integration. Every live research request begins with a Tavily retrieval call whose normalized evidence is passed downstream to both synthesis and verification.

## Verified live benchmark

A final GitHub Actions run completed all **3/3 paired comparisons** using identical Tavily evidence, GLM drafts, and initial Nemotron assessments within each pair.

| Measure | Dredge Echo dynamic routing | Always-Kimi baseline | Observed difference |
|---|---:|---:|---:|
| Nemotron-assessed `SUPPORTED` final answers | **3/3** | **1/3** | Dynamic route received a supported assessment on all three |
| Model API attempts | **9** | **13** | **30.8% fewer** |
| Total tokens | **47,172** | **65,567** | **28.1% fewer** |
| Aggregate latency | **211.9 s** | **275.5 s** | **23.1% less** |
| Tavily credits | **6 total** | Shared per pair | Same evidence basis |

Dredge Echo skipped unnecessary escalation on two questions and spent additional reasoning on the one answer that required repair. `SUPPORTED` is the benchmark critic's evidence assessment, not an independent factual-accuracy score. This is a controlled three-question sample, not a claim of universal accuracy, average production latency, or exact dollar savings. Model-specific pricing means token reductions should not be presented as invoice savings without a separate pricing calculation.

[Inspect the completed workflow and artifact](https://github.com/QueenFi703/Dredge-echo-agent/actions/runs/35348811242).

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
export NEBIUS_MODEL="zai-org/GLM-5.3"
export ARBITRATION_MODEL="moonshotai/Kimi-K3"
export NVIDIA_MODEL="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
```

Never commit API keys. In Hugging Face Spaces, add the keys under **Secrets** and the non-sensitive configuration under **Variables**.

### 3. Launch

```bash
python app.py
```

Open the local Gradio URL printed in the terminal, enter a current research question, and select **Research**.

A strong demo question is:

> What are the most important recent developments in open-source AI agents, and which claims are strongly supported by current sources?

## Use the research agent in Python

```python
from bridge.research_agent import ResearchAgent
from bridge.search_adapter import TavilySearchAdapter
from bridge.llm_adapter import LLMAdapter
from bridge.verification import NemotronVerifier

search = TavilySearchAdapter()
architect = LLMAdapter(backend="nebius", model="zai-org/GLM-5.3", max_tokens=2048)
critic = LLMAdapter(backend="nebius", model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", max_tokens=2048)
kimi = LLMAdapter(backend="nebius", model="moonshotai/Kimi-K3", max_tokens=2048)

agent = ResearchAgent(
    search=search,
    llm=architect,
    verifier=NemotronVerifier(critic),
    repairer=architect,
    arbitrator=kimi,
)

result = agent.research("What changed, and what evidence supports it?")
print(result.answer)
print(result.evidence["sources"])
print(result.trace)
```

## Verification contract

Nemotron evaluates each material claim using structured statuses:

- `SUPPORTED` — the evidence directly backs the claim;
- `PARTIAL` — the evidence supports only part of the claim or requires qualification;
- `CONFLICTED` — retrieved evidence materially disagrees;
- `UNSUPPORTED` — the retrieved packet does not establish the claim.

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
Tavily retrieval → GLM synthesis → Nemotron verification → dynamic repair or Kimi escalation → grounded answer → trace
```

Launch it from `.github/workflows/dredge-echo-research.yml`. Required credentials stay in GitHub Actions secrets; the workflow prints only non-secret execution evidence.

## Project map

| Path | Purpose |
|---|---|
| `app.py` | Gradio research interface |
| `bridge/search_adapter.py` | Tavily retrieval and evidence normalization |
| `bridge/llm_adapter.py` | Nebius Token Factory / OpenAI-compatible model access |
| `bridge/verification.py` | Nemotron claim assessment |
| `bridge/research_agent.py` | Dredge Echo orchestration and arbitration |
| `scripts/smoke_research.py` | End-to-end research smoke test |
| `tests/test_research_agent.py` | Pipeline and failure-boundary tests |
| `docs/TAVILY_RESEARCH.md` | Deeper architecture and configuration notes |

## The work behind Dredge Echo

Dredge Echo is not one prompt or one model wrapper. Fi designed and directed a complete evidence-aware research system:

- **Retrieval:** live Tavily search, source normalization, project-level usage tracking, and evidence packets shared across compared routes.
- **Synthesis:** grounded GLM drafting through Nebius Token Factory with explicit source and uncertainty instructions.
- **Independent challenge:** NVIDIA Nemotron claim-by-claim verification using structured `SUPPORTED`, `PARTIAL`, `CONFLICTED`, and `UNSUPPORTED` states.
- **Dynamic orchestration:** Dredge Echo skips needless arbitration, routes partial claims through focused repair, and reserves Kimi K3 for serious disputes.
- **Final-answer safety:** truncated completions are rejected, and every repaired or escalated answer receives another Nemotron check before it reaches the user.
- **Product experience:** a Gradio interface on Hugging Face Spaces with sources, evidence status, route selection, timing, and safe failure messages.
- **Operational proof:** deterministic route tests, provider smoke tests, GitHub Actions workflows, public benchmark artifacts, timeout diagnostics, and secret-safe logs.
- **Cost-aware design:** routine questions stay on the economical path while difficult questions are allowed to consume deeper reasoning.
- **Transparent limitations:** missing evidence, provider failures, truncated completions, and unresolved claims remain visible instead of being disguised as success.

The resulting cadence is **Scout → Architect → Challenger → Router → Arbiter → Final Check**. Dredge Echo decides how much intelligence the evidence actually requires.

## Known limitations

- Source quality still depends on what retrieval can find and normalize.
- Verification is evidence-bounded; it does not prove truth beyond the retrieved packet.
- Unchanged answers reuse their initial critic assessment. Repaired or escalated answers receive a second Nemotron check; unresolved evidence limitations remain visible. This is bounded verification, not an open-ended debate.
- Provider availability and rate limits can affect live latency.
- The trace explains orchestration state and evidence status; it is not private model chain-of-thought.

## Vision

Dredge Echo is a step toward research agents that earn trust through structure.

Not a black box that sounds certain.  
A living instrument that retrieves, reasons, challenges, reconciles—and knows when silence is more honest than invention.

## License

Released under the [MIT License](LICENSE).

## Final-answer verification and routing benchmark

The returned verification and confidence describe the final answer. The original
assessment is retained as `draft_verification`, and the trace records a separate
`final_verification` stage. A malformed final assessment fails the request rather
than returning an unchecked revision.

Run `python scripts/benchmark_routing.py routing-benchmark.json` with the documented
provider environment configured, or use the **Echo paired routing benchmark**
Actions workflow. It compares three paired questions using identical retrieved
evidence, GLM draft, and initial Nemotron assessment within each pair. The baseline
always runs Kimi and then checks its answer. Both routes include final-answer
verification. Execution order alternates across pairs.

The artifact reports measured latency, provider-reported token usage by model,
model-call counts, final evidence statuses, and a top-level `comparison_status`.
Provider availability failures produce an `INCOMPLETE` artifact, while unexpected
code or integration defects still fail the workflow. Pull requests run the
deterministic routing gate without exposing provider secrets; trusted main-branch
runs perform the live comparison. The latest official run completed 3/3 pairs and
is summarized above.
