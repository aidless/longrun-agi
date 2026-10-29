# Provenance: cpu-program-v0 v11

## Scope

CPU-only integrated validation after adding the strict subgroup claim schema
to P5. P5 now reports `implemented-v2`, while the other symbolic/model
boundaries remain unchanged.

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
make program
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
python3 scripts/audit_portfolio.py
make verify
```

## Checks

- Unit tests: `157 passed`
- Compile check: passed
- Fixed-seed repeated full-program canonical output: equal
- CPU probes completed: `8/8`
- P5 status: `implemented-v2`
- Claim-schema cases: `110`
- Strict false discoveries: `0`
- Strict valid-discovery rate: `0.5`
- Accepted / rejected / non-evaluable: `20 / 70 / 20`
- Declared confounding detected: `10/10`
- Undeclared confounding detected: `0/10`; blocked `10/10`
- Valid but undeclared positive claims blocked: `10/10`
- GPU used: false
- External API calls: `0`
- Portfolio audit: `71/71`
- Artifact versions verified by `make verify`: `33/33`
- Scientific result: `false`
- Novelty status: `not-established`

## P5 Boundary

The 80-case research-agent probe, 90-case confounding control, and 110-case
strict schema control are separate case sets and are not pooled.

Strict gating reaches zero false discoveries in the synthetic suite because it
blocks positive claims that lack subgroup metadata. That is an enforcement
result, not evidence that hidden confounding was detected.

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | `651537061f91c1df6fa179aa3c39adb08180cfaa064b9022cccb7a80803fe699` |
| `results/program.json` | `5a4406418a4dccf823702f6e50cc97a670fbceb08aedc2d67201163436ecc401` |

Canonical output SHA-256:
`103f64aff17240a7b4adf74997cd5afe94b3dcd5fccda22aaa4253150e8d87df`

Source and benchmark hashes are recorded in `artifact.json`.

## Limitations

- All eight packages still have CPU harness or symbolic evidence only.
- P1, P4, P6, and P8 are not model-level results.
- P5 has no live research-agent evaluation.
- The strict schema does not recover subgroup metadata or causal identification.
- This artifact does not establish external validity, novelty, or publication
  readiness.
