# Experiment 015 Log

## 2026-10-28: Verifier reward protocol

Implemented four reward modes over the same synthetic math/code/planning task
distribution with tabular Q-learning and held-out ID/OOD evaluation.

Commands:

```bash
cd <repository-root>
make verifier-rewards
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
```

Formal seed `20261028`, 600 training episodes, 300 ID and 300 OOD evaluations.

| reward | ID success | OOD success | transfer drop | mean cost | reward hacking |
| --- | ---: | ---: | ---: | ---: | ---: |
| answer | 0.7367 | 0.4333 | 0.3033 | 1.370 | 0.1731 |
| process | 0.7800 | 0.4867 | 0.2933 | 1.553 | 0.0000 |
| self-verification | 0.7433 | 0.5267 | 0.2167 | 1.457 | 0.0507 |
| ensemble-disagreement | 0.7167 | 0.5233 | 0.1933 | 1.380 | 0.1141 |

Relative to answer reward, ensemble-disagreement improves OOD success and
reduces transfer drop. Process reward has the highest ID success but a larger
OOD drop and higher reasoning cost. Self-verification is close to the ensemble
on OOD success and has a lower hacking rate in this seed, so no reward mode is
declared dominant across success, calibration, hacking, and cost.

Raw output SHA-256:
`8fb999a10deebcdcc515f8e29933263041d073c4005391f95b34770100980aa9`.
Canonical SHA-256 after removing `generated_at`:
`5186d73260b16fad0fa52ccaceb9703060846b2cd16752d10190d5685f5e19eb`.

This is a synthetic tabular protocol, not Qwen/Llama training.
