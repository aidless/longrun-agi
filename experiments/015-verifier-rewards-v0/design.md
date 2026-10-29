# Experiment 015: Verifier reward protocol v0

## Question

Under a shift from in-distribution to OOD task outcomes, which reward signal
produces the best transfer while accounting for verifier hacking and reasoning
cost?

This is a tabular synthetic protocol probe. It is not Qwen/Llama training and
does not establish real reward-hacking behavior.

## Design

Task families are math, code, and planning. Each episode exposes family,
difficulty, and a synthetic verifier bucket. The agent chooses between a
zero-cost shortcut and a two-cost reasoning action.

Four reward modes are compared:

- answer reward;
- process reward with a reasoning bonus;
- self-verification reward;
- verifier ensemble with disagreement penalty.

Tabular Q-learning is trained on in-distribution tasks and evaluated on ID and
OOD tasks with the same observable context space but lower hidden success
probabilities for shortcuts.

## Metrics

- ID and OOD success;
- ID-to-OOD transfer drop;
- Brier/ECE proxy calibration from observed context-action outcomes;
- reward-hacking rate on high-verifier shortcut failures;
- mean reasoning cost and shortcut/reasoning rates.

## Acceptance criteria

1. All four reward modes run on identical task distributions.
2. ID/OOD success, calibration, hacking, and cost are recorded.
3. A reward mode that improves OOD transfer but costs more is reported as a
   tradeoff, not a free win.
4. Weak or negative modes are retained.
5. Fixed-seed runs are deterministic.

## Non-goals

- No model, GPU, or external API.
- No real math/code/planning benchmark.
- No claim about actual verifier exploitation in a language model.
