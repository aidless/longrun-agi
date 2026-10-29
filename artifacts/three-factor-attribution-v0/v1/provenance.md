# Provenance: three-factor-attribution-v0 v1

## Scope

CPU-only harness validation. This is not a scientific result about a language model and does not establish novelty.

## Environment

- Python: 3.12.3
- Platform: Linux-7.0.0-38-generic-x86_64-with-glibc2.39
- Accelerator: none
- Network/API calls during the experiment: 0
- Dependencies: Python standard library and pytest only

## Commands

```bash
cd <repository-root>
python3 -m pytest -q
make three-factor
python3 scripts/verify_artifact.py artifacts/three-factor-attribution-v0/v1
```

## Source hashes

| Input | SHA-256 |
| --- | --- |
| `src/longrun/clear/generators.py` | `76b3a9a208a85308e688a6c280b414bd4271393c51f76c29cc659bf4e15d9776` |
| `src/longrun/clear/policies.py` | `d125f15e4f6fa3a98ec1f0044d2e188d62980d96919ce17b3c200a21a3e956d4` |
| `src/longrun/clear/runner.py` | `0d5f5ba392677b4b176e7acaa5759aa3fa3b8dde13896c7858481cb4c5cee645` |
| `src/longrun/cli.py` | `b11446e9da38772e51dd4a9feccf81174228b45f1627422335f03f210861e64b` |
| `tests/test_clear_policies.py` | `157ea1fc996713daa6db6069389415241997b0384abd4c64ba1772cb0c36ff08` |
| `literature/search_20261027.md` | `9980818e82205f0f40c003f6b4299f113ba9d52d3fe46e188185b715255b2a7a` |
| `literature/arxiv_verified_20261027.json` | `c7c75426cb8202c02598a9392492e936b914bafa05203d3beae28940271760d0` |

## Output hash

| Output | SHA-256 |
| --- | --- |
| `results/three-factor-eval.json` | `ae439bfa4d5c76f6e3f6e55eb4dd8b3a8ad35fe4cbcb33f4126bafd73faae531` |

## Checks

- pytest: 20 passed
- normalized_repeat_equal: True
- compile_check: passed
- all_eight_cells_per_family: True
- synthetic_three_way_estimator_test: passed

## Notes

- No evaluated scripted policy produced a nonzero three-way interaction.
- Memory-poison effects are policy-dependent; provenance-aware memory falls back to the spec.
- This v0 does not establish novelty for combining three already-studied factors.
- Literature metadata and search log hashes are included in the artifact inputs.

## Limits

- Synthetic routing families only; no LLM evaluation.
- Scripted-policy effects validate experimental control, not model capability.
- The related-work search found substantial prior work on each factor and on counterfactual/factorial agent evaluation; novelty remains unestablished.
