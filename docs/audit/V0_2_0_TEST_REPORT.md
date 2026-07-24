# V0.2.0/V0.2.1 Test Report

**Date**: 2026-07-24  
**Version**: 0.2.1  

---

## Backend Tests

### Summary

| Metric | Value |
|--------|-------|
| Total tests collected | 369 |
| Tests passed (full) | 369 |
| Tests passed (CI, not slow) | 348 |
| Tests failed | 0 |
| Coverage | 88.31% |
| Threshold | 85% |
| Duration (full) | 390s (6m30s) |
| Duration (CI, not slow) | 47s |

### Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| Unit tests | 348 | Non-slow, run in CI |
| Integration tests | 13 | Slow, run locally |
| E2E tests | 3 | Slow, run locally |
| API tests | 22 | FastAPI TestClient |
| Persistence tests | 26 | SQLAlchemy + SQLite |
| Application service tests | 20 | 6 services |
| Job system tests | 17 | Manager + Worker |
| Dataset service tests | 11 | Upload, validate, preview |
| Report/migration tests | 13 | Report paths, schema version |

### Coverage by Module

| Module | Coverage |
|--------|----------|
| persistence/models.py | 100% |
| application/project_service.py | 100% |
| application/report_service.py | 100% |
| jobs/events.py | 100% |
| jobs/models.py | 100% |
| jobs/recovery.py | 100% |
| product/workspace.py | 100% |
| domain/data_contract.py | 99% |
| application/settings_service.py | 98% |
| config.py | 94% |
| evaluation/metrics.py | 93% |
| data/adapters.py | 90% |
| factors/dsl.py | 92% |
| evaluation/dedup.py | 96% |
| evaluation/scorer.py | 93% |
| pipeline/runner.py | 85% |
| cli.py | 76% |
| quality/pipeline.py | 70% |
| **TOTAL** | **88%** |

## Frontend Tests

| Metric | Value |
|--------|-------|
| Framework | Vitest + React Testing Library |
| Test files | 6 |
| Coverage target | 80% |
| E2E framework | Playwright |
| E2E tests | 5 |

### Frontend Test Files

1. `App.test.tsx` - App rendering, navigation, disclaimer
2. `ProjectsPage.test.tsx` - Loading, empty, list, error states
3. `FactorLabPage.test.tsx` - DSL validator, seed factors, empty state
4. `Pages.test.tsx` - Runs, Dashboard, Settings page tests
5. `api.test.ts` - API client exports
6. `types.test.ts` - TypeScript type definitions

### E2E Tests (Playwright)

1. Health check
2. Version endpoint
3. Create project -> list -> delete
4. Factor seed (21 factors)
5. Settings defaults

## CI Results

| Workflow | OS | Duration | Status |
|----------|-----|----------|--------|
| Backend CI | Ubuntu 3.11 | ~10m | PASS |
| Backend CI | Windows 3.11 | ~13m | PASS |
| Frontend CI | Ubuntu Node 20 | ~2m | PASS |
| E2E CI | Ubuntu Playwright | ~5m | PASS |
| Docker CI | Ubuntu | ~5m | PASS |
| Security | Ubuntu | ~40s | PASS |

## Quality Checks

| Check | Status |
|-------|--------|
| ruff check | PASS |
| ruff format | PASS |
| mypy | PASS (0 issues) |
| pytest --cov-fail-under=85 | PASS (88%) |
| ESLint | PASS |
| TypeScript typecheck | PASS |
