# feat: deliver CogAlpha Research MVP v0.1.0

## Build Objective

Build a reproducible, leakage-aware quantitative factor research MVP for A-share research,
following the detailed specification and the 41-page CogAlpha operations manual.

## Core Modules

- **Domain Layer**: Data contract (StandardMarketData), sample boundary (Train/OOS isolation with SHA256 fingerprinting)
- **Data Layer**: 6 adapters (LocalCSV, LocalParquet, Synthetic, AStockDataExport, GlobalStockDataExport, VibeTradingExport)
- **Factor Layer**: Safe DSL parser (AST-based, no exec/eval), 26 whitelisted functions, 21 seed factors across 7 levels
- **Quality Layer**: 9-stage serial pipeline with time-series truncation leakage detection
- **Evaluation Layer**: IC/ICIR/RankIC/RankICIR metrics, qualified/elite classification, structural + numerical dedup
- **Portfolio Layer**: Research-only backtest (top/bottom quantile, long-short, equal-weight) with transaction costs
- **Reporting Layer**: HTML/CSV/JSON report generation
- **Pipeline Layer**: 11-step orchestrator with full reproducibility

## Data Isolation

- Train/OOS dates are strictly non-overlapping
- SHA256 fingerprints for both train and OOS data
- LeakageGuard prevents OOS access during training phase
- OOS uses train-determined factor directions and parameters

## Anti-Future-Leakage

- DSL parser blocks: negative shifts, future references, imports, attribute chains
- Time-series truncation test: compares full vs truncated factor values at random dates
- 4 known bad factors (bad_negative_shift, bad_future_global_mean, bad_full_sample_normalization, bad_last_row_reference) all rejected

## Tests

- 98 tests (91 unit + 4 integration + 3 e2e) - ALL PASS
- Coverage: 72.3%
- Numeric assertions for IC, RankIC, ICIR, turnover
- ruff check + ruff format + mypy all pass

## Demo

```bash
python -m cogalpha_mvp.cli demo
```

Runs full pipeline with synthetic data: data generation -> quality check -> evaluation -> dedup -> OOS -> backtest -> report.

## Unimplemented Scope

- LLM-based factor generation (seed factors work without API key)
- Direct a-stock-data ingestion (export adapter exists, direct bridge is future work)
- Point-in-time fundamental data
- Survivorship-bias-free universe snapshots

## Risks

- Synthetic data may not produce elite factors (honest reporting, no threshold relaxation)
- pandas/numpy version compatibility (fixed for 2.x, may need updates for future versions)
- Windows encoding (fixed Unicode issues, but console codepage varies)

## Reproduction

```powershell
git clone https://github.com/GK0421/cogalpha-research-mvp.git
cd cogalpha-research-mvp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m cogalpha_mvp.cli demo
python -m pytest tests/ -v
```
