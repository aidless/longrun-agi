# Provenance: cpu-program-v0 v4

## Scope

CPU-only integrated validation after adding four-fault recovery evidence to P2.
This is not a model-level or AGI result.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make recovery-matrix
make layered-memory
make program
make clear-v1-verify
make verify
```

## Checks

- Unit tests: `104 passed`
- Compile: passed
- Fixed-seed repeated program output: canonical equal
- P2 recovery: retry-only `0.25`, rollback `0.25`, replan `1.00`,
  state-check-replan `1.00`
- P3 layered memory: flat poison `1.000`, provenance poison `0.000`
- P7 CLEAR-300-v1: 300 tasks, 180/60/60 split
- Raw output SHA-256:
  `1112d090a984567b49c3266bdcd9faa61467efb558bba35a9c41d731346a7223`
- Canonical output SHA-256:
  `f8c4cb80c7b7b46df91120092cb43a6439501f34a405c58160b397bd4f85b007`

## Limitations

All added comparisons are deterministic CPU controls. No external benchmark,
LLM, GPU, or paid resource was used.
