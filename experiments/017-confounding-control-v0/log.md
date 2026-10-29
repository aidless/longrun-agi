# Experiment 017 Log

## 2026-10-29: Cloud CPU formal run

All computation ran on the cloud CPU target `ecs-hz` (Ubuntu 22.04.5,
Python 3.12.15, 2 logical CPUs, no GPU). No experiment was run on the
authoring workstation.

Command:

```bash
PYTHONPATH=src python3 -m longrun.cli confounding-control \
  --output experiments/017-confounding-control-v0/results/confounding-control.json
```

Observed results:

- Cases: `90` across `9` categories.
- Naive false discoveries: `70`.
- v0 gated false discoveries: `20`.
- Stratified v1 false discoveries: `10`.
- Declared confounding detected: `10/10`.
- Undeclared confounding detected: `0/10`.
- Residual undeclared blind spot: `10` cases.
- False alarms on declared valid cases: `0`.
- Valid-discovery rate: `1.0`.

The command was run twice with a fixed configuration. After removing
`generated_at`, the canonical output was identical.

Final cloud verification passed `140` tests, `compileall`, the `65/65`
portfolio audit, and `make verify` across all `30` artifact versions.

| Value | SHA-256 |
| --- | --- |
| Raw output | `2bac106e2ac62b1b93f80f26c61773a415cc34bf8076a5a6242cd73474e4b02e` |
| Canonical output | `3cf4db0788f73a585e5d28200fca061eb4cc8fe52225acb4aff600a78cc15dc5` |

This validates the synthetic control. It does not establish that a research
agent detects confounding or that the residual blind spot is solved.
