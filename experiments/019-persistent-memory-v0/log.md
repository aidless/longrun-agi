# Experiment 019 Log

## 2026-10-29: Cloud CPU formal run

The persistent SQLite memory probe completed on `ecs-hz`. It recorded 160
records before forgetting, reopened retrieval correct rate `1.0`, poison or
stale selection rate `0.0`, atomic rollback for the invalid batch, equal
export/import counts, and SQLite integrity `ok`.

Raw output SHA-256:
`281e99021360450192d956ac959fcb8978c8095798652a2ee51b72e51caf7707`

Canonical output SHA-256:
`e68070ec95ce87c597d37b4ec8f4ec935e0fa7fe02b8814d21777da955233890`

This validates persistence engineering only; it is not LongMemEval or LoCoMo.
