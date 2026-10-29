# LongRun-AGI Portfolio Status

Status date: 2026-10-28 America/Los_Angeles (2026-10-29 UTC)

## Decision

The CPU evidence substrate is complete enough for consolidation and the next
engineering steps. The portfolio is **not ready for a model-level capability
claim**. All eight work packages have runnable CPU probes, but none has an
external benchmark result, a language-model result, or an established
scientific contribution.

Current state:

- Work packages with a CPU probe: `8/8`.
- Frozen CLEAR-300-v1 tasks: `300` (`180/60/60` train/dev/test).
- Manifest experiments: `15`.
- Registered artifacts after this audit: `18`.
- Verification suite: `174` tests across `31` test files.
- Model evaluations completed: `0`.
- GPU jobs, model downloads, paid API calls, submissions, and publications: `0`.

## Work Package Matrix

| Package | CPU evidence | Maturity | Honest result | Next gate |
| --- | --- | --- | --- | --- |
| P1 Verifier-Gap RL | Toy MDP plus four reward modes on synthetic ID/OOD tasks | symbolic probe | Ensemble-disagreement OOD success is `0.5233` versus `0.4333` for answer reward, but no mode dominates success, calibration, hacking, and cost together. | Real open-weight model and task split |
| P2 FailRecover | Four-fault matrix and retry, rollback, replan, and state-check controllers | CPU substrate | Replan and state-check-replan reach `1.0`; retry-only and rollback reach `0.25`. | Real OS, browser, or tool environment |
| P3 ProvMem | Three-layer memory with provenance, trust, expiry, supersession, conflicts, validation, and forgetting | CPU substrate | Flat poison rate is `1.0`; layered provenance poison rate is `0.0` in the declared synthetic probe. | Persistent store and LongMemEval/LoCoMo protocol |
| P4 World Model | Symbolic lag model, ensemble uncertainty, calibration, rollout, and planning probe | weak/negative probe | ID accuracy is `1.0` but OOD accuracy is `0.25`; OOD error AUROC is `0.5`; uncertainty-penalized planning is `0.5`, equal to argmax. | Learned world model with measured compute |
| P5 Evidence Gate | Seven deterministic controls, an 80-case agent probe, a 90-case confounding control, and a 110-case strict schema control | CPU substrate | Agent-probe false discoveries fall from `60` to `10`. Strict schema reaches `0` false discoveries but blocks `10/10` undeclared confounding and `10/10` valid undeclared positives, leaving valid-discovery rate `0.5`. | Live research-agent schema adoption |
| P6 Goal-Drift Probe | Shared-event probe plus synthetic held-out logistic monitor | weak/negative probe | Held-out AUROC is `0.8295`, but early-warning rate is `0.0` and monitored final correctness equals the baseline at `0.5556`. | Activation access and a model-level warning protocol |
| P7 CLEAR-Bench | Paired shifts, second generator, CLEAR-300-v1, factorial designs, estimator checks, trace/resume audit | CPU substrate | Current-rule scripted success is `1.0`; sticky-first-rule scripted success is `0.3133`. This is a harness contrast, not model behavior. | Frozen model-evaluation protocol |
| P8 Compute Controller | Synthetic scheduler plus five-action contextual bandit | weak/negative probe | Value-density earns `807` with `88` deadline misses; safe-value-density earns `530` with `0` misses. The adaptive controller has `0.4833` success and `0` memory writes. | Real tool/retriever costs and fixed/oracle baselines |

## Evidence Ledger

| Evidence | Status | Boundary |
| --- | --- | --- |
| `artifacts/cpu-program-v0/v12/artifact.json` | harness validation | Eight CPU probes ran; P1/P4/P6/P8 are symbolic or weak probes. |
| `artifacts/clear-300-v1/v1/artifact.json` | frozen benchmark | Deterministic local mocks, not real browser or game environments. |
| `artifacts/layered-memory-v0/v3/artifact.json` | harness validation | Synthetic memory conflicts, not an external memory benchmark. |
| `artifacts/recovery-v0/v2/artifact.json` | harness validation | Scripted controllers, not a model policy. |
| `artifacts/negative-control-agent-v0/v1/artifact.json` | harness validation | Synthetic cases with a measured confounding blind spot. |
| `artifacts/confounding-control-v0/v1/artifact.json` | harness validation | Declared subgroup confounding only; undeclared confounding remains non-evaluable. |
| `artifacts/persistent-memory-v0/v1/artifact.json` | harness validation | SQLite persistence and recovery controls, not an external memory benchmark. |
| `artifacts/model-protocol-v0/v1/artifact.json` | harness validation | Frozen train/dev protocol dry run; test split remains sealed. |
| `artifacts/real-faults-v0/v1/artifact.json` | harness validation | Temporary filesystem and subprocess recovery, not production resilience. |
| `artifacts/claim-schema-v0/v1/artifact.json` | harness validation | Strict schema blocks missing declarations but does not detect their hidden confounding. |
| `artifacts/goal-drift-monitor-v0/v1/artifact.json` | weak evidence | Ranking signal exists, but no pre-drift warning or recovery benefit was shown. |
| `artifacts/world-model-calibration-v0/v1/artifact.json` | weak evidence | Symbolic model only; OOD error ranking and planning gain failed. |
| `artifacts/verifier-rewards-v0/v2/artifact.json` | harness validation | Synthetic reward protocol; no real RL training. |
| `artifacts/adaptive-controller-v0/v1/artifact.json` | weak evidence | No runtime integration, token costs, or learned memory writes. |
| `artifacts/portfolio-v3/v1/artifact.json` | portfolio audit | Verifies links and hashes after the strict claim-schema update; it does not upgrade any scientific claim. |

## Scientific Boundary

The following statements are supported:

- The CPU harness is deterministic for the recorded fixed seeds and commands.
- The frozen benchmark files match their generator and recorded hashes.
- The stratified control detects the constructed declared-subgroup
  regressions without rejecting the constructed valid cases.
- The strict claim schema rejects malformed declarations and blocks positive
  claims that omit subgroup metadata.
- Scripted policies expose intended contrasts between stale and current rules,
  recovery strategies, memory policies, and scheduler policies.
- Artifact output hashes can be checked without network access.

The following statements are not supported:

- A language model has demonstrated long-horizon AGI-relevant capability.
- Any symbolic probe is a neural-model result.
- CLEAR-300-v1 predicts external benchmark or leaderboard performance.
- The factorial or estimator work establishes novelty.
- A declared-subgroup check solves confounding when subgroup data is absent.
- Blocking a positive claim for missing metadata means the hidden confounding
  was detected.
- The strict schema preserves all valid discoveries; in the declared suite it
  rejects ten valid but undeclared positive claims.
- The current goal-drift, world-model, or adaptive-controller probes show a
  positive model-level effect.
- Any result is publication-ready.

## Model Gate

Model work remains on hold because no exact model artifact or download/runtime
approval is recorded and no exact cloud target has passed a model-capacity
preflight. The authoring workstation's lack of a GPU and current disk pressure
are recorded as authoring-host context only; they are not used as a proxy for
cloud execution readiness. See `MODEL-GATE.md` for the required approval and
preflight contract.

No model should be downloaded, loaded, or evaluated merely to remove this hold.
The gate is cleared only by a recorded user decision plus a measured capacity
preflight for the exact model artifact.

## Current Risks

1. **Claim inflation:** scripted success can be mistaken for model capability.
2. **Mock-environment overreach:** browser and grid-world tasks are local mocks.
3. **Weak probes:** P4, P6, and P8 currently contain negative or weak evidence.
4. **Undeclared confounding:** P5 can check effect heterogeneity only when a
   subgroup breakdown is declared; absence of that breakdown remains a
   measured blind spot.
5. **Strict-schema false negatives:** the conservative contract blocks valid
   claims that lack subgroup metadata; the observed valid-discovery cost is
   `10` cases.
6. **Authoring-host pressure:** the local workspace filesystem was about
   `95.9%` used in the earlier snapshot. This limits local staging, not cloud
   model readiness.
7. **Evaluation drift:** changing CLEAR-300-v1 in place would invalidate the
   frozen comparison and must require a new benchmark version.

## Next Engineering Order

1. Apply the strict schema to a live research-agent path without weakening the
   residual-blind-spot or false-negative labels.
2. Specify a persistent ProvMem adapter without selecting an external dataset
   or model.
3. Freeze the model-evaluation protocol against CLEAR-300-v1 while leaving the
   test split untouched.
4. Clear the model gate only after an exact artifact, license, resource plan,
   and user approval are recorded.
5. Move P4, P6, and P8 to model-level work only after the model gate passes.

## Reproduction

```bash
cd /home/liuzewen/projects/longrun-agi-20261027
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make claim-schema
python3 scripts/audit_portfolio.py
make verify
```

The audit writes:

- `artifacts/portfolio-v3/v1/results/portfolio-audit.json`
- `artifacts/portfolio-v3/v1/results/environment-audit.json`

Portfolio integrity and model readiness are separate outcomes. A passing
portfolio audit means links, documents, status fields, and output hashes agree;
it does not mean the model gate is open.
