# Provenance: recovery-v0 v2

## Scope

Preserves the recovery matrix output and updates the CLI input hash after the
research-agent CLI command was added.

## Output

`results/recovery-matrix.json` SHA-256:
`37fd761c4ac01fbfc1966711aee09f953f463b2784be95bda3017c042c55080b`.

Canonical SHA-256:
`2e58cc8c087f310782aeda5f274662417930607d61da533a4438dd5a5321e9b1`.

## Checks

- 108 tests passed.
- Replan and state-check-replan: `1.00` success.
- Retry-only and rollback: `0.25` success.

## Limits

This is the same synthetic result as v1; only provenance metadata changed.
