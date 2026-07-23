"""Tests for evaluation metrics: IC, ICIR, RankIC, RankICIR."""

import numpy as np
import pandas as pd
import pytest

from cogalpha_mvp.evaluation.metrics import (
    FactorMetrics,
    compute_all_metrics,
    compute_ic,
    compute_icir,
    compute_rank_ic,
    compute_rank_icir,
    compute_turnover,
)


class TestIC:
    """Tests for IC computation."""

    def test_perfect_positive_ic(self):
        """Test IC with perfectly correlated data."""
        factor = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        returns = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        ic = compute_ic(factor, returns)
        assert ic == pytest.approx(1.0, abs=1e-6)

    def test_perfect_negative_ic(self):
        """Test IC with perfectly negatively correlated data."""
        factor = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        returns = pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1], dtype=float)
        ic = compute_ic(factor, returns)
        assert ic == pytest.approx(-1.0, abs=1e-6)

    def test_zero_ic(self):
        """Test IC with uncorrelated data."""
        rng = np.random.default_rng(42)
        factor = pd.Series(rng.normal(0, 1, 1000))
        returns = pd.Series(rng.normal(0, 1, 1000))
        ic = compute_ic(factor, returns)
        assert abs(ic) < 0.1  # Should be close to 0

    def test_nan_handling(self):
        """Test that NaN values are handled."""
        factor = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8], dtype=float)
        returns = pd.Series([1, 2, 3, 4, np.nan, 6, 7, 8], dtype=float)
        ic = compute_ic(factor, returns)
        assert not np.isnan(ic)

    def test_too_few_valid(self):
        """Test that too few valid values return NaN."""
        factor = pd.Series([1, 2, np.nan, np.nan], dtype=float)
        returns = pd.Series([1, 2, np.nan, np.nan], dtype=float)
        ic = compute_ic(factor, returns)
        assert np.isnan(ic)


class TestRankIC:
    """Tests for RankIC computation."""

    def test_perfect_positive_rankic(self):
        """Test RankIC with perfectly rank-correlated data."""
        factor = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        returns = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], dtype=float)
        rankic = compute_rank_ic(factor, returns)
        assert rankic == pytest.approx(1.0, abs=1e-6)

    def test_perfect_negative_rankic(self):
        """Test RankIC with perfectly negatively rank-correlated data."""
        factor = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        returns = pd.Series([100, 90, 80, 70, 60, 50, 40, 30, 20, 10], dtype=float)
        rankic = compute_rank_ic(factor, returns)
        assert rankic == pytest.approx(-1.0, abs=1e-6)


class TestICIR:
    """Tests for ICIR computation."""

    def test_positive_icir(self):
        """Test ICIR with positive IC series."""
        ic_series = pd.Series([0.05, 0.06, 0.04, 0.07, 0.05, 0.06, 0.04, 0.05])
        icir = compute_icir(ic_series)
        assert icir > 0

    def test_zero_std(self):
        """Test ICIR with zero standard deviation."""
        ic_series = pd.Series([0.05, 0.05, 0.05, 0.05])
        icir = compute_icir(ic_series)
        assert icir == 0.0  # std is 0, return 0

    def test_negative_icir(self):
        """Test ICIR with negative IC series."""
        ic_series = pd.Series([-0.05, -0.06, -0.04, -0.07, -0.05])
        icir = compute_icir(ic_series)
        assert icir < 0


class TestRankICIR:
    """Tests for RankICIR computation."""

    def test_positive_rankicir(self):
        """Test RankICIR with positive RankIC series."""
        rankic_series = pd.Series([0.05, 0.06, 0.04, 0.07, 0.05, 0.06])
        rankicir = compute_rank_icir(rankic_series)
        assert rankicir > 0


class TestComputeAllMetrics:
    """Tests for full metrics computation."""

    @pytest.fixture
    def sample_data(self):
        """Create sample factor values and market data."""
        dates = pd.bdate_range("2020-01-01", "2020-03-31")
        symbols = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        rng = np.random.default_rng(42)

        records = []
        for sym in symbols:
            prices = 100 * np.cumprod(1 + rng.normal(0, 0.02, len(dates)))
            for i, date in enumerate(dates):
                records.append(
                    {
                        "symbol": sym,
                        "trade_date": date,
                        "close": prices[i],
                    }
                )

        market_data = pd.DataFrame(records)

        # Create factor values with some predictive power
        factor_records = []
        for sym in symbols:
            for _i, date in enumerate(dates):
                factor_records.append(
                    {
                        "symbol": sym,
                        "trade_date": date,
                        "factor_value": rng.normal(0, 1),
                    }
                )
        factor_values = pd.DataFrame(factor_records)

        return factor_values, market_data

    def test_metrics_computed(self, sample_data):
        """Test that all metrics are computed."""
        factor_values, market_data = sample_data
        metrics = compute_all_metrics(factor_values, market_data, "test_factor", forward_period=1)
        assert isinstance(metrics, FactorMetrics)
        assert metrics.factor_id == "test_factor"
        assert metrics.n_valid_dates > 0

    def test_coverage_in_range(self, sample_data):
        """Test that coverage is in [0, 1]."""
        factor_values, market_data = sample_data
        metrics = compute_all_metrics(factor_values, market_data, "test")
        assert 0.0 <= metrics.coverage <= 1.0


class TestTurnover:
    """Tests for turnover computation."""

    def test_zero_turnover(self):
        """Test turnover with stable rankings."""
        dates = pd.bdate_range("2020-01-01", "2020-01-10")
        factor_values = pd.DataFrame(
            {
                "symbol": ["A"] * len(dates) + ["B"] * len(dates),
                "trade_date": list(dates) + list(dates),
                "factor_value": [1.0] * len(dates) + [2.0] * len(dates),
            }
        )
        turnover = compute_turnover(factor_values)
        assert turnover == pytest.approx(0.0, abs=0.01)

    def test_high_turnover(self):
        """Test turnover with changing rankings."""
        dates = pd.bdate_range("2020-01-01", "2020-01-10")
        n = len(dates)
        # Alternating factor values cause high turnover
        factor_values = pd.DataFrame(
            {
                "symbol": ["A"] * n + ["B"] * n,
                "trade_date": list(dates) + list(dates),
                "factor_value": ([1.0, 2.0] * 5)[:n] + ([2.0, 1.0] * 5)[:n],
            }
        )
        turnover = compute_turnover(factor_values)
        assert turnover > 0
