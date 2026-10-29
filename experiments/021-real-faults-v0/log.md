# Experiment 021 Log

## 2026-10-29: Cloud CPU formal run

The real temporary-filesystem and subprocess fault matrix completed on
`ecs-hz`. Retry-only recovered `0/5`, rollback `4/5`, and both
state-check-replan and replan recovered `5/5`.

Raw output SHA-256:
`2f51789c0b1f5e7e3768759d497aed95f2d3250fb02f6fdfd3eb49b177908fa6`

Canonical output SHA-256:
`28c69674e8ac490263af26a12f27fd19adf41ded4d841f505c06ea9094be6b17`

This validates sandbox recovery mechanics only; it does not claim production
resilience or model quality.
