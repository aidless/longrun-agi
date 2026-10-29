# Provenance: layered-memory-v0 v3

## Scope

Preserves the layered-memory result and updates provenance after the CLI gained
the research-agent command. This is still a synthetic CPU memory probe.

## Output

`results/layered-memory.json` SHA-256:
`b229eb8497badb364717767ed96cb053a7a8dd3ebd6e71bcc1ade2050ef1715e`.

Canonical SHA-256:
`0b9df56fe35d24b543777eeae67a0c98dfb3e2f91891671ecf2936d892ad9f11`.

## Checks

- 108 tests passed.
- Flat poison `1.000`; layered provenance poison `0.000`.
- All three layers `100/100` correct.

## Limits

This is the same synthetic result as v1/v2; only provenance metadata changed.
