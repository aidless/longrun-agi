# Provenance: recovery-v0 v1

## Scope

CPU-only deterministic recovery probe for stale state, transient tool errors,
misleading documentation, and environment rule changes. It is not an external
agent benchmark or a language-model result.

## Commands

```bash
cd <repository-root>
make recovery-matrix
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 scripts/verify_artifact.py artifacts/recovery-v0/v1
```

## Configuration

- 4 fault kinds;
- 10 instances per fault;
- 4 controllers;
- 40 episodes per controller.

## Output

`results/recovery-matrix.json` SHA-256:
`37fd761c4ac01fbfc1966711aee09f953f463b2784be95bda3017c042c55080b`.

Canonical SHA-256 after removing `generated_at`:
`2e58cc8c087f310782aeda5f274662417930607d61da533a4438dd5a5321e9b1`.

## Observations

- Retry-only: `0.25` success, mean 3.75 steps.
- Rollback: `0.25` success, mean 4.75 steps.
- Replan: `1.00` success, mean 4.00 steps.
- State-check-replan: `1.00` success, mean 4.50 steps.
- Human interventions: `0`.

## Limits

The probe is synthetic and only tests explicit scripted controllers. It does
not establish behavior on OSWorld, WebArena, TAU-bench, or an LLM agent.
