# Routing measurement (September 17, 2026)

## Controlled routing execution

The regression test uses simulated provider responses to exercise the real
ResearchAgent orchestration and paired-report accounting. These figures count
model calls, not Tavily retrieval calls, latency, dollars, or factual accuracy.

| Initial assessment | Dynamic model calls | Always-Kimi baseline calls | Dynamic Kimi calls | Baseline Kimi calls |
| --- | ---: | ---: | ---: | ---: |
| Supported | 2 | 4 | 0 | 1 |
| Partial, with correction | 4 | 4 | 0 | 1 |
| Unsupported, with correction | 4 | 4 | 1 | 1 |

The supported path eliminates two model calls (50%) against this baseline.
The partial path replaces Kimi with GLM repair; its total call count is unchanged.
The serious-dispute path retains Kimi. Revised answers get a final Nemotron check
in both routes; unchanged answers reuse the initial check.

Reproduce: `python3 -m unittest tests.test_benchmark_routing -v`.
See `tests/test_final_verification.py` for final-answer, failure, and presentation checks.

## Live paired benchmark

The script shares the live evidence packet, GLM draft and initial Nemotron check
within each pair. It alternates dynamic-first and baseline-first execution.
Its baseline always calls Kimi and then verifies the result. The report includes
provider-reported token usage by model, elapsed latency and final evidence status.
There are three questions, each run once per route: this is an exploratory sample.

Initial run: https://github.com/QueenFi703/Dredge-echo-agent/actions/runs/35266878730

All three cases hit APITimeoutError before any paired comparison completed.
Therefore that run establishes **no live latency, token, cost or accuracy benefit**.
The artifact is retained by GitHub Actions. The diagnostic retry records the exact
stage and exception class, and stops repeated shared-stage failures.

No dollar-savings or production-speedup claim should be inferred from call counts.

Diagnostic retry: https://github.com/QueenFi703/Dredge-echo-agent/actions/runs/35267903216

The retry completed retrieval, then GLM synthesis hit a ReadTimeout after
120,715 ms. It stopped at that shared stage with zero complete pairs. Neither
run reached a live final-answer verification assessment. Local regression checks
and the CI unit/integration jobs pass; live final verification remains unverified.

## Workflow interpretation

Routing correctness and live-provider availability are now reported separately.
The deterministic routing suite is a required CI gate. The live workflow caps each
model response at 512 tokens, disables retries, and applies a 60-second request
timeout. It always writes `comparison_status: COMPLETE|INCOMPLETE` when the process
can produce an artifact. An incomplete provider run remains visible in the job
summary and artifact but no longer mislabels tested routing code as broken.
