# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-07-24

### Added - Spec Compliance Patch

#### Windows Installation Scripts
- `scripts/install_studio.ps1` - Full installer (checks Python/Node/Git, creates .venv, installs deps, builds frontend)
- `scripts/start_studio.ps1` - Start with port check, health check, browser open, PID tracking
- `scripts/stop_studio.ps1` - Stop by PID only (no process-name killing)
- `scripts/reset_studio.ps1` - Clear cache; metadata deletion requires explicit confirmation
- `scripts/uninstall_studio.ps1` - Remove venv/node_modules; user data preserved unless --IncludeUserData

#### Docker Separation
- `docker/Dockerfile.api` - Backend-only image (non-root user, healthcheck)
- `docker/Dockerfile.web` - Frontend-only image (Node build -> Nginx serve)
- `docker/nginx.conf` - SPA routing + API proxy
- `.dockerignore` - Build context optimization

#### CI Workflows
- `.github/workflows/backend-ci.yml` - Backend CI (Ubuntu+Windows, Python 3.11)
- `.github/workflows/frontend-ci.yml` - Frontend CI (lint+typecheck+test+build)
- `.github/workflows/e2e.yml` - E2E CI (Playwright)
- `.github/workflows/docker.yml` - Docker build CI

#### Frontend Tests
- Vitest + React Testing Library setup with jsdom
- 6 test files: App, ProjectsPage, FactorLabPage, Pages, API client, Types
- Playwright E2E: 5 tests (health, version, project CRUD, factor seed, settings)
- ESLint configuration (.eslintrc.json)
- vitest.config.ts with 80% coverage threshold
- playwright.config.ts

#### CLI Studio Commands
- `studio` - Start CogAlpha Studio web workbench (--port, --no-browser, --log-level, --workspace)
- `studio-status` - Check if Studio is running
- `studio-stop` - Stop Studio
- `workspace-info` - Show workspace directory information

#### Product Documentation (12 files)
- `docs/product/product_overview.md`
- `docs/product/installation_windows.md`
- `docs/product/installation_docker.md`
- `docs/product/getting_started.md`
- `docs/product/data_import_guide.md`
- `docs/product/factor_lab_guide.md`
- `docs/product/research_run_guide.md`
- `docs/product/result_interpretation.md`
- `docs/product/llm_setup.md`
- `docs/product/troubleshooting.md`
- `docs/product/privacy_and_security.md`
- `docs/product/product_roadmap.md`

#### Audit Reports (6 files)
- `docs/audit/V0_2_0_BUILD_REPORT.md`
- `docs/audit/V0_2_0_TEST_REPORT.md`
- `docs/audit/V0_2_0_SECURITY_REPORT.md`
- `docs/audit/V0_2_0_PRODUCT_AUDIT.md`
- `docs/audit/V0_2_0_GITHUB_REPORT.md`
- `docs/audit/V0_2_0_PRODUCT_PR.md`

#### Frontend Dependencies Added
- @tanstack/react-table, react-hook-form, zod, @hookform/resolvers
- @vitest/coverage-v8, jsdom, @testing-library/react, @testing-library/jest-dom
- @testing-library/user-event, eslint-plugin-react-hooks, eslint-plugin-react-refresh
- @playwright/test

### Changed
- docker-compose.yml updated to use separate api/web services
- apps/web/package.json version bumped to 0.2.1 with new scripts (test:coverage, test:e2e)

## [0.2.0] - 2026-07-24

### Added - CogAlpha Studio (Browser-Based Workbench)
- **FastAPI backend** with 43 API routes across 8 router modules
  - Project, Dataset, Factor, Run, Report, Settings, Health, Results endpoints
  - Pydantic schemas for request/response validation
  - Unified error handler with structured error responses
- **SQLAlchemy persistence layer** with SQLite (WAL mode)
  - 6 ORM models: Project, Dataset, FactorDefinition, ResearchRun, Artifact, AppSetting
  - 6 repository classes with full CRUD operations
  - Database migration support
- **Application services layer** (6 services)
  - ProjectService, DatasetService, FactorService, RunService, ReportService, SettingsService
- **Background job system** with persistence and recovery
  - JobManager with thread-based execution
  - JobWorker with 11-stage pipeline progress tracking
  - Interrupted run recovery on startup
- **React + TypeScript + Vite frontend** (7 pages)
  - Dashboard, Projects, Project Detail, Factor Lab, Runs, Run Detail, Settings
  - ECharts integration ready, React Query for data fetching
  - Dark theme UI with research disclaimer
- **Docker support** (multi-stage build: Node frontend + Python backend)
- **Quick start script** (scripts/studio_start.py) with dev/production modes
- **79 new backend tests** (persistence, services, API, jobs, workspace)
- Localhost-only binding by default (security)
- 21 seed factors accessible via API
- Safe DSL expression validator accessible via API
- LLM configuration endpoint (6 providers, all optional)

### Changed
- Version bumped to 0.2.0
- pyproject.toml: Added sqlalchemy, fastapi, uvicorn, python-multipart, pydantic, httpx dependencies
- Product name updated to "CogAlpha Studio" (package name remains cogalpha_mvp)

## [0.1.2] - 2026-07-24

### Changed
- Repository visibility changed from PRIVATE to PUBLIC
- Reference PDF removed from git tracking (1.6MB binary, moved to .gitignore)
  - SHA256 manifest preserved in source_manifest.json for traceability
  - Requirements extract remains in cogalpha_manual_requirements.md
- Local file paths redacted from source_manifest.json for privacy
- Author name anonymized in audit documents for public release

### Added
- LLM Integration section in README with clear optionality documentation
- iFlytek Spark (讯飞星辰) support: OpenAI-compatible API with multi-model access
  - IFLYTEK_SPARK_API_KEY, IFLYTEK_SPARK_BASE_URL, IFLYTEK_SPARK_MODEL env vars
  - Supports Spark X2, GLM-5.2, DeepSeek-V4-Pro, Kimi-K2.6, MiniMax-M2.5, Qwen3.5
  - Model ID: astron-code-latest (auto-routing)
- MINIMAX_API_KEY support in CLI doctor command and .env.example
- Enhanced .env.example with OPENAI_BASE_URL proxy support and detailed comments
- All 6 supported LLM providers listed in doctor check

### Security
- Security desensitization audit completed before public release
- No API keys, tokens, or secrets found in codebase
- No personal names, local paths, or internal identifiers in tracked files
- .mypy_cache confirmed gitignored (not tracked)
- results/ confirmed gitignored (no run artifacts committed)

## [0.1.1] - 2026-07-24

### Fixed
- Repository visibility changed from PUBLIC to PRIVATE (spec compliance)
- Coverage threshold restored from 70% to 85% in pyproject.toml (spec compliance)
- Default branch set to main (was feature/mvp-v0.1)

### Added
- Reference PDF archived at docs/reference/ with SHA256 manifest
- Comprehensive CLI tests covering all 11 commands and exit codes
- Comprehensive data adapter tests covering all 6 adapters and edge cases
- Backtest engine unit tests covering all strategy types
- Report generator and logging config unit tests
- Pipeline runner integration tests with fast synthetic data
- Advanced DSL interpreter tests covering comparisons, bool ops, and arithmetic
- Advanced quality pipeline tests covering edge cases
- Scorer tests covering score_all and classification thresholds
- Real market data end-to-end validation (A-stock daily data, 2015-2025)
- Real data test configuration (configs/real_data_test.yaml)
- 6th GitHub Issue: ESG factor data contract

### Changed
- Total test coverage increased from 72.36% to 91%+ 
- CLI coverage: 0% -> 95%
- Data adapter coverage: 37% -> 90%
- Pipeline runner coverage: 0% -> 95%
- Backtest engine coverage: 0% -> 92%
- Report generator coverage: 0% -> 89%
- DSL interpreter coverage: 72% -> 90%

### Notes
- Real data covers 2015-2025 (not 2011-2025 as originally specified)
- Date range deviation: DEVIATION_REQUIRES_AUTHOR_APPROVAL
- Real data results stored separately from synthetic data results
- v0.1.0 tag preserved and not modified

## [0.1.0] - 2026-07-23

### Added
- Seven-level agent architecture with 21 seed factors
- Safe factor DSL parser and interpreter (no exec/eval)
- Data contract with CSV, Parquet, and synthetic data adapters
- Train/OOS sample boundary isolation with SHA256 fingerprinting
- 9-stage factor quality checking pipeline
- Time-series truncation leakage detection
- IC, ICIR, RankIC, RankICIR evaluation metrics
- Qualified/elite factor classification with configurable thresholds
- Structural and numerical factor deduplication
- Out-of-sample validation with decay analysis
- Research-only portfolio backtest with transaction costs
- HTML, CSV, JSON report generation
- CLI with doctor, init, demo, run-all commands
- GitHub Actions CI (Ubuntu + Windows, Python 3.11)
- Security scanning workflow
- Comprehensive test suite (unit, integration, e2e)
- Full documentation suite (architecture, data contract, factor protocol, methodology)
