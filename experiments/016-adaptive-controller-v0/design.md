# Experiment 016: Adaptive compute-memory controller v0

## Question

Can a contextual bandit choose among retrieve, reflect, tool, write-memory,
and stop from CLEAR-300-v1 context features while balancing success, cost, and
long-horizon stability?

This is a CPU synthetic controller probe. It does not use a language model or
real runtime resources.

## Design

The controller observes environment, a coarse variant bucket, and task family.
It chooses one of five runtime actions. Synthetic outcome probabilities depend
on environment, variant, family, action, and an active memory bonus. Fixed
policies select one action everywhere; the adaptive policy uses tabular
Q-learning with a cost penalty.

Evaluation uses the frozen dev/test task metadata and reports:

- success and cost per success;
- token and latency proxies;
- calibration error;
- five-block stability range;
- action mix and memory writes.

## Acceptance criteria

1. All five actions are available in the controller.
2. Fixed baselines and adaptive policy share the same evaluation tasks and
   outcome simulator.
3. The adaptive policy is not allowed to use the exact held-out variant label.
4. Cost, calibration, and stability are reported alongside success.
5. Weak or non-dominant adaptive behavior is retained.

## Non-goals

- No real model, API, retriever, tool, or memory service.
- No claim that token/latency proxies match real inference costs.
- No leaderboard or external validity claim.
