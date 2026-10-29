# Contributing

LongRun-AGI welcomes small, evidence-backed changes. Open an issue before a large change.

## Boundaries

- Do not describe scripted or synthetic results as model capability.
- Do not access the sealed test split during development.
- Do not download or run a model, use GPU or paid API resources, or submit results without a recorded gate decision.
- Preserve failed and negative results. Never overwrite a sealed artifact; add a new version.
- Never commit credentials, private prompts, account data, or machine-specific secrets.

## Development

Use Python 3.11 or newer. Keep runtime dependencies at zero unless a proposal explains why that must change.

```bash
python -m pip install pytest==9.1.1
PYTHONPATH=src python -m pytest
python -m compileall -q src tests scripts
python scripts/audit_portfolio.py --check
make verify
```

New behavior requires a test. A pull request must explain the evidence changed, the boundary that remains, and the commands actually run.
