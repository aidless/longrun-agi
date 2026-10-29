# Provenance: adaptive-controller-v0 v1

## Scope

CPU-only tabular contextual-bandit probe on CLEAR-300-v1 metadata. It is not a
runtime model controller.

## Commands

```bash
cd <repository-root>
make adaptive-controller
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 scripts/verify_artifact.py artifacts/adaptive-controller-v0/v1
```

## Results

- Adaptive success: `0.4833`
- Mean cost: `1.7333`
- Cost per success: `3.5862`
- Five-block stability range: `0.0417`
- Action mix: retrieve `56`, reflect `16`, tool `40`, stop `8`,
  write-memory `0`

## Limit

The adaptive controller is not superior to fixed reflect (`0.592` success) in
the probe and never writes memory. The result is retained as weak/negative
evidence about the current controller.
