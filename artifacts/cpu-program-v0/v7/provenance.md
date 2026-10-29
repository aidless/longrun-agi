# Provenance: cpu-program-v0 v7

## Scope

CPU-only integrated validation after adding the symbolic calibrated-world-model
probe to P4. This is not a neural or real-environment world-model result.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make world-model-calibration
make program
make verify
```

## Checks

- Unit tests: `116 passed`
- Fixed-seed repeated program output: canonical equal
- P4: ID accuracy `1.0`, OOD accuracy `0.25`
- P4: ID uncertainty `0.5373`, OOD uncertainty `1.0`
- P4: OOD error AUROC `0.5`
- P4: planning success `0.5` for both planners
- Raw output SHA-256:
  `6920882cdde80e6fe5e39ccdfa586feb3e8247ee44f642c9f083ff84b15fe7f4`
- Canonical output SHA-256:
  `cd5345be8d557ee2dd3ef323d3475fb4f6f4946b38810d849f6bf38bc8a391c2`

## Limit

The probe demonstrates uncertainty on unseen states, but not useful OOD error
ranking or planning improvement.
