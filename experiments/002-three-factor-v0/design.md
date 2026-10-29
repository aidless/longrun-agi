# Experiment 002: Three-factor attribution v0

## Question

Can the CPU-only harness cross three environmental failure factors without
changing the core task, and can it estimate marginal effects and pairwise /
three-way interaction contrasts?

This experiment is a measurement-control check. It is not an LLM experiment
and does not establish benchmark novelty.

## Design

The generator uses the same three routing families as experiment 001 and
crosses:

- `rule_shift` in `{0, 1}`;
- `tool_fault` in `{0, 1}`;
- `memory_poison` in `{0, 1}`;
- four instances per cell.

Every task contains `memory/routing-note.json`. The clean note contains the
same routing map as the current specification, has source `docs/SPEC.md`, and
trust `0.95`. The poisoned note contains the opposite map, has source
`user-note.txt`, and trust `0.10`. The task instruction still makes the current
`docs/SPEC.md` authoritative.

Two memory policies are compared:

- `memory-naive`: accepts the newest cached note without checking provenance.
- `memory-provenance`: rejects a note unless its source is `docs/SPEC.md` and
  trust is at least `0.5`, then falls back to the current specification.

Four specification policies retain the earlier rule-shift x tool-fault
controls:

- `spec-recheck`;
- `spec-no-retry`;
- `sticky-rule`;
- `fragile-sticky`.

## Estimands

For each factor, the marginal effect is the mean success at level `0` minus the
mean success at level `1`, averaged over the other two factors. Pairwise
interactions are unnormalized difference-in-differences. The three-way
interaction is the pairwise rule x tool contrast at memory level `0` minus the
same contrast at memory level `1`.

These contrasts are descriptive for the realized balanced design. They are
not regression coefficients and do not identify arbitrary model behavior.

## Acceptance criteria

1. `3 families x 2 x 2 x 2 x 4` produces 96 tasks with all eight cells.
2. A specification-checking policy has zero effects.
3. `spec-no-retry` has a tool-fault effect of `1.0`.
4. `sticky-rule` has a rule-shift effect of `1.0`.
5. `memory-naive` has a memory-poison effect of `1.0`.
6. `memory-provenance` has zero effects.
7. A synthetic eight-cell unit test verifies the three-way contrast formula.
8. The command, configuration, output, and hash are recorded.

The absence of a nonzero three-way effect for the tested scripted policies is a
result, not a reason to fabricate one. It means this v0 has no policy that
combines all three mechanisms in a way that produces a measured three-way
interaction.

## Non-goals

- No model inference, GPU, paid API, external dataset, or submission.
- No claim that combining three previously studied factors is novel.
- No claim that a scripted-policy effect predicts LLM-agent behavior.

