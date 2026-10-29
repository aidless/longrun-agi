# Experiment Log

## 2026-10-27

- Initialized the CPU-only workspace.
- Chose a dependency-light Python harness because no `research_init` tool is
  exposed in this session; the manifest was initialized from the local schema
  and will be treated as provisional until checked.
- Added CLEAR-Bench v0, fault injection, ProvMem, and deterministic Evidence
  Gate.
- Added tests that separate harness validation from model evidence.

## Verification

- `python3 -m pytest`: 11 passed.
- Python compile check: passed.
- All CLI outputs were repeated; normalized JSON was identical after removing
  `generated_at`.
- CLEAR-Bench: 36 tasks; reactive shift success 1.000, sticky shift success
  0.000.
- Fault recovery: 2/2.
- ProvMem: recency-only poison rate 1.000; provenance-aware poison rate 0.000.
- Evidence Gate: all 7 seeded expectations matched.
- Artifact: `artifacts/cpu-bootstrap-v0/v1`.
- Local MLflow: experiment `longrun-agi-cpu-bootstrap` (id `12`), run
  `e16a8b9efa2f49e9844a992c05d1f02a`; 6 evidence files indexed by hash.
