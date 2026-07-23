"""Factor evaluation metrics: IC, ICIR, RankIC, RankICIR.

All metrics are computed cross-sectionally per trading date,
then aggregated across dates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("cogalpha_mvp")


@dataclass
class FactorMetrics:
    """Metrics for a single factor.

    Attributes:
        factor_id: Factor identifier.
        ic_mean: Mean Information Coefficient.
        ic_std: Standard deviation of IC.
        icir: IC Information Ratio (ic_mean / ic_std).
        rankic_mean: Mean Rank IC.
        rankic_std: Standard deviation of Rank IC.
        rankicir: Rank IC Information Ratio.
        n_valid_dates: Number of dates with valid IC computation.
        positive_ic_ratio: Fraction of dates with positive IC.
        coverage: Factor coverage ratio (non-NaN fraction).
        turnover: Average daily turnover.
        composite_score: Composite percentile score.
    """

    factor_id: str = ""
    ic_mean: float = 0.0
    ic_std: float = 0.0
    icir: float = 0.0
    rankic_mean: float = 0.0
    rankic_std: float = 0.0
    rankicir: float = 0.0
    n_valid_dates: int = 0
    positive_ic_ratio: float = 0.0
    coverage: float = 0.0
    turnover: float = 0.0
    composite_score: float = 0.0
    # Annualized versions (for reporting)
    raw_icir: float = 0.0
    annualized_icir: float = 0.0
    raw_rank_icir: float = 0.0
    annualized_rank_icir: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "factor_id": self.factor_id,
            "ic_mean": self.ic_mean,
            "ic_std": self.ic_std,
            "icir": self.icir,
            "rankic_mean": self.rankic_mean,
            "rankic_std": self.rankic_std,
            "rankicir": self.rankicir,
            "n_valid_dates": self.n_valid_dates,
            "positive_ic_ratio": self.positive_ic_ratio,
            "coverage": self.coverage,
            "turnover": self.turnover,
            "composite_score": self.composite_score,
            "raw_icir": self.raw_icir,
            "annualized_icir": self.annualized_icir,
            "raw_rank_icir": self.raw_rank_icir,
            "annualized_rank_icir": self.annualized_rank_icir,
        }


def compute_next_returns(data: pd.DataFrame, period: int = 1) -> pd.Series:
    """Compute forward returns for each symbol.

    Args:
        data: Market data with columns [symbol, trade_date, close].
        period: Forward period in days.

    Returns:
        Series of forward returns indexed same as data.
    """
    data = data.sort_values(["symbol", "trade_date"]).copy()
    data["next_return"] = data.groupby("symbol")["close"].pct_change(periods=period).shift(-period)
    return data["next_return"]


def compute_ic(factor_values: pd.Series, forward_returns: pd.Series) -> float:
    """Compute Pearson IC (Information Coefficient).

    Args:
        factor_values: Cross-sectional factor values for one date.
        forward_returns: Corresponding forward returns.

    Returns:
        Pearson correlation coefficient.
    """
    valid = factor_values.notna() & forward_returns.notna()
    if valid.sum() < 5:
        return np.nan
    return float(factor_values[valid].corr(forward_returns[valid]))


def compute_rank_ic(factor_values: pd.Series, forward_returns: pd.Series) -> float:
    """Compute Spearman Rank IC.

    Args:
        factor_values: Cross-sectional factor values for one date.
        forward_returns: Corresponding forward returns.

    Returns:
        Spearman rank correlation coefficient.
    """
    valid = factor_values.notna() & forward_returns.notna()
    if valid.sum() < 5:
        return np.nan
    return float(stats.spearmanr(factor_values[valid], forward_returns[valid]).correlation)


def compute_icir(ic_series: pd.Series) -> float:
    """Compute ICIR (IC Information Ratio).

    Args:
        ic_series: Series of daily IC values.

    Returns:
        IC mean / IC std. Returns 0 if std is 0.
    """
    valid = ic_series.dropna()
    if len(valid) < 2:
        return 0.0
    std = valid.std()
    if std == 0 or pd.isna(std):
        return 0.0
    return float(valid.mean() / std)


def compute_rank_icir(rankic_series: pd.Series) -> float:
    """Compute RankICIR (Rank IC Information Ratio).

    Args:
        rankic_series: Series of daily Rank IC values.

    Returns:
        RankIC mean / RankIC std. Returns 0 if std is 0.
    """
    return compute_icir(rankic_series)


def compute_turnover(factor_values: pd.DataFrame) -> float:
    """Compute average daily turnover of factor rankings.

    Args:
        factor_values: DataFrame with [symbol, trade_date, factor_value].

    Returns:
        Average daily turnover (fraction of rank changes).
    """
    if factor_values.empty:
        return 0.0

    pivot = factor_values.pivot_table(index="trade_date", columns="symbol", values="factor_value")
    ranks = pivot.rank(axis=1, pct=True)
    daily_changes = ranks.diff().abs()
    avg_turnover = float(daily_changes.mean().mean())
    return avg_turnover if not np.isnan(avg_turnover) else 0.0


def compute_all_metrics(
    factor_values: pd.DataFrame,
    market_data: pd.DataFrame,
    factor_id: str = "",
    forward_period: int = 1,
    annualization_factor: float = 252.0,
) -> FactorMetrics:
    """Compute all evaluation metrics for a factor.

    Args:
        factor_values: DataFrame with [symbol, trade_date, factor_value].
        market_data: Market data with close prices.
        factor_id: Factor identifier.
        forward_period: Forward return period.
        annualization_factor: Number of trading days per year.

    Returns:
        FactorMetrics object with all computed metrics.
    """
    # Compute forward returns
    returns_df = market_data[["symbol", "trade_date", "close"]].copy()
    returns_df = returns_df.sort_values(["symbol", "trade_date"])
    returns_df["forward_return"] = (
        returns_df.groupby("symbol")["close"]
        .pct_change(periods=forward_period)
        .shift(-forward_period)
    )

    # Merge factor values with forward returns
    merged = factor_values.merge(
        returns_df[["symbol", "trade_date", "forward_return"]],
        on=["symbol", "trade_date"],
        how="inner",
    )

    if merged.empty:
        return FactorMetrics(factor_id=factor_id)

    # Compute daily IC and RankIC
    daily_ic = []
    daily_rankic = []

    for date, group in merged.groupby("trade_date"):
        valid = group["factor_value"].notna() & group["forward_return"].notna()
        if valid.sum() < 5:
            continue

        ic = compute_ic(
            group.loc[valid, "factor_value"],
            group.loc[valid, "forward_return"],
        )
        rankic = compute_rank_ic(
            group.loc[valid, "factor_value"],
            group.loc[valid, "forward_return"],
        )

        daily_ic.append({"date": date, "ic": ic})
        daily_rankic.append({"date": date, "rankic": rankic})

    ic_df = pd.DataFrame(daily_ic)
    rankic_df = pd.DataFrame(daily_rankic)

    if ic_df.empty:
        return FactorMetrics(factor_id=factor_id)

    ic_series = ic_df.set_index("date")["ic"]
    rankic_series = rankic_df.set_index("date")["rankic"]

    # Aggregate metrics
    ic_mean = float(ic_series.mean())
    ic_std = float(ic_series.std()) if len(ic_series) > 1 else 0.0
    icir = compute_icir(ic_series)

    rankic_mean = float(rankic_series.mean())
    rankic_std = float(rankic_series.std()) if len(rankic_series) > 1 else 0.0
    rankicir = compute_rank_icir(rankic_series)

    positive_ic_ratio = float((ic_series > 0).mean())
    coverage = float(factor_values["factor_value"].notna().mean())
    turnover = compute_turnover(factor_values)

    # Annualized versions (for reporting only, not used for thresholds)
    annualized_icir = icir * np.sqrt(annualization_factor) if icir != 0 else 0.0
    annualized_rank_icir = rankicir * np.sqrt(annualization_factor) if rankicir != 0 else 0.0

    return FactorMetrics(
        factor_id=factor_id,
        ic_mean=ic_mean,
        ic_std=ic_std,
        icir=icir,
        rankic_mean=rankic_mean,
        rankic_std=rankic_std,
        rankicir=rankicir,
        n_valid_dates=len(ic_series),
        positive_ic_ratio=positive_ic_ratio,
        coverage=coverage,
        turnover=turnover,
        raw_icir=icir,
        annualized_icir=float(annualized_icir),
        raw_rank_icir=rankicir,
        annualized_rank_icir=float(annualized_rank_icir),
    )
