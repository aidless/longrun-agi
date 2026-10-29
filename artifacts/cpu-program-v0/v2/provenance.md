# Provenance: cpu-program-v0 v2

## Scope

CPU-only integrated validation of project-defined P1-P8 after adding the frozen
CLEAR-300-v1 benchmark to P7. This is not a model-level or AGI result.

## Environment

- Date: 2026-10-28 UTC
- Python: 3.12.3
- Platform: Linux x86_64
- GPU: not used
- Network/API calls: 0

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make program
make clear-v1-verify
make verify
```

## Checks

- Unit tests: `91 passed`
- Compile check: passed
- Fixed-seed repeat: canonical output equal after removing `generated_at`
- CPU probes: `8/8`
- CLEAR-300-v1: 300 tasks, `180/60/60` split
- Current-rule scripted baseline: `1.000`
- Sticky-first-rule scripted baseline: `0.3133`
- Raw output SHA-256:
  `3b3307cc01ed9067ec61c8491b915d5abce7939742306d75b9c1c6a2ca356881`
- Canonical output SHA-256:
  `79f8ffe7f8155158e675549493e2bb900623aa0017f642f367033b5a3d078319`

## What changed from v1

- Added the frozen 300-task CLEAR benchmark to P7 evidence.
- Added the benchmark's automatic expected-state verifier and scripted rule
  baselines.
- Kept all symbolic/toy labels for P1, P4, P6, and P8.

## Limitations

- Browser and gridworld tasks are local mocks.
- No language model was evaluated.
- The scripted baseline contrast is a harness check, not a capability claim.
