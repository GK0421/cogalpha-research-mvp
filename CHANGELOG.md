# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
