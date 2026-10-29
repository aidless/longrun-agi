# Provenance: cpu-program-v0 v3

## Scope

CPU-only integrated validation after adding three-layer memory evidence to P3.
This is not a model-level or AGI result.

## Environment

- Python: 3.12.3
- Platform: Linux x86_64
- GPU: not used
- Network/API calls: 0

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
make layered-memory
make program
make clear-v1-verify
make verify
```

## Checks

- Unit tests: `98 passed`
- Compile: passed
- Fixed-seed repeated program output: canonical equal
- Layered memory: 3 layers, flat poison `1.000`, provenance poison `0.000`
- CLEAR-300-v1: 300 tasks, current-rule `1.000`, sticky `0.3133`
- Raw output SHA-256:
  `c6c7bc318f300caf2482688e51bcae1cad8e3428f7fc5ef413786c52e44d6bfe`
- Canonical output SHA-256:
  `eb626873c12b8e55f59b14c19e9b18d46051cb769f8a9d747e14ef1b76aa1b94`

## Limitations

The memory probe is synthetic; no LongMemEval/LoCoMo, persistent vector store,
LLM, GPU, or external API was used.
