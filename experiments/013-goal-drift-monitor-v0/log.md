# Experiment 013 Log

## 2026-10-28: Synthetic goal-drift monitor

Implemented a held-out synthetic trajectory monitor over pinned, recency, and
decay policies. A logistic-regression monitor used observable state features,
not model activations.

Commands:

```bash
cd <repository-root>
make goal-drift-monitor
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
```

Observed:

- AUROC: `0.8295`
- evaluated steps: `1440`
- drift episodes in test: `24`
- mean warning lead: `0.0`
- early-warning rate before drift: `0.0`
- false-alarm rate: `0.0833`
- intervention rate: `0.6944`
- intervention recovery rate: `0.36`
- baseline final correct rate: `0.5556`
- monitored final correct rate: `0.5556`

The monitor ranks some synthetic drift risk but does not provide useful
pre-drift warning in this construction, and checkpoint intervention did not
improve final correctness. This is a retained weak/negative result.

Raw output SHA-256:
`b3fc68e4ae7980241d26260f106a456652651b50926f3106c970d7bc4c1b283d`.
Canonical SHA-256 after removing `generated_at`:
`43fbf0424f78bd0e392835bab769c48d646c7745bf5aefc58a19f83426afdaa2`.
