# Experiment 001 Log

## 2026-10-27: CPU-only factorial attribution prototype

Added a crossed rule-shift x tool-fault generator and a configurable scripted
policy. This is an attribution-harness check, not a model experiment.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -q
make factorial
```

## Result

The command produced `experiments/001-factorial-v0/results/factorial-eval.json`
with SHA-256
`73de0279c64f9a0cb1124762c6da67c4fb07a79d67ec96056412872cc04f89aa`.

The design contains 48 tasks: three families x two rule-shift levels x two
tool-fault levels x four instances.

| policy | rule-shift effect | tool-fault effect | interaction |
| --- | ---: | ---: | ---: |
| robust | 0.000 | 0.000 | 0.000 |
| no-retry | 0.000 | 1.000 | 0.000 |
| sticky-rule | 1.000 | 0.000 | 0.000 |
| fragile | 0.500 | 0.500 | 1.000 |

## Interpretation

- The factorial harness passes its expected scripted contrasts.
- `no-retry` isolates the injected tool-fault failure path.
- `sticky-rule` isolates the stale-rule failure path.
- `fragile` shows both marginal effects and the constructed interaction.
- These numbers demonstrate experimental control only. They do not establish
  language-model behavior, external validity, or novelty.

## Checks

- `python3 -m pytest -q`: 20 passed.
- Python compile check: passed.
- The factorial output contains all four cells for every family.
- The output is deterministic after removing `generated_at`.

## Next gates

- Add a memory-poison factor only if that factor can be shown to change action
  outcomes rather than merely changing a side table.
- Preserve a separate clean development split before any model comparison.
- Complete a targeted related-work check before making a novelty claim.

