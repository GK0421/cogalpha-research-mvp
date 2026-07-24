# V0.2.1 PR Description

## Product Goal

Transform CogAlpha from a CLI-only tool into a local-first, browser-based
quantitative research workbench (CogAlpha Studio), with full spec compliance.

## Product Boundary

- Research-only (no live trading)
- Local-first (localhost binding)
- LLM optional (works with zero API keys)
- Zero default telemetry

## What's New in v0.2.1 (Spec Compliance Patch)

### Windows Installation Scripts (5 new)
- `scripts/install_studio.ps1` - Full installer (Python+Node+frontend)
- `scripts/start_studio.ps1` - Start with health check + browser
- `scripts/stop_studio.ps1` - Stop by PID (no process name killing)
- `scripts/reset_studio.ps1` - Reset cache (metadata needs confirmation)
- `scripts/uninstall_studio.ps1` - Uninstall (user data preserved by default)

### Docker (3 new files)
- `docker/Dockerfile.api` - Backend image (non-root, healthcheck)
- `docker/Dockerfile.web` - Frontend image (Node build -> Nginx serve)
- `.dockerignore` - Build context optimization
- `docker/nginx.conf` - SPA routing + API proxy

### CI Workflows (4 new)
- `backend-ci.yml` - Backend CI (Ubuntu+Windows, Python 3.11)
- `frontend-ci.yml` - Frontend CI (lint+typecheck+test+build)
- `e2e.yml` - E2E CI (Playwright)
- `docker.yml` - Docker build CI

### Frontend Tests (6 new test files)
- Vitest + React Testing Library setup
- Playwright E2E configuration
- Tests: App, ProjectsPage, FactorLabPage, Pages, API client, Types
- ESLint configuration
- Coverage threshold: 80%

### CLI Studio Commands (4 new)
- `studio` - Start web workbench
- `studio-status` - Check status
- `studio-stop` - Stop Studio
- `workspace-info` - Show workspace info

### Product Documentation (12 new files)
- product_overview.md, installation_windows.md, installation_docker.md
- getting_started.md, data_import_guide.md, factor_lab_guide.md
- research_run_guide.md, result_interpretation.md, llm_setup.md
- troubleshooting.md, privacy_and_security.md, product_roadmap.md

### Audit Reports (6 new files)
- V0_2_0_BUILD_REPORT.md, V0_2_0_TEST_REPORT.md
- V0_2_0_SECURITY_REPORT.md, V0_2_0_PRODUCT_AUDIT.md
- V0_2_0_GITHUB_REPORT.md, V0_2_0_PRODUCT_PR.md

### Frontend Dependencies Added
- @tanstack/react-table, react-hook-form, zod, @hookform/resolvers
- @vitest/coverage-v8, jsdom, @testing-library/react, @testing-library/jest-dom
- @testing-library/user-event, eslint-plugin-react-hooks, eslint-plugin-react-refresh
- @playwright/test

## Architecture

```
Browser (React+TS+Vite, port 5173/8080)
    |
    v
FastAPI Backend (127.0.0.1:8765)
    +-- SQLAlchemy + SQLite (WAL)
    +-- Background job manager
    +-- CogAlpha MVP core
```

## Data Security
- Localhost-only binding
- No API keys in code
- File upload security (size, extension, sanitization)
- No real data/PDF/secrets in git

## LLM Boundary
- 6 providers, all optional
- Works with zero API keys
- Graceful degradation

## Testing
- Backend: 369 tests (348 in CI), 88% coverage
- Frontend: Vitest + Playwright E2E
- CI: 6 workflows, all green

## Installation
- Windows: `scripts\install_studio.ps1 && scripts\start_studio.ps1`
- Docker: `cd docker && docker compose up`

## Known Limitations
1. SQLite only (no PostgreSQL/MySQL)
2. Single-user (no concurrent access)
3. No real-time data feeds
4. Threading-based job manager

## Rollback
- v0.2.0 tag preserved and unchanged
- `git checkout v0.2.0` to revert to previous version

Co-Authored-By: Craft Agent <agents-noreply@craft.do>
