## Change

## Evidence affected

## Verification run

- [ ] Focused tests
- [ ] Full pytest suite
- [ ] `python -m compileall -q src tests scripts`
- [ ] `python scripts/audit_portfolio.py --check`
- [ ] `make verify`

## Boundaries

- [ ] No credential, private data, or machine-specific secret is included.
- [ ] No sealed test split was accessed during development.
- [ ] Model/GPU/API/account/publication actions are either absent or explicitly gated.
- [ ] Failed and negative results remain visible.
