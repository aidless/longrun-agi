# Experiment 018: Strict Subgroup Claim Schema v0

## Question

Can a claim gate require a complete subgroup declaration before accepting a
positive improvement claim, without relabeling a missing declaration as a
confounding detection?

This experiment evaluates a deterministic evidence-processing policy. It does
not evaluate a live research agent or a model.

## Design

The suite extends the historical 90-case confounding control with 20
strict-schema cases:

| Category | Cases | Positive aggregate | Valid experiment |
| --- | ---: | --- | --- |
| `valid-positive` | 10 | yes | yes |
| `valid-negative` | 10 | no | yes |
| `split-overlap` | 10 | yes | no |
| `target-leakage` | 10 | yes | no |
| `broken-baseline` | 10 | yes | no |
| `p-hacking` | 10 | yes | no |
| `unreproducible` | 10 | yes | no |
| `confounded-declared` | 10 | yes | no |
| `confounded-undeclared` | 10 | yes | no |
| `valid-positive-undeclared` | 10 | yes | yes |
| `invalid-subgroup-declaration` | 10 | yes | no |

The two new categories measure the cost and enforcement behavior of a strict
schema:

- `valid-positive-undeclared` is a valid aggregate result but lacks the
  metadata needed to evaluate confounding;
- `invalid-subgroup-declaration` has duplicate subgroup identifiers while its
  aggregate accuracy still appears valid.

Four policies are compared:

1. `naive` accepts every positive aggregate improvement.
2. `gated_v0` applies the existing split, leakage, baseline, seed, and
   reproducibility checks.
3. `gated_v1` also rejects declared subgroup regressions, but still accepts
   positive claims with no subgroup declaration.
4. `strict_v2` additionally rejects malformed declarations and marks missing
   subgroup metadata as `non-evaluable`.

## Claim Gate Contract

All positive claims require a declared subgroup breakdown. The declaration
must satisfy:

- non-empty, unique subgroup identifiers;
- positive subgroup sample sizes;
- candidate and baseline accuracies within `[0, 1]`;
- `test_n` present, positive, and equal to the sum of subgroup sample sizes;
- weighted subgroup accuracies reproduce the reported aggregate accuracies;
- no materially weighted subgroup regression when aggregate improvement is
  positive.

Decision precedence:

- invalid base evidence or invalid subgroup schema: `rejected`;
- valid evidence, positive claim, missing declaration: `non-evaluable`;
- declared confounding regression: `rejected`;
- otherwise: `accepted`.

`non-evaluable` blocks a positive claim, but it is not counted as a confounding
detection.

## Expected Outcomes

| Policy | Positive claims | True discoveries | False discoveries | Valid discovery rate |
| --- | ---: | ---: | ---: | ---: |
| `naive` | 100 | 20 | 80 | 1.0 |
| `gated_v0` | 50 | 20 | 30 | 1.0 |
| `gated_v1` | 40 | 20 | 20 | 1.0 |
| `strict_v2` | 10 | 10 | 0 | 0.5 |

Strict decisions: accepted `20`, rejected `70`, non-evaluable `20`.

The strict policy detects `10/10` declared confounding cases. It detects
`0/10` undeclared confounding cases, but blocks all `10/10` as non-evaluable.
It also blocks all `10/10` valid but undeclared positive claims. That lost
half of the valid discoveries is an explicit cost of the strict contract.

## Acceptance Criteria

1. The suite contains 110 unique cases across 11 categories.
2. All policy counts match the expected table exactly.
3. Missing subgroup metadata produces `non-evaluable`, never `detected`.
4. All `10` invalid subgroup declarations are rejected.
5. Existing Evidence Gate, confounding control, and artifacts remain
   behaviorally compatible.
6. The output is deterministic after removing `generated_at`.
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

- No live research-agent or model-backed evaluation.
- No causal adjustment or unmeasured-confounding sensitivity analysis.
- No claim that blocking missing metadata detects confounding.
- No scientific, novelty, publication, or AGI capability claim.
