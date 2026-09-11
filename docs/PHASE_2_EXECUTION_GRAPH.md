# Phase 2 — Adaptive Execution Graph

## Objective

Phase 2 turns Dredge Echo Astra from a controller that selects intelligence states into a runtime that can **materialize, mutate, preserve, and retire work while an investigation is in flight**.

The core principle is:

> Dredge does not follow a workflow. Dredge builds the workflow the problem deserves.

## Relationship to Phase 1

Phase 1 established two adaptive axes:

1. **Reasoning depth** — how much reasoning budget a task or subtask receives.
2. **Orchestration depth** — which topology is required: direct, grounded, investigative, adversarial, deliberative, or escalated.

Phase 2 adds a third layer:

3. **Execution graph** — the concrete runtime work graph that instantiates the selected topology and changes as the investigation evolves.

The control plane decides *what configuration is warranted*. The execution graph decides *what work exists right now*.

## Runtime model

The graph is composed of `ExecutionNode` objects. Each node represents an observable unit of work such as:

- evidence scout
- parallel scout
- claim mapper
- Astra investigator
- challenger
- counter-evidence scout
- hypothesis builder
- hypothesis judge
- source-quality auditor
- independent verifier
- arbiter

Each node has:

- stable node id
- role
- lifecycle status
- assigned reasoning effort
- optional dependencies
- compact result metadata

Node lifecycle states:

- `pending`
- `running`
- `complete`
- `preserved`
- `retired`
- `failed`

## Materialization

Whenever the control plane emits an `IntelligenceState`, the execution graph materializes it.

Example:

```text
State: GROUNDED / MEDIUM

Graph:
[n001 evidence_scout]
        ↓
[n002 astra_investigator]
        ↓
[n003 evidence_checker]
```

If contradiction appears:

```text
State: ADVERSARIAL / HIGH

Existing graph is preserved where useful.
New work is spawned:

+ challenger
+ counter_evidence_scout
+ arbiter
```

Existing nodes should not be recreated simply because the topology expands.

## Graph mutation

A topology transition should create a structured graph mutation describing:

```json
{
  "event": "GRAPH_MATERIALIZED",
  "spawned": ["n004", "n005", "n006"],
  "retired": [],
  "preserved": [],
  "details": {
    "mode": "adversarial",
    "reasoning": "high"
  }
}
```

The runtime should make these mutations streamable to the client.

## Mid-run steering

Steering is a graph mutation, not a restart.

A steering instruction may identify:

- roles or branches to preserve
- roles or branches to retire
- new branches to spawn
- a new reasoning effort
- the user steering instruction

Example:

```text
User: Focus on St. Louis regulation and ignore national averages.

Preserve:
✓ claim_mapper
✓ hardware_economics

Retire:
× national_market_scout

Spawn:
+ local_regulation_scout
+ st_louis_market_scout
```

The graph should record a `GRAPH_STEERED` mutation and continue from the surviving state.

## Information-value pruning

Codex implementation should add a lightweight expected-information-value policy after the graph lifecycle is stable.

Candidate branches should be retired when:

- evidence coverage is already high,
- the branch is duplicating evidence already gathered,
- new information is unlikely to change a material conclusion,
- latency or cost exceeds expected information gain,
- source quality remains persistently poor.

This allows Dredge to collapse work because additional investigation has low expected value, not merely because a hardcoded agent count was reached.

## Concurrency contract

The graph should be designed for concurrent execution even if the first implementation executes some nodes serially.

Codex should preserve these invariants:

1. Independent nodes may run concurrently.
2. Dependencies gate only the nodes that actually require them.
3. A completed node remains reusable after topology expansion.
4. Steering invalidates only affected branches.
5. Retired nodes do not silently re-enter the graph.
6. Failed nodes produce explicit failure metadata and may trigger control-plane escalation.
7. The graph snapshot is serializable and safe to stream.

## Control loop

Target Phase 2 runtime loop:

```text
QUESTION
   ↓
CONTROL PLANE
   ↓
EXECUTION GRAPH MATERIALIZE
   ↓
RUN READY NODES
   ↓
OBSERVE RESULTS
   ↓
UPDATE SIGNALS
   ↓
CONTROL PLANE RE-EVALUATE
   ↓
GRAPH MUTATE
   ├─ spawn
   ├─ preserve
   ├─ retire
   └─ escalate reasoning
   ↓
repeat until conclusion is stable
```

The graph is therefore not a static DAG created once at the beginning. It is a **living execution graph**.

## API telemetry

Add graph-oriented streaming events to `/v1/reason`:

- `graph_created`
- `node_spawned`
- `node_started`
- `node_completed`
- `node_failed`
- `node_preserved`
- `node_retired`
- `graph_steered`
- `graph_collapsed`
- `reasoning_escalation`
- `answer`

Do not stream internal hidden reasoning. Stream only operational state, evidence state, compact rationale codes, and lifecycle telemetry.

## Current implementation boundary

Implemented in this phase:

- `bridge/execution_graph.py`
- execution node lifecycle
- graph materialization from `IntelligenceState`
- expansion without recreating existing nodes
- targeted preserve/retire/spawn steering mutations
- serializable graph snapshots
- unit tests for materialization, expansion, and steering

Still to implement:

- concurrent node scheduler
- dependency-aware ready queue
- evidence/result attachment to graph nodes
- automatic graph mutation from live `AdaptiveResearchAgent` checkpoints
- user steering endpoint/event ingestion
- information-value pruning
- SSE or WebSocket graph event stream
- persisted/resumable investigation state

## Codex implementation priority

Implement in this order:

1. Wire `ExecutionGraph` into `AdaptiveResearchAgent` checkpoints.
2. Materialize graph after each control-plane decision.
3. Mark nodes running/complete as work executes.
4. Add dependency-aware async scheduler.
5. Convert topology changes into graph mutations.
6. Add steer input that preserves unaffected nodes.
7. Add graph event streaming.
8. Add information-value pruning and collapse.
9. Add resumable graph snapshots.
10. Build the Product Hunt visualization from the same event stream.

## Definition of success

Phase 2 succeeds when a live investigation can visibly change shape without restarting:

```text
GROUNDED
   ↓ conflict
ADVERSARIAL
   ↓ user steer
ADVERSARIAL + local branch
   ↓ convergence
GROUNDED / collapsed
   ↓
VERIFIED ANSWER
```

The same execution graph should survive all of those transitions.
