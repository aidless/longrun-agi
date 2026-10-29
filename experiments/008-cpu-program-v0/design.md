# Experiment 008: Integrated CPU program v0

## Question

Can all eight currently defined work packages run from one reproducible CPU
program while preserving the distinction between implemented harnesses,
symbolic probes, and model-level evidence?

This is an integration and measurement-control experiment. It is not a claim
that any work package has become a complete AGI research result.

## Components

1. P1: toy verifier-gap MDP and tabular Q-learning with proxy and true rewards.
2. P2: transient and permanent fault matrix plus retry/recovery controls.
3. P3: provenance-aware memory under poison, expiry, and supersession events.
4. P4: one-step and lag-context symbolic world models, evaluated on a held-out
   stream, with a bounded planning probe.
5. P5: deterministic Evidence Gate controls and per-check ablations.
6. P6: pinned, recency, and decay goal-following policies sharing an event
   stream.
7. P7: CLEAR-Bench, second generator, factorial attribution, estimator
   validity, cross-family transfer, and long-run loop audit.
8. P8: synthetic scheduling under a hard budget, including value and deadline
   metrics and seed robustness.

## Acceptance criteria

1. All eight packages execute on CPU with no external API or GPU.
2. The program reports one status per package and does not call symbolic probes
   model-level evidence.
3. Transient tool faults are recoverable; malformed or missing specification
   faults are not counted as recovered.
4. Poison/no-provenance controls and provenance-aware controls are separated.
5. World-model evaluation uses a held-out split.
6. Goal-drift policies share the same synthetic event stream.
7. Scheduler output contains both value and deadline-miss counts; no overspend.
8. The final JSON is deterministic after removing `generated_at`, and its
   SHA-256 is recorded in the artifact.

## Non-goals

- No model download, LLM inference, GPU training, paid API, external dataset,
  submission, account change, or real scheduling of paid compute.
- No claim that P1-P8 are the user's original eight research points.
- No claim of model capability, AGI, external validity, or novelty.
