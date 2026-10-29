# Experiment 001: Factorial attribution v0

## Question

When a long-horizon file-operation agent fails after a rule change or a
transient tool error, can a controlled 2x2 design separate the two proposed
failure factors and measure their interaction?

This experiment tests the attribution harness, not language-model capability.

## Design

The generator constructs a crossed design with three task families:

- `rule_shift` in `{0, 1}`: whether `docs/SPEC.md` uses a different routing
  map from the base rule.
- `tool_fault` in `{0, 1}`: whether the first `move` action receives one
  injected transient failure.
- four instances per cell.

Each task retains the same file shape within a family and instance. The
expected final state is computed from the rule in that task's current
`docs/SPEC.md`, not from a cached rule.

The scripted policy switch controls two mechanisms:

- `retain_rule`: reuse the previous rule within a family instead of re-reading
  the current specification for each task.
- `retry_on_error`: retry the failed action instead of aborting.

The crossed conditions are:

| label | current rule | retry |
| --- | --- | --- |
| `robust` | re-read | yes |
| `no-retry` | re-read | no |
| `sticky-rule` | retain | yes |
| `fragile` | retain | no |

## Estimands

With `S(rs, tf)` denoting success in a cell:

- rule-shift main effect:
  `((S(0,0) + S(0,1)) - (S(1,0) + S(1,1))) / 2`
- tool-fault main effect:
  `((S(0,0) + S(1,0)) - (S(0,1) + S(1,1))) / 2`
- rule x tool interaction:
  `(S(0,0) - S(1,0)) - (S(0,1) - S(1,1))`

The main effects are marginal success contrasts averaged over the other factor.
The interaction is an unnormalized difference-in-differences of the two factors.
It is not a regression coefficient and is not divided by two.

## Acceptance criteria

1. The generator emits `3 x 2 x 2 x instances` tasks with all four cells
   represented.
2. `robust` succeeds in all cells and has zero effects.
3. `no-retry` has a tool-fault effect of `1.0` while rule-shift effect is
   `0.0`.
4. `sticky-rule` has a rule-shift effect of `1.0`.
5. `fragile` has marginal rule-shift and tool-fault effects of `0.5` and an
   interaction of `1.0`.
6. The command, configuration, output, and SHA-256 hash are recorded.

Failure to meet these criteria means the attribution harness is broken; the
result must not be interpreted as evidence about an agent model.

## Non-goals

- No LLM inference, GPU, model download, paid API, or external dataset.
- No claim that this 2x2 construction is a novel benchmark or a complete
  account of long-horizon failures.
- No claim that scripted-policy effects generalize to model agents.

