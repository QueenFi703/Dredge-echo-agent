# Dredge Echo Astra

> **Ask once. Dredge until the answer holds.**

Dredge Echo Astra is an adaptive intelligence control plane for API responses that must survive scrutiny. It does not treat reasoning depth, agent count, verification, or tool use as fixed pipeline settings. It dynamically changes both **how deeply the system reasons** and **how intelligence is orchestrated** as evidence, uncertainty, risk, and contradictions evolve.

## Product thesis

Most AI APIs follow a fixed shape:

`prompt -> model -> response`

Dredge Echo follows a changing intelligence topology:

`intent -> evidence -> hypotheses -> challenge -> arbitration -> verified response`

The topology is not static. Dredge observes the current epistemic state and decides what machinery is warranted next.

## Two adaptive dimensions

### 1. Dynamic reasoning depth

Different work receives different reasoning budgets. Simple extraction or scouting should not consume the same reasoning depth as conflict resolution or final arbitration.

Example allocation:

- Scout: low
- Claim mapper: low/medium
- Primary Astra investigator: medium/high
- Challenger: high
- Hypothesis judge: xhigh
- Final arbiter: xhigh when material uncertainty remains

Reasoning depth can escalate when evidence conflict, uncertainty, or materiality rises, and it can de-escalate when evidence converges.

### 2. Dynamic orchestration depth

Dredge chooses the smallest sufficient topology, then expands or collapses it at runtime.

Internal orchestration modes:

- **DIRECT** — Astra handles low-complexity work directly.
- **GROUNDED** — evidence scout + Astra + evidence check.
- **INVESTIGATIVE** — multiple evidence branches and claim mapping.
- **ADVERSARIAL** — challenger and counter-evidence are spawned when conflict appears.
- **DELIBERATIVE** — competing hypotheses are built and judged independently.
- **ESCALATED** — high-stakes unresolved work receives independent verification, source-quality auditing, and deep arbitration.

These are not user-facing presets. They are controller states selected from observable signals.

## Control-plane signals

The controller may consider:

- task complexity
- whether external evidence is required
- evidence coverage
- contradiction score
- uncertainty
- materiality / consequence of error
- source quality
- tool failure rate
- number of competing hypotheses
- user risk tolerance

The controller should emit compact audit metadata, not hidden chain-of-thought.

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
  "rationale_codes": ["EVIDENCE_CONFLICT"],
  "may_collapse": false
}
```

## Verified Intelligence Response

The final API should return more than prose. It should expose the state of the evidence and the system's confidence discipline without exposing private reasoning.

Target response shape:

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

## Evidence Graph

Dredge should model conclusions as claims connected to supporting and conflicting evidence. Confidence should be informed by evidence coverage, contradiction, independence, recency, source quality, and unresolved assumptions.

The graph should make it possible to answer questions such as:

- Which material claim depends on only one source?
- Which claims are contradicted?
- Which conclusions depend on inference rather than direct evidence?
- Which source is carrying disproportionate weight?
- Is additional verification likely to change the conclusion?

## Collapse is intelligence too

Dredge must know when **not** to add more agents. When evidence coverage is high, contradiction is low, uncertainty is low, and source quality is strong, the controller can collapse the topology and finish early.

This prevents "agent count" from becoming a proxy for intelligence and keeps latency/cost proportional to epistemic difficulty.

## Interruptible intelligence

Astra-native steering should allow a user to redirect an active investigation without discarding completed useful work. Dredge should preserve compatible evidence, invalidate only the affected branches, and re-plan the remaining work.

The visible experience should communicate:

- what work is preserved
- what is being re-scoped
- what new branches are being created
- how the intelligence state changed

## API direction

Primary endpoint target:

`POST /v1/reason`

Suggested streaming event vocabulary:

- `plan`
- `orchestration_state`
- `search`
- `evidence`
- `claim`
- `conflict`
- `reasoning_escalation`
- `topology_change`
- `verification`
- `arbitration`
- `answer`

The API should make adaptive cognition observable as structured telemetry rather than expose private chain-of-thought.

## Product Hunt demo principle

The demo should prove one behavior exceptionally well:

1. User asks a material research question.
2. Dredge begins in a lean topology.
3. Parallel evidence arrives.
4. A contradiction is detected.
5. Reasoning depth increases.
6. The orchestration topology expands into an adversarial or deliberative configuration.
7. The user steers the investigation mid-run.
8. Compatible work is preserved; affected branches are re-planned.
9. Dredge verifies and arbitrates.
10. A structured Verified Intelligence Response is streamed with evidence state, uncertainty, and decision telemetry.

The user should not need to be told that Dredge is sophisticated. They should be able to watch the system behave sophisticatedly.

## Boundary with the Nebius submission

The Nebius hackathon implementation remains the stable submission on `main`. Astra development occurs only on `feat/gpt-6-astra` until an intentional release decision is made. The Astra architecture may preserve useful concepts from the Kimi + Nemotron research pipeline, but it must not disturb the submitted Nebius path.
