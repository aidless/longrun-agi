# Provenance: portfolio-v2 v1

## Scope

Portfolio consolidation after the P5 stratified-confounding update. This
artifact checks document presence, manifest links, work-package mapping,
scientific-boundary fields, and non-self output hashes. It also records the
cloud CPU environment and separates authoring-host limits from exact-target
model-capacity preflight.

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
- Disk: about 28.02 GiB free, 28.17% used
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

- Latest portfolio selected: `portfolio-v2`
- Unit tests: `140 passed`
- Compile check: passed
- Manifest experiments: `14`
- Registered artifacts: `16`
- Work packages mapped: `8/8`
- Portfolio audit checks: `65/65`
- Non-self artifact output hashes verified by the audit: `22`
- Artifact versions verified by `make verify`: `30/30`
- Model gate: `hold`
- Scientific result: `false`
- Novelty status: `not-established`

The audit selected the latest portfolio by numeric family version and skipped
only its own two outputs for in-report hashing. `portfolio-v1` remains sealed
history and its two outputs are now checked as ordinary non-self outputs.

Model-gate hold reasons:

1. No approved model-download/runtime record is in the manifest.
2. No exact cloud model target has passed a model-capacity preflight.

The authoring workstation's GPU absence and prior disk pressure are context for
local staging only; they are not used as a proxy for cloud model readiness.

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | `539c92268f5a903c3545aab52ea518f8b296b1184ac483609639c1e696fbf84b` |
| `results/portfolio-audit.json` | `8940a3b01960c4a4e8235ed3ceffa68b7137a6201ee4cf43ae42c0e42b48543a` |
| `results/environment-audit.json` | `210d9d863a65294120e47b40672bf437b1980c508f960f50bafea2f867bd9719` |

Source hashes are recorded in `artifact.json`.

## Self-reference

The portfolio audit report includes checks of the other registered artifacts
but cannot include a stable hash of its own output. The audit therefore skips
only `portfolio-v2` output hashing and records that choice explicitly. Both
portfolio outputs are checked externally by `scripts/verify_artifact.py`
through `make verify`.

## Limitations

- The audit proves internal consistency, not scientific validity.
- It validates current source hashes for the recorded portfolio inputs but does
  not retroactively validate all historical source revisions.
- It does not establish external benchmark validity, model capability, novelty,
  publication readiness, or AGI progress.
- The environment snapshot is time-sensitive and must be refreshed for a future
  model preflight.
