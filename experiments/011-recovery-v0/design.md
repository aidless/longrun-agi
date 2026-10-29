# Experiment 011: Failure recovery v0

## Question

Do stale state, transient tool errors, misleading documentation, and
environment rule changes require different recovery actions, and which
scripted controller recovers without human intervention?

This is a deterministic CPU recovery-state probe. It is not OSWorld, WebArena,
TAU-bench, or a language-model experiment.

## Design

Four fault kinds are injected into a small recovery state machine:

- `stale_state`: the observed rule is older than the authoritative rule;
- `tool_error`: the first action fails transiently;
- `misleading_doc`: the visible documentation is stale until replanning;
- `rule_change`: the environment changes after the initial read.

Four controllers are compared:

- `retry-only`: repeat the action;
- `rollback`: restore a checkpoint and retry;
- `replan`: refresh the authoritative state and act again;
- `state-check-replan`: validate state, replan when stale, then act.

Each fault has ten deterministic instances, giving 40 task episodes per
controller and 160 total episodes.

## Acceptance criteria

1. Retry-only recovers the transient tool error and fails the other three.
2. Rollback does not substitute for authoritative state refresh.
3. Replan recovers all four fault kinds with zero human interventions.
4. State-check-replan recovers all four and records its extra replanning cost.
5. Every episode respects the declared step bound.
6. The run is deterministic and includes step, recovery, rollback, and human
   intervention metrics.

## Non-goals

- No real OS, browser, or tool environment.
- No model agent or external benchmark.
- No claim that replanning wins in every real environment.
