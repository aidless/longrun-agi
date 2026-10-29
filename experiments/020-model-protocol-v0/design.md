# Experiment 020: CLEAR-300-v1 Model Protocol Dry Run v0

## Question

Can CLEAR-300-v1 be given a stable model-facing prompt, response schema,
scoring, and failure contract before any model is downloaded or loaded, while
keeping the 60-task test split sealed?

This experiment does not evaluate a model.

## Design

The protocol uses the frozen CLEAR-300-v1 300-task split:

- dry-run subset: `240` train and dev tasks;
- sealed test subset: `60` tasks, not accessed or scored.

The prompt requires the agent to read the task and current authoritative rule
and return only JSON. The response schema permits `output`, optional
`reasoning_summary`, and optional `abstain`.

Scoring is exact output equality. Invalid JSON, schema violations, timeouts,
transport errors, and abstentions are never counted as success. Final attempts
are scored, and every attempt is retained in a real model run.

The dry run uses two deterministic fixture policies:

1. `valid-fixture` returns each task's expected output.
2. `mixed-failure-fixture` injects timeout, invalid JSON, and wrong output
   cases on deterministic indexes.

## Acceptance Criteria

1. The protocol object is deterministic and contains a SHA-256.
2. Exactly 240 train/dev tasks are dry-run and 60 test tasks remain sealed.
3. The valid fixture scores 240/240.
4. The mixed fixture records only timeout, invalid JSON, and wrong-output
   failures; no failure is counted as success.
5. No model is downloaded or loaded, and network and paid API calls are zero.
6. Output records `scientific_result=false` and
   `novelty_status=not-established`.

## Compute and Data Boundary

- Execution target: cloud CPU host.
- Model download or load: none.
- Network calls: none.
- Paid API calls: none.
- Test split access: none.

## Non-goals

- No model capability result.
- No external benchmark or leaderboard claim.
- No prompt tuning or model selection.
- No publication claim.
