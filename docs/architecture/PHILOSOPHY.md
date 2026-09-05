# Philosophy

## The Invariants

These are the fundamental truths we encode into this system:

### 1. Behavior is invariant — tools change, behavior doesn't

The **what** remains constant even when the **how** shifts. A "resource check" behaves identically whether it runs on GitHub Actions, in Docker, on a local machine, or on a GPU cluster. The substrate changes; the behavior doesn't.

**Why this matters:** Teams waste enormous energy re-learning systems when tools change. By separating behavior from substrate, we build muscle memory that transfers across contexts.

### 2. Structure teaches — people learn by living in the system

The folder layout, naming conventions, and phase ordering aren't arbitrary. They're pedagogical. A new contributor should be able to navigate the repository after 15 minutes because **the structure itself is the documentation**.

**Why this matters:** Documentation rots. Structure doesn't. When structure teaches, the system remains comprehensible even as people change.

### 3. Failure is information — systems fail informatively, not silently

When something breaks, the system tells you:
- What broke (specific error)
- Where it broke (phase, step, context)
- Why it broke (resource exhaustion, timeout, dependency failure)
- How to fix it (recovery hint, runbook reference)

**Why this matters:** Silent failures waste hours. Informative failures waste minutes. The difference compounds over time.

### 4. Coherence under pressure — elegance during crisis, not just calm

The system doesn't just work when everything is normal. It **holds its shape** when:
- Disk is full
- Memory is exhausted
- Networks are flaky
- Dependencies drift
- Timeouts expire

**Why this matters:** Systems that only work under ideal conditions aren't production systems. Real systems live in entropy.

---

## Why These Invariants?

Because systems that lack them exhibit predictable failure modes:

### Without invariant behavior:
- Every new tool requires complete relearning
- No muscle memory develops
- Tribal knowledge becomes critical
- Turnover becomes catastrophic

### Without structure that teaches:
- Onboarding takes weeks instead of hours
- Documentation is always out of date
- People ask the same questions repeatedly
- Knowledge exists in Slack threads, not the repository

### Without informative failure:
- Debugging requires deep system knowledge
- Junior engineers can't diagnose issues
- Incidents become multi-hour affairs
- Postmortems say "we need better monitoring"

### Without coherence under pressure:
- Systems collapse during incidents
- Emergency changes break everything
- Recovery requires heroics
- Culture becomes firefighting culture

---

## What We Optimize For

**Sustained coherence over short-term speed.**

We don't optimize for:
- Fastest time to first commit
- Minimum lines of code
- Fewest dependencies

We optimize for:
- Lowest time to understanding
- Fastest debugging
- Most graceful degradation
- Longest system half-life

---

## The Fractal Property

The same pattern repeats at every scale:

**At the repository level:**
```
Repository
├── Manifests (what matters)
├── Scripts (how to do it)
├── Actions (composable behaviors)
├── Workflows (orchestration)
└── Docs (why)
```

**At the workflow level:**
```
Workflow
├── Init (establish context)
├── Prepare (ready resources)
├── Execute (do work)
├── Report (communicate state)
├── Cleanup (manage entropy)
└── Seal (finalize)
```

**At the action level:**
```
Action
├── Inputs (context)
├── Validate (readiness)
├── Execute (work)
├── Report (state)
└── Outputs (results)
```

**At the script level:**
```
Script
├── Parse args (context)
├── Check prerequisites (readiness)
├── Run logic (work)
├── Log output (state)
└── Exit with code (results)
```

The **rhythm is identical**. This is why it's fractal.

---

## The Teaching Property

The system teaches in three ways:

### 1. By Structure
Consistent patterns make the unfamiliar feel familiar. When every action has the same internal structure, learning one teaches all.

### 2. By Failure
Errors explain themselves. A resource check doesn't just fail; it tells you exactly what threshold was crossed and what the current value is.

### 3. By Metrics
The system shows you what matters. Metrics aren't hidden in log files; they're in structured JSON, markdown summaries, and GitHub step summaries.

---

## What This Philosophy Produces

**Systems that:**
- Remain coherent as people change
- Degrade gracefully under pressure
- Teach through use, not documentation
- Scale across substrates
- Fail informatively
- Recover automatically

**Not code that works once.**

**Structure that holds its shape.**

---

## Further Reading

- [PRINCIPLES.md](./PRINCIPLES.md) - The 10 laws derived from this philosophy
- [PATTERNS.md](./PATTERNS.md) - Recurring structures and why they exist
- [DECISION_LOG.md](./DECISION_LOG.md) - Specific choices and their rationale
