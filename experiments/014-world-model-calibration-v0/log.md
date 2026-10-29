# Experiment 014 Log

## 2026-10-28: Calibrated symbolic world model

Built a held-out 4-symbol / 4-action table-world probe with two-model ensemble
uncertainty, calibration, counterfactual consistency, rollout drift, planning,
and sample-efficiency metrics.

Commands:

```bash
cd <repository-root>
make world-model-calibration
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
```

Observed:

- ID accuracy: `1.000`
- OOD accuracy: `0.250`
- ID mean uncertainty: `0.5373`
- OOD mean uncertainty: `1.0000`
- OOD error AUROC: `0.5000`
- ID ECE: `0.1823`
- OOD ECE: `0.0000`
- counterfactual error: ID `0.0`, OOD `1.6667`
- rollout drift: ID `0.5`, OOD `0.5`
- planning success: argmax `0.5`, uncertainty-penalized `0.5`

Uncertainty separated ID from OOD state coverage, but it did not rank OOD errors
or improve planning in this construction. The negative result is preserved.

Raw output SHA-256:
`b9467660668f27806f67beb1e40c6c43b820dfdc48ba1d59dbb3aded6864c448`.
Canonical SHA-256 after removing `generated_at`:
`6603a71866e3280cf33b03c7395a1c85f0b89e3ababf9db55a5b56eb8f4944ce`.
