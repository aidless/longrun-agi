# Provenance: estimator-validity-v0 v1

## Scope

CPU-only validation of the factorial estimator used by LongRun-AGI experiment
003. This is a harness-validation result, not a scientific claim about a
language model, an AGI system, or benchmark novelty.

## Environment

- Date: 2026-10-28
- Platform: Linux 7.0.0-38-generic x86_64
- Python: 3.12.3
- Accelerator: none
- GPU: not used
- Network/API calls: 0
- Runtime dependencies: Python standard library and pytest

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest
python3 -m compileall src tests
make estimator-validity
python3 scripts/verify_artifact.py artifacts/estimator-validity-v0/v1
```

## Configuration

- Seed: `20261027`
- Monte Carlo repetitions: `200`
- Bootstrap replicates per repetition: `299`
- Confidence level: `0.95`
- Multiplicity alpha: `0.05`
- Factors: `A`, `B`, `C`
- Families per repetition: `24`
- Episodes per family and cell: `20`
- Episodes per condition per repetition: `3,840`
- Conditions: global null and alternative with two planted zero interactions
- Interval: percentile nested family/episode cluster bootstrap
- Multiplicity: Holm-Bonferroni FWER and Benjamini-Hochberg FDR

## Checks

- Unit tests: `45 passed`
- Python compile check: passed
- Fixed-seed repeat: canonical outputs equal after removing `generated_at`
- Design balance: all eight cells balanced in both conditions
- Raw output hash: matches `artifact.json`

## Output hashes

| Output | SHA-256 |
| --- | --- |
| `results/estimator-grid.json` | `62fc42429131fe9c01eec2ce80cff80c93238b83d95cb1332b94ee5ae56b6e75` |

Canonical output SHA-256 after removing `generated_at`:
`88fca75c04b552439bf6628993e30fb5b717ec8f536df443b21c6ffe595bc1cc`.

## Key observations

- Alternative overall 95% CI coverage: `0.9929`
- Alternative coverage range across terms: `0.9800` to `1.0000`
- Global-null overall 95% CI coverage: `0.9879`
- Maximum absolute alternative bias: `0.00263`
- Maximum alternative RMSE: `0.01561`
- FWER under the global null: `0.0050`
- Power to detect any true effect: `1.0000`
- Power for the three-way effect: `0.9700`
- Realized BH FDR: `0.00167` (`2` false discoveries out of `1,001`)

These are finite-sample values for the declared simulation and sample sizes.
They are not asymptotic guarantees or external-validity claims.

## Preserved failure

An earlier formal run used 16 families, 12 episodes per family and cell, and
larger planted effects. Several constructed cell probabilities were clipped to
`[0.05, 0.95]`, and alternative coverage was `0.804`. The clipping is a
plausible explanation, but the run was not isolated as a clipping-only
ablation. The earlier run remains recorded in the experiment log and was not
used as the final artifact.

## Not completed

- No model inference, model download, GPU workload, paid API, external dataset,
  account change, or submission was performed.
- No real-agent data was analyzed.
- No arbitrary dependence structure, unequal-cell design, or non-Bernoulli
  outcome was evaluated.
- No novelty assessment or mapping to the user's still-unspecified original
  eight AGI research points was performed.
