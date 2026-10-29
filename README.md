# LongRun-AGI

LongRun-AGI is a CPU-first research workspace for long-horizon agents that must
reason, act, remember, recover from failures, and stay auditable. It is released
under the MIT License.

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

## License

MIT. See `LICENSE`.

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
Portfolio integrity is checked by `scripts/audit_portfolio.py`.
