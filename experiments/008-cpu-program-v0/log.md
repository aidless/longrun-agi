# Experiment 008 Log

## 2026-10-29: P5 strict subgroup claim schema integration

Integrated the 110-case strict claim-schema control into P5. The full program
now reports:

- strict positive claims `10` with `0` false discoveries;
- accepted / rejected / non-evaluable decisions `20 / 70 / 20`;
- declared confounding detected `10/10`;
- undeclared confounding detected `0/10` but blocked `10/10` as non-evaluable;
- invalid subgroup declarations rejected `10/10`;
- valid but undeclared positive claims blocked `10/10`;
- strict valid-discovery rate `0.5`.

The full program ran twice on the cloud CPU target `ecs-hz` with equal canonical
output.

| Value | SHA-256 |
| --- | --- |
| Raw output | `5a4406418a4dccf823702f6e50cc97a670fbceb08aedc2d67201163436ecc401` |
| Canonical output | `103f64aff17240a7b4adf74997cd5afe94b3dcd5fccda22aaa4253150e8d87df` |

The full run completed `8/8` CPU probes with GPU use `false` and no external
API calls. Final cloud verification passed `157` tests, `compileall`, the
`71/71` portfolio audit, and `make verify` across all `33` artifact versions.

## 2026-10-29: P5 stratified confounding integration

Integrated the 90-case stratified confounding control into P5. The full
program now reports both the original 80-case research-agent probe and the new
declared-subgroup comparison:

- research-agent false discoveries: naive `60`, gated `10`;
- confounding-control false discoveries: naive `70`, v0 `20`, stratified `10`;
- declared confounding detected `10/10`;
- undeclared confounding detected `0/10`, retained as `10` residual cases;
- valid-case false alarms `0`.

The full program ran twice on the cloud CPU target `ecs-hz` with equal canonical
output.

| Value | SHA-256 |
| --- | --- |
| Raw output | `b7d7c97715c447397d7993e57339ea501c2d580c3837d645bf61d93222264642` |
| Canonical output | `177e091f8416b7c198698d3f34334a8924ab156482ef191ad7063a09236effdd` |

The full run completed `8/8` CPU probes with GPU use `false` and no external
API calls. Final cloud verification passed `140` tests, `compileall`, the
`65/65` portfolio audit, and `make verify` across all `30` artifact versions.

## 2026-10-28: P8 adaptive controller integration

Added the five-action contextual controller to P8:

- adaptive success `0.4833`;
- mean cost `1.7333`;
- stability range `0.0417`;
- action counts retrieve 56, reflect 16, tool 40, stop 8, write-memory 0.

The controller did not beat fixed reflect on success and never wrote memory.
The full program repeated with equal canonical output and creates
`artifacts/cpu-program-v0/v9`.

## 2026-10-28: P1 verifier reward protocol integration

Added comparison of answer, process, self-verification, and
ensemble-disagreement rewards:

- answer OOD success `0.4333`; ensemble OOD `0.5233`;
- answer transfer drop `0.3033`; ensemble drop `0.1933`;
- answer mean cost `1.37`; ensemble `1.38`.

The ensemble improves OOD transfer in this synthetic protocol but does not
dominate all metrics. The full program was repeated with equal canonical
output and now creates `artifacts/cpu-program-v0/v8`.

## 2026-10-28: P4 calibrated world model integration

Added the symbolic calibrated-world-model probe to the integrated program:

- ID accuracy `1.000`; OOD accuracy `0.250`;
- ID uncertainty `0.5373`; OOD uncertainty `1.0000`;
- OOD error AUROC `0.5000`;
- planning success `0.5` for both argmax and uncertainty-penalized planners.

The uncertainty separates unseen states but does not improve error ranking or
planning in this construction. The full program was repeated with equal
canonical output and now creates `artifacts/cpu-program-v0/v7`.

## 2026-10-28: P6 goal-drift monitor integration

Added the synthetic held-out goal-drift monitor to the integrated program:

- AUROC `0.8295`;
- early-warning rate `0.0`;
- false-alarm rate `0.0833`;
- baseline and monitored final correctness both `0.5556`.

This is retained as a weak/negative monitoring result, not an activation-level
claim. The full program was repeated with equal canonical output and now creates
`artifacts/cpu-program-v0/v6`; v1-v5 remain history.

## 2026-10-28: P5 negative-control agent integration

The integrated program now includes the 80-case synthetic research-agent
comparison:

- naive false discoveries `60`;
- evidence-gated false discoveries `10`;
- valid discovery rate `1.0`;
- confounding blind spot `10`.

The full program was repeated with equal canonical output. This creates
`artifacts/cpu-program-v0/v5`; v1-v4 remain available as history.

## 2026-10-28: P2 recovery matrix integration

Added four-fault recovery evidence to the integrated program:

- retry-only and rollback recover only transient tool errors;
- replan and state-check-replan recover stale state, misleading docs, tool
  errors, and rule changes;
- replan averages 4.0 steps; state-check-replan averages 4.5;
- no controller required human intervention in the probe.

The full program was repeated with equal canonical output. This creates
`artifacts/cpu-program-v0/v4`; v1-v3 remain available as history.

## 2026-10-28: P3 layered memory integration

Added the three-layer episodic/semantic/procedural memory probe to the integrated
program. The full run now reports:

- flat-recency poison rate `1.000`;
- layered-provenance poison rate `0.000`;
- layered final correct rate `1.000`;
- 34 conflict cases;
- `98 passed` unit tests.

The program was repeated with equal canonical output. This creates
`artifacts/cpu-program-v0/v3`; v1 and v2 remain available as history.

## 2026-10-28: P7 CLEAR-300-v1 integration

The integrated CPU program now includes the frozen CLEAR-300-v1 benchmark in
P7:

- 300 tasks across filesystem, mock-browser, and gridworld;
- split `train=180`, `dev=60`, `test=60`;
- current-rule scripted success `1.000`;
- sticky-first-rule scripted success `0.3133`;
- canonical task hash
  `a8c1c421662f67a6e447ad1beda42a057fb8c7104ff740e0ab029998634b5c22`.

The full program was repeated with the same canonical result. Unit tests
increased to `91 passed`. This update supersedes the v1 integrated artifact with
v2; v1 remains available as history.

## 2026-10-28: Integrated CPU program

Added CPU implementations for all eight project-defined work packages and a
single `program` CLI entry point. The P1/P4/P6/P8 additions are deliberately
small symbolic or toy probes; they are not substitutes for model-level
experiments.

During review, three comparison defects were found and corrected:

- goal-drift policies initially consumed different random event streams;
- the nominally safe scheduler initially did not skip deadline-breaking jobs;
- cross-family transfer initially recreated the policy per direction instead of
  retaining it across source and target families.

The corrected comparisons are retained as regression tests. A later review also
fixed permanent fault classification: a schema or missing-source failure is no
longer counted as recovered merely because an exception ended the episode.

## Formal run

```bash
cd <repository-root>
make program
```

- Raw output SHA-256:
  `9c4aeaa05e5d8015b6333d71c07fdac85e993b09e48b7607f6574ce773a04c41`
- Canonical SHA-256 after removing `generated_at`:
  `201e645d876c3985e48f1acf43b50517aa76444ac02a6cdddd959f27be5e6f5d`
- Repeat run: canonical output equal
- CPU probes completed: 8/8
- GPU used: false
- External API calls: 0
- Unit tests: 83 passed
- Compile check: passed

### Observed controls

- P1 proxy-reward Q-learning selected the hazardous stop action and had final
  true reward `-3.0`; true-reward learning selected verify and had `4.0`.
- P2 recovered all three transient faults with retry and none without retry.
  The two permanent faults were not classified as recovered.
- P3 recency-only selection was poisoned on every poison event; source/trust
  memory was poisoned on zero events.
- P4 held-out one-step accuracy was `0.8939` for lag-1 and `0.9213` for lag-2.
  This is a small symbolic context-model comparison.
- P5 all seven controls matched expectations and all six per-check ablations
  changed behavior as expected.
- P6 final accuracy was `1.00` for pinned, `0.12` for recency, and `0.34` for
  decay on the shared event stream.
- P7 estimator coverage was `0.9929` and FWER `0.005`; the second generator and
  factorial recheck passed. Retained cross-family transfer fell to zero when the
  same sticky policy moved to a different routing family.
- P8 value-density produced the most value (`807`) among the tested schedules,
  while safe-value-density produced `530` with zero executed deadline misses.
  The safe policy is not called better: it trades away about 34% of value.

All observed differences are properties of deliberately constructed CPU
controls. They do not establish model capability, AGI, external validity, or
novelty.
