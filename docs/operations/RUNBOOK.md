# Runbook

Operational procedures for living inside this system.

---

## When Workflows Fail

### Symptom: Workflow fails at phase-init

**Diagnosis:**
1. Check the failure report artifact
2. Look for resource warnings in step summary
3. Review trace context ID in logs

**Common Causes:**
- Insufficient disk space
- Insufficient memory
- Missing required commands

**Resolution:**
```bash
# Check latest workflow run
gh run view --log-failed

# Look for resource metrics in artifacts
gh run download <run-id> --name metrics-init

# Review system state
cat .metrics/metrics-init-*.json
```

**Prevention:**
- Adjust thresholds in `manifests/thresholds.yml` if false positives
- Clean up old caches before running
- Use `strict-health-check: 'false'` for non-critical workflows

---

## When Disk Space Is Low

### Symptom: "No space left on device" or resource-check warning

**Diagnosis:**
1. Check `.metrics/resource-history.json`
2. Review cache sizes
3. Check artifact retention policies

**Immediate Resolution:**
```bash
# Manually trigger cleanup
gh workflow run .github/workflows/cleanup.yml  # If exists

# Or run cleanup action locally
bash scripts/adapters/local-adapter.sh cleanup-disk --aggressive true
```

**Long-term Resolution:**
1. Adjust cache pruning in `manifests/cleanup-policies.yml`:
   ```yaml
   cache_pruning:
     triggers:
       - condition: "disk_space < 15gb"  # Increase threshold
   ```

2. Review large artifacts:
   ```bash
   gh api repos/:owner/:repo/actions/artifacts --jq '.artifacts[] | select(.size_in_bytes > 100000000)'
   ```

3. Reduce artifact retention:
   ```yaml
   manifests/cleanup-policies.yml:
   artifact_retention:
     default_retention: 30d  # Reduce from 90d
   ```

**Prevention:**
- The system auto-prunes at 10GB
- Metrics warn at 15GB
- Set up alerts for disk warnings

---

## When Tests Fail

### Symptom: phase-execute fails with test failures

**Diagnosis:**
1. Check test report artifact
2. Review execution metrics
3. Look at failure summary

**Resolution:**
```bash
# Get test output
gh run view <run-id> --log-failed

# Download test artifacts
gh run download <run-id> --name metrics-execute

# Review specific test failures
cat .metrics/summary-execute.md
```

**Common Patterns:**
- **Flaky tests:** Shows in metrics as intermittent failures
  - Solution: Review test stability metrics, add retries
  
- **Environment issues:** Resource constraints
  - Solution: Check resource metrics before test execution
  
- **Dependency conflicts:** New dependencies break tests
  - Solution: Review prepare phase output, check cache hit

---

## When Deployments Fail

### Symptom: deploy workflow fails at phase-execute

**Diagnosis:**
1. Check deployment status
2. Review failure report
3. Verify health check

**Resolution:**
```bash
# View deployment logs
gh run view <run-id> --log

# Check health status
cat .metrics/trace-context.json

# Review rollback status (if auto-rollback enabled)
gh run list --workflow=deploy --limit 5
```

**Rollback Procedure:**
```yaml
# If auto-rollback not enabled, manually trigger:
- name: Manual Rollback
  run: |
    # Your rollback command
    ./scripts/rollback.sh
```

**Prevention:**
- Use `strict-health-check: 'true'` for deploy workflows
- Implement smoke tests after deployment
- Set up monitoring for deployed services

---

## When Cache Is Corrupted

### Symptom: Build failures after cache restore, unexpected dependency versions

**Diagnosis:**
```bash
# Check cache hit metrics
gh run view <run-id> --log | grep "cache-hit"

# Review prepare phase
cat .metrics/summary-prepare.md
```

**Resolution:**
1. Clear cache manually:
   ```bash
   gh cache list
   gh cache delete <cache-key>
   ```

2. Or trigger cache cleanup:
   ```bash
   # Use prune-cache action
   bash scripts/adapters/local-adapter.sh prune-cache --max-age-days 0
   ```

3. Re-run workflow (will rebuild cache)

**Prevention:**
- Use specific cache keys: `${{ runner.os }}-${{ hashFiles('**/lock-file') }}`
- Set cache size limits in `manifests/cleanup-policies.yml`
- Monitor cache hit rates

---

## When Cleanup Fails

### Symptom: phase-cleanup reports failures, resources still elevated

**Diagnosis:**
```bash
# Check cleanup metrics
cat .metrics/summary-cleanup.md

# Review resource state
cat .metrics/metrics-cleanup-*.json
```

**Resolution:**
1. Run aggressive cleanup:
   ```yaml
   - uses: ./.github/actions/cadence/phase-cleanup
     with:
       aggressive: 'true'
   ```

2. Or manually clean:
   ```bash
   # Remove temp files
   find . -name "*.tmp" -delete
   find . -name "*.log" -delete
   
   # Clear caches
   rm -rf node_modules/.cache
   rm -rf .cache
   ```

**Prevention:**
- Always use `if: always()` for cleanup
- Set `aggressive: 'true'` for long-running workflows
- Monitor cleanup success rate

---

## When Metrics Aren't Being Collected

### Symptom: No metrics artifacts, missing summaries

**Diagnosis:**
1. Check if metrics-collect action is included
2. Verify .metrics directory creation
3. Review action outputs

**Resolution:**
```yaml
# Ensure metrics collection in workflow:
- name: Collect metrics
  uses: ./.github/actions/observability/metrics-collect
  with:
    phase: <current-phase>
```

**Common Issues:**
- `.metrics` directory not created → Create in init phase
- Metrics action not called → Add to each phase
- Artifacts not uploaded → Check retention settings

---

## When Workflows Are Slow

### Symptom: Workflows take longer than expected

**Diagnosis:**
```bash
# Check timing metrics
gh run view <run-id> --log | grep "Duration"

# Review phase durations
cat .metrics/phase-*-metrics.json | jq '.duration_seconds'
```

**Optimization Strategies:**

1. **Cache hit rate:**
   ```bash
   # Check cache effectiveness
   cat .metrics/summary-prepare.md | grep "Cache Hit"
   ```
   - Low hit rate → Review cache keys
   - No cache → Implement caching

2. **Parallel execution:**
   ```yaml
   # Use matrix for parallel tests
   strategy:
     matrix:
       test-suite: [unit, integration, e2e]
   ```

3. **Resource constraints:**
   ```bash
   # Check resource metrics during execution
   cat .metrics/metrics-execute-*.json
   ```
   - High CPU → Reduce parallelism
   - Low memory → Reduce batch sizes

4. **Dependency installation:**
   - Use cache for dependencies
   - Consider pre-built Docker images

---

## When Alerts Fire

### Disk Space Warning
```
Alert: Disk space below threshold (15GB available)
```
**Action:**
1. Check current usage: Review latest metrics
2. Trigger cleanup: Run cleanup workflow
3. Adjust threshold if false positive

### Memory Warning
```
Alert: Memory below threshold (1000MB available)
```
**Action:**
1. Check running processes
2. Reduce parallel jobs
3. Review memory-intensive operations

### Test Failure Threshold
```
Alert: Test failures exceed threshold (5 failures)
```
**Action:**
1. Block merges until resolved
2. Review failure patterns
3. Identify root cause (flaky vs. real)

---

## Emergency Procedures

### Workflow Stuck
```bash
# Cancel workflow
gh run cancel <run-id>

# Check for hung processes
gh run view <run-id> --log
```

### System Unresponsive
```bash
# Check system state
gh api repos/:owner/:repo/actions/runs?status=in_progress

# Cancel all running workflows (use with caution)
gh run list --status in_progress --json databaseId --jq '.[].databaseId' | xargs -I {} gh run cancel {}
```

### Critical Resource Exhaustion
```bash
# Emergency cleanup
bash scripts/core/cleanup-emergency.sh

# Or manually
rm -rf .cache/* node_modules/.cache .pytest_cache
```

---

## Health Checks

### Daily
- [ ] Review workflow success rates
- [ ] Check resource trends
- [ ] Monitor cache hit rates

### Weekly
- [ ] Review failure reports
- [ ] Analyze slow workflows
- [ ] Update thresholds if needed

### Monthly
- [ ] Audit cache sizes
- [ ] Review artifact retention
- [ ] Update documentation

---

## Getting Help

### Check Documentation
1. [DEBUGGING.md](./DEBUGGING.md) - Debugging techniques
2. [METRICS.md](./METRICS.md) - Understanding metrics
3. [RECOVERY.md](./RECOVERY.md) - Recovery procedures

### Review System State
```bash
# Latest workflow status
gh run list --limit 10

# System health
bash scripts/core/health-check.sh

# Resource state
bash scripts/core/metric-collector.sh --type resource
```

### Create Issue
If problem persists:
1. Gather metrics and logs
2. Create issue with template
3. Include trace context ID
4. Attach failure reports

---

## Further Reading

- [DEBUGGING.md](./DEBUGGING.md) - How to debug failures
- [METRICS.md](./METRICS.md) - What metrics mean
- [RECOVERY.md](./RECOVERY.md) - Recovery strategies
