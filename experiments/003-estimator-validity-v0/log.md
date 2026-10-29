# Experiment 003 Log

## 2026-10-28: Estimator validity CPU prototype

Added an independent valid 2-level factorial estimator so the existing
descriptive `factorial_effects()` function remains unchanged. The new module
validates balance and factor types, uses standard orthogonal contrasts, and
implements nested family/episode bootstrap intervals plus Holm FWER and
Benjamini-Hochberg FDR adjustments.

### Estimate correction during implementation

The first local test fixture divided higher-order terms by an extra
`2^(k-|S|)`, which makes those terms inconsistent with the standard contrast
formula. The fixture was corrected to use the same `1/2` cell-to-contrast
scaling as the estimator. This was a test-math error, not an estimator result.

### Formal run

```bash
cd <repository-root>
make estimator-validity
```

Configuration: `200` Monte Carlo repetitions, `299` bootstrap replicates per
repetition, and seed `20261027`. Each condition has 24 families, 20 episodes
per family and cell, eight cells, and 3,840 episodes. The design was balanced
in every repetition.

The raw output SHA-256 is
`62fc42429131fe9c01eec2ce80cff80c93238b83d95cb1332b94ee5ae56b6e75`.
The canonical SHA-256 after removing only the nondeterministic `generated_at`
field is
`88fca75c04b552439bf6628993e30fb5b717ec8f536df443b21c6ffe595bc1cc`.
A second fixed-seed run had the same canonical digest.

### Formal observations

| metric | observed |
| --- | ---: |
| Alternative overall 95% CI coverage | 0.9929 |
| Alternative per-term coverage range | 0.9800 to 1.0000 |
| Global-null overall 95% CI coverage | 0.9879 |
| Alternative maximum absolute bias | 0.00263 |
| Alternative maximum RMSE | 0.01561 |
| FWER under the global null (Holm) | 0.0050 |
| Power to detect any true effect (Holm) | 1.0000 |
| Power for the three-way contrast (Holm) | 0.9700 |
| Realized FDR (Benjamini-Hochberg) | 0.00167 |
| BH false discoveries / total discoveries | 2 / 1,001 |

The FDR calculation has two planted null terms (`A x C` and `B x C`) in the
alternative condition. It is a finite-sample simulation estimate, not a formal
proof of asymptotic FDR control.

### Preserved first formal run

The first formal grid used 16 families, 12 episodes per family and cell, and
large planted effects. As a consequence, several generated cell probabilities
were clipped to `[0.05, 0.95]` after contrast construction. That run produced
overall alternative coverage `0.804` and maximum absolute bias about `0.040`.
It was not used as the final artifact. The observed shortfall is consistent with
the nonlinearity introduced by clipping, but this diagnosis was verified only
by changing to a design with no clipping and observing nominal coverage; it was
not isolated with a separate clipping-only ablation.

### Interpretation

The observations support using the new estimator as a deterministic measurement
component inside the declared balanced synthetic design. They do not establish
validity for arbitrary dependence, model-generated episodes, or task families.
The scripted and simulated outcomes are not evidence of LLM or AGI capability.
