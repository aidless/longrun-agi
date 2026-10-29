# Provenance: cpu-program-v0 v9

## Scope

CPU-only integrated validation after adding the adaptive compute-memory
contextual bandit to P8. This is not a runtime model controller.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make adaptive-controller
make program
make verify
```

## Checks

- Unit tests: `124 passed`
- Fixed-seed repeated program output: canonical equal
- Adaptive success `0.4833`, mean cost `1.7333`, stability range `0.0417`
- Adaptive action counts: retrieve 56, reflect 16, tool 40, stop 8,
  write-memory 0
- Raw output SHA-256:
  `141f86147fae57a38e32fd4dabad4f77d3ac58e8b193208a7c83921fd2bf6414`
- Canonical output SHA-256:
  `0cd8b626bff48f3a1bc639069da82cf9cf95817f94c1452bcf470ed81721a5cf`

## Limit

The adaptive controller is more stable across blocks than fixed policies but
does not beat fixed reflect on success and never selects write-memory.
