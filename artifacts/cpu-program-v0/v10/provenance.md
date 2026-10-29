# Provenance: cpu-program-v0 v10

## Scope

CPU-only integrated validation after adding the stratified confounding control
to P5. The program continues to distinguish scripted harness controls and
symbolic probes from model-level evidence.

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
make program
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 -m compileall -q src tests scripts
python3 scripts/audit_portfolio.py
make verify
```

## Checks

- Unit tests: `140 passed`
- Compile check: passed
- Fixed-seed repeated full-program canonical output: equal
- CPU probes completed: `8/8`
- P5 research-agent cases: `80`
- P5 stratified confounding cases: `90`
- Declared confounding detected: `10/10`
- Undeclared confounding residual: `10` cases
- GPU used: false
- External API calls: `0`
- Portfolio audit: `65/65`
- Artifact versions verified by `make verify`: `30/30`
- Scientific result: `false`
- Novelty status: `not-established`

## P5 contrast

The original 80-case research-agent probe reduced false discoveries from
naive `60` to gated `10`. Separately, the 90-case stratified control reduced
false discoveries from naive `70` / v0-gated `20` to stratified `10`. The two
case sets are not pooled.

The stratified control raises no false alarms on the constructed valid cases,
but it cannot evaluate records that omit a subgroup breakdown.

## Hashes

| File | SHA-256 |
| --- | --- |
| `artifact.json` | `18abaf82340186a8732e5bd87af0988e14f8170c11f5d88762c19ca297ebcce1` |
| `results/program.json` | `b7d7c97715c447397d7993e57339ea501c2d580c3837d645bf61d93222264642` |

Canonical output SHA-256:
`177e091f8416b7c198698d3f34334a8924ab156482ef191ad7063a09236effdd`

Source and benchmark hashes are recorded in `artifact.json`.

## Limitations

- All eight packages still have CPU harness or symbolic evidence only.
- P1, P4, P6, and P8 are not model-level results.
- P5 has no live research-agent evaluation and no unmeasured-confounding
  sensitivity analysis.
- This artifact does not establish external validity, novelty, or publication
  readiness.
