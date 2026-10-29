# Provenance: cpu-program-v0 v8

## Scope

CPU-only integrated validation after adding the four-mode verifier reward
protocol to P1. This is not a model or GPU result.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make verifier-rewards
make program
make verify
```

## Checks

- Unit tests: `120 passed`
- Fixed-seed repeated program output: canonical equal
- P1 answer OOD success: `0.4333`
- P1 ensemble OOD success: `0.5233`
- P1 answer transfer drop: `0.3033`
- P1 ensemble transfer drop: `0.1933`
- P1 mean reasoning cost: answer `1.37`, ensemble `1.38`
- Raw output SHA-256:
  `7f56f5d0ef455699fc076ec6d026a7640974bb63a7b52f8762ca955ddbe1bd45`
- Canonical output SHA-256:
  `94fa7ac595e63c6f467485f04db32c09b51e2a5be889e58925152ac3ade4da90`

## Limit

The verifier signals and learner are synthetic. No reward mode dominates all
metrics; this is a protocol check rather than a language-model claim.
