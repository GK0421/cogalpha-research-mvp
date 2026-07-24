# Research Run Guide

## Overview

A research run executes the full quantitative factor research pipeline:

```
Data Load -> Quality Check -> Factor Evaluation -> Dedup -> OOS Validation -> Backtest -> Report
```

## Creating a Run

1. Go to **Runs** page
2. Click **New Run**
3. Select project and dataset
4. Choose run type:
   - **Full**: Complete pipeline (quality + evaluation + OOS + backtest)
   - **Evaluate**: Quality + evaluation only (faster)
5. Click **Start**

## Pipeline Stages

| Stage | Description |
|-------|-------------|
| 1. Data loading | Load CSV/Parquet into memory |
| 2. Quality check | NaN rates, coverage, leakage detection |
| 3. Factor computation | Evaluate all factor expressions |
| 4. IC evaluation | IC, RankIC, ICIR per factor |
| 5. Deduplication | Remove correlated factors (>0.85) |
| 6. OOS validation | Out-of-sample decay analysis |
| 7. Backtest | Portfolio simulation (research-only) |
| 8. Report | HTML report generation |

## Progress Tracking

The Runs page shows real-time progress through 11 stages. Background jobs
survive crashes - interrupted runs are recovered on restart.

## Results

After completion:
- **Factor metrics**: IC, RankIC, ICIR, decay analysis
- **Portfolio results**: Sharpe, max drawdown, cumulative returns
- **HTML report**: Full visual report downloadable

## Important Notes

- Training and OOS data are strictly separated
- Time-series truncation leakage is detected and rejected
- Backtest is research-only (no live trading)
- Results include known bias disclosures
