# Provenance: portfolio-v3 v1

## Scope

Portfolio consolidation after the strict subgroup claim-schema update. The
artifact checks manifest links, documents, work-package mapping, scientific
boundaries, and non-self output hashes. It also preserves the separation
between cloud CPU execution readiness and the still-closed model gate.

This is not a model evaluation, external benchmark, novelty assessment, or
scientific result.

## Environment

- Execution role: cloud CPU target
- Cloud alias: `ecs-hz`
- OS: Ubuntu 22.04.5 LTS
- Kernel: `5.15.0-181-generic`
- Platform: Linux x86_64
- Python: CPython 3.12.15
- CPU: Intel Xeon Platinum, 2 logical CPUs
- Memory: 1,687,068,672 bytes total in the recorded audit
- Disk: about 28.01 GiB free, 28.19% used
- GPU: no NVIDIA device or `nvidia-smi` detected
- Model loaded: false
- GPU job started: false
- Network, external API, and paid API calls from the audit: 0

Available memory and disk are live values. The exact audit snapshot is in
`results/environment-audit.json`.

## Commands

```bash
cd /root/codex-work/longrun-agi-20261027-p5-20261029
python3 scripts/audit_portfolio.py
python3 scripts/audit_portfolio.py --check
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make verify
```

## Checks

- Latest portfolio selected: `portfolio-v3`
- Unit tests: `157 passed`
- Compile check: passed
- Manifest experiments: `15`
- Registered artifacts: `18`
- Work packages mapped: `8/8`
- Portfolio audit checks: `71/71`
- Non-self artifact output hashes verified by the audit: `25`
- Artifact versions verified by `make verify`: `33/33`
- Model gate: `hold`
- Scientific result: `false`
- Novelty status: `not-established`

The audit selected the latest portfolio by numeric family version and skipped
only its own two outputs for in-report hashing. The previous portfolio
artifacts remain sealed history and are checked as ordinary non-self outputs.

Model-gate hold reasons:

1. No approved model-download/runtime record is in the manifest.
2. No exact cloud model target has passed a model-capacity preflight.

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | `a6148998cb2fde1ab355b06f860d98bccb705df65ba77455e0dc6e6b9ef47905` |
| `results/portfolio-audit.json` | `6866fe905d960dbca6f6d02436098bbe9e1bb0beba1f7cebb713a237035970b5` |
| `results/environment-audit.json` | `0a8965000e2007d6142043f1111956d0d4d0c15cf595621c3d5564897d48e912` |

Source hashes are recorded in `artifact.json`.

## Self-reference

The portfolio audit report includes checks of the other registered artifacts
but cannot include a stable hash of its own output. The audit therefore skips
only `portfolio-v3` output hashing and records that choice explicitly. Both
portfolio outputs are checked externally by `scripts/verify_artifact.py`
through `make verify`.

## Limitations

- The audit proves internal consistency, not scientific validity.
- It validates current source hashes for the recorded portfolio inputs but does
  not retroactively validate every historical source revision.
- The strict schema preserves a residual undeclared-confounding blind spot and
  a measured valid-claim rejection cost.
- The environment snapshot is time-sensitive and must be refreshed for a future
  model preflight.
