# Research Methodology

## IC (Information Coefficient)

Pearson correlation between factor values and forward returns, computed cross-sectionally
per trading date, then averaged across dates.

```
IC_t = corr(factor_t, return_{t+1})
IC_mean = mean(IC_t for all t)
```

## RankIC

Spearman rank correlation between factor values and forward returns.

```
RankIC_t = spearmanr(factor_t, return_{t+1})
RankIC_mean = mean(RankIC_t for all t)
```

## ICIR (IC Information Ratio)

```
ICIR = IC_mean / IC_std
```

## RankICIR

```
RankICIR = RankIC_mean / RankIC_std
```

## Factor Direction

Factor direction (+1 or -1) is determined during the training phase. The OOS phase uses
the same direction determined during training. Direction is NOT re-optimized on OOS data.

## Missing Value Handling

- Factor values that are NaN are excluded from cross-sectional IC computation
- If fewer than 5 valid observations exist for a date, IC is NaN for that date
- Forward returns that are NaN are excluded

## Stock Universe Filtering

Interfaces are provided for filtering:
- ST/*ST stocks
- Limit up/down stocks
- New listings (< 1 year)
- Suspended stocks

## Transaction Costs

Default costs:
- Transaction cost: 10 bps
- Slippage: 5 bps
- Total round-trip: ~30 bps

## Future Information Leakage Prevention

### Static Check
Pattern matching for forbidden operations (negative shift, future references, etc.)

### Dynamic Check (Time-Series Truncation)
For random dates T:
1. Run factor on full data D_full
2. Truncate data to T, run factor on D_truncated
3. Compare factor values at date T
4. Max absolute difference must be < 1e-10
5. Correlation must be > 0.9999

## Survivorship Bias

**Current status: Not fully addressed.**

The MVP does not implement point-in-time survivorship-bias-free universe snapshots.
This is a known limitation. Users should be aware that results may be biased
toward stocks that survived the entire test period.

## Multiple Testing Risk

With 21+ factors tested, multiple testing bias is present. The MVP does not
apply Bonferroni correction or FDR control. This is a known limitation.

## Data Mining Bias

The factor selection process (IC thresholds, composite scores) is optimized
on training data. OOS validation helps detect overfitting but cannot
eliminate it entirely.
