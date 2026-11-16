# FAILURE_MODES

These are design limits of the closed recovery-matrix result and of the named in-progress modules. They are not new measurements.

## Scripted-baseline ceiling

`RetryOnlyPolicy`, `RollbackPolicy`, `ReplanPolicy`, and `StateCheckReplanPolicy` in `src/longrun/clear/recovery.py` are fixed action lists. `Replan` writes `corrected_rule` into the visible state before the successful `ACT`. On the committed 160 rows, replan and state-check-replan therefore succeed on every task (`1.0`), and retry-only and rollback succeed only on `tool_error` (`0.25`). That `1.0` is the script ceiling.

The 10 instances of a fault share `initial_rule=rule-v1` and `corrected_rule=rule-v2`. They are copies of one episode with different ids. The rate is not an estimate over distinct tasks, and it is not a learned policy.

## Task-family leakage

Recovery-matrix instances do not cross task families. Treating the 40 ids as independent samples would leak one template into every replicate.

CLEAR-300-v1 is a separate frozen split, not this headline. `src/longrun/benchmarks/clear_v1.py` assigns variants 0–2 to train, variant 3 to dev, and variant 4 to test (`_split_for_variant`). The same `family_id` is present in every split, so a policy can see a family's structure in train and meet it again in test. `make check` rebuilds `canonical_sha256` and checks the 180/60/60 counts. It does not claim the split is leakage-free or externally valid.

## Bootstrap assumptions

The headline rates are counts over the frozen 40 tasks. They are not bootstrap estimates. Do not attach the estimator-validity intervals to `1.0` or `0.25`.

Estimator-validity v0 is an in-progress module. `estimate_factorial` in `src/longrun/analysis/factorial.py` resamples families with replacement, then resamples episodes inside the drawn family with replacement. It requires the balanced design the same function checks. Intervals are percentiles. `_bootstrap_p_value` centers the draws on the observed estimate before counting tails, so the p-value is not a test against a zero-effect null. Holm-Bonferroni and Benjamini-Hochberg then adjust those p-values.

`artifacts/estimator-validity-v0/v1/provenance.md` records finite-sample coverage on the declared simulation only: alternative overall 95% CI coverage `0.9929`, global-null FWER `0.0050`. Those figures are not guarantees on agent outcomes.

## Poisoned-memory design limits

Three-factor attribution v0 is an in-progress module, not the headline. The poison cell is one cached note whose map is the opposite of `docs/SPEC.md`, with source `user-note.txt` and trust `0.10` (`experiments/002-three-factor-v0/design.md`). `memory-provenance` keeps a note only when the source is `docs/SPEC.md` and trust is at least `0.5`.

In `artifacts/three-factor-attribution-v0/v1/results/three-factor-eval.json`, `memory-naive` has a `memory_poison` main effect of `1.0` and a three-way interaction of `0.0`. `memory-provenance` has main effects `0.0` and a three-way interaction of `0.0`. That is a scripted filter on a constructed note. It is not LongMemEval, LoCoMo, or a human-annotated memory attack. No annotation file is committed.
