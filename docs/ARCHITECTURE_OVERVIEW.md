# Architecture Overview

Visual guide to the Fractal Operational Coherence architecture.

---

## System at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                     TEACHING LAYER                          │
│  Documents why. Makes patterns visible. Encodes thinking.   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              BEHAVIOR LAYER                           │ │
│  │  Defines what stays invariant across contexts        │ │
│  │                                                       │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │          REALITY LAYER                          │ │ │
│  │  │  Handles entropy, failure, resource limits      │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Hierarchy

```
QueenFi703Be-operational-coherence/
│
├── 📋 manifests/                    [Configuration as Data]
│   ├── phases.yml                   Phase definitions & ordering
│   ├── metrics.yml                  What to measure
│   ├── thresholds.yml               When to alert
│   └── cleanup-policies.yml         Resource management rules
│
├── 🔧 scripts/                      [Substrate-Agnostic Logic]
│   ├── core/                        Pure behavior (no deps)
│   │   ├── phase-runner.sh         Phase execution engine
│   │   ├── metric-collector.sh     Metrics gathering
│   │   └── health-check.sh         System validation
│   └── adapters/                    Context wrappers
│       ├── ci-adapter.sh           For GitHub Actions
│       ├── docker-adapter.sh       For containers
│       └── local-adapter.sh        For local dev
│
├── 🎭 .github/actions/              [Composable Actions]
│   ├── cadence/                     [BEHAVIOR LAYER]
│   │   ├── phase-init/             Context establishment
│   │   ├── phase-prepare/          Resource preparation
│   │   ├── phase-execute/          Work execution
│   │   ├── phase-report/           Result reporting
│   │   └── phase-cleanup/          Resource cleanup
│   ├── survival/                    [REALITY LAYER]
│   │   ├── resource-check/         Validate resources
│   │   ├── cleanup-disk/           Free disk space
│   │   ├── prune-cache/            Remove old caches
│   │   ├── validate-health/        System health check
│   │   └── graceful-fail/          Failure handling
│   └── observability/               [TEACHING LAYER]
│       ├── metrics-collect/        Gather metrics
│       ├── summary-generate/       Create summaries
│       ├── trace-context/          Execution tracing
│       └── failure-report/         Failure analysis
│
├── 🔄 .github/workflows/            [Orchestration]
│   ├── _template.yml               Canonical pattern
│   ├── ci.yml                      Continuous integration
│   ├── test-suite.yml              Test execution
│   └── deploy.yml                  Deployment
│
└── 📚 docs/                         [Documentation]
    ├── architecture/                Why & how it works
    │   ├── PHILOSOPHY.md           Core invariants
    │   ├── PRINCIPLES.md           The 10 laws
    │   ├── PATTERNS.md             Recurring structures
    │   └── DECISION_LOG.md         Design decisions
    ├── operations/                  How to operate
    │   └── RUNBOOK.md              Operational procedures
    └── onboarding/                  How to learn
        ├── MENTAL_MODEL.md         How to think about it
        ├── WORKFLOW_ANATOMY.md     How workflows work
        └── CONTRIBUTING.md         How to extend it
```

---

## The Cadence Pattern

Every workflow follows this rhythm:

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐    ┌──────┐
│  INIT    │ → │  PREPARE  │ → │  EXECUTE  │ → │  REPORT  │ → │ CLEANUP │ → │ SEAL │
└──────────┘    └───────────┘    └───────────┘    └──────────┘    └─────────┘    └──────┘
     │               │                 │                │               │             │
     ├─ Context      ├─ Cache         ├─ Build        ├─ Summary      ├─ Prune      └─ Health
     ├─ Resources    ├─ Dependencies  ├─ Test         ├─ Metrics      ├─ Clean          Check
     ├─ Health       └─ Ready         ├─ Deploy       └─ Artifacts    └─ Report
     └─ Baseline                      └─ Collect

Always in this order. Always with the same structure.
```

---

## Action Composition

Actions compose like building blocks:

```
Workflow Level:
┌─────────────────────────────────────────────┐
│  ci.yml                                     │
│  ├─ uses: phase-init                        │
│  ├─ uses: phase-prepare                     │
│  ├─ uses: phase-execute                     │
│  ├─ uses: phase-report                      │
│  └─ uses: phase-cleanup                     │
└─────────────────────────────────────────────┘
                    ↓
Action Level:
┌─────────────────────────────────────────────┐
│  phase-init/action.yml                      │
│  ├─ uses: trace-context                     │
│  ├─ uses: resource-check                    │
│  ├─ uses: validate-health                   │
│  └─ uses: metrics-collect                   │
└─────────────────────────────────────────────┘
                    ↓
Script Level:
┌─────────────────────────────────────────────┐
│  health-check.sh                            │
│  ├─ Parse args                              │
│  ├─ Check disk                              │
│  ├─ Check memory                            │
│  ├─ Validate commands                       │
│  └─ Exit with status                        │
└─────────────────────────────────────────────┘

Fractal: Same pattern at every zoom level
```

---

## Data Flow

```
Inputs flow down ↓        Outputs flow up ↑        Metrics flow throughout →

┌─────────────┐           ┌─────────────┐          ┌──────────────┐
│  Workflow   │           │  Workflow   │          │   .metrics/  │
│   inputs    │           │   outputs   │          │              │
└──────┬──────┘           └──────▲──────┘          │  JSON files  │
       │                         │                 │  Summaries   │
       ↓                         │                 │  Reports     │
┌─────────────┐           ┌─────────────┐          │  Artifacts   │
│   Action    │           │   Action    │          └──────────────┘
│   inputs    │           │   outputs   │                 ▲
└──────┬──────┘           └──────▲──────┘                 │
       │                         │                        │
       ↓                         │                        │
┌─────────────┐           ┌─────────────┐          Collected at
│   Script    │           │   Script    │          every phase
│    args     │           │   results   │
└─────────────┘           └─────────────┘
```

---

## Layer Responsibilities

```
┌────────────────────────────────────────────────────────┐
│                   TEACHING LAYER                       │
│  observability/                                        │
│  ├─ Collects metrics                                   │
│  ├─ Generates summaries                                │
│  ├─ Creates trace context                              │
│  └─ Reports failures                                   │
│                                                        │
│  Makes the invisible visible                           │
└────────────────────────────────────────────────────────┘
                         ↕
┌────────────────────────────────────────────────────────┐
│                   BEHAVIOR LAYER                       │
│  cadence/                                              │
│  ├─ Defines workflow phases                            │
│  ├─ Establishes rhythm                                 │
│  ├─ Ensures consistency                                │
│  └─ Provides structure                                 │
│                                                        │
│  What stays the same everywhere                        │
└────────────────────────────────────────────────────────┘
                         ↕
┌────────────────────────────────────────────────────────┐
│                   REALITY LAYER                        │
│  survival/                                             │
│  ├─ Checks resources                                   │
│  ├─ Cleans up disk                                     │
│  ├─ Prunes caches                                      │
│  ├─ Validates health                                   │
│  └─ Handles failures                                   │
│                                                        │
│  Deals with entropy and failure                        │
└────────────────────────────────────────────────────────┘
```

---

## Failure Handling

```
Error Occurs
     │
     ↓
┌─────────────────────┐
│  Continue or Fail?  │
└──────┬──────────────┘
       │
       ├──→ Continue (continue-on-error: true)
       │        │
       │        ↓
       │    ┌──────────────────┐
       │    │  Graceful Fail   │
       │    │  ├─ Record error │
       │    │  ├─ Add context  │
       │    │  └─ Suggest fix  │
       │    └──────────────────┘
       │
       └──→ Fail (default)
                │
                ↓
          ┌──────────────────┐
          │  Always Execute: │
          │  ├─ Report phase │
          │  └─ Cleanup phase│
          └──────────────────┘
                │
                ↓
          ┌──────────────────┐
          │  Failure Report  │
          │  ├─ What failed  │
          │  ├─ Where failed │
          │  ├─ Why failed   │
          │  └─ How to fix   │
          └──────────────────┘
```

---

## Metrics Collection Flow

```
Every Phase:
    │
    ├─ Start
    │    │
    │    └─→ Record start time
    │
    ├─ Execute
    │    │
    │    └─→ Collect resource metrics
    │
    └─ End
         │
         ├─→ Record end time
         ├─→ Calculate duration
         ├─→ Write to .metrics/
         ├─→ Generate summary
         └─→ Upload artifact

Result:
    .metrics/
    ├── metrics-init-1234567890.json
    ├── metrics-prepare-1234567891.json
    ├── metrics-execute-1234567892.json
    ├── summary-execute.md
    └── trace-context.json
```

---

## Resource Management

```
Workflow Start
     │
     ↓
┌────────────────┐
│  Check Initial │  ← Phase: Init
│  Resources     │    Disk: 50GB, Memory: 8GB
└────────┬───────┘
         │
         ↓
┌────────────────┐
│  Use Resources │  ← Phase: Execute
│                │    Disk: 45GB, Memory: 6GB
└────────┬───────┘
         │
         ↓
    Low disk?
    ┌─────┴─────┐
    │           │
   Yes         No
    │           │
    ↓           ↓
┌───────────┐   Continue
│  Cleanup  │
│  ├─ Prune │
│  ├─ Clear │
│  └─ Free  │
└─────┬─────┘
      │
      ↓
┌────────────────┐
│  Check Final   │  ← Phase: Cleanup
│  Resources     │    Disk: 48GB, Memory: 7GB
└────────┬───────┘
         │
         ↓
    Workflow End
```

---

## Substrate Abstraction

```
Same Behavior, Different Substrates:

┌──────────────────────────────────────┐
│         GitHub Actions               │
│  ├─ Uses ci-adapter.sh               │
│  ├─ GITHUB_WORKSPACE set             │
│  └─ Uses actions/cache               │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│      Core Scripts (Bash)             │
│  ├─ phase-runner.sh                  │
│  ├─ metric-collector.sh              │  ← Same logic
│  └─ health-check.sh                  │     everywhere
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│         Docker Container             │
│  ├─ Uses docker-adapter.sh           │
│  ├─ /workspace set                   │
│  └─ Volume mounts for cache          │
└──────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│         Local Machine                │
│  ├─ Uses local-adapter.sh            │
│  ├─ Current directory                │
│  └─ Local cache                      │
└──────────────────────────────────────┘
```

---

## Quick Reference

### File Locations

| What | Where |
|------|-------|
| Workflow patterns | `.github/workflows/_template.yml` |
| Phase actions | `.github/actions/cadence/` |
| Resource management | `.github/actions/survival/` |
| Observability | `.github/actions/observability/` |
| Core logic | `scripts/core/` |
| Configuration | `manifests/` |
| Documentation | `docs/` |

### Action Purposes

| Action | Layer | Purpose |
|--------|-------|---------|
| phase-init | Behavior | Establish context |
| phase-prepare | Behavior | Ready resources |
| phase-execute | Behavior | Do work |
| phase-report | Behavior | Communicate results |
| phase-cleanup | Behavior | Manage resources |
| resource-check | Reality | Validate resources |
| cleanup-disk | Reality | Free disk space |
| prune-cache | Reality | Remove old caches |
| validate-health | Reality | Check system health |
| graceful-fail | Reality | Handle failures |
| metrics-collect | Teaching | Gather metrics |
| summary-generate | Teaching | Create summaries |
| trace-context | Teaching | Establish tracing |
| failure-report | Teaching | Analyze failures |

---

## Further Reading

- [README.md](../../README.md) - Start here
- [PHILOSOPHY.md](../architecture/PHILOSOPHY.md) - Why it exists
- [MENTAL_MODEL.md](../onboarding/MENTAL_MODEL.md) - How to think about it
- [WORKFLOW_ANATOMY.md](../onboarding/WORKFLOW_ANATOMY.md) - Deep dive
