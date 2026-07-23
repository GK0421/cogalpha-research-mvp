"""Tests for data contract and adapters."""

import pandas as pd

from cogalpha_mvp.data.adapters import SyntheticDataAdapter
from cogalpha_mvp.domain.data_contract import (
    DataRequest,
    StandardMarketData,
)


class TestStandardMarketData:
    """Tests for data contract validation and normalization."""

    def test_validate_valid_data(self):
        """Test that valid data passes validation."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B", "A", "B"],
                "trade_date": pd.to_datetime(
                    ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
                ),
                "open": [10.0, 20.0, 11.0, 21.0],
                "high": [12.0, 22.0, 13.0, 23.0],
                "low": [9.0, 19.0, 10.0, 20.0],
                "close": [11.0, 21.0, 12.0, 22.0],
                "volume": [1000, 2000, 1500, 2500],
            }
        )
        errors = StandardMarketData.validate(df)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_validate_missing_fields(self):
        """Test that missing required fields are detected."""
        df = pd.DataFrame({"symbol": ["A"], "trade_date": ["2020-01-01"]})
        errors = StandardMarketData.validate(df)
        assert any("Missing required fields" in e for e in errors)

    def test_validate_negative_prices(self):
        """Test that non-positive prices are detected."""
        df = pd.DataFrame(
            {
                "symbol": ["A"],
                "trade_date": pd.to_datetime(["2020-01-01"]),
                "open": [-1.0],
                "high": [10.0],
                "low": [5.0],
                "close": [8.0],
                "volume": [100],
            }
        )
        errors = StandardMarketData.validate(df)
        assert any("non-positive" in e for e in errors)

    def test_validate_negative_volume(self):
        """Test that negative volume is detected."""
        df = pd.DataFrame(
            {
                "symbol": ["A"],
                "trade_date": pd.to_datetime(["2020-01-01"]),
                "open": [10.0],
                "high": [12.0],
                "low": [9.0],
                "close": [11.0],
                "volume": [-100],
            }
        )
        errors = StandardMarketData.validate(df)
        assert any("negative" in e.lower() for e in errors)

    def test_validate_duplicate_keys(self):
        """Test that duplicate primary keys are detected."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "A"],
                "trade_date": pd.to_datetime(["2020-01-01", "2020-01-01"]),
                "open": [10.0, 10.0],
                "high": [12.0, 12.0],
                "low": [9.0, 9.0],
                "close": [11.0, 11.0],
                "volume": [100, 100],
                "market": ["CN", "CN"],
                "exchange": ["SSE", "SSE"],
            }
        )
        errors = StandardMarketData.validate(df)
        assert any("duplicate" in e.lower() for e in errors)

    def test_normalize_renames_columns(self):
        """Test that column normalization works."""
        df = pd.DataFrame(
            {
                "TS_CODE": ["A"],
                "DATE": ["2020-01-01"],
                "OPEN": [10.0],
                "HIGH": [12.0],
                "LOW": [9.0],
                "CLOSE": [11.0],
                "VOL": [100],
            }
        )
        normalized = StandardMarketData.normalize(df)
        assert "symbol" in normalized.columns
        assert "trade_date" in normalized.columns
        assert "volume" in normalized.columns

    def test_compute_fingerprint(self):
        """Test that fingerprint computation is stable."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "trade_date": pd.to_datetime(["2020-01-01", "2020-01-01"]),
                "open": [10.0, 20.0],
                "high": [12.0, 22.0],
                "low": [9.0, 19.0],
                "close": [11.0, 21.0],
                "volume": [100, 200],
            }
        )
        fp1 = StandardMarketData.compute_fingerprint(df)
        fp2 = StandardMarketData.compute_fingerprint(df.copy())
        assert fp1 == fp2, "Fingerprint should be stable"


class TestSyntheticDataAdapter:
    """Tests for synthetic data generation."""

    def test_generates_data(self):
        """Test that synthetic data is generated."""
        adapter = SyntheticDataAdapter()
        request = DataRequest(start_date="2020-01-01", end_date="2020-03-31")
        data = adapter.load(request)
        assert len(data) > 0
        assert "symbol" in data.columns
        assert "close" in data.columns

    def test_date_range(self):
        """Test that data covers the requested date range."""
        adapter = SyntheticDataAdapter()
        request = DataRequest(start_date="2020-01-01", end_date="2020-01-31")
        data = adapter.load(request)
        assert data["trade_date"].min() >= pd.Timestamp("2020-01-01")
        assert data["trade_date"].max() <= pd.Timestamp("2020-01-31")

    def test_deterministic(self):
        """Test that the same seed produces the same data."""
        adapter1 = SyntheticDataAdapter()
        adapter2 = SyntheticDataAdapter()
        request = DataRequest(start_date="2020-01-01", end_date="2020-01-10")
        data1 = adapter1.load(request)
        data2 = adapter2.load(request)
        pd.testing.assert_frame_equal(data1, data2)

    def test_multiple_symbols(self):
        """Test that data contains multiple symbols."""
        adapter = SyntheticDataAdapter()
        request = DataRequest(start_date="2020-01-01", end_date="2020-01-10")
        data = adapter.load(request)
        assert data["symbol"].nunique() > 1
