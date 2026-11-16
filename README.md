# LongRun-AGI

<!-- problem:start -->
Long-horizon scores are easy to over-read, so this repository closes one scripted recovery contrast and leaves every other module in progress.
On 40 frozen tasks and 160 committed traces, replan and state-check-replan succeed at 1.0 on all four faults; retry-only and rollback succeed at 0.25 and only on transient tool error.
That shows the state machine can tell a repeated action from a replaced rule. It does not show LLM recovery, external benchmark validity, or finished human annotation.
<!-- problem:end -->

STATUS: WORK-IN-PROGRESS — not A yet

The remaining A-bar gap is the live GitHub About text. README, the Research OS pages, and CI agree on the recovery-matrix headline. The About description, the `llm` topic, and the empty homepage do not. Replacement text is in [GitHub About](#github-about). This branch cannot edit repository settings.

`model_gate: hold`. Scripted controllers are not LLM agents. Human annotation is not done.

<!-- headline-result:start -->
result_id: recovery-matrix-v1
controllers: scripted
tasks: 40
traces: 160
replan: 1.0
state-check-replan: 1.0
retry-only: 0.25
rollback: 0.25
retry_and_rollback_succeed_only_on: tool_error
clear-300-v1-canonical-sha256: a8c1c421662f67a6e447ad1beda42a057fb8c7104ff740e0ab029998634b5c22
clear-300-v1-splits: 180/60/60
human_annotation: not-done
model_gate: hold
<!-- headline-result:end -->

CLEAR-300-v1 stays a frozen 300-task split (180/60/60, canonical SHA-256 above). `make check` rebuilds that hash from the generator and the committed manifest. The split is not the headline result. No annotation corpus is committed. Open review requests #1, #7, #8, #9, and #10 have no completed annotation.

## Reproduce

Fresh clone, offline after clone, no pip:

```bash
git clone https://github.com/aidless/longrun-agi.git
cd longrun-agi
make check
```

`make check` replays the scripted controllers on `benchmarks/recovery-matrix-v1/tasks.json`, aggregates `artifacts/recovery-v0/v2/results/recovery-matrix.json` rows, and exits non-zero if this README, the pages, or the CLEAR-300 hash drift. Python 3.11+ standard library only.

Optional suite, not the headline gate: `python -m pip install pytest==9.1.1` then `make test`.

## What the headline does not show

- An LLM or other learned agent recovered from faults.
- External benchmark validity, novelty, or production resilience.
- A confidence interval. The rates are counts on 40 copied tasks. See `FAILURE_MODES.md`.
- Finished human annotation.

## In-progress modules

These have committed harness artifacts. They are not the closed result.

| Module | Where |
| --- | --- |
| CLEAR-Bench v0 and CLEAR-300-v1 | `benchmarks/clear-300-v1/`, hash checked by `make check` |
| Factorial attribution v0 | `artifacts/factorial-attribution-v0/v2/` |
| Three-factor attribution v0, including poisoned memory | `artifacts/three-factor-attribution-v0/v1/` |
| Estimator validity v0 (nested bootstrap, Holm/BH) | `artifacts/estimator-validity-v0/v1/` |
| ProvMem, layered memory, persistent memory | `artifacts/layered-memory-v0/`, `artifacts/persistent-memory-v0/` |
| Evidence gate, claim schema, confounding control | `artifacts/negative-control-agent-v0/`, `artifacts/claim-schema-v0/`, `artifacts/confounding-control-v0/` |
| Real filesystem/subprocess faults (separate 5-case suite) | `artifacts/real-faults-v0/v1/` |
| CPU probes for verifier rewards, world model, goal drift, adaptive control | `artifacts/cpu-program-v0/` |
| Model-protocol dry run, test split sealed | `artifacts/model-protocol-v0/v1/` |
| Portfolio integrity audit | `artifacts/portfolio-v4/v1/`, `model_gate: hold` |

Limits for the scripted ceiling, CLEAR-300 family overlap, bootstrap assumptions, and the poisoned-memory note are in `FAILURE_MODES.md`.

## Tests that fail by design

Designed failures: none. `make check` must pass. The pytest suite is expected to pass and is not marked xfail for this result.

Historical note, not a current failure: on 2026-11-11 two `tests/test_portfolio.py` tests failed because `audit_portfolio.py --check` reported 82/83 after README and manifest edits. The 2026-11-13 amendment narrowed the document pin; see `artifacts/portfolio-v4/v1/RECORD-AMENDMENT.md`. This branch re-seals the `Makefile` and `ci.yml` hashes because `make check` changes those executable inputs. That re-seal keeps `scientific_result: false` and `model_gate: hold`. It does not create a model result.

The portfolio-v4 artifact still records `190 passed` and `83/83` as the seal's own check fields. The Research OS home page labels those figures as the seal record. This branch adds three tests in `tests/test_headline_check.py` and does not rewrite the seal's `190 passed` field.

## Author-machine path

Author-machine path: `/home/liuzewen/projects/longrun-agi-20261027` in `PORTFOLIO-STATUS.md`, and the roots stored in `artifacts/portfolio-v1/v1/results/environment-audit.json` and `artifacts/portfolio-v4/v1/results/environment-audit.json`, are host snapshots. A fresh clone uses `make check` from the repository root. Do not treat those paths as the reproduction command.

## GitHub About

Observed live description: "CPU-first benchmark and evidence harness for long-horizon, continual agents". Topics: `agent`, `evaluation`, `llm`, `long-horizon`. Homepage: empty.

Replacement text:

- Description: `Scripted recovery-matrix check on 40 frozen tasks (replan 1.0, retry-only 0.25). Not an LLM evaluation. model_gate: hold.`
- Website: `https://aidless.github.io/longrun-agi/`
- Remove topic: `llm`
- Topics that match the closed result: `agent`, `evaluation`, `reproducibility`

## License

MIT. See `LICENSE`.

Research OS pages: [aidless.github.io/longrun-agi](https://aidless.github.io/longrun-agi/).
