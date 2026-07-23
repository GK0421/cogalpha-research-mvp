# CogAlpha Research MVP v0.1.0 Release Notes

## Features

- **Seven-level agent architecture** with 21 seed factors across market structure, risk, volume-price, volatility, multi-scale, stability, and geometry levels
- **Safe factor DSL** - custom AST parser and tree-walking interpreter (no exec/eval/compile)
- **Data contract** with CSV, Parquet, and synthetic data adapters
- **Train/OOS sample isolation** with SHA256 fingerprinting and leakage guard
- **9-stage quality pipeline** with time-series truncation leakage detection
- **IC, ICIR, RankIC, RankICIR** evaluation metrics
- **Qualified/elite factor classification** with configurable thresholds
- **Structural + numerical deduplication**
- **OOS validation** with decay analysis
- **Research-only portfolio backtest** with transaction costs
- **HTML/CSV/JSON report generation**
- **CLI** with doctor, init, demo, run-all commands
- **GitHub Actions CI** (Ubuntu + Windows, Python 3.11)
- **Security scanning** workflow
- **98 tests** (unit, integration, e2e) - all passing

## Installation

```bash
git clone https://github.com/GK0421/cogalpha-research-mvp.git
cd cogalpha-research-mvp
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\Activate.ps1  # Windows
pip install -e ".[dev]"
```

## Demo Command

```bash
python -m cogalpha_mvp.cli demo
```

## Data Format

Standard data contract with required fields: symbol, trade_date, open, high, low, close, volume.
Supports CSV and Parquet input. See `docs/data_contract.md` for full specification.

## Sample Isolation

- Train period: 2011-01-01 to 2019-12-31 (configurable)
- OOS period: 2020-01-01 to 2025-12-31 (configurable)
- Strictly non-overlapping, SHA256 fingerprinted, leakage-guarded

## Anti-Leakage Mechanism

- DSL parser blocks future-looking operations
- Time-series truncation test detects dynamic leakage
- 4 known bad factors all rejected
- OOS data inaccessible during training phase

## Known Limitations

- Synthetic data may not produce elite factors (honest reporting)
- No survivorship-bias-free universe snapshots
- No point-in-time fundamental data
- LLM factor generation optional (requires API key)
- pandas/numpy version compatibility tested on 2.x/1.x

## Disclaimer

RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING

This MVP is for research purposes only. It does not execute real trades, connect to
broker APIs, or make any claims about real-world profitability.
