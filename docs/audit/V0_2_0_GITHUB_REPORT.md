# V0.2.0/V0.2.1 GitHub Report

**Date**: 2026-07-24  
**Version**: 0.2.1  

---

## Repository

| Field | Value |
|-------|-------|
| Repository | `GK0421/cogalpha-research-mvp` |
| Visibility | PUBLIC |
| Default branch | `main` |
| Current commit | (v0.2.1 HEAD) |

## Tags

| Tag | Commit | Release |
|-----|--------|---------|
| v0.1.0 | 86cc118 | CogAlpha Research MVP v0.1.0 |
| v0.1.1 | bee0f80 | v0.1.1 - Acceptance Deviation Fixes |
| v0.1.2 | cc2f4bf | v0.1.2 - Public Release |
| v0.2.0 | a9fad4f | CogAlpha Studio v0.2.0 |
| v0.2.1 | (new) | CogAlpha Studio v0.2.1 - Spec Compliance Patch |

## Pull Requests

| PR | Title | Status |
|----|-------|--------|
| #6 | feat: deliver CogAlpha Research MVP v0.1.0 | MERGED |
| #8 | fix(v0.1.1): Acceptance deviation fixes | MERGED |
| #9 | release(v0.1.2): Public repo, security, optional LLM | MERGED |
| #10 | feat: CogAlpha Studio v0.2.0 | MERGED |
| #11 | fix(v0.2.1): Spec compliance - scripts, Docker, CI, tests, docs | (this PR) |

## Issues

| # | Title | Status |
|---|-------|--------|
| 1 | feat: add direct a-stock-data ingestion bridge | OPEN |
| 2 | feat: add global-stock-data market normalization | OPEN |
| 3 | feat: evaluate optional Vibe-Trading integration | OPEN |
| 4 | data: add point-in-time fundamentals | OPEN |
| 5 | research: add survivorship-bias-free snapshots | OPEN |
| 7 | research: add ESG factor data contract | OPEN |

## CI Workflows

| Workflow | File | Status |
|----------|------|--------|
| Backend CI | backend-ci.yml | PASS (Ubuntu + Windows) |
| Frontend CI | frontend-ci.yml | PASS |
| E2E CI | e2e.yml | PASS |
| Docker CI | docker.yml | PASS |
| Security | security.yml | PASS |
| Legacy CI | ci.yml | PASS (deprecated, replaced by backend-ci) |

## Release Contents

v0.2.1 Release does NOT include:
- PDF files
- Real market data
- API keys
- .env files
- Local configurations
- Private run results
- Commercial data

## Verification

```bash
# Clone and verify
git clone https://github.com/GK0421/cogalpha-research-mvp.git
cd cogalpha-research-mvp
git tag -l  # Should show v0.1.0 through v0.2.1
gh release view v0.2.1
```
