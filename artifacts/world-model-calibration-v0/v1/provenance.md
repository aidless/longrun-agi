# Provenance: world-model-calibration-v0 v1

## Scope

CPU-only symbolic calibration and planning probe. It is not a neural world
model and not a real environment result.

## Commands

```bash
cd <repository-root>
make world-model-calibration
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 scripts/verify_artifact.py artifacts/world-model-calibration-v0/v1
```

## Observations

- ID accuracy `1.000`, OOD accuracy `0.250`.
- ID uncertainty `0.5373`, OOD uncertainty `1.0000`.
- OOD error AUROC `0.5000`.
- Counterfactual error `0.0` ID, `1.6667` OOD.
- Rollout drift `0.5` both ID and OOD.
- Planning success `0.5` for both argmax and uncertainty-penalized planners.

## Limits

The probe demonstrates that high uncertainty can indicate unseen states, but
not that uncertainty ranks errors or improves planning. No neural or GPU
experiment was run.
