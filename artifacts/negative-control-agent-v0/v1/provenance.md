# Provenance: negative-control-agent-v0 v1

## Scope

CPU-only synthetic probe of a naive research-claim policy versus an
Evidence-Gate policy over 80 seeded cases. It is not a live AI-scientist
benchmark.

## Commands

```bash
cd <repository-root>
make research-agent
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
python3 scripts/verify_artifact.py artifacts/negative-control-agent-v0/v1
```

## Results

- Naive: 70 claims, 10 true, 60 false, false-discovery rate `0.8571`.
- Gated: 20 claims, 10 true, 10 false, false-discovery rate `0.5000`.
- Valid-discovery rate: `1.0000` for both.
- Confounding blind spot: 10 cases; gate did not detect them.

## Hashes

`results/research-agent.json` SHA-256:
`e97852ed4bbb226e47d3970962528fcd41fdd160d785bbb2857aa0ef4960825a`.

Canonical SHA-256 after removing `generated_at`:
`5ca82bbea3e8e8b15abec3bc0ebb40ffab71a2a69eaed9d1dcd09a5f08fb25c8`.

## Limits

The cases are synthetic and the gate is deliberately narrow. Confounding is a
reported blind spot rather than a solved control.
