# recovery-matrix v1

Frozen input for the one closed headline result.

- Tasks: `tasks.json`, 40 tasks (4 fault kinds × 10 identical instances).
- Traces: `artifacts/recovery-v0/v2/results/recovery-matrix.json` key `rows` (160 scripted-controller episodes).
- Replay: `make check` runs the scripted policies on `tasks.json` and requires the episode outcomes to match those rows.
- Controllers are fixed action lists in `src/longrun/clear/recovery.py`. They are not LLM agents.

`release-commit.txt` records `v0.1.0`, which the Research OS pages cite. It is a repository tag, not a model result.
