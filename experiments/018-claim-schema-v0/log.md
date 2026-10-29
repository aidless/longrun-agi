# Experiment 018 Log

## 2026-10-29: Cloud CPU formal run

All generation ran on the cloud CPU target `ecs-hz` (Ubuntu 22.04.5,
Python 3.12.15, 2 logical CPUs, no GPU). No experiment was run on the
authoring workstation.

Command:

```bash
PYTHONPATH=src python3 -m longrun.cli claim-schema \
  --output experiments/018-claim-schema-v0/results/claim-schema.json
```

Observed results:

- Cases: `110` across `11` categories.
- Naive: `100` positive claims, `80` false discoveries.
- v0 gate: `50` claims, `30` false discoveries.
- v1 confounding gate: `40` claims, `20` false discoveries.
- Strict v2: `10` claims, `0` false discoveries.
- Strict decisions: accepted `20`, rejected `70`, non-evaluable `20`.
- Declared confounding detected: `10/10`.
- Undeclared confounding detected: `0/10`; blocked as non-evaluable: `10/10`.
- Invalid subgroup declarations rejected: `10/10`.
- Valid but undeclared positive claims blocked: `10/10`.
- Strict valid-discovery rate: `0.5`.

The command was run twice with fixed configuration. After removing
`generated_at`, the canonical output was identical.

| Value | SHA-256 |
| --- | --- |
| Raw output | `eb3f0c2e51ea73f0786729d085effa9e9754b68be6080d3354c607f2ac9ebdac` |
| Canonical output | `445130447acfde90587b98e810bcd39c1d7cba76838e65f2232bfa1f4e56a8d0` |

The strict policy blocks missing metadata rather than detecting hidden
confounding. Its loss of valid undeclared discoveries is retained as a measured
cost.

Final cloud verification passed `157` tests, `compileall`, the `71/71`
portfolio audit, and `make verify` across all `33` artifact versions.
