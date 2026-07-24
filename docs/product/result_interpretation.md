# Result Interpretation

## Factor Quality Tiers

| Tier | IC (abs) | ICIR (abs) | Description |
|------|----------|------------|-------------|
| Elite | >= 0.05 | >= 0.5 | Strong predictive power |
| Qualified | >= 0.03 | >= 0.3 | Moderate predictive power |
| Rejected | < 0.03 | < 0.3 | Insufficient predictive power |

## IC (Information Coefficient)

IC measures the correlation between factor values and forward returns.

- **IC > 0**: Factor positively predicts returns
- **IC < 0**: Factor negatively predicts returns
- **|IC| > 0.05**: Generally considered meaningful

## RankIC

RankIC uses Spearman rank correlation, which is more robust to outliers.

## ICIR (IC Information Ratio)

ICIR = mean(IC) / std(IC). Measures consistency of IC over time.

- **ICIR > 0.5**: Good consistency
- **ICIR > 1.0**: Excellent consistency

## OOS Validation

Out-of-sample validation tests whether factor performance persists beyond
the training period.

Key metrics:
- **Decay**: How quickly IC degrades over time
- **Sign consistency**: Whether IC direction remains stable
- **OOS IC**: IC computed on out-of-sample data

## Backtest Results

| Metric | Description |
|--------|-------------|
| Sharpe ratio | Risk-adjusted return |
| Max drawdown | Largest peak-to-trough decline |
| Cumulative return | Total return over period |
| Win rate | Percentage of profitable periods |

## Known Biases

Results should be interpreted with these biases in mind:

1. **Survivorship bias**: Delisted stocks may be excluded
2. **Multiple testing bias**: Testing many factors increases false positives
3. **Data mining bias**: Over-fitting to historical data
4. **Look-ahead bias**: Mitigated by truncation leakage detection

## Disclaimer

All results are for research purposes only. Past performance does not
guarantee future results. This is NOT a trading system.
