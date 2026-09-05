# Patterns

Recurring structures and why they exist.

---

## The Cadence Pattern

**Structure:**
```
Init → Prepare → Execute → Report → Cleanup → Seal
```

**Why it exists:**
Every workflow follows this rhythm because this is how robust execution works:
1. Establish context (where am I?)
2. Ready resources (do I have what I need?)
3. Do the work (execute)
4. Communicate results (what happened?)
5. Clean up (leave no mess)
6. Finalize (seal the envelope)

**Where you see it:**
- Every workflow file
- Every composite action internally
- Core scripts structure

**When to use it:**
Always. Every workflow should follow this pattern.

**Example:**
```yaml
- uses: ./.github/actions/cadence/phase-init
- uses: ./.github/actions/cadence/phase-prepare
- uses: ./.github/actions/cadence/phase-execute
- uses: ./.github/actions/cadence/phase-report
- uses: ./.github/actions/cadence/phase-cleanup
```

---

## The Three-Layer Pattern

**Structure:**
```
Teaching Layer (docs, metrics, summaries)
  ↓
Behavior Layer (actions, patterns, invariants)
  ↓
Reality Layer (resource checks, cleanup, failure handling)
```

**Why it exists:**
Systems operate at three levels:
- **Reality:** Dealing with entropy (disk fills, memory exhausts)
- **Behavior:** Consistent patterns despite reality
- **Teaching:** Making the system comprehensible

**Where you see it:**
- `.github/actions/` organized by layer
- Documentation structure
- Workflow composition

**When to use it:**
When designing new features, ask: "Which layer does this belong to?"

---

## The Input-Validate-Execute-Report-Output Pattern

**Structure:**
```yaml
inputs:
  # Declare what you need

steps:
  - name: Validate
    # Check prerequisites
    
  - name: Execute
    # Do work
    
  - name: Report
    # Log what happened
    
outputs:
  # Declare what you produce
```

**Why it exists:**
Composable actions need clear contracts. This pattern ensures every action:
- Declares dependencies (inputs)
- Checks readiness (validate)
- Does work (execute)
- Communicates results (report)
- Provides data (outputs)

**Where you see it:**
Every composite action follows this pattern internally.

**When to use it:**
Every time you create a new action.

---

## The Graceful Degradation Pattern

**Structure:**
```yaml
- name: Try operation
  id: operation
  continue-on-error: true
  
- name: Check result
  if: steps.operation.outcome == 'failure'
  uses: ./.github/actions/survival/graceful-fail
```

**Why it exists:**
Failures are inevitable. This pattern ensures:
- Failures are contained
- Context is preserved
- Recovery is attempted
- State is reported

**Where you see it:**
- Survival actions
- Critical workflow steps
- Resource management

**When to use it:**
Any operation that might fail and shouldn't crash the entire workflow.

---

## The Metric Collection Pattern

**Structure:**
```yaml
- name: Do work
  id: work
  
- name: Collect metrics
  uses: ./.github/actions/observability/metrics-collect
  with:
    phase: ${{ current-phase }}
    
- name: Generate summary
  uses: ./.github/actions/observability/summary-generate
  with:
    phase: ${{ current-phase }}
    metrics: ${{ steps.metrics.outputs.metrics-json }}
```

**Why it exists:**
Observable systems require measurement at every step. This pattern ensures:
- Metrics are collected consistently
- Summaries are generated automatically
- State is always visible

**Where you see it:**
End of every phase in every workflow.

**When to use it:**
After every significant operation.

---

## The Adapter Pattern

**Structure:**
```bash
# ci-adapter.sh
export METRICS_DIR=".metrics"
export WORKING_DIR="$GITHUB_WORKSPACE"
exec core-script.sh "$@"
```

**Why it exists:**
Core scripts are substrate-agnostic. Adapters translate between substrate-specific environments and core behavior.

**Where you see it:**
- `scripts/adapters/`
- Each adapter for a different substrate (CI, Docker, local)

**When to use it:**
When adding support for a new execution environment.

---

## The Always-Run Cleanup Pattern

**Structure:**
```yaml
- name: Cleanup
  if: always()
  uses: ./.github/actions/cadence/phase-cleanup
```

**Why it exists:**
Resources must be managed even when workflows fail. `if: always()` ensures cleanup runs regardless of previous step outcomes.

**Where you see it:**
- Cleanup phases
- Report phases
- Failure handlers

**When to use it:**
Any step that manages resources or reports state.

---

## The Manifest-Driven Pattern

**Structure:**
```yaml
# manifests/phases.yml
phases:
  - name: init
    order: 1
    timeout: 5m
```

```python
# Code reads manifest
with open('manifests/phases.yml') as f:
    phases = yaml.load(f)
    for phase in phases:
        run_phase(phase)
```

**Why it exists:**
Configuration as data is:
- Validatable
- Queryable
- Versionable
- Auditable

**Where you see it:**
- `manifests/*.yml`
- Scripts that read manifests

**When to use it:**
When you have configuration that might change or needs validation.

---

## The Trace Context Pattern

**Structure:**
```yaml
- name: Establish context
  id: trace
  uses: ./.github/actions/observability/trace-context
  
# Later steps reference trace ID
- name: Use context
  run: echo "Trace: ${{ steps.trace.outputs.context-id }}"
```

**Why it exists:**
Distributed execution needs correlation IDs. This pattern ensures:
- Every execution has a unique ID
- IDs propagate through steps
- Failures can be correlated

**Where you see it:**
- Phase init
- Observability actions

**When to use it:**
Start of every workflow.

---

## The Composite Action Pattern

**Structure:**
```yaml
# action.yml
name: My Action
runs:
  using: composite
  steps:
    - uses: other-action-1
    - uses: other-action-2
```

**Why it exists:**
Complex workflows are built from simple actions. Composite actions let you:
- Create reusable units
- Test components independently
- Maintain consistency

**Where you see it:**
All actions in `.github/actions/`

**When to use it:**
When you find yourself repeating the same sequence of steps.

---

## The Status Propagation Pattern

**Structure:**
```yaml
- name: Step 1
  id: step1
  
- name: Step 2
  id: step2
  
- name: Report
  if: always()
  with:
    status: ${{ job.status }}
    step1-status: ${{ steps.step1.outcome }}
    step2-status: ${{ steps.step2.outcome }}
```

**Why it exists:**
Understanding what happened requires knowing:
- Overall job status
- Individual step outcomes
- Relationships between them

**Where you see it:**
- Report phases
- Summary generation

**When to use it:**
When reporting outcomes.

---

## Anti-Patterns

### ❌ The God Script Pattern
```bash
# do_everything.sh (2000 lines)
```
**Why it's bad:** Untestable, unreusable, unmaintainable.

**Fix:** Break into composable scripts.

---

### ❌ The Hidden Dependency Pattern
```yaml
- name: Step 2
  run: use_output_from_step_1.sh  # But step 1 isn't declared
```
**Why it's bad:** Implicit ordering, breaks when refactored.

**Fix:** Use `needs:` or explicit step dependencies.

---

### ❌ The Silent Failure Pattern
```bash
command_that_might_fail || true  # Silently continue
```
**Why it's bad:** Failures are invisible until they cascade.

**Fix:** Use graceful-fail action with context.

---

### ❌ The Magic Number Pattern
```bash
if [ $DISK -lt 10 ]; then  # What is 10? Why 10?
```
**Why it's bad:** Unmaintainable, unclear.

**Fix:** Use manifests/thresholds.yml.

---

## Pattern Catalog

| Pattern | Layer | Purpose |
|---------|-------|---------|
| Cadence | Behavior | Consistent workflow structure |
| Three-Layer | Architecture | Separation of concerns |
| IVERO | Behavior | Action composability |
| Graceful Degradation | Reality | Failure handling |
| Metric Collection | Teaching | Observability |
| Adapter | Reality | Substrate abstraction |
| Always-Run Cleanup | Reality | Resource management |
| Manifest-Driven | Architecture | Configuration as data |
| Trace Context | Teaching | Execution correlation |
| Composite Action | Behavior | Reusability |
| Status Propagation | Teaching | Outcome visibility |

---

## Further Reading

- [PHILOSOPHY.md](./PHILOSOPHY.md) - Why patterns matter
- [PRINCIPLES.md](./PRINCIPLES.md) - Rules that generate patterns
- [WORKFLOW_ANATOMY.md](../onboarding/WORKFLOW_ANATOMY.md) - How patterns combine in workflows
