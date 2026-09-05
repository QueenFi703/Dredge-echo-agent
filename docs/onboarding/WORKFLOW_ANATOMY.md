# Workflow Anatomy

Deep dive into how workflows are structured.

---

## The Anatomy of a Workflow

Every workflow in this system follows the same anatomical structure.

---

## The Six Phases

### Phase 1: Init

**Purpose:** Establish context and validate readiness.

**What it does:**
- Creates trace context (unique execution ID)
- Checks system resources (disk, memory)
- Validates system health
- Records baseline metrics

**Actions used:**
- `phase-init` (orchestrates everything)
- `trace-context` (creates execution ID)
- `resource-check` (validates resources)
- `validate-health` (checks system)
- `metrics-collect` (records baseline)

**Example:**
```yaml
- name: Initialize
  id: init
  uses: ./.github/actions/cadence/phase-init
  with:
    context: ci
    strict-health-check: 'false'
```

**Outputs:**
- `context-id`: Unique execution identifier
- `baseline-metrics`: System state at start
- `health-status`: System health (healthy/degraded/unhealthy)

---

### Phase 2: Prepare

**Purpose:** Ready all resources needed for execution.

**What it does:**
- Restores caches (if available)
- Installs dependencies
- Validates environment
- Reports preparation status

**Actions used:**
- `phase-prepare` (orchestrates everything)
- `actions/cache` (GitHub's cache action)
- Language-specific installers

**Example:**
```yaml
- name: Prepare
  id: prepare
  uses: ./.github/actions/cadence/phase-prepare
  with:
    language: python
    cache-key: ${{ hashFiles('requirements.txt') }}
    install-dependencies: 'true'
```

**Outputs:**
- `cache-hit`: Whether cache was restored
- `preparation-status`: success/partial/failed

---

### Phase 3: Execute

**Purpose:** Do the actual work (build, test, deploy).

**What it does:**
- Executes the command
- Times execution
- Collects coverage (if requested)
- Reports outcomes

**Actions used:**
- `phase-execute` (orchestrates everything)
- `metrics-collect` (records timing)

**Example:**
```yaml
- name: Execute Tests
  id: execute
  uses: ./.github/actions/cadence/phase-execute
  with:
    command: pytest --cov
    timeout-minutes: 30
    collect-coverage: 'true'
```

**Outputs:**
- `exit-code`: Command exit code
- `metrics`: Execution metrics
- `status`: success/failure

---

### Phase 4: Report

**Purpose:** Communicate what happened.

**What it does:**
- Generates summaries
- Collects final metrics
- Updates step summary
- Uploads artifacts

**Actions used:**
- `phase-report` (orchestrates everything)
- `summary-generate` (creates markdown)
- `metrics-collect` (final state)
- `actions/upload-artifact` (preserves data)

**Example:**
```yaml
- name: Report Results
  if: always()
  uses: ./.github/actions/cadence/phase-report
  with:
    phase: execute
    status: ${{ job.status }}
    metrics: ${{ steps.execute.outputs.metrics }}
```

**Outputs:**
- `report-id`: Unique report identifier

---

### Phase 5: Cleanup

**Purpose:** Manage resources and entropy.

**What it does:**
- Prunes old caches (if requested)
- Cleans temporary files
- Checks final resource state
- Reports cleanup status

**Actions used:**
- `phase-cleanup` (orchestrates everything)
- `prune-cache` (removes old entries)
- `cleanup-disk` (removes temp files)
- `resource-check` (final validation)

**Example:**
```yaml
- name: Cleanup
  if: always()
  uses: ./.github/actions/cadence/phase-cleanup
  with:
    prune-cache: 'true'
    cleanup-disk: 'true'
    aggressive: 'false'
```

**Outputs:**
- `cleanup-status`: success/partial/failed
- `space-freed-mb`: Disk space recovered

---

### Phase 6: Seal (Optional)

**Purpose:** Final validation and state commitment.

**What it does:**
- Final health check
- Validates all phases succeeded
- Commits final state

**Actions used:**
- `validate-health`

**Example:**
```yaml
- name: Seal
  if: always()
  uses: ./.github/actions/survival/validate-health
  with:
    phase: seal
    strict: 'false'
```

---

## The Lifecycle of a Workflow Run

```
Trigger (push, PR, manual)
  ↓
Phase 1: Init
  ├─ Create trace context (ci-1234567890-run-567)
  ├─ Check resources (22GB disk, 14GB memory)
  ├─ Validate health (healthy)
  └─ Record baseline metrics
  ↓
Phase 2: Prepare
  ├─ Restore cache (hit/miss)
  ├─ Install dependencies
  └─ Validate readiness
  ↓
Phase 3: Execute
  ├─ Run command (pytest, npm test, etc)
  ├─ Time execution (45s)
  ├─ Collect output
  └─ Determine outcome (success/failure)
  ↓
Phase 4: Report
  ├─ Generate summary (markdown)
  ├─ Collect metrics (final state)
  ├─ Upload artifacts
  └─ Update GitHub summary
  ↓
Phase 5: Cleanup
  ├─ Prune caches (if needed)
  ├─ Clean temp files
  ├─ Check final resources
  └─ Report cleanup status
  ↓
Phase 6: Seal
  └─ Final health check
  ↓
Complete (success/failure)
```

---

## Data Flow

### Inputs Flow Down
```
Workflow inputs (context, language, command)
  ↓
Action inputs (specific parameters)
  ↓
Script arguments (concrete values)
  ↓
Commands execute
```

### Outputs Flow Up
```
Command outputs (exit code, stdout)
  ↓
Script outputs (metrics, status)
  ↓
Action outputs (structured data)
  ↓
Workflow outputs (final results)
```

### Metrics Flow Throughout
```
Every phase:
  ↓
Metrics collected
  ↓
Written to .metrics/
  ↓
Uploaded as artifacts
  ↓
Available for analysis
```

---

## Error Handling Flow

```
Error occurs in Execute phase
  ↓
Execute phase catches error
  ↓
Records exit code
  ↓
Sets status to 'failure'
  ↓
Report phase runs (if: always())
  ├─ Generates failure summary
  ├─ Records error metrics
  └─ Uploads failure report
  ↓
Cleanup phase runs (if: always())
  ├─ Attempts cleanup
  └─ Reports cleanup status
  ↓
Workflow completes with failure
```

---

## The `if: always()` Pattern

Critical for reliability:

```yaml
- name: Execute
  id: execute
  # This might fail
  
- name: Report
  if: always()  # Runs even if execute fails
  
- name: Cleanup
  if: always()  # Runs even if execute or report fail
```

**Why:**
- Ensures metrics collected even on failure
- Ensures resources cleaned even on failure
- Ensures state visible even on failure

---

## Composing Actions

Actions compose like functions:

```yaml
# High-level workflow
- uses: phase-init

# phase-init internally uses:
#   - trace-context
#   - resource-check
#   - validate-health
#   - metrics-collect

# Each of those uses core scripts:
#   - scripts/core/health-check.sh
#   - scripts/core/metric-collector.sh
```

**Fractal composition:**
- Workflows compose actions
- Actions compose other actions
- Actions compose scripts
- Same pattern at every level

---

## Adding Custom Steps

You can add steps within phases:

```yaml
- uses: ./.github/actions/cadence/phase-init

# Custom step within init phase
- name: Custom initialization
  run: |
    echo "Project-specific init"

- uses: ./.github/actions/cadence/phase-prepare

# Custom step within prepare phase
- name: Custom preparation
  run: |
    echo "Project-specific prep"
```

**Rule:** Don't skip phases, but you can augment them.

---

## Matrix Strategies

Workflows support matrix execution:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    python-version: [3.9, 3.10, 3.11]

steps:
  - uses: ./.github/actions/cadence/phase-init
    with:
      context: test-${{ matrix.os }}-${{ matrix.python-version }}
```

Each matrix cell follows the same phase pattern.

---

## Workflow Variables

Common variables available:

```yaml
${{ github.workflow }}        # Workflow name
${{ github.run_id }}          # Unique run ID
${{ github.run_number }}      # Sequential run number
${{ github.sha }}             # Commit SHA
${{ github.ref }}             # Branch/tag ref
${{ github.actor }}           # Who triggered it
${{ github.event_name }}      # What triggered it (push, pull_request, etc)
${{ job.status }}             # success, failure, cancelled
${{ steps.stepid.outputs.x }} # Step outputs
```

---

## Debugging Workflows

### View in GitHub UI
```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

### Download Artifacts
```bash
# Download all artifacts
gh run download <run-id>

# Download specific artifact
gh run download <run-id> --name metrics-execute
```

### Check Metrics Locally
```bash
# After download
cat .metrics/metrics-*.json
cat .metrics/summary-*.md
```

---

## Performance Considerations

### Cache Hit Rate
High cache hit rate = fast workflows

```yaml
- uses: ./.github/actions/cadence/phase-prepare
  with:
    cache-key: ${{ runner.os }}-${{ hashFiles('**/lock-file') }}
```

### Parallel Execution
Use matrix for parallelism:

```yaml
strategy:
  matrix:
    test-suite: [unit, integration, e2e]
```

### Resource Management
Monitor metrics for bottlenecks:

```bash
# Check phase durations
cat .metrics/phase-*-metrics.json | jq '.duration_seconds'
```

---

## Common Patterns

### Pattern 1: Conditional Execution
```yaml
- name: Deploy
  if: github.ref == 'refs/heads/main'
  uses: ./.github/actions/cadence/phase-execute
```

### Pattern 2: Failure Recovery
```yaml
- name: Execute
  id: execute
  continue-on-error: true
  
- name: Handle Failure
  if: steps.execute.outcome == 'failure'
  uses: ./.github/actions/survival/graceful-fail
```

### Pattern 3: Environment-Specific Config
```yaml
- name: Execute
  uses: ./.github/actions/cadence/phase-execute
  with:
    command: ${{ github.ref == 'refs/heads/main' && 'npm run build:prod' || 'npm run build:dev' }}
```

---

## Further Reading

- [_template.yml](../../.github/workflows/_template.yml) - The canonical workflow
- [ci.yml](../../.github/workflows/ci.yml) - CI example
- [PATTERNS.md](../architecture/PATTERNS.md) - Pattern catalog
- [CONTRIBUTING.md](./CONTRIBUTING.md) - How to modify workflows
