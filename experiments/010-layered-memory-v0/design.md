# Experiment 010: Layered memory v0

## Question

Does separating episodic, semantic, and procedural memory with source, trust,
expiry, supersession, validation, conflict detection, and active forgetting
avoid the failures of a flat recency-only memory under synthetic cross-session
conflicts?

This is a CPU-only memory-system probe, not an evaluation on LongMemEval,
LoCoMo, or any language model.

## Design

Three memory layers are stored separately:

- `episodic`: events and recent observations;
- `semantic`: durable facts;
- `procedural`: rules and procedures.

Every entry records `source`, `trust`, `observed_at`, optional `expires_at`,
optional supersession, and task-validation IDs. Retrieval is layer-specific and
prefers validated, high-trust, recent records. Conflict detection groups active
values by layer and key. Forgetting invalidates expired or low-trust entries
while preserving an auditable reason.

The probe creates 100 synthetic episodes. Each episode inserts a current
record, a newer low-trust poison record, and periodically an expired record for
each layer. It compares:

- `flat-rag`: newest entry only;
- `layered-provenance`: layer-specific trusted retrieval.

## Acceptance criteria

1. Episodic, semantic, and procedural records remain separated.
2. Low-trust and expired records are not selected above trusted current records.
3. Supersession invalidates the old record and validation is recorded.
4. Active forgetting removes expired and low-trust records from retrieval.
5. Flat recency shows poison exposure while layered provenance does not.
6. Results and layer-level metrics are deterministic for a fixed seed.

## Non-goals

- No external memory benchmark integration.
- No vector database, persistence daemon, or cross-process storage.
- No LLM or agent evaluation.
- No claim that the synthetic poison rate predicts real-world memory behavior.
