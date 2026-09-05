# Contributing

How to extend the system without breaking coherence.

---

## Before You Contribute

### Read These First
1. [PHILOSOPHY.md](../architecture/PHILOSOPHY.md) - Understand the why
2. [PRINCIPLES.md](../architecture/PRINCIPLES.md) - Learn the rules
3. [PATTERNS.md](../architecture/PATTERNS.md) - See the structures
4. [MENTAL_MODEL.md](./MENTAL_MODEL.md) - Get the mental model

**You don't need to memorize them.** Just read them once. The patterns will make sense as you work.

---

## The Golden Rules

### Rule 1: Follow Existing Patterns

Don't invent new patterns. Use what exists.

❌ **Bad:**
```yaml
- name: My Custom Init Step
  run: |
    # 50 lines of custom logic
```

✅ **Good:**
```yaml
- name: Initialize
  uses: ./.github/actions/cadence/phase-init
  with:
    context: my-workflow
```

### Rule 2: Make It Composable

Build small pieces that combine, not large pieces that stand alone.

❌ **Bad:**
```yaml
# action.yml that does everything
- run: setup && build && test && deploy && cleanup
```

✅ **Good:**
```yaml
- uses: ./.github/actions/cadence/phase-prepare
- uses: ./.github/actions/cadence/phase-execute
- uses: ./.github/actions/cadence/phase-cleanup
```

### Rule 3: Make It Observable

Always report what you're doing and what you found.

❌ **Bad:**
```bash
check_disk.sh  # Silent
```

✅ **Good:**
```bash
check_disk.sh  # Outputs: "Disk: 45GB available (minimum: 5GB)"
```

### Rule 4: Follow the Layer System

Put things in the right layer:
- **Reality** (survival/) - Resource checks, cleanup
- **Behavior** (cadence/) - Workflow patterns
- **Teaching** (observability/) - Metrics, reports

---

## How To Add...

### A New Workflow

1. **Start from the template:**
   ```bash
   cp .github/workflows/_template.yml .github/workflows/my-workflow.yml
   ```

2. **Customize the context and command:**
   ```yaml
   inputs:
     context: my-workflow
     command: my-command.sh
   ```

3. **Keep the phase structure:**
   - Don't skip phases
   - Don't reorder phases
   - Add steps within phases if needed

4. **Test it:**
   ```bash
   gh workflow run my-workflow.yml
   ```

**Example:**
```yaml
name: My New Workflow

on: [push]

jobs:
  execute:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Phase 1: Init
      - uses: ./.github/actions/cadence/phase-init
        with:
          context: my-workflow
      
      # Phase 2: Prepare
      - uses: ./.github/actions/cadence/phase-prepare
        with:
          language: python
      
      # Phase 3: Execute
      - uses: ./.github/actions/cadence/phase-execute
        with:
          command: python my_script.py
      
      # Phase 4: Report
      - uses: ./.github/actions/cadence/phase-report
        if: always()
      
      # Phase 5: Cleanup
      - uses: ./.github/actions/cadence/phase-cleanup
        if: always()
```

---

### A New Action

1. **Choose the right layer:**
   - Survival (handles resources/failure)
   - Cadence (workflow structure)
   - Observability (metrics/reports)

2. **Look at a similar action:**
   ```bash
   # For survival action:
   cat .github/actions/survival/resource-check/action.yml
   
   # For observability action:
   cat .github/actions/observability/metrics-collect/action.yml
   ```

3. **Follow the pattern:**
   ```yaml
   name: 'My Action'
   description: 'What it does'
   
   inputs:
     # What you need
     
   outputs:
     # What you produce
     
   runs:
     using: 'composite'
     steps:
       - name: Validate inputs
       - name: Do work
       - name: Report results
   ```

4. **Make it observable:**
   ```yaml
   - name: Report
     shell: bash
     run: |
       echo "Action completed: <summary>"
       echo "key=value" >> $GITHUB_OUTPUT
   ```

5. **Test it:**
   ```yaml
   # In a test workflow
   - uses: ./.github/actions/my-layer/my-action
     with:
       input: value
   ```

**Example:**
```yaml
name: 'Check Dependencies'
description: 'Verifies all dependencies are available'

inputs:
  package-manager:
    description: 'Package manager (npm, pip, etc)'
    required: true

outputs:
  status:
    description: 'ok, warning, critical'
    value: ${{ steps.check.outputs.status }}

runs:
  using: 'composite'
  steps:
    - name: Check dependencies
      id: check
      shell: bash
      run: |
        echo "Checking dependencies with ${{ inputs.package-manager }}"
        
        case "${{ inputs.package-manager }}" in
          npm)
            npm list 2>&1 || echo "status=warning" >> $GITHUB_OUTPUT
            ;;
          pip)
            pip check 2>&1 || echo "status=warning" >> $GITHUB_OUTPUT
            ;;
        esac
        
        echo "status=ok" >> $GITHUB_OUTPUT
```

---

### A New Script

1. **Put it in the right place:**
   - Core behavior → `scripts/core/`
   - Adapter → `scripts/adapters/`

2. **Follow the script pattern:**
   ```bash
   #!/bin/bash
   set -euo pipefail
   
   # Parse arguments
   
   # Validate prerequisites
   
   # Do work
   
   # Report results
   
   # Exit with code
   ```

3. **Make it reusable:**
   - Accept arguments
   - Don't hard-code paths
   - Output structured data

4. **Make it testable:**
   ```bash
   # Test locally
   bash scripts/core/my-script.sh --test-mode
   ```

**Example:**
```bash
#!/bin/bash
# validate-config.sh - Validates configuration files

set -euo pipefail

CONFIG_FILE="${1:-.config.yml}"

echo "Validating config: $CONFIG_FILE"

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: Config file not found: $CONFIG_FILE"
  exit 1
fi

# Validate YAML syntax
if ! command -v yq &> /dev/null; then
  echo "WARNING: yq not found, skipping validation"
  exit 0
fi

if yq eval '.' "$CONFIG_FILE" > /dev/null 2>&1; then
  echo "Config valid: $CONFIG_FILE"
  exit 0
else
  echo "ERROR: Invalid YAML in $CONFIG_FILE"
  exit 1
fi
```

---

### A New Manifest

1. **Understand what manifests are for:**
   - Configuration (not code)
   - Thresholds
   - Policies
   - Definitions

2. **Use YAML:**
   ```yaml
   # manifests/my-config.yml
   my_setting:
     description: "What this controls"
     value: 42
     unit: "seconds"
   ```

3. **Add documentation:**
   ```yaml
   # What this setting does
   # When to change it
   # What happens if you change it
   setting: value
   ```

4. **Update readers:**
   If you add a new manifest, update scripts that might read it.

---

### Documentation

1. **Update when you change behavior:**
   - Changed a threshold? Update RUNBOOK.md
   - Added a pattern? Update PATTERNS.md
   - Made a decision? Update DECISION_LOG.md

2. **Use the same structure:**
   Look at existing docs for the format.

3. **Explain why, not just what:**
   - What: "This action checks disk"
   - Why: "This action checks disk because workflows fail mysteriously when disk fills"

---

## Testing Your Changes

### Test Actions Locally

```bash
# Many actions can be tested with act
act -j my-job

# Or test the underlying script
bash scripts/core/my-script.sh --test-args
```

### Test Workflows

```bash
# Push to a branch
git push origin my-feature

# Trigger workflow
gh workflow run my-workflow.yml --ref my-feature

# Watch it run
gh run watch
```

### Verify Metrics

```bash
# After workflow completes
gh run view <run-id>

# Download metrics
gh run download <run-id> --name metrics-*

# Check they look right
cat .metrics/*.json
```

---

## Pull Request Checklist

Before submitting:

- [ ] Follows existing patterns
- [ ] Includes inputs/outputs documentation
- [ ] Adds metrics/observability
- [ ] Tests locally (if possible)
- [ ] Updates relevant documentation
- [ ] Follows the layer system
- [ ] Uses manifests for configuration
- [ ] Includes error handling
- [ ] Reports what it does

**PR Template:**
```markdown
## What This Changes

Brief description

## Which Layer

- [ ] Reality (survival)
- [ ] Behavior (cadence)
- [ ] Teaching (observability)
- [ ] Other

## Testing

How you tested this

## Documentation

Which docs you updated
```

---

## Code Review Guidelines

### What Reviewers Look For

✅ **Good signs:**
- Follows existing patterns
- Composable (small, focused)
- Observable (reports state)
- Documented (comments, outputs)
- Tested (evidence of testing)

❌ **Red flags:**
- Invents new patterns
- Does too much in one place
- Silent (no output)
- Hard-coded values
- No error handling

### How to Give Feedback

**Good feedback:**
```
This action is doing a lot. Consider splitting into:
1. Resource check action
2. Validation action
Then compose them in the workflow.
```

**Not helpful:**
```
This is wrong.
```

---

## Common Mistakes

### Mistake 1: Skipping Phases

❌ **Bad:**
```yaml
steps:
  - uses: actions/checkout@v4
  - run: npm test
```

✅ **Good:**
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: ./.github/actions/cadence/phase-init
  - uses: ./.github/actions/cadence/phase-prepare
  - uses: ./.github/actions/cadence/phase-execute
    with:
      command: npm test
```

### Mistake 2: Hard-Coding Configuration

❌ **Bad:**
```bash
if [ $DISK -lt 10 ]; then  # Magic number
```

✅ **Good:**
```bash
MIN_DISK=$(yq eval '.thresholds.disk_space.critical' manifests/thresholds.yml)
if [ $DISK -lt $MIN_DISK ]; then
```

### Mistake 3: Silent Failures

❌ **Bad:**
```bash
command || true  # Silently continue
```

✅ **Good:**
```yaml
- uses: ./.github/actions/survival/graceful-fail
  if: failure()
  with:
    phase: execute
    error-message: Command failed
```

---

## Getting Help

### Before Asking

1. Read existing patterns
2. Check similar implementations
3. Review documentation

### Where to Ask

- **Pattern questions:** Reference PATTERNS.md
- **Conceptual questions:** Reference PHILOSOPHY.md
- **How-to questions:** Reference this document
- **Bug reports:** Create issue

### What to Include

- What you're trying to do
- What you've tried
- What happened vs. what you expected
- Relevant code/workflow snippets

---

## Philosophy of Contributing

We optimize for:
- **Consistency over cleverness**
- **Composability over completeness**
- **Observability over performance**
- **Teaching over documenting**

This means:
- Your change should look like existing code
- Your action should combine with others
- Your code should report what it does
- Your structure should be self-explanatory

**Not:**
- Fastest possible implementation
- Most lines of code saved
- Cleverest solution

**But:**
- Most maintainable solution
- Most teachable solution
- Most coherent solution

---

## Further Reading

- [PATTERNS.md](../architecture/PATTERNS.md) - Patterns to follow
- [PRINCIPLES.md](../architecture/PRINCIPLES.md) - Rules to follow
- [WORKFLOW_ANATOMY.md](./WORKFLOW_ANATOMY.md) - How workflows work
