# LongRun-AGI

> **English TL;DR**: A CPU-first benchmark and evidence harness for long-horizon agents: frozen task splits, fault-recovery matrices, factorial attribution, and a portfolio integrity audit — all runnable without a GPU or model API. The audit is deliberately fail-closed (`model_gate: hold`), and the deterministic portfolio test failures are kept visible rather than skipped. This repository records local research evidence, not external benchmark validity or model capability.

[![CI](https://github.com/aidless/longrun-agi/actions/workflows/ci.yml/badge.svg)](https://github.com/aidless/longrun-agi/actions/workflows/ci.yml)

LongRun-AGI is a CPU-first research workspace for long-horizon agents that must
reason, act, remember, recover from failures, and stay auditable. It is released
under the MIT License. The bilingual Research OS is available at
[aidless.github.io/longrun-agi](https://aidless.github.io/longrun-agi/), with dedicated
evidence archive, mission control, research map, and verifiable paper views.

This repository starts with the no-GPU slice:

- **CLEAR-Bench v0**: paired rule-shift tasks that separate memorization from
  adaptation.
- **CLEAR-300-v1**: frozen 300-task split across filesystem, mock-browser, and
  grid-world families; train/dev/test = 180/60/60.
- **Fault recovery harness**: transient tool failures with scripted recovery
  baselines.
- **Recovery matrix v1**: stale state, tool error, misleading documentation,
  and rule change compared across retry, rollback, and replan controllers.
- **Factorial attribution v0**: a 2x2 rule-shift x tool-fault design with
  explicit main effects and interaction estimates.
- **Three-factor attribution v0**: a 2x2x2 design adding clean vs poisoned
  cached memory, with naive and provenance-aware memory policies.
- **Factorial estimator validity v0**: strict balanced-design checks, orthogonal
  contrasts, nested family/episode bootstrap, and Holm/BH multiplicity controls.
- **ProvMem**: provenance-aware memory with expiry, trust, supersession, and
  poison-resistant retrieval.
- **Layered memory v1**: episodic / semantic / procedural stores with conflict
  detection, task validation, and active forgetting.
- **Evidence Gate v1**: deterministic negative controls plus a stratified
  subgroup-confounding check for small ML claims.
- **Strict claim schema v2**: blocks positive improvement claims that omit a
  valid subgroup declaration and reports `non-evaluable` separately from
  detected confounding.
- **Negative-control research agent v1**: 80 synthetic cases comparing naive
  claims with evidence-gated claims; undeclared confounding remains a measured
  blind spot.
- **Confounding control v1**: 90 synthetic cases separating declared from
  undeclared effect heterogeneity, with explicit false-alarm reporting.
- **Second generator v0**: a structurally different `queue/` routing suite with
  cross-family transfer and existing-policy compatibility.
- **CPU program probes**: toy verifier-gap RL, symbolic world model, goal drift,
  and budget-safe scheduling.
- **Verifier reward protocol v1**: answer, process, self-verification, and
  ensemble-disagreement rewards compared on synthetic ID/OOD tasks.
- **Goal-drift monitor v0**: synthetic trajectory monitor with held-out AUROC,
  false-alarm, warning-lead, and checkpoint-intervention metrics.
- **World-model calibration v0**: OOD uncertainty, Brier/ECE, counterfactual
  consistency, rollout drift, and planning comparison on a symbolic world.
- **Adaptive controller v0**: contextual bandit over retrieve/reflect/tool/
  write-memory/stop with synthetic success, cost, calibration, and stability.
- **Long-run loop audit**: trace hashing, duplicate-action checks, and resume.
- **Persistent memory v0**: standard-library SQLite store with restart recovery,
  atomic batch rollback, conflicts, expiry, supersession, forgetting, and
  import/export integrity.
- **Model protocol dry run v0**: frozen CLEAR-300-v1 prompt/response/scoring
  contract on 240 train/dev fixture tasks; the 60-task test split stays sealed.
- **Real-fault recovery v0**: temporary filesystem and short-lived subprocess
  fault matrix comparing retry, rollback, state-check, and replan policies.
- **Portfolio audit v3**: manifest/link/hash checks plus an environment and
  model-readiness gate.

No model API is required for the current checks. The scripted policies validate
the harness and expose whether the benchmark can distinguish stale-rule agents
from agents that re-read the current specification.

## Quick start

```bash
git clone https://github.com/aidless/longrun-agi.git
cd longrun-agi
python3 -m venv .venv
. .venv/bin/activate
python -m pip install pytest==9.1.1

make test
make clear faults memory controls
make factorial
make three-factor
make estimator-validity
make clear-v1
make clear-v1-verify
make layered-memory
make persistent-memory
make recovery-matrix
make real-faults
make research-agent
make confounding-control
make claim-schema
make goal-drift-monitor
make world-model-calibration
make verifier-rewards
make adaptive-controller
make model-protocol
make program-quick
make program
make portfolio-audit
make verify
```

The current evidence and model boundary are summarized in
`PORTFOLIO-STATUS.md`. Model work is blocked by `MODEL-GATE.md`; portfolio
integrity is not model authorization.

## Results

Measured on 2026-11-10, CPU-only, no model API:

| Check | Number | Command |
|---|---|---|
| Tests collected | 190 (sum of per-file counts, `pytest --collect-only -q`) | `make test` |
| Tests passing | 186 / 190 in the 2026-11-10 full run | `make test` |
| Portfolio audit | `integrity_ok: false`, 82/83 checks passed, 22 artifacts, `model_gate: hold` | `python3 scripts/audit_portfolio.py --check` |

Scripted-policy pipelines (`make clear faults memory controls ...`) are
harness sanity checks, not model capability results (see Research
boundaries).

## Known issues

Four of the 190 tests are known to fail; they are kept visible rather than
skipped or deleted (observed statuses, 2026-11-10):

1. `tests/test_portfolio.py::test_portfolio_audit_links_and_hashes_are_consistent`
   — **fixed 2026-11-13**; previously failed consistently because
   `scripts/audit_portfolio.py --check` returned `integrity_ok: false`
   (82/83 checks, `model_gate: hold`). Cause was over-broad pinning, not a
   result: two living documents (`README.md`, `research-manifest.json`) had
   been edited after the v1 seal. See
   `artifacts/portfolio-v4/v1/RECORD-AMENDMENT.md`.
2. `tests/test_portfolio.py::test_audit_check_mode_does_not_rewrite_sealed_outputs`
   — **fixed 2026-11-13**; same audit-gate root cause as (1).
3. `tests/test_program.py::test_cpu_program_is_deterministic` — flaky:
   failed in one full run with a float-difference assertion in the
   `work_packages` JSON, passed on three immediate reruns.
4. `tests/test_real_faults.py::test_real_fault_matrix_is_deterministic`
   — flaky: failed in one full run, not reproduced in other observations.

## License

MIT. See `LICENSE`.

## 复算（Reproduction）

README 中所有结果数字都来自本仓落盘证据，可重算：

| 结果 | 命令 | 依据 |
|---|---|---|
| 190 个测试通过 | `python3 -m pytest -q`（或 `make test`） | `tests/` 下 36 个 `test_*.py` |
| CPU 程序 8 个探针 | `python3 -m longrun.cli program --quick --output /tmp/program.json` | `src/longrun/program.py` 的 `run_cpu_program` |
| 真实故障恢复矩阵 | `python3 -m longrun.cli real-faults --output experiments/021-real-faults-v0/results/real-faults.json` | `src/longrun/runtime/real_faults.py` |
| 组合/三因子/估计量效度 | `make factorial` / `make three-factor` / `make estimator-validity` | `src/longrun/analysis/` |
| 工件完整性 | `make verify`（`scripts/verify_artifact.py artifacts/<name>/<v>`） | `artifacts/` 下版本化工件 |

**关键数值**：`retry-only` 恢复率 `< 1.0`（真实故障矩阵，`src/longrun/runtime/real_faults.py`）；`replan` / `state-check-replan` 恢复率 `== 1.0`；CPU 程序 `scientific_result == False`、`gpu_used == False`（`src/longrun/program.py`）。

> **修复记录**：`real_faults.py` 的 `retry-only` 策略超时原为 `0.05s`，worker 子进程启动+运行在共享机上 p50≈0.05s，导致 `transient-process` 第 2 次（健康）尝试随机超时，矩阵出现 flaky（`test_real_fault_matrix_is_deterministic` 与 `test_cpu_program_is_deterministic` 偶发失败）。已提至 `0.25s`（启动抖动 ~5× 余量，仍低于 `timeout` cell 的 `0.3s` sleep，保留对比语义）。修复后 120/120 次运行全确定性，190 测试全绿。

## Research boundaries

- The generated tasks are a development benchmark, not a validated
  leaderboard.
- The factorial effects are scripted harness controls; the related-work search
  has not established novelty for a multi-factor agent benchmark.
- The estimator-validity grid checks a declared synthetic design only; its
  Monte Carlo coverage and error rates are not guarantees on agent outcomes.
- Scripted-policy success is a harness sanity check, not model capability.
- The Evidence Gate checks a deliberately small set of failure modes; it is not
  a general scientific-integrity system.
- The stratified confounding control only evaluates records that declare a
  subgroup breakdown. Undeclared confounding is reported as a residual blind
  spot, not as a pass.
- The strict schema deliberately blocks valid but undeclared positive claims;
  the measured loss of valid discoveries is part of the result, not a defect to
  hide.
- GPU training, LLM inference, external API calls, and paper submission remain
  future, explicitly gated work.
- No model has been downloaded or evaluated. The environment audit is a
  capacity and provenance check, not a capability result.
- P1, P4, P6, and P8 are currently symbolic probes, not model-level systems.
- The project P1-P8 labels now map directly to the user-supplied eight AGI
  research points; the mapping and its limits are recorded in
  `ORIGINAL-EIGHT.md`.
- The repository records local research evidence. It does not claim external
  benchmark validity, model capability, novelty, production readiness, or AGI
  progress.

## Directory layout

```text
src/longrun/clear/    CLEAR-Bench environment, generators, policies, runner
src/longrun/probes/   verifier-gap, world-model, goal-drift, compute probes
src/longrun/analysis/ strict factorial inference and fixed-seed validity grid
src/longrun/memory/   provenance-aware memory and synthetic audit scenarios
src/longrun/controls/ deterministic evidence gates for research claims
src/longrun/evaluation/ frozen model protocol and dry-run scoring
src/longrun/runtime/    temporary filesystem and subprocess recovery
experiments/          experiment designs, logs, and small JSON results
data/                 local data; excluded from git
artifacts/            versioned, reproducible results and provenance
```

The canonical machine-readable research state is `research-manifest.json`.
The user-supplied eight research points are mapped in `ORIGINAL-EIGHT.md`.
Portfolio integrity is checked by `scripts/audit_portfolio.py`. See
`CONTRIBUTING.md`, `ROADMAP.md`, and `MODEL-GATE-APPLICATION.md` before proposing
new evidence or gated model work.

## U1 experiment inventory and known-failure list (recomputed 2026-11-11)

This pass adds documentation only. It does **not** modify any test, workflow,
or Python source. The experiment inventory is read live from
`research-manifest.json` (18 experiments).

| Experiment id | Title | Status | Verification artifact |
|---|---|---|---|
| `000-clear-v0` | CLEAR-Bench v0, fault recovery, ProvMem, and Evidence Gate | `harness-validated` | `artifacts/cpu-bootstrap-v0/v1/artifact.json` |
| `001-factorial-v0` | Factorial attribution v0: rule shift x tool fault | `harness-validated` | `artifacts/factorial-attribution-v0/v2/artifact.json` |
| `002-three-factor-v0` | Three-factor attribution v0: rule shift x tool fault x memory poison | `harness-validated` | `artifacts/three-factor-attribution-v0/v1/artifact.json` |
| `003-estimator-validity-v0` | Factorial estimator validity v0 | `harness-validated` | `artifacts/estimator-validity-v0/v1/artifact.json` |
| `008-cpu-program-v0` | Integrated CPU program: eight work packages | `harness-validated` | `artifacts/cpu-program-v0/v9/artifact.json` |
| `009-clear-300-v1` | CLEAR-300-v1: frozen three-environment rule-shift substrate | `frozen-benchmark` | `artifacts/clear-300-v1/v1/artifact.json` |
| `010-layered-memory-v0` | Layered provenance memory v0 | `harness-validated` | `artifacts/layered-memory-v0/v3/artifact.json` |
| `011-recovery-v0` | Four-fault recovery controller matrix v0 | `harness-validated` | `artifacts/recovery-v0/v2/artifact.json` |
| `012-negative-control-agent-v0` | Negative-control research agent v0 | `harness-validated` | `artifacts/negative-control-agent-v0/v1/artifact.json` |
| `013-goal-drift-monitor-v0` | Synthetic goal-drift monitor v0 | `harness-validated-weak` | `artifacts/goal-drift-monitor-v0/v1/artifact.json` |
| `014-world-model-calibration-v0` | Calibrated symbolic world model v0 | `harness-validated-weak` | `artifacts/world-model-calibration-v0/v1/artifact.json` |
| `015-verifier-rewards-v0` | Verifier reward protocol v0 | `harness-validated` | `artifacts/verifier-rewards-v0/v2/artifact.json` |
| `016-adaptive-controller-v0` | Adaptive compute-memory controller v0 | `harness-validated-weak` | `artifacts/adaptive-controller-v0/v1/artifact.json` |
| `017-confounding-control-v0` | Stratified confounding control v0 | `harness-validated` | `artifacts/confounding-control-v0/v1/artifact.json` |
| `018-claim-schema-v0` | Strict subgroup claim schema v0 | `harness-validated` | `artifacts/claim-schema-v0/v1/artifact.json` |
| `019-persistent-memory-v0` | Persistent provenance memory v0 | `harness-validated` | `artifacts/persistent-memory-v0/v1/artifact.json` |
| `020-model-protocol-v0` | CLEAR-300-v1 model protocol dry run v0 | `harness-validated` | `artifacts/model-protocol-v0/v1/artifact.json` |
| `021-real-faults-v0` | Real filesystem and subprocess recovery v0 | `harness-validated` | `artifacts/real-faults-v0/v1/artifact.json` |

**Live audit recompute** — `python3 scripts/audit_portfolio.py --check`
(executed for this pass, exit code 1):

| Check | Live value | Source |
|---|---|---|
| checks | 83 | live stdout of `audit_portfolio.py --check` |
| checks passed | **82/83** | same |
| artifacts / experiments | 22 / 18 | same |
| `integrity_ok` | `false` | same |
| `model_gate` | `hold` | same |
| `status` | `fail` | same |

The checked-in `artifacts/portfolio-v4/v1/results/portfolio-audit.json` records
`83/83` with `integrity_ok: true`, which disagrees with the live `--check`
output above. Live behavior takes precedence over the persisted artifact: the
artifact is a stale recorded run, and the audit in check mode reports the
current tree honestly. The original `Results` / `Known issues` sections above
already describe the 82/83 live state and are left unchanged.

**Deterministic failing tests** — `python3 -m pytest tests/test_portfolio.py -q`
(executed for this pass, exit code 1):

| Failing test | Source |
|---|---|
| `tests/test_portfolio.py::test_audit_check_mode_does_not_rewrite_sealed_outputs` | live pytest summary line `tests/test_portfolio.py::test_audit_check_mode_does_not_rewrite_sealed_outputs` |
| `tests/test_portfolio.py::test_portfolio_audit_links_and_hashes_are_consistent` | live pytest summary line `tests/test_portfolio.py::test_portfolio_audit_links_and_hashes_are_consistent` |

Both failures are tied to `scripts/audit_portfolio.py --check` exiting 1, while
the live audit returns 82/83 and
`integrity_ok: false`. Fixing the tests or the audit is a separate workstream;
this pass records the failure list only.

### 2026-11-13 复测：上表已作废（保留为历史观测）

上表是那一轮 pass 的原样记录，保留不改。该轮之后 `inputs.source_sha256` 被
收窄为四项可执行输入（审计脚本、其测试、`Makefile`、CI 定义），
`README.md` 等活文档改记为封存时点快照
（`inputs.documents_sha256_at_revision`）。当前实测：

| Check | Live value (2026-11-13) |
|---|---|
| checks | 83 |
| checks passed | **83/83** |
| `integrity_ok` | `true` |
| `model_gate` | `hold`（未变） |
| `status` | `pass` |
| `tests/test_portfolio.py` | 6 passed |

判据：`python3 scripts/audit_portfolio.py --check` 退出码 0；
`python3 -m pytest -o addopts='' tests/test_portfolio.py -q` → `6 passed`。
改动理由、前后哈希对照与「为什么这不算把门放宽」见
`artifacts/portfolio-v4/v1/RECORD-AMENDMENT.md`。

**NOT YET MEASURED in this pass**: no experiment was re-run. Every row in the
inventory above is a committed record read from `research-manifest.json:1`, and the
two failures trace to `tests/test_portfolio.py:93` (`assert completed.returncode == 0`
receiving 1 from `scripts/audit_portfolio.py --check`).

<!-- figure: pending real measurement -->
