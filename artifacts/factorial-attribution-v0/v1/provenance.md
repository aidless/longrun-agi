# Provenance: factorial-attribution-v0 v1

## Scope

CPU-only harness validation for experiment 001. This is not a scientific result
about a language model or a novelty claim.

## Environment

- Date: 2026-10-27
- Python: 3.12.3
- Platform: Linux-7.0.0-38-generic-x86_64-with-glibc2.39
- Accelerator: none
- Network/API calls during the experiment: 0
- Dependencies: Python standard library and pytest only

## Commands

```bash
cd <repository-root>
python3 -m pytest -q
make factorial
```

## Checks

- Unit tests: 16 passed.
- Python compile check: passed.
- Repeat output: identical after removing `generated_at`.
- Design: 48 tasks, all four rule/tool cells in every family.
- Scripted effects: robust 0/0/0; no-retry tool effect 1.0;
  sticky-rule rule effect 1.0; fragile rule/tool/interaction 1.0.

## Source hashes

| Input | SHA-256 |
| --- | --- |
| `src/longrun/clear/generators.py` | `a7ba45b8071d61b5db93e335a3831e8052161402d7847581fc423e06d9de6a03` |
| `src/longrun/clear/policies.py` | `ce77fb31e3b2356c8a9273a2e1ad1e6ae4ccc1e2b9342fa9ace6995f76c5142c` |
| `src/longrun/clear/runner.py` | `c449b6731a0bd392c0972a9e7a7ad0c2ff58e309d1b92f5db2a63e84d73e59ee` |
| `src/longrun/cli.py` | `ffc68bab500759043090be5c85fea973295f6d7fa143f3f0b934ce8232309e0c` |
| `tests/test_clear_policies.py` | `d0f120c1553573ab0c0d6b7def6ddf3eda327b0b03e526703b3e44624aa718c7` |

## Output hash

| Output | SHA-256 |
| --- | --- |
| `results/factorial-eval.json` | `e385307eadfe29dc2e27e8b8a928dd344fc4c360829c6aa82ec6df2d2a255168` |

## Limits

- Three synthetic file-routing families only.
- Four scripted policies, no LLM evaluation.
- The interaction estimate is defined for a balanced 2x2 design and is not a
  general causal-identification guarantee.
- The literature audit found substantial prior work on counterfactual failure
  attribution and on each individual factor; novelty remains unestablished.
- No claim is made about external validity, model capability, or publication
  readiness.
