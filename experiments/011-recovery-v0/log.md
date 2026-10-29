# Experiment 011 Log

## 2026-10-28: Recovery matrix CPU probe

Implemented a deterministic four-fault recovery state machine and four
controllers. The full matrix contains 40 task instances per controller.

Commands:

```bash
cd <repository-root>
make recovery-matrix
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
```

Observed:

| controller | success | mean steps | human interventions |
| --- | ---: | ---: | ---: |
| retry-only | 0.25 | 3.75 | 0 |
| rollback | 0.25 | 4.75 | 0 |
| replan | 1.00 | 4.00 | 0 |
| state-check-replan | 1.00 | 4.50 | 0 |

Retry-only and rollback recover only the transient tool-error case. Replanning
is required for stale state, misleading documentation, and rule changes.

Raw output SHA-256:
`37fd761c4ac01fbfc1966711aee09f953f463b2784be95bda3017c042c55080b`.
Canonical SHA-256 after removing `generated_at`:
`2e58cc8c087f310782aeda5f274662417930607d61da533a4438dd5a5321e9b1`.
A repeat run produced the same canonical output.

This is a synthetic state-machine probe, not OSWorld, WebArena, or TAU-bench.
