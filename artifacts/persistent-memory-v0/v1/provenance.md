# Provenance: persistent-memory-v0 v1

## Scope

Persistent layered provenance memory implemented with standard-library SQLite.
The probe validates restart retrieval, atomic rollback, conflicts, expiry,
supersession, active forgetting, import/export, and integrity.

It is not an external memory benchmark or a model evaluation.

## Environment

- Execution role: cloud CPU target `ecs-hz`
- OS: Ubuntu 22.04.5 LTS; kernel `5.15.0-181-generic`
- Python: CPython 3.12.15
- Storage: temporary SQLite database, WAL, foreign keys
- GPU: none; model loaded: false; network and paid API calls: 0

## Commands

```bash
cd /root/codex-work/longrun-agi-20261027-p5-20261029
make persistent-memory
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
python3 scripts/audit_portfolio.py
make verify
```

## Checks

- Cases: `32`
- Records before forgetting: `160`
- Conflict detection rate: `1.0`
- Reopened retrieval correct rate: `1.0`
- Poison or stale selection rate: `0.0`
- Invalid batch rollback atomic: `true`
- Export/import records equal: `true`
- Forgotten records: `64`; active after forgetting: `64`
- SQLite integrity check: `ok`
- Fixed-seed repeated canonical output: equal
- Scientific result: `false`; novelty status: `not-established`

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | see artifact metadata |
| `results/persistent-memory.json` | `281e99021360450192d956ac959fcb8978c8095798652a2ee51b72e51caf7707` |

Canonical output SHA-256:
`e68070ec95ce87c597d37b4ec8f4ec935e0fa7fe02b8814d21777da955233890`

## Limitations

- Synthetic routes only; no LongMemEval or LoCoMo.
- No concurrent multi-process load.
- No semantic or vector retrieval.
- No model-backed memory policy.
