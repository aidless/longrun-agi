# Provenance: model-protocol-v0 v1

## Scope

Frozen model-facing evaluation protocol for CLEAR-300-v1 and a model-free
train/dev dry run using deterministic fixtures. The 60-task test split remains
sealed and is not accessed.

No model is downloaded or loaded.

## Environment

- Execution role: cloud CPU target `ecs-hz`
- OS: Ubuntu 22.04.5 LTS; kernel `5.15.0-181-generic`
- Python: CPython 3.12.15
- Model downloaded: false; model loaded: false
- GPU: none; network calls: 0; paid API calls: 0

## Commands

```bash
cd /root/codex-work/longrun-agi-20261027-p5-20261029
make model-protocol
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
python3 scripts/audit_portfolio.py
make verify
```

## Checks

- Protocol ID: `clear-v1-model-eval-v1`
- Protocol SHA-256: `1916f54b2d1a870c850bb2be7f7badae1f1e4193849635497c5f83297cd76655`
- Dry-run tasks: `240`
- Sealed test tasks: `60`
- Valid fixture: `240/240` success
- Mixed fixture: `203/240` success
- Injected failures: timeout `13`, invalid JSON `14`, wrong output `10`
- Test split accessed: `false`
- Fixed-seed repeated canonical output: equal
- Scientific result: `false`; novelty status: `not-established`

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | see artifact metadata |
| `results/model-protocol.json` | `94220f8c4f073e32e0d65ee6338da6eb66df91e70f357391fc5d3a877dfdba66` |

Canonical output SHA-256:
`bed43ac805ec30f43589c9e5f7a0fcb5f032a08f84fbc6303a887a09743b93dd`

## Limitations

- Fixture outputs are not model outputs.
- No model capability or leaderboard claim.
- Prompt tuning and model selection are out of scope.
- The frozen test split must not be accessed before a separately approved model
  run.
