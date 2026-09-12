---
title: Dredge Echo Astra
emoji: ⚡
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
license: mit
---

# Dredge Echo Astra

> **Ask once. Dredge until the answer holds.**

Dredge Echo Astra is an adaptive intelligence control plane built around GPT-6 Astra. Instead of treating every request as the same fixed pipeline, it changes both **reasoning depth** and **orchestration depth** as evidence, uncertainty, contradiction, and risk evolve.

It does not just answer a question. It decides how much intelligence the question deserves, expands when the evidence becomes difficult, collapses when the answer becomes stable, and exposes those decisions as structured telemetry.

## Two architectures, one Dredge control plane

The Astra branch exposes two explicit intelligence routes. **Astra Adaptive is the default** and the primary Product Hunt experience. The original Nebius architecture remains available only when a user deliberately selects it.

| Route | Runtime path | Best for |
|---|---|---|
| **Astra Adaptive (default)** | Tavily → Dredge control plane → GPT-6 Astra investigator → Astra evidence challenger → Dredge arbitration | Dynamic reasoning depth, topology changes, conflict expansion, and observable orchestration |
| **Nebius Verified (optional)** | Tavily → Kimi synthesis → NVIDIA Nemotron verification → Dredge arbitration | Comparing the original independent multi-model verification pipeline |

There is no silent provider fallback. Selecting Astra does not call Kimi, Nemotron, or Nebius. Selecting Nebius does not call Astra. Credentials are read only while building the route that the user chose.

In Astra mode, names such as `challenger`, `claim_mapper`, and `arbiter` are **Dredge execution roles**, not hidden external models. GPT-6 Astra performs the language-model work through separate role-specific calls while Dredge decides when those calls are needed and how deeply they should reason.

## Interactive investigations powered by Arcade

The demo is conversational. After the first answer, a judge can steer the same visible investigation with instructions such as:

- `Challenge that assumption.`
- `Focus on the Missouri evidence.`
- `What would change the recommendation?`

Each browser session receives a distinct runtime identity, and recent conversation context is carried into the next Dredge turn. The interface exposes two evidence channels:

| Evidence channel | Behavior |
|---|---|
| **Tavily web evidence (default)** | Uses the original grounded web-retrieval adapter. |
| **Arcade live news action** | Calls `GoogleNews.SearchNewsStories` through Arcade, normalizes the result into Dredge evidence, and records the Arcade tool and execution ID in the public trace. |

Arcade is an action runtime, not another reasoning model. Astra or the selected Nebius models still reason; Arcade governs the external tool call. Tool execution is allowlisted, tied to the current session user, and handled outside model context. If a future tool needs OAuth, the UI returns Arcade's HTTPS authorization link and waits for the user to retry rather than exposing credentials or letting the model manufacture an approval URL.

## The idea in one line

Most AI APIs look like this:

```text
prompt → model → response
```

Dredge Echo Astra behaves more like this:

```text
intent
  ↓
evidence
  ↓
hypotheses
  ↓
challenge
  ↓
arbitration
  ↓
verified response
```

And that topology can change while the investigation is running.

## Why this is different

Dredge Echo Astra adapts across two dimensions at once:

### Dynamic reasoning depth

Different stages receive different reasoning budgets.

```text
Scout              → low
Claim mapper       → low / medium
Astra investigator → medium / high
Challenger         → high
Hypothesis judge   → xhigh
Final arbiter      → xhigh when uncertainty remains
```

Reasoning escalates when contradiction, uncertainty, source disagreement, or materiality rises. It can de-escalate when evidence converges.

### Dynamic orchestration depth

The system selects the smallest sufficient topology, then expands or collapses it at runtime.

- **DIRECT** — lean Astra response for low-complexity work.
- **GROUNDED** — evidence scout + Astra + evidence check.
- **INVESTIGATIVE** — multiple evidence branches and claim mapping.
- **ADVERSARIAL** — challenger and counter-evidence branches are spawned.
- **DELIBERATIVE** — competing hypotheses are built and judged independently.
- **ESCALATED** — high-stakes unresolved work receives deeper verification and arbitration.

These are not user-facing presets. They are controller states chosen from observable signals.

## The signature demo moment

The Product Hunt demo is designed to prove one behavior exceptionally well:

```text
1. A user asks a material research question.
2. Dredge begins in a lean topology.
3. Evidence arrives in parallel.
4. A contradiction is detected.
5. Reasoning depth increases.
6. The execution graph expands.
7. Challenger / counter-evidence roles appear.
8. The user can steer the investigation mid-run.
9. Compatible work is preserved instead of discarded.
10. Dredge verifies, arbitrates, and returns a structured result.
```

The goal is simple: **you should be able to watch the intelligence reconfigure itself.**

## Execution graph

Dredge Echo Astra materializes controller decisions into an auditable runtime graph.

Nodes can be:

- spawned;
- retired;
- preserved;
- completed;
- failed;
- reassigned a deeper reasoning effort.

This makes steering a first-class behavior instead of a restart button.

Example transition:

```text
GROUNDED
├── evidence_scout
└── astra_investigator

        ↓ contradiction detected

ADVERSARIAL
├── evidence_scout          [preserved]
├── astra_investigator      [preserved]
├── challenger              [spawned]
├── counter_evidence_scout  [spawned]
└── arbiter                 [spawned]
```

## Observable control plane

Dredge exposes compact controller telemetry rather than hidden chain-of-thought.

Example:

```json
{
  "mode": "adversarial",
  "reasoning": "high",
  "agents": [
    "evidence_scout",
    "astra_investigator",
    "challenger",
    "counter_evidence_scout",
    "arbiter"
  ],
  "rationale_codes": [
    "EVIDENCE_CONFLICT"
  ],
  "may_collapse": false
}
```

The important question is not just *what did the model answer?* It is also:

> **Why did the system decide it needed more intelligence?**

## Verified Intelligence Response

The target API returns more than prose.

```json
{
  "answer": "...",
  "confidence": 0.91,
  "evidence_state": "verified",
  "claims": [
    {
      "claim": "...",
      "status": "supported",
      "sources": ["..."]
    }
  ],
  "contradictions": [],
  "uncertainties": [],
  "decision_trace": {
    "topology": "adversarial",
    "tools_used": 4,
    "revisions": 2
  },
  "reasoning_profile": {
    "initial_effort": "medium",
    "peak_effort": "xhigh",
    "reason": "evidence conflict"
  }
}
```

## Interruptible intelligence

A user should be able to redirect an active investigation without throwing away good work.

Dredge can preserve compatible branches, invalidate only affected work, and re-plan the remaining graph.

The visible experience should show:

- what work was preserved;
- what was retired;
- what new branches were created;
- how reasoning effort changed;
- why the topology changed.

## Collapse is intelligence too

More agents are not automatically smarter.

When evidence coverage is high, contradiction is low, uncertainty is low, and source quality is strong, Dredge can collapse its topology and finish early.

That keeps latency and cost proportional to epistemic difficulty.

## Core components

```text
bridge/control_plane.py
    Chooses orchestration mode, reasoning depth, and controller state.

bridge/execution_graph.py
    Materializes controller decisions into mutable runtime nodes.

bridge/adaptive_agent.py
    Runs the adaptive research loop and emits observable intelligence events.

bridge/architecture.py
    Defines the explicit Astra-default and Nebius-opt-in routing contract.

bridge/astra_verifier.py
    Runs Astra's independent evidence-challenger call for Dredge.

bridge/arcade_runtime.py
    Authorizes and executes allowlisted Arcade tools and normalizes live news evidence.

bridge/llm_adapter.py
    Provides the isolated OpenAI/Astra and Nebius model interfaces.

app.py
    Presents the architecture selector and dispatches only the chosen path.
```

## Run the branch

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the shared retrieval secret and the credentials for whichever routes the deployment should offer. Do not commit API keys.

```bash
export TAVILY_API_KEY="your-tavily-key"

# Default Astra Adaptive route
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-6-astra"

# Optional Nebius Verified route
export NEBIUS_API_KEY="your-nebius-key"
export NEBIUS_MODEL="your-kimi-model"
export NVIDIA_MODEL="your-nemotron-model"

# Optional Arcade live-action evidence channel
export ARCADE_API_KEY="your-arcade-project-key"
export ARCADE_TOOL_ALLOWLIST="GoogleNews.SearchNewsStories"
```

The selector invokes only the chosen route, so a deployment can run Astra alone or expose both architectures.

Then launch:

```bash
python app.py
```

Run the tests:

```bash
pytest -q
```

## What we are proving

Dredge Echo Astra is built around a different premise:

> Intelligence should not be a fixed amount of computation attached to every prompt.

The system should be able to notice when reality becomes more complicated, allocate more reasoning, create the right verification structure, preserve useful work during steering, and stop when further work is no longer justified.

That is the product.

## Competition branch boundary

This branch is intentionally isolated from the Nebius hackathon submission on `main`. It can demonstrate the original Nebius runtime as an optional comparison path without changing or redeploying that submission.

```text
main
└── stable Nebius submission

feat/gpt-6-astra
└── Dredge Echo Astra / Product Hunt development
```

The Astra work remains on `feat/gpt-6-astra` unless an intentional release or merge decision is made.

## Status

- ✅ Adaptive control plane
- ✅ Dynamic reasoning depth
- ✅ Dynamic orchestration modes
- ✅ Runtime execution graph
- ✅ Graph preservation / retirement / steering primitives
- ✅ Structured intelligence events
- ✅ Astra-specific architecture documentation
- ✅ Dedicated automated tests
- ✅ Live Astra demo path and judge-facing visualization
- ✅ Streaming topology transitions
- ✅ Final Product Hunt presentation layer
- ✅ Judge access flow with the published access code
- ✅ Astra-default / Nebius-opt-in architecture selector
- ✅ Provider-isolated runtime dispatch with no silent fallback
- ✅ Multi-turn conversational investigation and steering
- ✅ Arcade live-news tool execution with per-session identity
- ✅ Arcade allowlist, authorization handoff, and execution telemetry

---

**Dredge Echo Astra**  
**Ask once. Dredge until the answer holds.**
