# Experiment 009 Log

## 2026-10-28: CLEAR-300-v1 freeze

Created a 300-task CPU common substrate with five filesystem, five mock-browser,
and five grid-world families. Each family has five rule variants and four
instance-level task variations. The split is fixed by variant so dev and test
rule shifts are not in train.

During development, grid tasks initially generated positions outside the grid
bounds. The generator was corrected to use a centered seven-by-seven world and
the verifier now checks the declared grid size.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 scripts/freeze_clear_v1.py \
  --output-dir benchmarks/clear-300-v1 --seed 20261028
PYTHONPATH=src python3 scripts/verify_clear_v1.py
```

## Observed checks

- Tasks: `300`
- Environments: filesystem `100`, browser `100`, gridworld `100`
- Splits: train `180`, dev `60`, test `60`
- All current-rule tasks verified: `300/300`
- Current-rule scripted success: `1.000`
- Sticky-first-rule scripted success: `0.3133`
- Sticky success by environment: filesystem `0.20`, browser `0.32`,
  gridworld `0.42`
- Frozen task canonical SHA-256:
  `a8c1c421662f67a6e447ad1beda42a057fb8c7104ff740e0ab029998634b5c22`
- `tasks.json` SHA-256:
  `8537735a7751caf4a19a48473013b889ce364aa4d1fb4608a2168a62851b5d09`
- `split-manifest.json` SHA-256:
  `cacf2a6469a6810600ff9dbdb4c4e872fcc5cfa7c6cb67eec3c73b7302f63517`
- `scripted-baselines.json` SHA-256:
  `592fb4500d0dab5386f848bfb0817f458b6be147e9e145ac6cb35b8a71f594fb`

## Interpretation

The substrate has a deterministic rule-shift contrast in all three environment
types. The browser and gridworld parts are local mocks, so this result does not
establish behavior in real browsers or game engines.
