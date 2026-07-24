# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
