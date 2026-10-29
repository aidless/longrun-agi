# Provenance: goal-drift-monitor-v0 v1

## Scope

CPU-only synthetic trajectory monitor. It is not a model-activation probe.

## Commands

```bash
cd <repository-root>
make goal-drift-monitor
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 scripts/verify_artifact.py artifacts/goal-drift-monitor-v0/v1
```

## Results

- AUROC: `0.8295`
- early-warning rate: `0.0`
- false-alarm rate: `0.0833`
- intervention recovery: `0.36`
- baseline final correct: `0.5556`
- monitored final correct: `0.5556`

## Limitation

The monitor does not produce useful pre-drift warnings and intervention did not
improve final correctness in this synthetic construction. This negative result
is retained and is not promoted to an activation-level claim.
