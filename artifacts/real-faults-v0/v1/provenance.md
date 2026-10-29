# Provenance: real-faults-v0 v1

## Scope

Recovery matrix over real temporary files and short-lived Python subprocesses.
It compares retry-only, rollback, state-check-replan, and replan policies
across transient process, timeout, missing specification, stale tree, and
misleading documentation faults.

It is a sandboxed recovery mechanics control, not a production-system result.

## Environment

- Execution role: cloud CPU target `ecs-hz`
- OS: Ubuntu 22.04.5 LTS; kernel `5.15.0-181-generic`
- Python: CPython 3.12.15
- Filesystem: temporary directory only
- Subprocesses: short-lived local Python workers
- GPU: none; model loaded: false; network and paid API calls: 0

## Commands

```bash
cd /root/codex-work/longrun-agi-20261027-p5-20261029
make real-faults
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
python3 scripts/audit_portfolio.py
make verify
```

## Checks

- Fault/policy pairs: `20`
- Retry-only: `0/5`
- Rollback: `4/5`
- State-check-replan: `5/5`
- Replan: `5/5`
- Fixed-seed repeated canonical output: equal
- Scientific result: `false`; novelty status: `not-established`

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | see artifact metadata |
| `results/real-faults.json` | `2f51789c0b1f5e7e3768759d497aed95f2d3250fb02f6fdfd3eb49b177908fa6` |

Canonical output SHA-256:
`28c69674e8ac490263af26a12f27fd19adf41ded4d841f505c06ea9094be6b17`

## Limitations

- No real browser or production filesystem.
- No model policy evaluation.
- No claim of general system resilience.
