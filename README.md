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

# Dredge Echo — Astra Runtime

> **Ask once. Dredge until the answer holds.**

Dredge Echo is a dynamic intelligence control plane: it decides what work a problem deserves before asking a model to perform that work. This branch expresses that larger Dredge vision through GPT-6 Astra.

Instead of treating every request as the same fixed pipeline, Dredge changes both **reasoning depth** and **orchestration depth** as evidence, uncertainty, contradiction, and risk evolve. It expands when the evidence becomes difficult, collapses when the answer becomes stable, preserves useful work when the investigation changes, and exposes those decisions as structured telemetry.

## The Dredge Echo thesis

Dredge began with a simple conviction: the shape of the reasoning process should not be fixed before the system understands the problem.

That conviction became a control plane that can:

- inspect the difficulty and materiality of a question;
- choose the smallest sufficient reasoning topology;
- create research, challenge, hypothesis, verification, and arbitration roles only when needed;
- deepen reasoning when evidence conflicts;
- preserve completed work while retiring branches that no longer matter;
- stop when further computation is unlikely to improve the answer; and
- return an inspectable evidence and execution record instead of hiding the process behind a single response.

GPT-6 Astra supplies the frontier reasoning and research capability in this branch. Dredge supplies the intelligence architecture: when to call, what role each call performs, how deeply it should reason, what dependencies it must respect, and whether its result should be preserved, challenged, or retired.

Names such as `challenger`, `claim_mapper`, and `arbiter` are Dredge execution roles, not hidden external models. Astra performs the language-model work through separate role-specific calls while Dredge controls the evolving workflow.

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

bridge/llm_adapter.py
    Provides the model interface used by the Astra path.
```

## Run the branch

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the required runtime secrets in your deployment environment. Do not commit API keys.

```bash
export TAVILY_API_KEY="your-tavily-key"
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-6-astra"
```

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

This branch is intentionally isolated from the Nebius hackathon submission on `main`. Its documentation, runtime work, and deployment remain Astra-specific; the completed Nebius submission is not changed or redeployed.

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

---

**Dredge Echo Astra**  
**Ask once. Dredge until the answer holds.**
