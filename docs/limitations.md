# Known Limitations

## Not Implemented

The following features are **not implemented** in this MVP:

1. **Survivorship-bias-free universe snapshots** - No point-in-time stock universe tracking
2. **Point-in-time fundamentals** - No fundamental data with announcement-date alignment
3. **ESG factor data contract** - No ESG data integration
4. **Direct data ingestion bridges** - No direct API calls to data providers
5. **LLM-based factor generation** - Framework supports it but no API key is configured by default

## Research Limitations

1. **Synthetic Data**: Default demo uses synthetic data, not real market data
2. **Multiple Testing Bias**: No Bonferroni or FDR correction applied
3. **Data Mining Bias**: Factor selection is optimized on training data
4. **Survivorship Bias**: Results may be biased toward surviving stocks
5. **No Live Trading**: This system does NOT execute real trades

## Technical Limitations

1. **Single-threaded evaluation**: Factors are evaluated sequentially (parallel evaluation is future work)
2. **Memory-bound**: Large datasets may require chunked processing (not implemented)
3. **No real-time updates**: Batch processing only, no streaming data support

## What This MVP Does NOT Claim

- Does NOT claim any strategy has real profitability
- Does NOT claim factors will work in live trading
- Does NOT provide investment advice
- Does NOT connect to any broker or exchange
- Does NOT execute any orders

## Honest Reporting

The system is designed to report results honestly:
- If no elite factors are found, it reports zero (thresholds are NOT relaxed)
- If OOS performance is poor, it reports the decay
- All limitations are documented in the HTML report
