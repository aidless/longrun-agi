# Experiment 017: Stratified Confounding Control v0

## Question

Can an evidence gate reduce false discoveries from a declared confounding
pattern without rejecting valid improvements, and can it report the cases that
remain undetectable because no subgroup breakdown was declared?

This experiment evaluates an evidence-processing control over synthetic
records. It does not evaluate a research agent, a model, or a live scientific
claim.

## Design

The probe contains 90 deterministic cases:

| Category | Cases | Expected positive | Valid experiment |
| --- | ---: | --- | --- |
| `valid-positive` | 10 | yes | yes |
| `valid-negative` | 10 | no | yes |
| `split-overlap` | 10 | no | no |
| `target-leakage` | 10 | no | no |
| `broken-baseline` | 10 | no | no |
| `p-hacking` | 10 | no | no |
| `unreproducible` | 10 | no | no |
| `confounded-declared` | 10 | no | no |
| `confounded-undeclared` | 10 | no | no |

Three claim policies are compared on the same records:

1. `naive` accepts every positive aggregate improvement.
2. `gated_v0` adds the existing split, leakage, baseline, seed, and
   reproducibility checks.
3. `gated_v1` additionally checks declared subgroup breakdowns.

## Confounding Check

When subgroups are declared:

- weighted subgroup candidate and baseline accuracies must reproduce the
  reported aggregate accuracies within `1e-6`;
- if aggregate improvement is positive, any subgroup with weight at least
  `0.2` and non-positive improvement is flagged.

When subgroups are not declared, the check returns `evaluated=false`. It does
not treat missing subgroup data as a pass. The undeclared confounding cases
therefore remain a measured residual blind spot.

## Acceptance Criteria

1. The case set has 90 unique cases and 10 cases in each category.
2. The probe repeats deterministically after removing `generated_at`.
3. Valid cases produce no false alarms.
4. Declared confounding is detected in all 10 cases.
5. Undeclared confounding is detected in zero cases and reported as residual.
6. `gated_v1` has fewer false discoveries than `gated_v0`, without losing any
   valid positive discovery.
7. The output records `scientific_result=false` and
   `novelty_status=not-established`.

## Compute and Data Boundary

- Execution target: cloud CPU host, not the authoring workstation.
- External data: none.
- Model download or load: none.
- GPU use: none.
- Paid API calls: none.
- Network calls during the experiment: none.

## Non-goals

- No claim that subgroup checking solves confounding generally.
- No causal adjustment, propensity estimation, weighting, or sensitivity
  analysis.
- No live research-agent or model-backed evaluation.
- No scientific, novelty, publication, or AGI capability claim.
