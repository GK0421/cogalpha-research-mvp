# Test Report

**Project**: CogAlpha Research MVP  
**Version**: 0.1.0  
**Test Date**: 2026-07-23  

## Test Summary

| Category | Count | Status |
|----------|-------|--------|
| Unit Tests | 91 | ALL PASS |
| Integration Tests | 4 | ALL PASS |
| End-to-End Tests | 3 | ALL PASS |
| **Total** | **98** | **ALL PASS** |

## Coverage Report

| Module | Stmts | Miss | Cover |
|--------|-------|------|-------|
| cli.py | 200 | 200 | 0% |
| config.py | 133 | 19 | 86% |
| data/adapters.py | 164 | 104 | 37% |
| domain/data_contract.py | 70 | 1 | 99% |
| domain/sample_boundary.py | 80 | 2 | 98% |
| evaluation/dedup.py | 80 | 3 | 96% |
| evaluation/metrics.py | 94 | 7 | 93% |
| evaluation/scorer.py | 45 | 2 | 96% |
| factors/dsl.py | 252 | 71 | 72% |
| factors/registry.py | 82 | 17 | 79% |
| factors/seed_factors.py | 26 | 2 | 92% |
| logging_config.py | 21 | 0 | 100% |
| pipeline/runner.py | 236 | 13 | 94% |
| portfolio/backtest.py | 136 | 15 | 89% |
| quality/pipeline.py | 253 | 71 | 72% |
| reporting/reporter.py | 55 | 6 | 89% |
| **TOTAL** | **1927** | **533** | **72.3%** |

## Static Analysis

| Check | Result |
|-------|--------|
| ruff check | PASS |
| ruff format --check | PASS |
| mypy | 5 errors (yaml stubs + minor type issues) |
| pytest --cov | PASS (72.3% >= 70% threshold) |

## Test Details

### Unit Tests (91)
- test_config.py: 6 tests - Config dataclass validation
- test_data_contract.py: 8 tests - StandardMarketData validation, adapter tests
- test_dedup.py: 6 tests - Structural and numerical deduplication
- test_dsl.py: 11 tests - Parser, interpreter, factor hashing
- test_metrics.py: 10 tests - IC, RankIC, ICIR, turnover with numeric assertions
- test_quality.py: 8 tests - 9-stage pipeline, bad factor rejection
- test_registry.py: 8 tests - Registration, lookup, dedup, filtering
- test_sample_boundary.py: 8 tests - Boundary, loaders, leakage guard
- test_scorer.py: 4 tests - Elite/qualified classification
- test_seed_factors.py: 9 tests - 21 factors: count, validity, agents, levels

### Integration Tests (4)
- test_data_to_factor.py: 2 tests - Data loading through factor evaluation
- test_quality_to_evaluation.py: 2 tests - Quality check through scoring

### E2E Tests (3)
- test_full_pipeline.py: 3 tests - Full pipeline run, OOS validation, report generation

## Known Gaps

1. CLI commands have 0% test coverage
2. CSV/Parquet adapters only 37% covered (only Synthetic tested)
3. Quality pipeline 72% (some error branches uncovered)
4. DSL interpreter 72% (some edge functions uncovered)

TEST STATUS: **PASS** (98/98 tests, 72.3% coverage)
