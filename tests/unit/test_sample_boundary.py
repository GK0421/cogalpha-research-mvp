"""Tests for sample boundary isolation."""

import pandas as pd
import pytest

from cogalpha_mvp.config import Config
from cogalpha_mvp.domain.sample_boundary import (
    LeakageGuard,
    SampleBoundary,
    TrainDataLoader,
)


class TestSampleBoundary:
    """Tests for train/OOS boundary."""

    def test_boundary_creation(self):
        """Test boundary creation from config."""
        config = Config()
        boundary = SampleBoundary.from_config(config)
        assert boundary.train_start == "2011-01-01"
        assert boundary.train_end == "2019-12-31"
        assert boundary.oos_start == "2020-01-01"
        assert boundary.oos_end == "2025-12-31"

    def test_validate_no_overlap(self):
        """Test that boundary validation passes for non-overlapping periods."""
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2022-12-31",
            oos_start="2023-01-01",
            oos_end="2024-12-31",
        )
        boundary.validate()  # Should not raise

    def test_validate_overlap_raises(self):
        """Test that overlapping periods raise an error."""
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2023-06-30",
            oos_start="2023-01-01",
            oos_end="2024-12-31",
        )
        with pytest.raises(AssertionError):
            boundary.validate()

    def test_is_train_date(self):
        """Test date classification."""
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2022-12-31",
            oos_start="2023-01-01",
            oos_end="2024-12-31",
        )
        assert boundary.is_train_date("2021-06-15")
        assert not boundary.is_train_date("2023-06-15")
        assert boundary.is_oos_date("2023-06-15")
        assert not boundary.is_oos_date("2021-06-15")


class TestTrainDataLoader:
    """Tests for training data loader."""

    def test_loads_only_train_data(self):
        """Test that loader only returns training period data."""
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2020-06-30",
            oos_start="2020-07-01",
            oos_end="2020-12-31",
        )
        df = pd.DataFrame(
            {
                "symbol": ["A"] * 4,
                "trade_date": pd.to_datetime(
                    ["2020-03-15", "2020-06-15", "2020-09-15", "2020-12-15"]
                ),
                "close": [10, 11, 12, 13],
            }
        )
        loader = TrainDataLoader(boundary)
        train_df = loader.load(df)
        assert len(train_df) == 2
        assert all(train_df["trade_date"] <= pd.Timestamp("2020-06-30"))


class TestLeakageGuard:
    """Tests for leakage guard."""

    def test_detects_oos_in_training(self):
        """Test that OOS data in training is detected."""
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2020-06-30",
            oos_start="2020-07-01",
            oos_end="2020-12-31",
        )
        guard = LeakageGuard(boundary)
        df = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "trade_date": pd.to_datetime(["2020-03-15", "2020-09-15"]),
                "close": [10, 20],
            }
        )
        with pytest.raises(ValueError, match="LEAKAGE"):
            guard.check_no_oos_access(df, "test")

    def test_no_violation_for_train_only(self):
        """Test that train-only data passes."""
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2020-06-30",
            oos_start="2020-07-01",
            oos_end="2020-12-31",
        )
        guard = LeakageGuard(boundary)
        df = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "trade_date": pd.to_datetime(["2020-03-15", "2020-04-15"]),
                "close": [10, 20],
            }
        )
        guard.check_no_oos_access(df, "test")  # Should not raise

    def test_fingerprint_distinct(self):
        """Test that identical fingerprints are flagged."""
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2020-06-30",
            oos_start="2020-07-01",
            oos_end="2020-12-31",
        )
        guard = LeakageGuard(boundary)
        with pytest.raises(ValueError):
            guard.check_train_oos_fingerprints("abc123", "abc123")
