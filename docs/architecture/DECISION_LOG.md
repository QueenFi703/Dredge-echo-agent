# Decision Log

A record of significant architectural decisions and their rationale.

---

## Format

Each entry follows this structure:
- **Date:** When the decision was made
- **Decision:** What was decided
- **Context:** Why it mattered
- **Rationale:** Why this choice
- **Alternatives:** What else was considered
- **Consequences:** What this enables/prevents

---

## [2026-01-26] Use Composite Actions Instead of Reusable Workflows

**Decision:** Build the cadence system using composite actions, not reusable workflows.

**Context:** GitHub Actions offers two reusability mechanisms:
- Reusable workflows (workflow that calls workflow)
- Composite actions (steps that bundle steps)

**Rationale:**
- Composite actions are more granular (step-level vs job-level)
- Better composability (can mix multiple actions in one job)
- Clearer dependency chains
- Easier to test in isolation

**Alternatives Considered:**
- Reusable workflows: Too coarse-grained
- Bash scripts only: Not GitHub-native, loses platform features
- Monolithic workflows: Not composable

**Consequences:**
✅ Can compose multiple actions in one job
✅ Clear inputs/outputs at step level
✅ Better caching and parallelization
❌ Slightly more verbose than reusable workflows

---

## [2026-01-26] Manifests in YAML, Not JSON or Code

**Decision:** Store configuration in YAML files under `manifests/`, not JSON or hard-coded in scripts.

**Context:** Configuration needs to be:
- Human-readable
- Version-controlled
- Validatable
- Queryable

**Rationale:**
- YAML is more readable than JSON (comments, no quotes)
- More human-friendly than JSON for manual editing
- Standard in GitHub Actions ecosystem
- Easy to parse in any language

**Alternatives Considered:**
- JSON: Less readable, no comments
- TOML: Less familiar in Actions ecosystem
- Hard-coded: Not data-driven
- Python config files: Requires Python to read

**Consequences:**
✅ Easy to edit manually
✅ Can add comments
✅ Standard tooling available
❌ Less strict than JSON (indentation matters)

---

## [2026-01-26] Three-Layer Architecture (Teaching/Behavior/Reality)

**Decision:** Organize actions into three conceptual layers instead of a flat structure.

**Context:** Actions serve different purposes:
- Some handle resources (survival)
- Some collect metrics (observability)
- Some provide workflow structure (cadence)

**Rationale:**
- Clear separation of concerns
- Easier to understand system at a glance
- Natural grouping for documentation
- Matches how systems actually work

**Alternatives Considered:**
- Flat structure: Harder to navigate
- Feature-based grouping: Less clear principles
- MVC-style: Doesn't map well to infrastructure

**Consequences:**
✅ Clear mental model
✅ Easy to find actions
✅ Teachable structure
❌ Slightly longer paths

---

## [2026-01-26] Substrate-Agnostic Core Scripts

**Decision:** Core logic in bash scripts, adapters for each substrate.

**Context:** Need to run the same behavior in:
- GitHub Actions
- Docker containers
- Local machines
- CI runners
- Various cloud platforms

**Rationale:**
- Bash is universally available
- Adapters translate environment specifics
- Core logic tested once, runs everywhere
- Reduces platform lock-in

**Alternatives Considered:**
- GitHub Actions specific: Platform lock-in
- Python scripts: Requires Python installed
- Go binaries: Requires compilation
- Node.js: Requires Node runtime

**Consequences:**
✅ Runs anywhere with bash
✅ No external dependencies
✅ Easy to test locally
❌ Bash limitations (error handling, types)

---

## [2026-01-26] Always-Run Cleanup with `if: always()`

**Decision:** Use `if: always()` for cleanup and reporting steps.

**Context:** Resources need management even when workflows fail. Metrics need collection even when tests fail.

**Rationale:**
- Prevents resource leaks on failure
- Ensures metrics are always collected
- Provides visibility into failure modes
- Standard GitHub Actions pattern

**Alternatives Considered:**
- Try/catch pattern: Not available in YAML
- Bash traps: Only works within scripts
- Manual cleanup: Unreliable

**Consequences:**
✅ Resources always cleaned
✅ Metrics always collected
✅ State always reported
❌ Cleanup runs even on canceled workflows (can be expensive)

---

## [2026-01-26] Phase-Ordered Execution Pattern

**Decision:** Every workflow follows the same 6-phase pattern: Init → Prepare → Execute → Report → Cleanup → Seal.

**Context:** Workflows were ad-hoc, each with different structure. Hard to understand, hard to debug, hard to teach.

**Rationale:**
- Consistency enables learning
- Same pattern = same mental model
- Clear expectations at each phase
- Fractal property (pattern repeats at every level)

**Alternatives Considered:**
- Ad-hoc structure: Not teachable
- 3-phase (setup/run/teardown): Too coarse
- 10+ phases: Too fine-grained

**Consequences:**
✅ Predictable workflow structure
✅ Easy to onboard new contributors
✅ Clear where to add new functionality
❌ Slightly more verbose for simple workflows

---

## [2026-01-26] JSON for Metrics, Markdown for Summaries

**Decision:** Metrics as JSON, summaries as Markdown.

**Context:** Need both machine-readable and human-readable outputs.

**Rationale:**
- JSON for programmatic access (tooling, dashboards)
- Markdown for human reading (GitHub summaries)
- Both are text, both are versionable
- Standard in GitHub Actions (step summaries)

**Alternatives Considered:**
- Only JSON: Not human-friendly
- Only Markdown: Not machine-parseable
- XML: Too verbose
- Custom format: Requires custom tooling

**Consequences:**
✅ Machines can process metrics
✅ Humans can read summaries
✅ Both are text-based
❌ Need to maintain both formats

---

## [2026-01-26] Graceful Failure Over Crash-Fast

**Decision:** When failures occur, report context and attempt recovery before failing.

**Context:** Workflows were failing silently or with cryptic errors.

**Rationale:**
- Informative failures waste less time
- Context enables recovery
- Recovery hints reduce MTTR
- Failure reports create learning

**Alternatives Considered:**
- Crash-fast: Provides less context
- Auto-retry everything: Masks real issues
- Silent continuation: Propagates errors

**Consequences:**
✅ Failures are understandable
✅ Faster debugging
✅ Learning from failures
❌ More code for failure handling

---

## [2026-01-26] Artifacts for Metrics and Reports

**Decision:** Upload metrics and reports as artifacts with 30-90 day retention.

**Context:** Need to preserve execution history beyond logs.

**Rationale:**
- Logs expire quickly (typically 90 days, not always kept)
- Artifacts persist longer
- Structured data (JSON) more useful than logs
- Enables trend analysis

**Alternatives Considered:**
- Only logs: Expire too fast
- External storage: Requires infrastructure
- Git commits: Wrong tool, noise
- No persistence: Lose history

**Consequences:**
✅ Metrics history preserved
✅ Trend analysis possible
✅ Failure reports available
❌ Storage cost (minimal)

---

## [2026-01-26] Minimal Default Thresholds, Configurable via Manifests

**Decision:** Set conservative defaults (5GB disk, 500MB memory) but allow override via manifests.

**Context:** Different workflows have different resource needs.

**Rationale:**
- Defaults prevent catastrophic failures
- Configurability allows optimization
- Centralized in manifests, not scattered
- Auditable via git history

**Alternatives Considered:**
- Hard-coded everywhere: Not maintainable
- No defaults: Risk of forgetting
- Per-workflow config: Duplicated
- Environment variables: Not versionable

**Consequences:**
✅ Safe defaults
✅ Flexibility when needed
✅ Centralized configuration
❌ Need to know where to configure

---

## Future Decisions

Track future decisions here as they're made:

### To Decide: Metric Storage Strategy
- **Question:** Where do long-term metrics go?
- **Options:** GitHub API, external DB, S3, no long-term storage
- **Decision Date:** TBD

### To Decide: Multi-Repo Pattern
- **Question:** How do multiple repos share this architecture?
- **Options:** Template repo, git submodules, action marketplace
- **Decision Date:** TBD

---

## Revisiting Decisions

We revisit decisions when:
- New context emerges (new GitHub Actions features)
- Patterns show unexpected weaknesses
- Better alternatives become available
- Team grows and needs change

**Process:**
1. Create issue proposing revision
2. Document new context
3. Evaluate alternatives
4. Update this log
5. Implement change
6. Update docs

---

## Further Reading

- [PHILOSOPHY.md](./PHILOSOPHY.md) - Principles behind decisions
- [PRINCIPLES.md](./PRINCIPLES.md) - Laws that guide decisions
- [PATTERNS.md](./PATTERNS.md) - Structures that emerged from decisions
