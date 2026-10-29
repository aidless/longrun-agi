# Provenance: clear-300-v1 v1

## Scope

Frozen 300-task CPU benchmark substrate spanning filesystem, mock-browser, and
mock-gridworld rule shifts. This is not a model result and does not establish
benchmark novelty or external validity.

## Environment

- Date: 2026-10-28 UTC
- Python: 3.12.3
- Platform: Linux x86_64
- GPU: not used
- Network/API calls: 0

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 scripts/freeze_clear_v1.py \
  --output-dir benchmarks/clear-300-v1 --seed 20261028
PYTHONPATH=src python3 scripts/verify_clear_v1.py
PYTHONPATH=src python3 -m pytest
make verify
```

## Design

- 15 families: 5 filesystem, 5 mock-browser, 5 mock-gridworld.
- 5 rule variants per family and 4 instances per variant.
- 100 tasks per environment and 300 total.
- Train uses variants 0-2; dev uses variant 3; test uses variant 4.
- Split: train 180, dev 60, test 60.

## Checks

- Unique task IDs: `300`
- Current-rule verifier: `300/300`
- Frozen generator match: passed
- Frozen manifest match: passed
- Current-rule scripted success: `1.000`
- Sticky-first-rule scripted success: `0.3133`

## Hashes

| Output | SHA-256 |
| --- | --- |
| `tasks.json` | `8537735a7751caf4a19a48473013b889ce364aa4d1fb4608a2168a62851b5d09` |
| `split-manifest.json` | `cacf2a6469a6810600ff9dbdb4c4e872fcc5cfa7c6cb67eec3c73b7302f63517` |
| `scripted-baselines.json` | `592fb4500d0dab5386f848bfb0817f458b6be147e9e145ac6cb35b8a71f594fb` |

Canonical task-list SHA-256:
`a8c1c421662f67a6e447ad1beda42a057fb8c7104ff740e0ab029998634b5c22`.

## Preserved correction

An early grid generator allowed current-rule paths to leave the grid. The
generator was changed to a centered seven-by-seven world, and the verifier now
checks the declared grid size. No invalid task was used in this artifact.

## Limitations

The browser and gridworld environments are local mocks. Real browser, game, or
model agents have not been evaluated. The baseline contrast is scripted and may
not predict model behavior.
