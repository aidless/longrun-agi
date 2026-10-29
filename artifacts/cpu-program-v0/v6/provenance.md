# Provenance: cpu-program-v0 v6

## Scope

CPU-only integrated validation after adding the synthetic goal-drift monitor to
P6. This is not an activation probe or model capability result.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make goal-drift-monitor
make program
make verify
```

## Checks

- Unit tests: `112 passed`
- Fixed-seed repeated program output: canonical equal
- P6 monitor AUROC: `0.8295`
- P6 early-warning rate: `0.0`
- P6 false-alarm rate: `0.0833`
- P6 baseline/monitored final correct: `0.5556 / 0.5556`
- Raw output SHA-256:
  `f71f693f4a0bdb206a51c5138801cf32893e2e60d5c2baf3b80e336aa19534ad`
- Canonical output SHA-256:
  `b2fb2500d2646aa963aba1914cbd264d78e76e11f1e35bc121fee019f5ff7dcf`

## Limit

The monitor ranks synthetic risk but fails to warn before drift and does not
improve final correctness. This weak/negative result is retained.
