# Provenance: cpu-bootstrap-v0 v1

## Scope

CPU-only harness validation for LongRun-AGI experiment 000. This is not a
scientific result about a language model.

## Environment

- Date: 2026-10-27
- Host OS: Linux
- Python: 3.12.3
- Accelerator: none
- Network/API calls: 0
- Dependencies: Python standard library and pytest only

## Commands

```bash
cd <repository-root>
python3 -m pytest
PYTHONPATH=src python3 -m longrun.cli clear-eval --instances 4 \
  --output experiments/000-clear-v0/results/clear-eval.json
PYTHONPATH=src python3 -m longrun.cli clear-faults \
  --output experiments/000-clear-v0/results/clear-faults.json
PYTHONPATH=src python3 -m longrun.cli provmem-audit --scenarios 24 \
  --output experiments/000-clear-v0/results/provmem-audit.json
PYTHONPATH=src python3 -m longrun.cli controls-audit \
  --output experiments/000-clear-v0/results/controls-audit.json
```

## Checks

- Unit tests: `11 passed in 0.04s`
- Python compile check: passed
- Repeat run: every JSON result was identical after removing `generated_at`
- CLEAR-Bench: reactive shift success `1.000`; sticky shift success `0.000`
- Fault recovery: `2/2`
- ProvMem: recency-only poison rate `1.000`; provenance-aware poison rate `0.000`
- Evidence Gate: all seven seeded control expectations matched

## Output hashes

| Output | SHA-256 |
| --- | --- |
| `results/clear-eval.json` | `6d503364c11856e782a83e0423cd7291db8edb8a43b286444127599ed1a1e831` |
| `results/clear-faults.json` | `4a57d01d5ee9fcade67e62746e314efb3ab3c6631066c9a2b155a0ff2e2b2bf1` |
| `results/controls-audit.json` | `ae70ef733d1f66b0048043c57f147d8956f59a3f22203f76225d184e55216283` |
| `results/provmem-audit.json` | `fc5021fcfebdc94272394b9c48f80eb0f84305d1191a50c547e7c37ba9b8086a` |

## Limits

- The CLEAR suite is synthetic and has only three task families.
- Both policies are scripted reference policies.
- The memory poison suite is a controlled construction.
- The Evidence Gate covers only seven deterministic controls.
- No claim is made about external validity, model capability, or publication
  readiness.
