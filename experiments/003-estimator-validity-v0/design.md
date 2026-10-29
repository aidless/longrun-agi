# Experiment 003: Factorial estimator validity v0

## Question

Before using factorial contrasts as evidence about an agent mechanism, do the
contrasts recover known planted effects, and do their interval and multiplicity
procedures behave as claimed on balanced synthetic designs?

This is a statistics and harness-validation experiment. It is not an LLM
experiment, an AGI capability result, or a novelty claim.

## Design

The estimator accepts only a complete balanced two-level factorial design. For
this experiment, each family contains all eight cells of a `2 x 2 x 2` design
and the same number of episodes in every cell. The default grid uses:

- 24 independent families;
- 20 episodes per family and cell;
- a genuine nested cluster bootstrap that first samples families, then samples
  episodes within each sampled family and cell;
- percentile 95% confidence intervals;
- seven standard orthogonal contrast terms;
- Holm-Bonferroni family-wise error control across the seven terms;
- Benjamini-Hochberg false-discovery-rate control across the seven terms;
- fixed seed `20261027`.

Each success count is Bernoulli. All families share the stated marginal
contrasts, but each family receives a fixed random probability offset in
`[-0.02, 0.02]`. This creates family-level intraclass correlation and tests that
the interval procedure does not treat all episodes as independent. The planted
cell probabilities are checked to stay strictly inside `(0, 1)`, so no clipping
alters the estimands.

Two Monte Carlo conditions are run:

- **Null:** all seven contrasts are zero, used to measure false-positive
  behavior.
- **Alternative:** five contrasts are nonzero and the `A x C` and `B x C`
  interactions are exactly zero, used to measure power, bias, RMSE, interval
  coverage, and realized FDR.

## Estimands

The intercept is the unweighted mean of the eight cell success probabilities.
For every nonempty subset `S` of factors, the unnormalized standard orthogonal
contrast is:

```text
C(S) = sum_x sign(S, x) * mean(x) / 2^(k-1)
```

where `k` is the number of factors, `x` runs over all `2^k` cells, and
`sign(S, x)` is `+1` for level 0 and `-1` for level 1 on each factor in `S`.
Therefore a main effect is level `0` minus level `1`, and a two-way interaction
is the difference of differences. These are contrasts, not standardized effect
sizes and not regression coefficients for arbitrary observational data.

## Acceptance criteria

1. Malformed, incomplete, unbalanced, duplicated, or unknown-factor input is
   rejected before estimation.
2. Strict integer `0/1` factor levels are required; booleans, strings, floats,
   and missing values are rejected.
3. A balanced planted-effect fixture recovers all two-factor and three-factor
   contrasts to numerical precision.
4. Bootstrap confidence intervals and p-values are deterministic for a fixed
   seed.
5. Input row order does not change the canonical result.
6. The contrast scale and three-way interaction use the same formula for the
   known-effect fixture and the Monte Carlo generator.
7. Holm and Benjamini-Hochberg produce valid monotone adjusted p-values and
   their expected decisions on a deterministic example.
8. The grid reports planted-effect recovery, bias, RMSE, confidence-interval
   coverage, FWER under the global null, power under the alternative, realized
   FDR, and cell balance.
9. The output includes its command, configuration, seed, environment, and
   SHA-256; the artifact is labeled `harness-validation` with
   `scientific_result: false` and `novelty_status: not-established`.

## Interpretation boundary

Finite-sample Monte Carlo behavior is evidence about this estimator under the
declared simulation. It does not establish coverage or error control for
arbitrary agent tasks, arbitrary dependence structures, or arbitrary model
behavior. It also does not justify calling the resulting benchmark novel.

## Non-goals

- No model inference, model download, GPU, paid API, external dataset, or
  submission.
- No real-agent outcome is simulated or extrapolated from these results.
- No claim that the eight-cell construction alone is an AGI research
  contribution.
