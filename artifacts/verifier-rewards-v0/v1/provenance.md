# Provenance: verifier-rewards-v0 v1

## Scope

CPU-only tabular reward-protocol probe. It is not a model or GPU experiment.

## Commands

```bash
cd <repository-root>
make verifier-rewards
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 scripts/verify_artifact.py artifacts/verifier-rewards-v0/v1
```

## Observations

- Answer reward OOD success: `0.4333`.
- Ensemble-disagreement OOD success: `0.5233`.
- Answer transfer drop: `0.3033`.
- Ensemble transfer drop: `0.1933`.
- Mean reasoning cost: answer `1.37`, ensemble `1.38`.
- Reward hacking: answer `0.1731`, ensemble `0.1141`.

## Limits

The verifier signal is synthetic and the learner is a tabular two-action model.
The result supports a protocol check, not a language-model claim.
