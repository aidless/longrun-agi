# Provenance: cpu-program-v0 v1

## Scope

Integrated CPU-only validation of the project-defined P1-P8 work packages. This
does not establish model capability, AGI, external validity, or novelty. The
P1-P8 labels are not a substitute for the user's still-unspecified original
eight research points.

## Environment

- Date: 2026-10-28 UTC
- Platform: Linux 7.0.0-38-generic x86_64
- Python: 3.12.3
- Accelerator: none
- GPU: not used
- Network/API calls: 0
- Runtime dependencies: Python standard library and pytest

## Commands

```bash
cd <repository-root>
PYTHONPATH=src python3 -m pytest
python3 -m compileall src tests
make program
make verify
```

## Configuration

- Seed: `20261028`
- Estimator seed: `20261027`
- Estimator repetitions: `200`
- Estimator bootstrap replicates: `299`
- Long-run loop episodes: `200`
- Compute jobs/budget: `120` / `240`
- Compute robustness seeds: `40`
- Goal-drift episodes/steps: `100` / `50`
- World-model sequence length: `600`; held-out train fraction: `0.70`
- Q-learning episodes: `500`

## Checks

- pytest: `83 passed`
- Python compile: passed
- Fixed-seed repeat: canonical outputs equal after removing `generated_at`
- Raw artifact output hash: matches `artifact.json`
- P1/P4/P6/P8: explicitly labeled `cpu-symbolic-probe`
- P2/P3/P5/P7: labeled `implemented-v0`

## Output hashes

| Output | SHA-256 |
| --- | --- |
| `results/program.json` | `9c4aeaa05e5d8015b6333d71c07fdac85e993b09e48b7607f6574ce773a04c41` |

Canonical SHA-256 after removing `generated_at`:
`201e645d876c3985e48f1acf43b50517aa76444ac02a6cdddd959f27be5e6f5d`.

## Preserved corrections

- Goal-drift policies were initially run on separate random event streams. They
  now share the stream for each episode.
- The nominally safe scheduler initially did not skip deadline-breaking jobs.
  It now does, and its lower value is reported rather than hidden.
- Cross-family transfer initially recreated the policy per direction. It now
  retains one policy across source and target families.
- Permanent schema/missing-source faults were initially counted as successful
  because a retry changed the execution environment. They now remain failures.

## Limitations

- The world model is a symbolic context table, not a neural or learned model.
- The verifier-gap probe is a five-action toy MDP with tabular Q-learning.
- The goal-drift and compute-controller probes are synthetic controls.
- Cross-family transfer is negative under the retained routing rule; this is not
  evidence that transfer is impossible in general.
- No real model, external dataset, paid resource, account, or submission was
  used.
