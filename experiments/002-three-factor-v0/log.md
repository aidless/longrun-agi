# Experiment 002 Log

## 2026-10-27: Three-factor CPU prototype

Added a crossed rule-shift x tool-fault x memory-poison generator and a cached
memory policy with naive and provenance-aware modes.

## Commands

```bash
cd <repository-root>
python3 -m pytest -q
make factorial
make three-factor
```

## Result

`experiments/002-three-factor-v0/results/three-factor-eval.json` contains 96
tasks and six scripted policies. Its SHA-256 is
`ae439bfa4d5c76f6e3f6e55eb4dd8b3a8ad35fe4cbcb33f4126bafd73faae531`.

| policy | rule | tool | memory | rule x tool | three-way |
| --- | ---: | ---: | ---: | ---: | ---: |
| spec-recheck | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| spec-no-retry | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| sticky-rule | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| fragile-sticky | 0.500 | 0.500 | 0.000 | 1.000 | 0.000 |
| memory-naive | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| memory-provenance | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

The synthetic eight-cell unit test confirms that the three-way contrast is
computed from all cells. It is not a second empirical experiment.

## Interpretation

- The generator produces all eight cells without changing task size or action
  space.
- The memory factor changes action outcomes only for the naive memory policy.
- Provenance filtering removes the poisoned-note effect and falls back to the
  authoritative specification.
- No evaluated scripted policy produces a nonzero three-way interaction.
- These are harness-control observations, not model capability evidence.

## Checks

- `python3 -m pytest -q`: 20 passed.
- Python compile check: passed.
- Repeat output: identical after removing `generated_at`.
- All eight cells represented for every family.
- Local MLflow run: experiment `12`, run
  `90ca74fadc314d689fe8041d4bb2562d`; 7 evidence paths registered by hash.
- Final local MLflow run: experiment `12`, run
  `3ff9487161c447ba9229d9f6fa860057`; 8 evidence paths registered after the
  literature and artifact hashes were finalized.

## Failure and correction during development

The first implementation left `memory/routing-note.json` out of the expected
final state, so even a correct policy failed. The expected-state construction
was corrected to preserve every non-inbox file. This failure is retained here
rather than hidden.

## Next gates

- Build a policy that can jointly express rule retention, retry, and memory
  trust only if it represents a realistic agent mechanism.
- Test the same tasks with a model agent only after a separate compute and
  approval gate.
- Complete full-text related-work and venue searches before claiming novelty.

