# V0.2.0/V0.2.1 Build Report

**Date**: 2026-07-24  
**Version**: 0.2.1 (patch over v0.2.0)  
**Branch**: `feat/cogalpha-studio-v0.2.1`  

---

## Build Summary

### Phase 1: Architecture & Persistence
- SQLAlchemy ORM (6 models, 6 repositories)
- Application services (6 services)
- Background job system (JobManager, JobWorker, recovery)
- Workspace manager (~/.cogalpha/)

### Phase 2: API & Jobs
- FastAPI with 43 routes across 8 routers
- Pydantic v2 schemas (14 models)
- Localhost-only binding (127.0.0.1:8765)
- CORS restricted to localhost origins

### Phase 3: Frontend
- React 18 + TypeScript + Vite
- 7 pages: Dashboard, Projects, Project Detail, Factor Lab, Runs, Run Detail, Settings
- Dark theme with RESEARCH_BACKTEST_ONLY disclaimer
- TanStack Query + Axios API client
- ECharts, TanStack Table, React Hook Form, Zod

### Phase 4: Install & Docker
- Windows scripts: install, start, stop, reset, uninstall (5 scripts)
- Docker: Dockerfile.api, Dockerfile.web, docker-compose.yml, nginx.conf, .dockerignore
- Non-root Docker user, health checks, volume persistence
- CLI studio commands: studio, studio-status, studio-stop, workspace-info

### Phase 5: Tests & Docs
- Backend: 348 unit tests (88% coverage)
- Frontend: Vitest + React Testing Library + Playwright E2E
- CI: 6 workflows (backend-ci, frontend-ci, e2e, docker, security, legacy ci)
- Product docs: 12 files in docs/product/
- Audit reports: 6 files (this + 5 others)

## File Counts

| Category | Count |
|----------|-------|
| Python source (src/) | 6,642 LOC |
| Python tests (tests/) | 5,255 LOC |
| API (apps/api/) | 848 LOC |
| Frontend (apps/web/) | 1,696 LOC |
| PowerShell scripts | 5 new |
| Docker files | 5 new |
| CI workflows | 4 new |
| Product docs | 12 new |
| Audit reports | 6 new |

## Build Verification

```text
ruff check:    PASS
ruff format:   PASS
mypy:          PASS (0 issues in 22 source files)
pytest:        348 passed, 88% coverage
```
