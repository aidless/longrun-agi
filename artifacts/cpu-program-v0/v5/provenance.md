# Provenance: cpu-program-v0 v5

## Scope

CPU-only integrated validation after adding the 80-case negative-control
research-agent probe to P5. This is not a live research-agent or model result.

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make research-agent
make program
make verify
```

## Checks

- Unit tests: `108 passed`
- Fixed-seed repeated program output: canonical equal
- P5: 80 cases; naive false discoveries `60`; gated false discoveries `10`;
  confounding blind spot `10`
- Raw output SHA-256:
  `76c437c35f7af653bb5c89c21d9881be57492086140d3004ba0aa4fafa0510ad`
- Canonical output SHA-256:
  `de6107f1a258b0eac81a65b0ed0399cde1d60ba5e82decc5ec5d37ba43fe2667`

## Limits

The negative controls are synthetic. The confounding blind spot is explicitly
retained rather than treated as solved.
