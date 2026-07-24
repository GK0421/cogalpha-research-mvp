"""Unit tests for portfolio backtest engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cogalpha_mvp.config import PortfolioConfig
from cogalpha_mvp.portfolio.backtest import (
    RESEARCH_DISCLAIMER,
    BacktestEngine,
    PortfolioResult,
)


@pytest.fixture
def portfolio_config():
    return PortfolioConfig()


@pytest.fixture
def sample_market_data():
    """Create sample market data with multiple symbols."""
    dates = pd.bdate_range("2022-01-03", "2022-04-29")
    n = len(dates)
    rng = np.random.default_rng(42)
    records = []
    for sym in ["A", "B", "C", "D", "E"]:
        prices = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
        for i, date in enumerate(dates):
            records.append({
                "symbol": sym,
                "trade_date": date,
                "open": prices[i] * 0.99,
                "high": prices[i] * 1.01,
                "low": prices[i] * 0.98,
                "close": prices[i],
                "volume": int(rng.integers(1e6, 5e7)),
            })
    return pd.DataFrame(records)


@pytest.fixture
def sample_factor_values(sample_market_data):
    """Create factor values aligned with market data."""
    rng = np.random.default_rng(123)
    result = sample_market_data[["symbol", "trade_date"]].copy()
    result["factor_value"] = rng.normal(0, 1, len(result))
    return result


class TestBacktestEngine:
    """Tests for BacktestEngine."""

    def test_run_long_short(self, portfolio_config, sample_factor_values, sample_market_data):
        """Test long-short strategy."""
        engine = BacktestEngine(portfolio_config)
        result = engine.run(sample_factor_values, sample_market_data, strategy="long_short")
        assert isinstance(result, PortfolioResult)
        assert result.to_dict()["disclaimer"] == RESEARCH_DISCLAIMER

    def test_run_top_quantile(self, portfolio_config, sample_factor_values, sample_market_data):
        """Test top quantile strategy."""
        engine = BacktestEngine(portfolio_config)
        result = engine.run(sample_factor_values, sample_market_data, strategy="top_quantile")
        assert isinstance(result, PortfolioResult)

    def test_run_equal_weight(self, portfolio_config, sample_factor_values, sample_market_data):
        """Test equal weight strategy."""
        engine = BacktestEngine(portfolio_config)
        result = engine.run(sample_factor_values, sample_market_data, strategy="equal_weight")
        assert isinstance(result, PortfolioResult)

    def test_run_empty_data(self, portfolio_config):
        """Test with empty data returns empty result."""
        engine = BacktestEngine(portfolio_config)
        empty_factor = pd.DataFrame(columns=["symbol", "trade_date", "factor_value"])
        empty_market = pd.DataFrame(columns=["symbol", "trade_date", "close"])
        result = engine.run(empty_factor, empty_market)
        assert result.annual_return == 0.0

    def test_portfolio_result_to_dict(self, portfolio_config, sample_factor_values, sample_market_data):
        """Test that to_dict includes disclaimer."""
        engine = BacktestEngine(portfolio_config)
        result = engine.run(sample_factor_values, sample_market_data, strategy="long_short")
        d = result.to_dict()
        assert "disclaimer" in d
        assert "annual_return" in d
        assert "sharpe_ratio" in d
        assert "max_drawdown" in d
        assert d["disclaimer"] == RESEARCH_DISCLAIMER

    def test_research_disclaimer_constant(self):
        """Test that the research disclaimer is correct."""
        assert RESEARCH_DISCLAIMER == "RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING"

    def test_get_rebalance_dates_weekly(self, portfolio_config, sample_market_data):
        """Test weekly rebalancing."""
        engine = BacktestEngine(portfolio_config)
        dates = engine._get_rebalance_dates(sample_market_data)
        assert len(dates) > 0

    def test_compute_metrics_empty(self, portfolio_config):
        """Test metrics computation with empty returns."""
        engine = BacktestEngine(portfolio_config)
        result = engine._compute_metrics(pd.Series(dtype=float))
        assert result.annual_return == 0.0

    def test_turnover_computation(self, portfolio_config, sample_factor_values, sample_market_data):
        """Test that turnover is computed."""
        engine = BacktestEngine(portfolio_config)
        result = engine.run(sample_factor_values, sample_market_data, strategy="long_short")
        assert isinstance(result.turnover, float)

    def test_transaction_cost_applied(self, portfolio_config, sample_factor_values, sample_market_data):
        """Test that transaction costs are applied."""
        engine = BacktestEngine(portfolio_config)
        result = engine.run(sample_factor_values, sample_market_data, strategy="long_short")
        assert isinstance(result.total_cost, float)
        assert result.total_cost >= 0
