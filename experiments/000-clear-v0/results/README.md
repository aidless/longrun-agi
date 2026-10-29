# Experiment 000 Results

These are CPU-only harness-validation results.

| Check | Result |
| --- | --- |
| Unit tests | 11 passed |
| CLEAR task count | 36 |
| Reactive policy, shifted variants | 1.000 success |
| Sticky policy, shifted variants | 0.000 success |
| Transient fault recovery | 2/2 |
| Recency-only memory poison rate | 1.000 |
| Provenance-aware memory poison rate | 0.000 |
| Evidence Gate expectations | 7/7 matched |

The perfect contrast is expected because the two policies are deliberately
scripted. It shows that the harness detects stale-rule behavior; it does not
show that an LLM will behave the same way.
