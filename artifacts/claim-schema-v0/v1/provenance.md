# Provenance: claim-schema-v0 v1

## Scope

This artifact records the 110-case strict subgroup claim-schema control. It
extends the historical 90-case confounding suite with valid-but-undeclared and
malformed-declaration controls.

The artifact distinguishes three outcomes:

- `accepted`: evidence and schema are valid and the claim passes;
- `rejected`: base evidence, schema, or declared confounding fails;
- `non-evaluable`: a positive claim lacks the subgroup metadata required to
  evaluate confounding.

`non-evaluable` blocks the claim but is not a confounding detection.

## Environment

- Execution role: cloud CPU target
- Cloud alias: `ecs-hz`
- OS: Ubuntu 22.04.5 LTS
- Kernel: `5.15.0-181-generic`
- Platform: Linux x86_64
- Python: CPython 3.12.15
- Logical CPUs: 2
- GPU: none established
- Model loaded: false
- GPU job started: false
- Experiment network, external API, and paid API calls: 0

## Commands

```bash
cd /root/codex-work/longrun-agi-20261027-p5-20261029
make claim-schema
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
python3 scripts/audit_portfolio.py
make verify
```

## Checks

- Unit tests: `157 passed`
- Compile check: passed
- Cases: `110` across `11` categories
- Naive false discoveries: `80`
- v0 false discoveries: `30`
- v1 false discoveries: `20`
- Strict v2 false discoveries: `0`
- Strict decisions: accepted `20`, rejected `70`, non-evaluable `20`
- Declared confounding detected: `10/10`
- Undeclared confounding detected: `0/10`
- Undeclared confounding blocked as non-evaluable: `10/10`
- Invalid subgroup declarations rejected: `10/10`
- Valid but undeclared positive claims blocked: `10/10`
- Strict valid-discovery rate: `0.5`
- Fixed-seed repeated canonical output: equal
- Portfolio audit: `71/71`
- Artifact versions verified by `make verify`: `33/33`
- Scientific result: `false`
- Novelty status: `not-established`

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | `d8d90ec0117f19e5a6261990dd3b1055b3801b150df608c90c980245b092632e` |
| `results/claim-schema.json` | `eb3f0c2e51ea73f0786729d085effa9e9754b68be6080d3354c607f2ac9ebdac` |

Canonical output SHA-256:
`445130447acfde90587b98e810bcd39c1d7cba76838e65f2232bfa1f4e56a8d0`

Source hashes are recorded in `artifact.json`.

## Limitations

- The cases are synthetic and deliberately small.
- Strict gating eliminates false positives by rejecting both undeclared
  confounding and valid undeclared positives.
- The result does not establish live-agent behavior, external validity,
  novelty, or publication readiness.
- No causal adjustment or unmeasured-confounding sensitivity analysis is
  implemented.
