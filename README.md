# Fractal Operational Coherence

**Build systems that remain coherent under entropy and teach coherence through use.**

---

## What Is This?

This repository implements a **fractal architecture** for GitHub Actions workflows that:

- ✅ Remains **coherent** across substrates (GitHub Actions, Docker, local machines)
- ✅ Handles **entropy** gracefully (disk exhaustion, memory pressure, network failures)
- ✅ **Teaches** through structure (learn by living in the system)
- ✅ **Scales** through patterns that repeat at every level

Not code that works once.  
**Structure that holds its shape.**

---

## Quick Start

### Nebius Token Factory

The LLM bridge can run against Nebius Token Factory's OpenAI-compatible API.
Install the optional client, copy the environment template, and choose a model
from the Token Factory catalog:

```bash
pip install -e ".[nebius]"
cp .env.example .env
```

Set `NEBIUS_API_KEY` and `NEBIUS_MODEL` in your shell or deployment secret
manager, then initialize the bridge with `backend="nebius"`:

```python
from bridge.llm_adapter import LLMAdapter

agent = LLMAdapter(backend="nebius")
response = agent.generate(
    "distill_skill",
    source="execution_trace",
    target="verified_skill_candidate",
    source_value={"status": "success", "steps": ["inspect", "execute", "verify"]},
)
```

`NEBIUS_BASE_URL` defaults to `https://api.tokenfactory.nebius.com/v1` and can
be overridden for a compatible dedicated endpoint. Never commit the API key.

### For New Contributors

1. **Read the mental model:** [docs/onboarding/MENTAL_MODEL.md](docs/onboarding/MENTAL_MODEL.md)
2. **Explore a workflow:** [.github/workflows/ci.yml](.github/workflows/ci.yml)
3. **See the pattern:** [.github/workflows/_template.yml](.github/workflows/_template.yml)
4. **Start contributing:** [docs/onboarding/CONTRIBUTING.md](docs/onboarding/CONTRIBUTING.md)

### For Operators

1. **When things break:** [docs/operations/RUNBOOK.md](docs/operations/RUNBOOK.md)
2. **How to debug:** Check metrics in `.metrics/` directory
3. **System health:** Run `bash scripts/core/health-check.sh`

### For Architects

1. **Why this exists:** [docs/architecture/PHILOSOPHY.md](docs/architecture/PHILOSOPHY.md)
2. **Governing principles:** [docs/architecture/PRINCIPLES.md](docs/architecture/PRINCIPLES.md)
3. **Recurring patterns:** [docs/architecture/PATTERNS.md](docs/architecture/PATTERNS.md)
4. **Decision history:** [docs/architecture/DECISION_LOG.md](docs/architecture/DECISION_LOG.md)

---

## The Core Idea

Every workflow follows the same rhythm:

```
Init → Prepare → Execute → Report → Cleanup → Seal
```

This pattern repeats at every scale:
- **Workflows** follow this pattern
- **Actions** follow this pattern internally
- **Scripts** follow this pattern

Same pattern, different scales. **Fractal.**

---

## Directory Structure

```
.
├── .github/
│   ├── workflows/              # Orchestration layer
│   │   ├── _template.yml       # The canonical workflow pattern
│   │   ├── ci.yml              # Continuous integration
│   │   ├── test-suite.yml      # Test execution
│   │   └── deploy.yml          # Deployment
│   │
│   └── actions/                # Composable building blocks
│       ├── cadence/            # Behavior Layer (phase patterns)
│       │   ├── phase-init/
│       │   ├── phase-prepare/
│       │   ├── phase-execute/
│       │   ├── phase-report/
│       │   └── phase-cleanup/
│       │
│       ├── survival/           # Reality Layer (entropy handling)
│       │   ├── resource-check/
│       │   ├── cleanup-disk/
│       │   ├── prune-cache/
│       │   ├── validate-health/
│       │   └── graceful-fail/
│       │
│       └── observability/      # Teaching Layer (visibility)
│           ├── metrics-collect/
│           ├── summary-generate/
│           ├── trace-context/
│           └── failure-report/
│
├── docs/
│   ├── architecture/           # Why it's designed this way
│   │   ├── PHILOSOPHY.md       # The invariants we encode
│   │   ├── PRINCIPLES.md       # The 10 laws
│   │   ├── PATTERNS.md         # Recurring structures
│   │   └── DECISION_LOG.md     # Design decisions
│   │
│   ├── operations/             # How to operate the system
│   │   └── RUNBOOK.md          # Operational procedures
│   │
│   └── onboarding/             # How to learn the system
│       ├── MENTAL_MODEL.md     # How to think about it
│       └── CONTRIBUTING.md     # How to extend it
│
├── scripts/                    # Substrate-agnostic tooling
│   ├── core/                   # Pure behavior (runs anywhere)
│   │   ├── phase-runner.sh
│   │   ├── metric-collector.sh
│   │   └── health-check.sh
│   │
│   └── adapters/               # Context-specific wrappers
│       ├── ci-adapter.sh       # For GitHub Actions
│       ├── docker-adapter.sh   # For containers
│       └── local-adapter.sh    # For local development
│
└── manifests/                  # Configuration as data
    ├── phases.yml              # Phase definitions
    ├── metrics.yml             # What to measure
    ├── thresholds.yml          # When to care
    └── cleanup-policies.yml    # Resource management
```

---

## The Three Layers

### 1. Reality Layer (Survival)

Handles the messy reality of execution:
- Disk fills up
- Memory exhausts
- Networks fail
- Caches corrupt

**Actions:** `resource-check`, `cleanup-disk`, `prune-cache`, `validate-health`, `graceful-fail`

### 2. Behavior Layer (Cadence)

Defines patterns that remain invariant:
- Init (establish context)
- Prepare (ready resources)
- Execute (do work)
- Report (communicate state)
- Cleanup (manage entropy)

**Actions:** `phase-init`, `phase-prepare`, `phase-execute`, `phase-report`, `phase-cleanup`

### 3. Teaching Layer (Observability)

Makes the system comprehensible:
- Collects metrics
- Generates summaries
- Establishes trace context
- Reports failures informatively

**Actions:** `metrics-collect`, `summary-generate`, `trace-context`, `failure-report`

---

## Key Features

### ✅ Substrate-Agnostic

Core scripts work everywhere:
- GitHub Actions
- Docker containers
- Local machines
- CI runners
- Any system with Bash

### ✅ Observable

Every action reports:
- What it's doing
- What it found
- What it decided
- Why it decided it

Metrics flow to:
- GitHub step summaries
- JSON files (`.metrics/`)
- Artifacts (retained 30-90 days)

### ✅ Graceful Degradation

When things fail:
- Failures explain themselves
- Context is preserved
- Recovery is attempted
- State is reported

### ✅ Self-Teaching

The system teaches through:
- **Structure:** Consistent patterns make unfamiliar feel familiar
- **Failure:** Errors explain what happened and why
- **Metrics:** State is always visible

---

## Example Workflow

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Phase 1: Init
      - uses: ./.github/actions/cadence/phase-init
        with:
          context: ci
      
      # Phase 2: Prepare
      - uses: ./.github/actions/cadence/phase-prepare
        with:
          language: python
          cache-key: ${{ hashFiles('requirements.txt') }}
      
      # Phase 3: Execute
      - uses: ./.github/actions/cadence/phase-execute
        with:
          command: pytest
          collect-coverage: true
      
      # Phase 4: Report
      - uses: ./.github/actions/cadence/phase-report
        if: always()
        with:
          phase: execute
          status: ${{ job.status }}
      
      # Phase 5: Cleanup
      - uses: ./.github/actions/cadence/phase-cleanup
        if: always()
```

---

## Philosophy

We optimize for **sustained coherence**, not short-term speed.

### The Four Invariants

1. **Behavior is invariant** — Tools change, behavior doesn't
2. **Structure teaches** — People learn by living in the system
3. **Failure is information** — Systems fail informatively, not silently
4. **Coherence under pressure** — Elegance during crisis, not just calm

Read more: [docs/architecture/PHILOSOPHY.md](docs/architecture/PHILOSOPHY.md)

---

## Common Tasks

### Check System Health
```bash
bash scripts/core/health-check.sh
```

### Collect Metrics
```bash
bash scripts/core/metric-collector.sh --type resource
```

### Run Workflow Locally
```bash
# Use adapters for local execution
bash scripts/adapters/local-adapter.sh phase-runner --phase init --command "echo test"
```

### View Workflow Metrics
```bash
# After workflow completes
gh run view <run-id>
gh run download <run-id> --name metrics-*
cat .metrics/*.json
```

---

## Documentation

### For Learning
- [Mental Model](docs/onboarding/MENTAL_MODEL.md) - How to think about the system
- [Contributing](docs/onboarding/CONTRIBUTING.md) - How to extend it

### For Operating
- [Runbook](docs/operations/RUNBOOK.md) - What to do when things break

### For Understanding
- [Philosophy](docs/architecture/PHILOSOPHY.md) - Why it exists
- [Principles](docs/architecture/PRINCIPLES.md) - The 10 laws
- [Patterns](docs/architecture/PATTERNS.md) - Recurring structures
- [Decisions](docs/architecture/DECISION_LOG.md) - Why we chose X over Y

---

## What This Architecture Gives You

### 1. Consistency
Every workflow looks the same. Learn once, use everywhere.

### 2. Observability
Always know what's happening. Metrics, summaries, reports.

### 3. Resilience
Handles failure gracefully. Informative errors. Recovery hints.

### 4. Teachability
New contributors productive in hours, not weeks.

### 5. Substrate Freedom
Same code works in GitHub Actions, Docker, local machines.

---

## The Fractal Property

```
Repository (manifests → scripts → actions → workflows → docs)
  ↓
Workflow (init → prepare → execute → report → cleanup → seal)
  ↓
Action (inputs → validate → execute → report → outputs)
  ↓
Script (args → check → run → log → exit)
```

**Same rhythm at every level.**

---

## Questions This Answers

- ✅ "How do I make workflows consistent?" → **Use the cadence pattern**
- ✅ "How do I handle failure gracefully?" → **Use survival actions**
- ✅ "How do I make systems observable?" → **Use observability actions**
- ✅ "How do I teach new people?" → **Structure teaches through use**
- ✅ "How do I scale this?" → **Fractal patterns repeat everywhere**

---

## License

This architecture is a pattern, not code. Use it, adapt it, share it.

---

## Further Reading

Start here: [docs/onboarding/MENTAL_MODEL.md](docs/onboarding/MENTAL_MODEL.md)

**This is not just a CI/CD setup.**  
**This is an architecture for systems that hold their shape.**
