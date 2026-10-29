# Provenance: layered-memory-v0 v1

## Scope

CPU-only validation of a three-layer memory substrate under synthetic
cross-session poison, expiry, supersession, and conflict events. This is not a
LongMemEval/LoCoMo result and not a model capability claim.

## Commands

```bash
cd <repository-root>
make layered-memory
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 scripts/verify_artifact.py artifacts/layered-memory-v0/v1
```

## Environment

- Python: 3.12.3
- Platform: Linux x86_64
- GPU: not used
- Network/API calls: 0

## Configuration

- Seed: `20261028`
- Episodes: `100`
- Layers: episodic, semantic, procedural
- Retrieval: flat recency vs layered provenance

## Output

`results/layered-memory.json` SHA-256:
`b229eb8497badb364717767ed96cb053a7a8dd3ebd6e71bcc1ade2050ef1715e`.

Canonical SHA-256 after removing `generated_at`:
`0b9df56fe35d24b543777eeae67a0c98dfb3e2f91891671ecf2936d892ad9f11`.

## Observations

- Flat recency poison rate: `1.000`
- Layered provenance poison rate: `0.000`
- Layered final correct rate: `1.000`
- All three layers: `100/100` correct
- Conflict cases: `34`

## Limits

The event stream is synthetic, the task size is small, and no persistent
memory service or language model was used. External benchmark integration
remains a separate gate.
