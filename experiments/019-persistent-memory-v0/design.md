# Experiment 019: Persistent Provenance Memory v0

## Question

Can the existing layered provenance memory be persisted with standard-library
SQLite while preserving restart recovery, atomic rollback, conflict detection,
expiry, supersession, forgetting, and import/export integrity?

This is a persistence-engineering probe, not LongMemEval, LoCoMo, or a model
evaluation.

## Design

The probe creates 32 synthetic route cases in a temporary SQLite database.
Each case has a trusted current value, a low-trust poison value, an expired
archive value, and an old superseded value. It then performs:

1. retrieval in a reopened database;
2. an atomic batch containing one valid write and one invalid trust value;
3. conflict detection before and after supersession;
4. export from the first store and import into an empty store;
5. active forgetting of expired and low-trust records;
6. SQLite integrity and schema-version checks.

## Storage Contract

- Engine: Python standard-library `sqlite3`, WAL mode, foreign keys enabled.
- Tables: metadata, memory records, audit events.
- Record identity: stable ordered persistent IDs.
- Invalidation: explicit reason, never physical deletion.
- Retrieval: active, non-expired records above the minimum trust threshold,
  ranked by validation, trust, observation time, and stable record ID.
- Batch writes: transactional; any invalid mutation rolls back all writes.

## Acceptance Criteria

1. Reopened retrieval is correct for all 32 cases.
2. Poison and stale selection rate is zero.
3. Conflicting active values are detected before supersession.
4. The invalid batch rolls back completely.
5. Export and import preserve record count and active state.
6. Active forgetting removes exactly the expired and low-trust records.
7. SQLite integrity check reports `ok`.
8. The probe repeats deterministically after removing `generated_at`.
9. Output records `scientific_result=false`.

## Compute and Data Boundary

- Execution target: cloud CPU host.
- Database: temporary directory; no production or user data.
- Model: none.
- Network: none.
- GPU: none.

## Non-goals

- No external memory benchmark.
- No concurrent multi-process load test.
- No semantic embedding or vector retrieval.
- No model-backed memory policy.
