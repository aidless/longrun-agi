# Experiment 000: CPU bootstrap

## Goal

Build a deterministic, dependency-light harness for four questions:

1. Does a policy re-read the current rule after a rule shift?
2. Does a policy recover from a transient tool failure?
3. Does provenance-aware memory ignore stale, expired, and low-trust records?
4. Can a deterministic gate reject deliberately invalid research evidence?

## Design

### CLEAR-Bench v0

Tasks use a virtual file system and a typed action space: `list`, `read`, `move`,
and `finish`. Three families exercise extension routing, prefix routing, and
suffix routing. Each family has three variants with the same file shape but a
different routing map in `docs/SPEC.md`.

The key contrast is:

- `ReactiveSpecPolicy`: reads `docs/SPEC.md` for every task.
- `StickySpecPolicy`: reuses the first rule it learned within a family.

If the benchmark is sensitive, the reactive policy should pass all variants and
the sticky policy should fail shifted variants. That is a harness-validation
result, not evidence about a language model.

### Fault recovery

Fault tasks inject one transient error on the first read or first move. A
retry-capable reference policy should recover; an unrecovered run should retain
the error and final failure.

### ProvMem

Synthetic sessions contain a current high-trust rule, a stale rule, an expired
record, and a low-trust poisoned note. Recency-only memory should select the
poison; provenance-aware memory should select the current trusted rule.

### Evidence Gate

Small synthetic experiment records cover split overlap, target leakage,
baseline mismatch, one-seed evidence, invalid metric bounds, and test-set reuse.
The gate is intentionally narrow and must not be described as a general
research-integrity system.

## Success criteria

- All unit tests pass on CPU.
- Reactive policy passes all clean tasks.
- Sticky policy passes base variants and fails at least one shifted variant.
- Fault recovery reports a recovered failure separately from clean success.
- Provenance policy beats recency-only memory on the synthetic poison suite.
- Evidence Gate rejects every seeded invalid control while accepting the valid
  control.

## Non-goals

- No LLM inference.
- No GPU, paid API, external dataset download, or submission.
- No claim that the synthetic benchmark is externally valid.
