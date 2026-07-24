# Factor Lab Guide

## What is Factor Lab?

Factor Lab is an interactive workspace for defining, validating, and managing
quantitative factor expressions using CogAlpha's safe DSL.

## Safe DSL

The DSL uses Python's `ast` module to parse expressions. It does NOT use
`exec()`, `eval()`, or `compile()`. Only whitelisted functions and fields
are allowed.

### Whitelisted Fields

| Field | Description |
|-------|-------------|
| open | Opening price |
| high | Highest price |
| low | Lowest price |
| close | Closing price |
| volume | Trading volume |
| amount | Trading amount |

### Whitelisted Functions (26)

| Function | Description |
|----------|-------------|
| `mean(x, n)` | Rolling mean over n periods |
| `std(x, n)` | Rolling standard deviation |
| `max(x, n)` | Rolling maximum |
| `min(x, n)` | Rolling minimum |
| `sum(x, n)` | Rolling sum |
| `rank(x)` | Cross-sectional rank |
| `delay(x, n)` | Value n periods ago |
| `delta(x, n)` | Change over n periods |
| `ts_rank(x, n)` | Time-series rank |
| `corr(x, y, n)` | Rolling correlation |
| `cov(x, y, n)` | Rolling covariance |
| `log(x)` | Natural logarithm |
| `abs(x)` | Absolute value |
| `sign(x)` | Sign (-1, 0, 1) |
| ... | (26 total) |

## Example Factors

```python
# Momentum (20-day)
ts_rank(close, 20)

# Volume ratio
mean(volume, 5) / mean(volume, 20)

# Price reversal
-1 * (close - delay(close, 1)) / delay(close, 1)

# Volatility
std(close / delay(close, 1) - 1, 20)

# High-low spread
(high - low) / close
```

## 21 Seed Factors

CogAlpha includes 21 built-in factors across 7 levels:

| Level | Factors |
|-------|---------|
| L1 Price | momentum, reversal, volatility |
| L2 Volume | volume_ratio, amount_trend, turnover |
| L3 Value | pe_ratio, pb_ratio, dividend_yield |
| L4 Quality | roe, roa, gross_margin |
| L5 Growth | revenue_growth, profit_growth, eps_growth |
| L6 Sentiment | news_sentiment, analyst_rating |
| L7 Composite | multi_factor_score, risk_adjusted, sector_neutral |

## Validation

Use the Factor Lab page to validate expressions before running research.
The validator checks syntax, field names, and function names.

## LLM-Based Generation (Optional)

If an LLM API key is configured, Factor Lab can generate new factor expressions
using AI. This is entirely optional - all 21 seed factors work without any API key.
