"""Research portfolio backtesting engine.

RESEARCH_BACKTEST_ONLY
NO_LIVE_TRADING

This module does NOT implement:
- Order execution
- Broker connections
- Real account interfaces
- Automatic order placement
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from cogalpha_mvp.config import PortfolioConfig

logger = logging.getLogger("cogalpha_mvp")

RESEARCH_DISCLAIMER = "RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING"


@dataclass
class PortfolioResult:
    """Results of a portfolio backtest.

    Attributes:
        cumulative_return: Cumulative return series.
        annual_return: Annualized return.
        annual_volatility: Annualized volatility.
        sharpe_ratio: Sharpe ratio.
        max_drawdown: Maximum drawdown.
        calmar_ratio: Calmar ratio (annual return / max drawdown).
        turnover: Average turnover.
        total_cost: Total transaction cost.
        return_before_cost: Return before transaction costs.
        return_after_cost: Return after transaction costs.
    """

    cumulative_return: pd.Series = field(default_factory=pd.Series)
    annual_return: float = 0.0
    annual_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    turnover: float = 0.0
    total_cost: float = 0.0
    return_before_cost: float = 0.0
    return_after_cost: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary (excluding Series)."""
        return {
            "annual_return": self.annual_return,
            "annual_volatility": self.annual_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "calmar_ratio": self.calmar_ratio,
            "turnover": self.turnover,
            "total_cost": self.total_cost,
            "return_before_cost": self.return_before_cost,
            "return_after_cost": self.return_after_cost,
            "disclaimer": RESEARCH_DISCLAIMER,
        }


class BacktestEngine:
    """Research-only portfolio backtest engine.

    Supports:
    - Top/bottom quantile portfolios
    - Long-short portfolios
    - Equal-weight portfolios
    - Daily/weekly/monthly rebalancing
    - Transaction costs and slippage
    """

    def __init__(self, config: PortfolioConfig):
        self.config = config

    def run(
        self,
        factor_values: pd.DataFrame,
        market_data: pd.DataFrame,
        strategy: str = "long_short",
    ) -> PortfolioResult:
        """Run a portfolio backtest.

        Args:
            factor_values: DataFrame with [symbol, trade_date, factor_value].
            market_data: Market data with [symbol, trade_date, close].
            strategy: One of "top_quantile", "bottom_quantile", "long_short", "equal_weight".

        Returns:
            PortfolioResult with performance metrics.
        """
        logger.info("Running %s backtest (disclaimer: %s)", strategy, RESEARCH_DISCLAIMER)

        # Compute forward returns
        returns_df = market_data[["symbol", "trade_date", "close"]].copy()
        returns_df = returns_df.sort_values(["symbol", "trade_date"])
        returns_df["daily_return"] = returns_df.groupby("symbol")["close"].pct_change()

        # Merge factor with returns
        merged = factor_values.merge(
            returns_df[["symbol", "trade_date", "daily_return"]],
            on=["symbol", "trade_date"],
            how="inner",
        )

        if merged.empty:
            logger.warning("No data after merge for backtest")
            return PortfolioResult()

        # Determine rebalance dates
        rebalance_dates = self._get_rebalance_dates(merged)

        # Build portfolio weights
        weights = self._build_weights(merged, rebalance_dates, strategy)

        # Compute portfolio returns
        portfolio_returns = self._compute_returns(merged, weights)

        # Apply transaction costs
        portfolio_returns, total_cost = self._apply_costs(
            portfolio_returns, weights, rebalance_dates
        )

        # Compute metrics
        result = self._compute_metrics(portfolio_returns)
        result.total_cost = total_cost
        result.turnover = self._compute_turnover(weights, rebalance_dates)

        return result

    def _get_rebalance_dates(self, data: pd.DataFrame) -> list:
        """Get rebalance dates based on configuration."""
        dates = sorted(data["trade_date"].unique())

        if self.config.rebalance == "daily":
            return dates
        elif self.config.rebalance == "weekly":
            return dates[::5]
        elif self.config.rebalance == "monthly":
            # Approximate monthly
            return dates[::21]
        else:
            return dates

    def _build_weights(
        self,
        data: pd.DataFrame,
        rebalance_dates: list,
        strategy: str,
    ) -> pd.DataFrame:
        """Build portfolio weights for each date."""
        weight_records = []

        for date in rebalance_dates:
            date_data = data[data["trade_date"] == date].dropna(subset=["factor_value"])

            if date_data.empty:
                continue

            n = len(date_data)
            top_n = max(int(n * self.config.top_quantile), 1)
            bottom_n = max(int(n * self.config.bottom_quantile), 1)

            sorted_data = date_data.sort_values("factor_value", ascending=False)

            if strategy == "top_quantile":
                selected = sorted_data.head(top_n)
                weight = min(1.0 / top_n, self.config.max_single_weight)
                weights = {s: weight for s in selected["symbol"]}
            elif strategy == "bottom_quantile":
                selected = sorted_data.tail(bottom_n)
                weight = min(1.0 / bottom_n, self.config.max_single_weight)
                weights = {s: weight for s in selected["symbol"]}
            elif strategy == "long_short":
                top = sorted_data.head(top_n)
                bottom = sorted_data.tail(bottom_n)
                long_w = min(1.0 / top_n, self.config.max_single_weight)
                short_w = min(1.0 / bottom_n, self.config.max_single_weight)
                weights = {}
                for s in top["symbol"]:
                    weights[s] = long_w
                for s in bottom["symbol"]:
                    weights[s] = -short_w
            elif strategy == "equal_weight":
                weights = {s: 1.0 / n for s in date_data["symbol"]}
            else:
                weights = {}

            for symbol, w in weights.items():
                weight_records.append(
                    {
                        "trade_date": date,
                        "symbol": symbol,
                        "weight": w,
                    }
                )

        return pd.DataFrame(weight_records)

    def _compute_returns(
        self,
        data: pd.DataFrame,
        weights: pd.DataFrame,
    ) -> pd.Series:
        """Compute daily portfolio returns from weights."""
        if weights.empty:
            return pd.Series(dtype=float)

        merged = data.merge(weights, on=["trade_date", "symbol"], how="inner")
        merged["weighted_return"] = merged["daily_return"] * merged["weight"]

        daily_returns = merged.groupby("trade_date")["weighted_return"].sum()
        return daily_returns

    def _apply_costs(
        self,
        returns: pd.Series,
        weights: pd.DataFrame,
        rebalance_dates: list,
    ) -> tuple[pd.Series, float]:
        """Apply transaction costs and slippage."""
        cost_bps = self.config.transaction_cost_bps + self.config.slippage_bps
        cost_per_trade = cost_bps / 10000.0

        # Compute weight changes at rebalance dates
        total_cost = 0.0
        adjusted_returns = returns.copy()

        set(rebalance_dates)

        # Simple cost model: charge cost at each rebalance date
        for date in rebalance_dates:
            if date in adjusted_returns.index:
                # Estimate turnover at this date (simplified)
                date_weights = weights[weights["trade_date"] == date]
                turnover = date_weights["weight"].abs().sum()
                cost = turnover * cost_per_trade
                adjusted_returns[date] -= cost
                total_cost += cost

        return adjusted_returns, total_cost

    def _compute_turnover(self, weights: pd.DataFrame, rebalance_dates: list) -> float:
        """Compute average turnover at rebalance dates."""
        if weights.empty:
            return 0.0

        turnovers = []
        dates = sorted(weights["trade_date"].unique())

        for i in range(1, len(dates)):
            prev_w = weights[weights["trade_date"] == dates[i - 1]].set_index("symbol")["weight"]
            curr_w = weights[weights["trade_date"] == dates[i]].set_index("symbol")["weight"]

            # Align
            all_symbols = prev_w.index.union(curr_w.index)
            prev_w = prev_w.reindex(all_symbols, fill_value=0)
            curr_w = curr_w.reindex(all_symbols, fill_value=0)

            turnover = (curr_w - prev_w).abs().sum() / 2
            turnovers.append(turnover)

        return float(np.mean(turnovers)) if turnovers else 0.0

    def _compute_metrics(self, returns: pd.Series) -> PortfolioResult:
        """Compute performance metrics from daily returns."""
        if returns.empty:
            return PortfolioResult()

        cumulative = (1 + returns).cumprod() - 1

        # Annual return
        n_days = len(returns)
        if n_days > 0:
            total_return = float(cumulative.iloc[-1])
            annual_return = (1 + total_return) ** (252 / n_days) - 1
        else:
            annual_return = 0.0

        # Annual volatility
        annual_vol = float(returns.std() * np.sqrt(252))

        # Sharpe ratio
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0.0

        # Max drawdown
        cummax = cumulative.cummax()
        drawdown = cumulative - cummax
        max_dd = float(drawdown.min())

        # Calmar ratio
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0.0

        return PortfolioResult(
            cumulative_return=cumulative,
            annual_return=annual_return,
            annual_volatility=annual_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            calmar_ratio=calmar,
            return_before_cost=total_return,
            return_after_cost=float(cumulative.iloc[-1]),
        )
