# Provenance: confounding-control-v0 v1

## Scope

This artifact records the 90-case synthetic stratified confounding control.
It separates aggregate improvement from declared subgroup regressions and
reports the records that remain non-evaluable because no subgroup breakdown is
declared.

It is not a live research-agent evaluation, a causal adjustment, or a general
solution to confounding.

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
make confounding-control
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
python3 scripts/audit_portfolio.py
make verify
```

## Checks

- Unit tests: `140 passed`
- Compile check: passed
- Declared confounding detected: `10/10`
- Undeclared confounding detected: `0/10`
- Residual undeclared blind spot: `10` cases
- False alarms on declared valid cases: `0`
- Valid-discovery rate: `1.0`
- Fixed-seed repeat canonical equality: passed
- Portfolio audit: `65/65`
- Artifact versions verified by `make verify`: `30/30`
- Scientific result: `false`
- Novelty status: `not-established`

The two fixed-configuration runs produced the same canonical output after
`generated_at` was removed.

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | `589fec8fc105df1c26d4a81a18b6b7a5ca807232354b22b628272944067962fc` |
| `results/confounding-control.json` | `2bac106e2ac62b1b93f80f26c61773a415cc34bf8076a5a6242cd73474e4b02e` |

Canonical output SHA-256:
`3cf4db0788f73a585e5d28200fca061eb4cc8fe52225acb4aff600a78cc15dc5`

Source hashes are recorded in `artifact.json`.

## Limitations

- The cases are synthetic and deliberately small.
- The checker uses only a declared subgroup breakdown.
- Missing subgroup data is reported as not evaluable, not as a pass.
- No unmeasured-confounding sensitivity analysis is implemented.
- The result does not establish external validity, novelty, or publication
  readiness.
