# Provenance: portfolio-v1 v1

## Scope

Portfolio consolidation for the eight LongRun-AGI CPU work packages. The
artifact checks document presence, manifest links, work-package mapping,
scientific-boundary fields, and non-self output hashes. It also records the
current environment and model-gate state.

This is not a model evaluation, external benchmark, novelty assessment, or
scientific result.

## Environment

- Date: 2026-10-29 UTC
- OS: Ubuntu 24.04.5 LTS
- Kernel: `7.0.0-38-generic`
- Platform: Linux x86_64
- Python: CPython 3.12.3
- CPU: AMD Ryzen 7 5800H, 16 logical CPUs
- Memory: 14.97 GiB total in the recorded audit
- GPU: no NVIDIA device or `nvidia-smi` detected
- Workspace filesystem: about 25.22 GiB free, 95.88% used
- Model loaded: false
- GPU job started: false
- Network, external API, and paid API calls from the audit: 0

Available memory and free disk are live values. The exact audit snapshot is in
`results/environment-audit.json`.

## Commands

```bash
cd <repository-root>
python3 scripts/audit_portfolio.py
python3 scripts/audit_portfolio.py --check
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make verify
```

## Checks

- Unit tests: `129 passed`
- Compile check: passed
- Manifest experiments: `13`
- Registered artifacts: `14`
- Work packages mapped: `8/8`
- Portfolio audit checks: `59/59`
- Non-self artifact output hashes verified by the audit: `19`
- Portfolio artifact output hashes verified by `scripts/verify_artifact.py`: `2/2`
- Model gate: `hold`
- Scientific result: `false`
- Novelty status: `not-established`

Model-gate hold reasons:

1. No approved model-download/runtime record is in the manifest.
2. No usable accelerator was established by the environment audit.
3. The workspace filesystem is at least 90% used.

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | `1d4f07513ef0c700c4f3046b551d84bf6558fe64f35c6bf3c90b293dca9cbe80` |
| `results/portfolio-audit.json` | `35217aba5c561f876f9b5d60616bcd87b3e89d354f893e184b8336cbfb3774bd` |
| `results/environment-audit.json` | `b9363b691aadcd571c095ed91ca99ae5a6e6d95c06e75e50c482efbe35ee6d07` |

Source hashes are recorded in `artifact.json`.

## Self-reference

The portfolio audit report includes checks of the other registered artifacts,
but it cannot include a stable hash of its own output. The audit therefore
skips only `portfolio-v1` output hashing and records that choice explicitly.
Both portfolio outputs are checked externally by `scripts/verify_artifact.py`
through `make verify`.

## Limitations

- The audit proves internal consistency, not scientific validity.
- It does not validate historical source hashes because source files have
  evolved since earlier artifacts were created.
- It does not establish external benchmark validity, model capability,
  novelty, publication readiness, or AGI progress.
- The environment snapshot is time-sensitive and must be refreshed for a
  future model preflight.
