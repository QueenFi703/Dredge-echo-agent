# Mental Model

How to think about this system.

---

## The Core Metaphor: A Factory Floor

Think of this system as a **factory with stations**:

```
Raw Materials → Station 1 → Station 2 → Station 3 → Quality Check → Shipping
                 (Init)     (Prepare)   (Execute)    (Report)      (Cleanup)
```

Each station:
- Has a specific job
- Checks inputs before starting
- Does its work
- Reports what it did
- Cleans up before the next station

**This is why every workflow has the same phases.**

---

## The Three Views

The system operates at three levels simultaneously:

### 1. The Reality Layer (What Actually Happens)

```
Disk fills up
Memory runs out
Networks fail
Commands timeout
Dependencies break
```

This is **entropy**. It's always happening. The system doesn't pretend it doesn't exist.

### 2. The Behavior Layer (What Should Happen)

```
Check resources
Restore cache
Run tests
Generate report
Clean up
```

These are **invariant patterns**. They work the same way every time, in every environment.

### 3. The Teaching Layer (How To Understand It)

```
Metrics
Summaries
Documentation
Failure reports
```

This makes the system **comprehensible**. You can see what's happening and why.

---

## Key Mental Models

### Model 1: Phases Are Like Chapters

A workflow is a story told in chapters:

- **Chapter 1 (Init):** "Once upon a time, in a clean environment..."
- **Chapter 2 (Prepare):** "We gathered the tools we needed..."
- **Chapter 3 (Execute):** "We did the work..."
- **Chapter 4 (Report):** "Here's what we learned..."
- **Chapter 5 (Cleanup):** "We cleaned up and went home."

You always know which chapter you're in. You always know what comes next.

### Model 2: Actions Are Lego Blocks

Each action is a **brick**:
- Specific shape (inputs/outputs)
- Specific purpose
- Combines with other bricks
- Reusable

You build workflows by snapping bricks together:

```yaml
- uses: phase-init       # Brick 1
- uses: phase-prepare    # Brick 2
- uses: phase-execute    # Brick 3
```

### Model 3: Metrics Are Breadcrumbs

Imagine walking through a forest while dropping breadcrumbs:

```
Start → breadcrumb → breadcrumb → breadcrumb → End
```

Metrics are your breadcrumbs. When something goes wrong, you follow them back:

```
Init (10GB disk) → Prepare (9GB) → Execute (3GB) → FAIL
```

"Ah, disk filled up during execute!"

### Model 4: Manifests Are Laws

Think of manifests as **laws of physics** for your workflows:

```yaml
# manifests/thresholds.yml
disk_space:
  critical: 5gb
```

This isn't a suggestion. It's a law. When disk drops below 5GB, the system **must** react.

Laws are:
- Visible (not hidden in code)
- Debatable (can be changed through PR)
- Enforced (scripts read and obey them)

### Model 5: Failure Is A Teacher

When something breaks, the system doesn't just fail. It **teaches**:

```
❌ Deployment Failed

What: Healthcheck timeout
Where: Phase 3 (Execute), step "Deploy to production"
Why: Service didn't respond in 30s
How to fix: Check service logs, verify deployment
Resources: 45GB disk, 2048MB memory (sufficient)
Context: deploy-1234567890-run-567
```

This is a **lesson**, not just an error.

---

## How Information Flows

```
User triggers workflow
  ↓
Workflow calls action
  ↓
Action calls script
  ↓
Script collects metrics
  ↓
Metrics flow back up
  ↓
Summary generated
  ↓
User sees result
```

At each level:
- Inputs flow down
- Outputs flow up
- Metrics flow up
- Errors flow up (with context)

---

## The Fractal Property

**Same pattern, different scales.**

### At Repository Level
```
manifests/ (config)
scripts/ (behavior)
actions/ (composition)
workflows/ (orchestration)
docs/ (teaching)
```

### At Workflow Level
```
init
prepare
execute
report
cleanup
seal
```

### At Action Level
```
inputs
validate
execute
report
outputs
```

### At Script Level
```
parse args
check prereqs
run logic
log output
exit
```

**The rhythm is identical.**

This means: Learn it once, use it everywhere.

---

## Navigation Patterns

### "Where do I find X?"

**Looking for behavior:**
- Core logic → `scripts/core/`
- Reusable actions → `.github/actions/`
- Workflows → `.github/workflows/`

**Looking for configuration:**
- What matters → `manifests/metrics.yml`
- Thresholds → `manifests/thresholds.yml`
- Phases → `manifests/phases.yml`

**Looking for understanding:**
- Why → `docs/architecture/PHILOSOPHY.md`
- How → `docs/architecture/PATTERNS.md`
- When things break → `docs/operations/RUNBOOK.md`

### "How do I do X?"

**Add a new workflow:**
1. Copy `.github/workflows/_template.yml`
2. Change context and command
3. Follow the same phase structure

**Add a new action:**
1. Look at existing action in same layer
2. Copy the pattern (inputs → validate → execute → report → outputs)
3. Put it in the right layer directory

**Change a threshold:**
1. Edit `manifests/thresholds.yml`
2. System reads it automatically
3. No code changes needed

---

## Common Misconceptions

### ❌ "More phases = better"
No. The 6 phases are **sufficient**. Adding more creates confusion.

### ❌ "Actions should do everything"
No. Actions should be **composable**. Small, focused, combinable.

### ❌ "Manifests are optional"
No. Manifests are how the system knows **what matters**. Use them.

### ❌ "Metrics slow things down"
Metrics cost microseconds. Debugging without metrics costs hours.

### ❌ "Documentation is separate from code"
No. Structure **is** documentation. Docs explain the structure.

---

## Mental Shortcuts

### Quick Diagnosis
```
Workflow failed → Check phase
Phase failed → Check step
Step failed → Check metrics
Metrics show → Root cause
```

### Quick Implementation
```
Need new behavior → Check for existing action
No action → Create action using pattern
Need workflow → Copy template
Need config → Edit manifest
```

### Quick Learning
```
New to system → Read PHILOSOPHY.md
Need to contribute → Read CONTRIBUTING.md
Need to debug → Read RUNBOOK.md
Need to understand structure → Read this file
```

---

## The "Aha!" Moments

When you "get" this system, you'll notice:

1. **"Every workflow looks the same!"**
   - Yes. That's intentional. Consistency is learnable.

2. **"Actions are just building blocks!"**
   - Yes. Lego bricks. Compose them.

3. **"Failures actually explain themselves!"**
   - Yes. Informative failure is a design goal.

4. **"I can run this locally!"**
   - Yes. Substrate-agnostic means it works anywhere.

5. **"The structure teaches me!"**
   - Yes. You're learning by living in it.

---

## Next Steps

Now that you have the mental model:

1. **Read a workflow:** `.github/workflows/ci.yml`
   - Notice the phases
   - See the pattern

2. **Read an action:** `.github/actions/cadence/phase-init/action.yml`
   - Notice inputs/outputs
   - See the composition

3. **Read a manifest:** `manifests/phases.yml`
   - Notice it's data
   - See how it defines structure

4. **Try it:** Run a workflow
   - Watch the phases
   - See metrics collected
   - Notice the summaries

---

## Further Reading

- [WORKFLOW_ANATOMY.md](./WORKFLOW_ANATOMY.md) - Deep dive into workflow structure
- [CONTRIBUTING.md](./CONTRIBUTING.md) - How to add to the system
- [PHILOSOPHY.md](../architecture/PHILOSOPHY.md) - Why it's designed this way
