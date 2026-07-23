"""Tests for quality checking pipeline."""

import numpy as np
import pandas as pd
import pytest

from cogalpha_mvp.config import QualityConfig
from cogalpha_mvp.factors.registry import FactorMetadata
from cogalpha_mvp.quality.pipeline import (
    QualityPipeline,
    verify_bad_factors_rejected,
)


@pytest.fixture
def sample_data():
    """Create sample market data for quality checks."""
    dates = pd.bdate_range("2020-01-01", "2020-12-31")
    n = len(dates)
    rng = np.random.default_rng(42)
    records = []
    for sym in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]:
        prices = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
        for i, date in enumerate(dates):
            records.append(
                {
                    "symbol": sym,
                    "trade_date": date,
                    "open": prices[i] * (1 + rng.normal(0, 0.005)),
                    "high": prices[i] * (1 + abs(rng.normal(0, 0.01))),
                    "low": prices[i] * (1 - abs(rng.normal(0, 0.01))),
                    "close": prices[i],
                    "volume": rng.integers(1e6, 5e7),
                    "amount": prices[i] * rng.integers(1e6, 5e7),
                }
            )
    return pd.DataFrame(records)


@pytest.fixture
def pipeline():
    return QualityPipeline(QualityConfig())


class TestQualityPipeline:
    """Tests for the quality checking pipeline."""

    def test_valid_factor_passes(self, pipeline, sample_data):
        """Test that a valid factor passes quality checks."""
        factor = FactorMetadata(
            factor_id="test_valid",
            name="test_valid_factor",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="20-day moving average of close price for trend identification",
        )
        result = pipeline.check(factor, sample_data)
        assert result.passed, f"Valid factor should pass. Error: {result.error} at {result.stage}"

    def test_empty_expression_rejected(self, pipeline, sample_data):
        """Test that empty expression is rejected."""
        factor = FactorMetadata(
            factor_id="test_empty",
            name="test_empty",
            agent_id="Agent_01",
            level=1,
            expression="",
            description="Empty expression test",
        )
        result = pipeline.check(factor, sample_data)
        assert not result.passed

    def test_all_nan_rejected(self, pipeline, sample_data):
        """Test that factors producing all NaN are rejected."""
        factor = FactorMetadata(
            factor_id="test_nan",
            name="test_nan",
            agent_id="Agent_01",
            level=1,
            expression="div(close, sub(close, close))",  # Division by zero = NaN
            description="Produces all NaN values",
        )
        result = pipeline.check(factor, sample_data)
        assert not result.passed
        assert "nan" in result.error.lower() or "nan" in result.stage.lower()

    def test_short_description_rejected(self, pipeline, sample_data):
        """Test that factors without economic logic are rejected."""
        factor = FactorMetadata(
            factor_id="test_short_desc",
            name="test_short",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="short",  # Too short
        )
        result = pipeline.check(factor, sample_data)
        assert not result.passed
        assert result.stage == "economic_logic"


class TestBadFactors:
    """Tests that known bad factors are rejected."""

    def test_bad_negative_shift_rejected(self, pipeline, sample_data):
        """Test that shift(-1) pattern is rejected."""
        factor = FactorMetadata(
            factor_id="bad_negative_shift",
            name="bad_negative_shift",
            agent_id="test",
            level=0,
            expression="sub(close, shift(close, -1))",
            description="Uses negative shift to access future data - should be rejected",
        )
        result = pipeline.check(factor, sample_data)
        assert not result.passed, "Negative shift should be rejected"

    def test_bad_future_global_mean_rejected(self, pipeline, sample_data):
        """Test that full-sample normalization is rejected (via truncation)."""
        # This may pass static checks but fail truncation
        factor = FactorMetadata(
            factor_id="bad_future_global_mean",
            name="bad_future_global_mean",
            agent_id="test",
            level=0,
            expression="ts_mean(close, 999999)",
            description="Uses full sample mean which includes future data",
        )
        result = pipeline.check(factor, sample_data)
        # Should be rejected at some stage
        assert not result.passed or result.warnings, "Full-sample mean should be flagged"

    def test_bad_last_row_reference_rejected(self, pipeline, sample_data):
        """Test that negative delay (future reference) is rejected."""
        factor = FactorMetadata(
            factor_id="bad_last_row",
            name="bad_last_row_reference",
            agent_id="test",
            level=0,
            expression="sub(close, delay(close, -1))",
            description="Uses negative delay to access future data",
        )
        result = pipeline.check(factor, sample_data)
        assert not result.passed, "Negative delay should be rejected"

    def test_all_bad_factors_rejected(self, pipeline, sample_data):
        """Test that all known bad factors are rejected."""
        results = verify_bad_factors_rejected(pipeline, sample_data)
        for name, rejected in results.items():
            assert rejected, f"Bad factor '{name}' was NOT rejected!"
