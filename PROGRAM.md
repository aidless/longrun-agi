# LongRun-AGI Program

## Current scope and honest boundary

This file uses the project work-package taxonomy P1-P8. The user-supplied
original eight AGI research points are now mapped in `ORIGINAL-EIGHT.md`. All
results below are CPU-only harness validation unless a row explicitly says
otherwise.

## Central question

Can a single agent remain reliable and adaptive over a long series of tasks when
the rules change, tools fail, memory is stale or poisoned, and evidence must be
audited?

## CPU-first phase

The current phase is deliberately model-free. It builds the measurement and
evidence substrate before spending compute on training.

| Work package | CPU deliverables | Current status |
| --- | --- | --- |
| P7 CLEAR-Bench | paired rule-shift tasks, frozen 300-task three-environment split, verifier, second generator, cross-family transfer | implemented as v1 CPU substrate |
| P2 FailRecover | four-fault matrix, retry/rollback/replan/state-check controllers, recovery metrics | implemented as v1 CPU substrate |
| P3 ProvMem | three layers, provenance, trust, expiry, supersession, conflicts, validation, active forgetting, poison controls | implemented as v1 CPU substrate |
| P7b Factorial attribution | 2x2 rule/tool and 2x2x2 rule/tool/memory crossed designs with scripted controls | implemented as v0; novelty not established |
| P7c Estimator validity | strict balance/type checks, orthogonal contrasts, nested bootstrap, Holm/BH, fixed-seed Monte Carlo grid | implemented as v0; scope-limited |
| P5 Evidence Gate | split, leakage, baseline, seed, reproducibility, declared-subgroup checks, and strict claim schema; 80-case agent probe, 90-case confounding control, and 110-case schema control | implemented as v2 CPU substrate |
| P1 Verifier-Gap RL | reward-mismatch MDP and four-mode tabular reward protocol | CPU symbolic probe only; real RL/GPU deferred |
| P4 World Model | symbolic lag prediction, ensemble uncertainty, calibration, counterfactual/rollout metrics, planning comparison | CPU symbolic probe only; learned model deferred |
| P6 Goal-Drift Probe | shared-event controls, synthetic logistic monitor, held-out monitoring, checkpoint intervention | CPU weak/negative probe; activation probe deferred |
| P8 Compute Controller | synthetic scheduling, budget guards, and five-action contextual bandit on CLEAR contexts | CPU weak/negative probe; real runtime deferred |

## Program CLI

```bash
PYTHONPATH=src python3 -m longrun.cli program --quick \
  --output experiments/008-cpu-program-v0/results/quick.json
PYTHONPATH=src python3 -m longrun.cli program \
  --output experiments/008-cpu-program-v0/results/program.json
PYTHONPATH=src python3 -m longrun.cli confounding-control \
  --output experiments/017-confounding-control-v0/results/confounding-control.json
PYTHONPATH=src python3 -m longrun.cli claim-schema \
  --output experiments/018-claim-schema-v0/results/claim-schema.json
```

The full run is CPU-only; the estimator grid alone took about 2m17s in the
recorded 200-repetition run.
The quick run uses the same code paths with fewer Monte Carlo repetitions.

## Acceptance gates

1. A task generator must be deterministic for a fixed seed and configuration.
2. A correct reference policy must pass the clean task suite.
3. A stale-memory policy must fail shifted tasks; otherwise the benchmark is not
   measuring the intended contrast.
4. A transient fault must be observable, recoverable, and counted separately
   from clean-task success.
5. Every reported result must be written to JSON with a command and input hash.
6. A result from a scripted policy must be labeled as harness validation, not
   model evidence.
7. Inferential output must reject incomplete or unbalanced designs and report
   its clustering, interval, multiplicity, and simulation scope.
8. A fault matrix must distinguish transient recovery from permanent failure.
9. A symbolic probe must be labeled as such and must not be counted as model
   capability or AGI evidence.
10. A scheduler comparison must report both value and deadline behavior; a
    low-deadline-miss policy with lower value is not automatically better.

## Completed CPU gates

- A second independent task generator with a different input format.
- A frozen 300-task CLEAR split across filesystem, mock-browser, and grid-world.
- A three-layer memory substrate with conflict detection and active forgetting.
- A four-fault recovery matrix with replanning and state-check controllers.
- An 80-case negative-control research-agent probe with a documented confound
  blind spot.
- A 90-case stratified confounding control: declared confounding detected
  `10/10`, valid-case false alarms `0`, and `10/10` undeclared cases retained
  as a residual blind spot.
- A 110-case strict claim-schema control: the strict policy accepts `10`
  positive claims with `0` false discoveries, blocks `10/10` undeclared
  confounding cases as non-evaluable, and also blocks `10/10` valid but
  undeclared positive claims.
- Adversarial memory events, expiry, supersession, and cross-family transfer.
- Trace, duplicate-action, and resume checks for the local long-run loop.
- P1/P4/P6/P8 symbolic probes with explicit scientific boundaries.

## Next gates

- Keep model work on hold until `MODEL-GATE.md` has an exact artifact and an
  explicit approval record.
- Re-run `make portfolio-audit` after any manifest, artifact, or boundary-document
  change; a passing audit only verifies portfolio integrity.
- Apply the strict subgroup schema to any future live research-agent claim path
  and retain the measured cost of rejecting undeclared valid claims.
- Use `CLEAR-300-v1` train/dev/test without editing frozen tasks before any
  model comparison.
- Run a small open-weight CPU model only after memory pressure is checked and
  an explicit model-download gate is approved.
- Replace symbolic probes with learned or model-level measurements only when
  compute and evidence contracts are approved.
- Connect the mock browser and grid-world tasks to real engines only after the
  frozen CLEAR-300-v1 split has a stable model-evaluation protocol.
