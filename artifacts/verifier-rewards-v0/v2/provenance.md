# Provenance: verifier-rewards-v0 v2

## Scope

Preserves the P1 verifier-reward result and updates the test input hash after
review. It remains a CPU tabular synthetic protocol.

## Output

`results/rewards.json` SHA-256:
`8fb999a10deebcdcc515f8e29933263041d073c4005391f95b34770100980aa9`.

Canonical SHA-256:
`5186d73260b16fad0fa52ccaceb9703060846b2cd16752d10190d5685f5e19eb`.

## Observation

Ensemble-disagreement improves OOD success and transfer drop relative to answer
reward, but does not dominate self-verification on hacking or process reward on
ID success. Unit tests: `120 passed`.
