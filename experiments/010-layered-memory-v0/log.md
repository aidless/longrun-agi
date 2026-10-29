# Experiment 010 Log

## 2026-10-28: Layered memory CPU probe

Implemented separate episodic, semantic, and procedural memory with provenance,
trust, expiry, supersession, task validation, conflict detection, and active
forgetting.

Commands:

```bash
cd <repository-root>
make layered-memory
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
```

Configuration: seed `20261028`, 100 synthetic cross-session episodes, and three
memory layers.

Observed:

- Flat recency-only poison rate: `1.000`
- Layered provenance poison rate: `0.000`
- Layered final correct rate: `1.000`
- Layer-level correct counts: episodic `100/100`, semantic `100/100`,
  procedural `100/100`
- Conflict cases: `34`
- Raw output SHA-256:
  `b229eb8497badb364717767ed96cb053a7a8dd3ebd6e71bcc1ade2050ef1715e`
- Canonical SHA-256 after removing `generated_at`:
  `0b9df56fe35d24b543777eeae67a0c98dfb3e2f91891671ecf2936d892ad9f11`
- Repeat run: canonical output equal

The probe is synthetic. It does not evaluate LongMemEval, LoCoMo, or an LLM.
