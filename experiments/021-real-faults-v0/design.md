# Experiment 021: Real Filesystem and Process Recovery v0

## Question

Can recovery controllers be distinguished when faults occur over real
temporary files and short-lived subprocesses rather than only simulated task
objects?

This validates recovery mechanics in a sandbox; it does not evaluate a model
or real production systems.

## Design

Five real faults are injected into temporary workspaces:

| Fault | Behavior |
| --- | --- |
| `transient-process` | worker exits once with status 3 |
| `timeout` | worker sleeps beyond a policy timeout |
| `missing-spec` | specification file is removed |
| `stale-tree` | workspace gains an unseen input file |
| `misleading-doc` | documentation maps routes incorrectly |

Four policies run every fault:

1. `retry-only`: no state refresh, no restore, short timeout;
2. `rollback`: restores from checkpoint but retains stale cached state and
   non-authoritative documentation;
3. `state-check-replan`: refreshes state, restores on retry, and uses the
   authoritative manifest;
4. `replan`: same recovery rules with explicit replan counting.

All worker operations run as local subprocesses inside the temporary directory.
Each attempt is verified against the expected sorted tree.

## Acceptance Criteria

1. The matrix contains all 20 fault-policy pairs exactly once.
2. `retry-only` and `rollback` do not recover all five faults.
3. `state-check-replan` and `replan` recover all five faults.
4. Replanning policies record at least one replan.
5. No operation occurs outside the temporary sandbox.
6. Network calls and paid API calls are zero.
7. Output records `scientific_result=false`.

## Environment Boundary

- Execution target: cloud CPU host.
- Real filesystem: yes, under `TemporaryDirectory`.
- Subprocesses: yes, short-lived Python workers.
- Model: none.
- Network: none.
- GPU: none.

## Non-goals

- No real browser or production filesystem.
- No model policy evaluation.
- No claim of general system resilience.
