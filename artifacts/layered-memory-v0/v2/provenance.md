# Provenance: layered-memory-v0 v2

## Scope

This version preserves the v1 layered-memory output and updates the source
hash after the CLI gained the recovery command. It is still a synthetic CPU
probe, not a LongMemEval/LoCoMo or model result.

## Output

`results/layered-memory.json` SHA-256:
`b229eb8497badb364717767ed96cb053a7a8dd3ebd6e71bcc1ade2050ef1715e`.

Canonical SHA-256 after removing `generated_at`:
`0b9df56fe35d24b543777eeae67a0c98dfb3e2f91891671ecf2936d892ad9f11`.

## Checks

- 104 tests passed.
- Flat poison rate: `1.000`.
- Layered provenance poison rate: `0.000`.
- Three layers each: `100/100` correct.

## Limitation

The result is unchanged from v1; only provenance metadata changed. External
memory benchmark and model-agent evaluation remain future work.
