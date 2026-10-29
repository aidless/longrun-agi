# Experiment 016 Log

## 2026-10-28: Adaptive compute-memory controller

Implemented a tabular contextual bandit over CLEAR-300-v1 context metadata.
The evaluation used 120 dev/test tasks and five blocks.

Commands:

```bash
cd <repository-root>
make adaptive-controller
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings
```

Adaptive result:

- success `0.4833`
- mean cost `1.7333`
- cost per success `3.5862`
- token proxy `211.33`
- latency proxy `153 ms`
- calibration error `0.2287`
- stability range `0.0417`
- action counts: retrieve `56`, reflect `16`, tool `40`, stop `8`,
  write-memory `0`

Fixed reflect had success `0.592` and cost `2.0`; the adaptive policy is more
stable across blocks but not better on success or cost per success. The
controller also never selected write-memory, so this is not a successful
memory-allocation result.

Raw output SHA-256:
`aa201b02cfd3910d41b45d105ee594db709f45fe080a1800b683529ce063824d`.
Canonical SHA-256 after removing `generated_at`:
`e71e375817e872781a4595ff2929cabb6f3e96e691044cb6571c78ef8d798272`.
