# Original Eight AGI Research Points

This file maps the eight research points supplied by the user to the current
LongRun-AGI work packages. It records what is already implemented, the next
concrete deliverable, and the main resource gate. The goal is to make the
one-person, CPU-first execution order explicit without overstating maturity.

## P1 — Verifier-Gap RL

**User question:** Does the model learn reasoning, or learn to fool the
verifier? Can ability transfer when the verifier is absent at deployment?

**Current state:** A five-action toy MDP and tabular Q-learning probe show a
proxy/true reward gap. A second CPU protocol compares answer, process,
self-verification, and ensemble-disagreement rewards on synthetic ID/OOD tasks.
Ensemble reward improves OOD transfer over answer reward but does not dominate
all metrics.

**Next deliverable:** Port the four reward modes to a small reproducible
open-weight model setup and evaluate real math/code/planning tasks.

**Main gate:** Requires a 4B–8B open-weight model, GPU access, and a clear
training/evaluation split. The current protocol is tabular synthetic control.

## P2 — FailRecover Agent

**User question:** Is the main long-horizon bottleneck now failure recovery
rather than initial planning?

**Current state:** The repo already has:

- transient read/list/move faults;
- permanent schema corruption and missing-source faults;
- retry vs no-retry controls;
- stale state, tool error, misleading documentation, and rule-change probes;
- retry-only, rollback, replan, and state-check-replan controllers;
- recovery-rate metrics.

**Next deliverable:** Port the four-fault controller protocol into OSWorld,
WebArena, or TAU-bench task wrappers and evaluate a model policy.

**Main gate:** External environments and a model agent are required; the local
CPU controller matrix is already testable.

## P3 — ProvMem

**User question:** Is source-aware, conflict-resolving, forgetting-aware memory
better than plain vector RAG for cross-session tasks?

**Current state:** The repo already has:

- provenance metadata;
- trust and expiry;
- supersession and invalidation;
- episodic / semantic / procedural layers;
- conflict detection, task validation, and active forgetting;
- poison, stale, and adversarial memory events;
- source-trust vs recency-only controls.

**Next deliverable:** Add a persistent memory service and run the same conflict
protocol on LongMemEval or LoCoMo.

**Main gate:** External cross-session benchmarks and a model agent require an
approved dataset/model setup. The synthetic CPU substrate is already testable.

## P4 — Calibrated World Model

**User question:** Is planning value driven more by calibrated uncertainty than
by reconstruction quality?

**Current state:** A symbolic lag-context world model has held-out accuracy,
ensemble uncertainty, Brier/ECE, OOD calibration, counterfactual consistency,
rollout drift, and a bounded planning probe. In v0, uncertainty separated
unseen states but did not rank OOD errors or improve planning.

**Next deliverable:** Port the same uncertainty/planning protocol to a small
learned model on MiniHack or Crafter.

**Main gate:** A learned latent world model needs GPU training and an explicit
compute approval. The current version is symbolic, not neural.

## P5 — Negative-Control Research Agent

**User question:** Can an AI scientist detect invalid experiments rather than
produce plausible false conclusions?

**Current state:** The repo has an Evidence Gate with seven deterministic
controls, per-check ablations, an 80-case synthetic research-agent probe, and
a 90-case stratified confounding control. A strict claim schema v2 now blocks
positive improvement claims without a complete subgroup declaration. It marks
missing declarations as `non-evaluable`, rather than claiming that confounding
was detected.

In the 110-case schema suite, the strict policy has `0` false discoveries,
detects `10/10` declared confounding cases, blocks `10/10` undeclared
confounding cases as non-evaluable, and blocks `10/10` valid but undeclared
positive claims. The resulting valid-discovery rate is `0.5`; that conservative
cost is part of the evidence.

**Next deliverable:** Apply the schema to a live research-agent path over
small-ML tasks without accepting model-level evidence before the model gate.

**Main gate:** Current gate detects split leakage, target leakage, broken
baselines, single-seed evidence, unreproducibility, declared subgroup
regressions, and malformed or missing subgroup schemas. Undeclared confounding
remains undetectable in this record-only design; strict policy blocks such
positive claims instead of treating them as passes. A model-backed agent
requires separate access.

## P6 — Goal-Drift Probe

**User question:** Does internal goal drift appear before the final output
fails?

**Current state:** A shared-event-stream goal-drift probe compares pinned,
recency, and decay policies. A held-out synthetic logistic monitor is now
implemented, but its early-warning rate is zero and checkpoint intervention did
not improve final correctness in the current construction.

**Next deliverable:** Move the same trajectory labels and monitoring protocol
to linear probes or SAE features on a small open-weight model.

**Main gate:** Requires activation access and a 4B–8B model. The current monitor
is a weak synthetic control, not an interpretability result.

## P7 — CLEAR-Bench

**User question:** Can the same agent adapt after rules change, rather than
memorize the original task?

**Current state:** The repo already has:

- paired rule-shift tasks;
- a frozen 300-task split across filesystem, mock-browser, and grid-world;
- a second independent generator;
- factorial and three-factor attribution;
- strict estimator validity checks;
- cross-family transfer;
- long-run trace and resume audit.

**Next deliverable:** Connect the mock browser and grid-world tasks to real
engines, then freeze a model-evaluation protocol on CLEAR-300-v1.

**Main gate:** Browser and grid-world environments need additional
engineering; model agents need explicit compute approval.

## P8 — Adaptive Compute-Memory Controller

**User question:** Can a small controller decide when to retrieve, reflect,
call a tool, write memory, or stop?

**Current state:** A synthetic scheduler compares FIFO, shortest-job,
value-density, and safe-value-density policies under a hard budget. A
contextual bandit also chooses among retrieve/reflect/tool/write-memory/stop on
CLEAR-300 contexts, but it does not beat fixed reflect and never writes memory
in v0.

**Next deliverable:** Add real cost instrumentation and evaluate a model-backed
controller with strong fixed-action and oracle baselines.

**Main gate:** Needs a frozen 4B/8B model, real tool/retriever integration, and
explicit runtime cost accounting. The current version is a simulation.

## Recommended one-person execution order

1. **P7 CLEAR-Bench first.** It is the shared substrate for P2, P3, P5, P6,
   and P8.
2. **P3 ProvMem second.** It is high-leverage, low-compute, and directly
   extends P7.
3. **P2 FailRecover third.** It reuses P7 tasks and adds the recovery layer.
4. **P5 Negative-Control Research Agent fourth.** It builds on P7/P3 and gives
   the project a clear differentiation story.
5. **P6 Goal-Drift fifth.** Move to model-level probes after the task and trace
   substrate is stable.
6. **P4 Calibrated World Model sixth.** Start with symbolic calibration, then
   add a small learned model.
7. **P1 Verifier-Gap RL seventh.** This needs a real model and training loop;
   do not spend GPU before the benchmark substrate is stable.
8. **P8 Adaptive Compute-Memory Controller last.** It depends on the other
   components and has the strongest baseline competition.

## Current boundary

The repository currently has CPU harnesses and symbolic probes for all eight
points. It does **not** yet have:

- a real language-model evaluation;
- a trained world model;
- activation-level interpretability;
- a production runtime controller;
- external benchmark or leaderboard results;
- a publication-ready claim.

Those remain explicitly gated.

`PORTFOLIO-STATUS.md` records the current maturity matrix and claim boundary.
`MODEL-GATE.md` records the approval and preflight contract that must pass
before any model download, load, or evaluation.
