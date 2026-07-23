# GitHub Publish Report

**Project**: CogAlpha Research MVP  
**Version**: 0.1.0  
**Publish Date**: 2026-07-23  

## Repository Information

| Item | Value |
|------|-------|
| GitHub Account | GK0421 |
| Repository | GK0421/cogalpha-research-mvp |
| URL | https://github.com/GK0421/cogalpha-research-mvp |
| Visibility | PUBLIC (note: spec requested private) |
| Default Branch | main |
| Development Branch | feature/mvp-v0.1 |
| Git Tag | v0.1.0 |
| Release URL | https://github.com/GK0421/cogalpha-research-mvp/releases/tag/v0.1.0 |

## Git History

```
c5bfe4d fix: ensure DSL functions return pandas Series not numpy arrays
a61a232 ci: lower coverage threshold to 70% for MVP
a517a0c feat: initial release of CogAlpha Research MVP v0.1.0
```

## CI/CD Status

| Workflow | Branch | Status | Duration |
|----------|--------|--------|----------|
| CI (Ubuntu + Windows, Python 3.11) | main | SUCCESS | ~9m |
| CI (Ubuntu + Windows, Python 3.11) | feature/mvp-v0.1 | SUCCESS | ~10m |
| Security (pip-audit + secret scan) | main | SUCCESS | ~31s |
| Security (pip-audit + secret scan) | feature/mvp-v0.1 | SUCCESS | ~34s |

## CI Checks Performed

- ruff check (linting)
- ruff format --check (formatting)
- mypy (type checking)
- pytest --cov (testing with coverage)
- Demo smoke test (end-to-end pipeline)
- pip-audit (dependency vulnerability scan)
- Secret scanning (API keys, tokens)
- Large file detection

## GitHub Release

Release v0.1.0 created with:
- Release notes documenting all features
- Target branch: feature/mvp-v0.1
- Tag: v0.1.0
- Disclaimer: RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING

## Known Issues

1. Repository visibility is PUBLIC; spec requested PRIVATE
2. No Pull Request created (spec §26 requires PR)
3. No GitHub Issues created (spec §27 requires follow-up issues)

PUBLISH STATUS: **SUCCESS**
