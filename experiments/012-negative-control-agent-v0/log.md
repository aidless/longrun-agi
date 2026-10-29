# Experiment 012 Log

## 2026-10-28: Negative-control research agent probe

Generated 80 synthetic research cases and compared a naive claim rule with the
Evidence Gate. The gated policy reduced false discoveries from `60` to `10`.
The remaining ten are the deliberate confounding blind spot.

Commands:

```bash
cd <repository-root>
make research-agent
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
```

Observed:

| policy | claims | true discoveries | false discoveries | false discovery rate |
| --- | ---: | ---: | ---: | ---: |
| naive | 70 | 10 | 60 | 0.8571 |
| gated | 20 | 10 | 10 | 0.5000 |

The valid-discovery rate is `1.0` for both policies. The gate does not detect
confounding, by design in this v0.

Raw output SHA-256:
`e97852ed4bbb226e47d3970962528fcd41fdd160d785bbb2857aa0ef4960825a`.
Canonical SHA-256 after removing `generated_at`:
`5ca82bbea3e8e8b15abec3bc0ebb40ffab71a2a69eaed9d1dcd09a5f08fb25c8`.

This is a synthetic case suite, not a live research agent or external
benchmark.
