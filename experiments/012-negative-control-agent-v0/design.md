# Experiment 012: Negative-control research agent v0

## Question

Can a simple evidence gate reduce false research claims across a mixed set of
valid, leaky, non-reproducible, p-hacked, and confounded synthetic experiments,
and what remains outside its coverage?

This is a CPU-only synthetic research-case probe, not a live AI-scientist
benchmark and not a model evaluation.

## Design

The generator produces 80 cases, ten in each category:

- valid positive;
- valid negative;
- train/test overlap;
- target leakage;
- broken baseline;
- single-seed / p-hacking pattern;
- unreproducible reported metric;
- confounded experiment.

The naive policy claims a discovery whenever reported candidate accuracy
exceeds the reported baseline. The gated policy additionally requires the
Evidence Gate to pass. The confounded category is intentionally not detectable
by the current gate.

## Acceptance criteria

1. Exactly 80 unique cases are generated.
2. Valid positives are discovered and valid negatives are not claimed.
3. Gate rejection lowers false discoveries relative to naive claims.
4. The confounded blind spot is reported explicitly.
5. The result is deterministic.

## Non-goals

- No model or API-based research agent.
- No live experiment execution.
- No claim that the gate is a general scientific-integrity system.
