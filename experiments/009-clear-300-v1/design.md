# Experiment 009: CLEAR-300-v1 frozen common substrate

## Question

Can CLEAR-Bench provide a deterministic, automatically verifiable 300-task
substrate shared by filesystem, mock-browser, and grid-world rule-change tasks
without leaking the held-out rule variants into training?

This is benchmark construction and harness validation. It is not a language
model evaluation and does not establish benchmark novelty or leaderboard
quality.

## Design

The generator contains 15 families:

- five filesystem routing families;
- five deterministic mock-browser families;
- five deterministic grid-world families.

Each family has five rule variants and four content instances. Therefore each
environment contributes `5 x 5 x 4 = 100` tasks, for 300 total.

The split is fixed by rule variant:

- variants 0, 1, and 2: `train`;
- variant 3: `dev`;
- variant 4: `test`.

This yields 180 train, 60 dev, and 60 test tasks. The split is balanced across
all environments and families. Test variants are never included in train.

Every task contains its current rule and an exact expected final state. The
verifier compares the produced final state with the declared expected state.
No model or external service is needed to verify the substrate.

## Baselines

Two deterministic scripted baselines are frozen with the task data:

- `current-rule`: read and apply each task's current rule;
- `sticky-first-rule`: reuse the first rule observed in that family.

These baselines check that the benchmark has a rule-shift contrast. They are
not model baselines and must not be reported as agent capability.

## Acceptance criteria

1. Exactly 300 task IDs exist and all are unique.
2. Each environment contributes 100 tasks.
3. Split counts are exactly train 180, dev 60, test 60.
4. Every task has a valid current-rule solution and expected-state verifier.
5. The `current-rule` baseline succeeds on all tasks.
6. The `sticky-first-rule` baseline fails on shifted variants in every
   environment.
7. Frozen task JSON regenerates byte-for-byte from the generator and seed.
8. Task and split SHA-256 values are stored in the frozen manifest and artifact.

## Non-goals

- Browser and grid-world environments are local deterministic mocks, not
  Playwright, WebArena, MiniHack, or Crafter.
- No LLM or open-weight model is evaluated.
- No leaderboard, external-validity, novelty, or publication claim is made.
- No task file in the frozen directory may be edited in place. Create v2 for
  any change.
