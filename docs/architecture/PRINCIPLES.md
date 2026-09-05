# Principles

The 10 laws that govern this system.

---

## 1. Explicit Over Implicit

Every phase is named. Every dependency is declared. Every metric is defined.

**Bad:**
```yaml
steps:
  - run: do_stuff.sh
```

**Good:**
```yaml
steps:
  - name: Phase 3 - Execute
    uses: ./.github/actions/cadence/phase-execute
    with:
      command: do_stuff.sh
```

**Why:** Implicit behavior requires archaeology. Explicit behavior is self-documenting.

---

## 2. Composable Over Monolithic

Build small, focused actions that combine into workflows. Not large, do-everything scripts.

**Bad:**
```bash
# mega_deploy.sh (500 lines)
# Does everything
```

**Good:**
```yaml
- uses: ./.github/actions/cadence/phase-init
- uses: ./.github/actions/cadence/phase-prepare
- uses: ./.github/actions/cadence/phase-execute
```

**Why:** Composable systems can be recombined. Monoliths must be rewritten.

---

## 3. Observable Over Silent

Every action reports what it's doing and what it found.

**Bad:**
```bash
check_resources.sh  # Silently succeeds or fails
```

**Good:**
```yaml
uses: ./.github/actions/survival/resource-check
# Outputs: disk-available, memory-available, status
# Logs: "Disk available: 45GB (minimum: 5GB)"
```

**Why:** Invisible state is undebuggable state.

---

## 4. Graceful Over Brittle

When something fails, clean up and explain. Don't just exit 1.

**Bad:**
```bash
./deploy.sh || exit 1
```

**Good:**
```yaml
- name: Deploy
  id: deploy
  run: ./deploy.sh
  
- name: Handle failure
  if: failure()
  uses: ./.github/actions/survival/graceful-fail
  with:
    phase: deploy
    error-message: ${{ steps.deploy.outputs.error }}
```

**Why:** Brittle systems amplify failures. Graceful systems contain them.

---

## 5. Data Over Code

Configuration should be data that code interprets, not code that configures.

**Bad:**
```python
PHASES = ["init", "prepare", "execute"]  # Hard-coded
```

**Good:**
```yaml
# manifests/phases.yml
phases:
  - name: init
    order: 1
  - name: prepare
    order: 2
```

**Why:** Data can be validated, queried, and transformed. Code just runs.

---

## 6. Substrate-Agnostic Over Substrate-Specific

Write once, run anywhere. Not "write for GitHub Actions, rewrite for Docker."

**Bad:**
```yaml
- run: |
    echo "::set-output name=result::$VALUE"  # GitHub Actions specific
```

**Good:**
```bash
# Core script works everywhere
echo "$VALUE" > $OUTPUT_FILE
```

**Why:** Substrate-specific code has infinite rewrite cost.

---

## 7. Measured Over Assumed

Don't assume resources exist. Measure them. Don't assume commands succeed. Verify them.

**Bad:**
```bash
npm install  # Assumes disk space, network, etc.
```

**Good:**
```yaml
- uses: ./.github/actions/survival/resource-check
- run: npm install
```

**Why:** Assumptions fail silently. Measurements fail loudly.

---

## 8. Consistent Over Clever

The same pattern in every workflow is better than a clever pattern in one.

**Bad:**
```yaml
# workflow-1.yml uses custom pattern
# workflow-2.yml uses different custom pattern
```

**Good:**
```yaml
# All workflows follow _template.yml pattern
```

**Why:** Consistency is learnable. Cleverness requires the original author.

---

## 9. Failure Recovery Over Failure Prevention

You can't prevent all failures. You can prepare for all failures.

**Bad:**
```bash
# Assume nothing ever fails
deploy.sh
```

**Good:**
```yaml
- name: Deploy
  id: deploy
  run: deploy.sh
  
- name: Rollback on failure
  if: failure()
  run: rollback.sh
  
- name: Report failure
  if: failure()
  uses: ./.github/actions/observability/failure-report
```

**Why:** Failure is inevitable. Recovery is optional.

---

## 10. Teaching Over Documenting

The system should teach how it works through its structure, not through separate documentation.

**Bad:**
```
# docs/how-to-add-phase.md (25 pages)
```

**Good:**
```
# Look at existing phase-* actions
# Copy the pattern
# It works
```

**Why:** Documentation rots. Structure doesn't.

---

## How To Apply These Principles

### When adding a new workflow:
1. Start from `_template.yml`
2. Follow the phase pattern
3. Use composite actions
4. Report metrics
5. Handle cleanup

### When adding a new action:
1. Make it composable (inputs/outputs)
2. Make it observable (logs/metrics)
3. Make it substrate-agnostic (core scripts)
4. Make it consistent (same pattern as others)

### When debugging:
1. Check metrics (what was measured?)
2. Check logs (what was reported?)
3. Check manifests (what was expected?)
4. Check patterns (is this consistent?)

---

## Anti-Patterns to Avoid

❌ **Hidden dependencies** - Action depends on something not in inputs

❌ **Silent failures** - Failure with no explanation

❌ **Substrate coupling** - Only works in one environment

❌ **Inconsistent naming** - phase-init vs init_phase vs initPhase

❌ **Monolithic scripts** - One script does everything

❌ **Implicit ordering** - Step B depends on A but not declared

❌ **Magic values** - Hard-coded thresholds instead of manifests

❌ **No metrics** - Action runs but reports nothing

---

## Principle Conflicts

Sometimes principles conflict. Here's how to resolve:

### Observable vs. Performance
**Choose:** Observable. Slow and visible beats fast and invisible.

### Composable vs. Simple
**Choose:** Composable. Simple monoliths become complex monoliths.

### Consistent vs. Optimal
**Choose:** Consistent. The cost of inconsistency exceeds the benefit of optimization.

---

## Further Reading

- [PHILOSOPHY.md](./PHILOSOPHY.md) - Why these principles exist
- [PATTERNS.md](./PATTERNS.md) - How principles manifest as patterns
- [CONTRIBUTING.md](../onboarding/CONTRIBUTING.md) - Applying principles when contributing
