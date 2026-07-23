# CogAlpha Operations Manual - Requirements Extract

**Source PDF:** CogAlpha全自动因子挖掘框架：从零部署到样本外验证的完整操作手册.pdf
**Pages:** 41
**Extracted:** 2026-07-23

## Data Format

- Minimum required fields: `open`, `high`, `low`, `close`, `volume`
- Recommended storage: Parquet or HDF5
- Time range: 2011-01-01 to 2025-12-31

## Time Range and Sample Split

- Full data: 2011-01-01 to 2025-12-31
- Training period: 2011-01-01 to 2019-12-31
- OOS test period: 2020-01-01 to 2025-12-31

## Seven-Level Architecture

1. Level 1: Market Structure & Cycle (trend, volatility, state transition)
2. Level 2: Extreme Risk & Fragility (downside, tail, liquidity)
3. Level 3: Volume-Price Dynamics (correlation, impact, anomaly)
4. Level 4: Price Volatility Behavior (momentum, reversal, clustering)
5. Level 5: Multi-scale Complexity (multiscale trend, long memory, drawdown)
6. Level 6: Stability & Regime Control (stability, regime filter, signal decay)
7. Level 7: Geometry & Fusion (candle geometry, conditional fusion, nonlinear)

## 21 Agents

Each level has 3 agents, totaling 21. Each agent has a specific financial analysis perspective.

## Five Generation Modes

| Mode | Temperature Range | Purpose |
|------|------------------|---------|
| Mild | 0.1 - 0.3 | Minimal modification, baseline |
| Moderate | 0.3 - 0.5 | Natural rephrasing |
| Creative | 0.5 - 0.7 | Explore alternative reasoning |
| Divergent | 0.7 - 0.9 | Broaden search space |
| Concrete | 0.5 - 0.7 | Quantify abstract logic |

## FactorObject Design

Each factor object contains:
- Raw code / DSL expression
- Agent ID
- Generation mode
- Quality check log
- Fitness metrics
- Status (valid/invalid/qualified/elite)

## Factor Quality Check Pipeline

Four-stage serial pipeline:
1. Code quality detection (syntax + static scan)
2. Code repair (auto-fix simple errors)
3. Semantic evaluation (logic consistency, future info check)
4. Logic enhancement (optimization, simplification)

## Time-Series Truncation Detection

1. Sample random dates T from training data
2. Prepare D_full and D_truncated (data up to T)
3. Run factor on both datasets
4. Compare factor values at date T
5. Max diff < 1e-10 and correlation ≈ 1 => no leakage

## IC, ICIR, RankIC, RankICIR

- IC: Pearson correlation between factor and next-period return
- ICIR: IC mean / IC std
- RankIC: Spearman rank correlation
- RankICIR: RankIC mean / RankIC std

## Qualified and Elite Factor Thresholds

### Qualified Factors
- Composite score >= 65th percentile
- IC >= 0.005
- ICIR >= 0.05
- RankIC >= 0.005
- RankICIR >= 0.05

### Elite Factors
- Composite score >= 80th percentile
- IC >= 0.01
- ICIR >= 0.10
- RankIC >= 0.01
- RankICIR >= 0.10

## Mutation, Crossover, Injection

- **Mutation**: Modify single factor (adjust parameters, add transforms)
- **Crossover**: Fuse two factors' core logic
- **Injection**: Periodically introduce new factors to maintain diversity

## Factor Deduplication

Two layers:
1. Structural: AST or expression hash comparison
2. Numerical: Factor value correlation (threshold configurable)

## OOS Validation

- OOS IC, ICIR, RankIC, RankICIR
- Decay ratio from train to OOS
- Sign consistency
- Annual/bull/bear/bange market grouping
- Parameter ±10% sensitivity
- Factor correlation matrix

## Robustness Checks

1. Annual/market state sub-period analysis
2. Parameter sensitivity (±10%)
3. Factor correlation and independence
4. Future info leakage re-check

## Logging, Config Snapshot, and Final Output

- All runs logged with timestamps
- Config snapshot saved for reproducibility
- Final output includes: factor library, elite factor report, performance summary, complete logs, config archive
