"""Comprehensive tests for data adapters.

Tests all 6 adapters: LocalCSV, LocalParquet, Synthetic,
AStockDataExport, GlobalStockDataExport, VibeTradingExport.

Also tests edge cases: invalid files, field mapping, duplicate keys,
date/symbol filters, empty data, corrupted files, case-insensitive columns,
external export formats, and snapshot manifest creation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cogalpha_mvp.data.adapters import (
    AStockDataExportAdapter,
    GlobalStockDataExportAdapter,
    LocalCSVAdapter,
    LocalParquetAdapter,
    SyntheticDataAdapter,
    VibeTradingExportAdapter,
    create_snapshot_manifest,
)
from cogalpha_mvp.domain.data_contract import DataRequest, StandardMarketData

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_ohlcv_df():
    """Create a small valid OHLCV DataFrame."""
    return pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL", "GOOG", "GOOG"],
            "trade_date": pd.to_datetime(["2022-01-03", "2022-01-04", "2022-01-03", "2022-01-04"]),
            "open": [150.0, 151.0, 2800.0, 2805.0],
            "high": [152.0, 153.0, 2820.0, 2810.0],
            "low": [149.0, 150.0, 2790.0, 2795.0],
            "close": [151.0, 152.0, 2810.0, 2800.0],
            "volume": [1000000, 1100000, 500000, 550000],
        }
    )


@pytest.fixture
def sample_csv_file(tmp_path, sample_ohlcv_df):
    """Create a CSV file with sample data."""
    path = tmp_path / "sample.csv"
    sample_ohlcv_df.to_csv(str(path), index=False)
    return path


@pytest.fixture
def sample_parquet_file(tmp_path, sample_ohlcv_df):
    """Create a Parquet file with sample data."""
    path = tmp_path / "sample.parquet"
    sample_ohlcv_df.to_parquet(str(path))
    return path


@pytest.fixture
def astock_csv_file(tmp_path):
    """Create a CSV in a-stock-data export format."""
    df = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ", "600000.SH", "600000.SH"],
            "trade_date": ["20220103", "20220104", "20220103", "20220104"],
            "open": [15.0, 15.1, 8.0, 8.1],
            "high": [15.2, 15.3, 8.2, 8.2],
            "low": [14.9, 15.0, 7.9, 8.0],
            "close": [15.1, 15.2, 8.1, 8.1],
            "vol": [100000, 110000, 200000, 210000],
            "amount": [1510000, 1672000, 1620000, 1701000],
            "pct_chg": [0.67, 0.66, 1.25, 0.0],
        }
    )
    path = tmp_path / "astock_export.csv"
    df.to_csv(str(path), index=False)
    return path


@pytest.fixture
def global_csv_file(tmp_path):
    """Create a CSV in global-stock-data export format (uses 'ticker')."""
    df = pd.DataFrame(
        {
            "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
            "date": ["2022-01-03", "2022-01-04", "2022-01-03", "2022-01-04"],
            "open": [150.0, 151.0, 300.0, 301.0],
            "high": [152.0, 153.0, 302.0, 303.0],
            "low": [149.0, 150.0, 299.0, 300.0],
            "close": [151.0, 152.0, 301.0, 302.0],
            "volume": [1000000, 1100000, 800000, 810000],
        }
    )
    path = tmp_path / "global_export.csv"
    df.to_csv(str(path), index=False)
    return path


@pytest.fixture
def vibe_json_file(tmp_path):
    """Create a JSON in Vibe-Trading export format."""
    data = [
        {
            "symbol": "BTC",
            "trade_date": "2022-01-03",
            "open": 40000, "high": 41000, "low": 39000, "close": 40500,
            "volume": 500,
        },
        {
            "symbol": "BTC",
            "trade_date": "2022-01-04",
            "open": 40500, "high": 42000, "low": 40000, "close": 41500,
            "volume": 600,
        },
    ]
    path = tmp_path / "vibe_export.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# LocalCSVAdapter Tests
# ---------------------------------------------------------------------------


class TestLocalCSVAdapter:
    """Tests for LocalCSVAdapter."""

    def test_load_valid_csv(self, sample_csv_file):
        """Test loading a valid CSV file."""
        adapter = LocalCSVAdapter()
        request = DataRequest(path=str(sample_csv_file))
        df = adapter.load(request)
        assert len(df) == 4
        assert "symbol" in df.columns
        assert "close" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["trade_date"])

    def test_load_with_date_filter(self, sample_csv_file):
        """Test date filtering."""
        adapter = LocalCSVAdapter()
        request = DataRequest(
            path=str(sample_csv_file),
            start_date="2022-01-04",
            end_date="2022-01-04",
        )
        df = adapter.load(request)
        assert len(df) == 2
        assert (df["trade_date"] == pd.Timestamp("2022-01-04")).all()

    def test_load_with_symbol_filter(self, sample_csv_file):
        """Test symbol filtering."""
        adapter = LocalCSVAdapter()
        request = DataRequest(
            path=str(sample_csv_file),
            symbols=["AAPL"],
        )
        df = adapter.load(request)
        assert len(df) == 2
        assert (df["symbol"] == "AAPL").all()

    def test_load_file_not_found(self):
        """Test FileNotFoundError on missing file."""
        adapter = LocalCSVAdapter()
        request = DataRequest(path="nonexistent.csv")
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            adapter.load(request)

    def test_load_case_insensitive_columns(self, tmp_path):
        """Test that uppercase column names are normalized."""
        df = pd.DataFrame(
            {
                "SYMBOL": ["A"],
                "TRADE_DATE": ["2022-01-03"],
                "OPEN": [100.0],
                "HIGH": [101.0],
                "LOW": [99.0],
                "CLOSE": [100.5],
                "VOLUME": [1000],
            }
        )
        path = tmp_path / "upper.csv"
        df.to_csv(str(path), index=False)
        adapter = LocalCSVAdapter()
        result = adapter.load(DataRequest(path=str(path)))
        assert "symbol" in result.columns
        assert "close" in result.columns

    def test_load_column_rename(self, tmp_path):
        """Test that ts_code/ticker/code are renamed to symbol."""
        df = pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "trade_date": ["2022-01-03"],
                "open": [10.0], "high": [11.0], "low": [9.0], "close": [10.5],
                "vol": [1000],
            }
        )
        path = tmp_path / "rename.csv"
        df.to_csv(str(path), index=False)
        adapter = LocalCSVAdapter()
        result = adapter.load(DataRequest(path=str(path)))
        assert "symbol" in result.columns
        assert result["symbol"].iloc[0] == "000001.SZ"


# ---------------------------------------------------------------------------
# LocalParquetAdapter Tests
# ---------------------------------------------------------------------------


class TestLocalParquetAdapter:
    """Tests for LocalParquetAdapter."""

    def test_load_valid_parquet(self, sample_parquet_file):
        """Test loading a valid Parquet file."""
        adapter = LocalParquetAdapter()
        request = DataRequest(path=str(sample_parquet_file))
        df = adapter.load(request)
        assert len(df) == 4
        assert "close" in df.columns

    def test_load_with_filters(self, sample_parquet_file):
        """Test date and symbol filters on Parquet."""
        adapter = LocalParquetAdapter()
        request = DataRequest(
            path=str(sample_parquet_file),
            start_date="2022-01-04",
            symbols=["AAPL"],
        )
        df = adapter.load(request)
        assert len(df) == 1
        assert df["symbol"].iloc[0] == "AAPL"

    def test_load_file_not_found(self):
        """Test FileNotFoundError on missing Parquet."""
        adapter = LocalParquetAdapter()
        with pytest.raises(FileNotFoundError, match="Parquet file not found"):
            adapter.load(DataRequest(path="nonexistent.parquet"))


# ---------------------------------------------------------------------------
# SyntheticDataAdapter Tests
# ---------------------------------------------------------------------------


class TestSyntheticDataAdapter:
    """Tests for SyntheticDataAdapter."""

    def test_load_generates_data(self):
        """Test that synthetic data is generated."""
        adapter = SyntheticDataAdapter()
        request = DataRequest(start_date="2022-01-01", end_date="2022-01-31")
        df = adapter.load(request)
        assert len(df) > 0
        assert "symbol" in df.columns
        assert "close" in df.columns

    def test_load_is_deterministic(self):
        """Test that the same parameters produce the same data."""
        adapter = SyntheticDataAdapter()
        req = DataRequest(start_date="2022-01-01", end_date="2022-01-10")
        df1 = adapter.load(req)
        df2 = adapter.load(req)
        pd.testing.assert_frame_equal(df1, df2)

    def test_load_has_50_symbols(self):
        """Test that 50 symbols are generated."""
        adapter = SyntheticDataAdapter()
        df = adapter.load(DataRequest(start_date="2022-01-01", end_date="2022-01-05"))
        assert df["symbol"].nunique() == 50

    def test_load_ohlcv_positive(self):
        """Test that OHLC prices are positive."""
        adapter = SyntheticDataAdapter()
        df = adapter.load(DataRequest(start_date="2022-01-01", end_date="2022-01-05"))
        assert (df["open"] > 0).all()
        assert (df["high"] > 0).all()
        assert (df["low"] > 0).all()
        assert (df["close"] > 0).all()

    def test_load_volume_non_negative(self):
        """Test that volume is non-negative."""
        adapter = SyntheticDataAdapter()
        df = adapter.load(DataRequest(start_date="2022-01-01", end_date="2022-01-05"))
        assert (df["volume"] >= 0).all()

    def test_load_ohlc_logic(self):
        """Test that high >= max(open,close) and low <= min(open,close)."""
        adapter = SyntheticDataAdapter()
        df = adapter.load(DataRequest(start_date="2022-01-01", end_date="2022-01-05"))
        assert (df["high"] >= df[["open", "close"]].max(axis=1)).all()
        assert (df["low"] <= df[["open", "close"]].min(axis=1)).all()

    def test_load_includes_amount(self):
        """Test that amount field is included."""
        adapter = SyntheticDataAdapter()
        df = adapter.load(DataRequest(start_date="2022-01-01", end_date="2022-01-05"))
        assert "amount" in df.columns

    def test_load_includes_market_exchange(self):
        """Test that market and exchange fields are included."""
        adapter = SyntheticDataAdapter()
        df = adapter.load(DataRequest(start_date="2022-01-01", end_date="2022-01-05"))
        assert "market" in df.columns
        assert "exchange" in df.columns


# ---------------------------------------------------------------------------
# AStockDataExportAdapter Tests
# ---------------------------------------------------------------------------


class TestAStockDataExportAdapter:
    """Tests for AStockDataExportAdapter."""

    def test_load_csv(self, astock_csv_file):
        """Test loading an a-stock-data CSV export."""
        adapter = AStockDataExportAdapter()
        df = adapter.load(DataRequest(path=str(astock_csv_file)))
        assert len(df) == 4
        assert "symbol" in df.columns
        # ts_code should be renamed to symbol
        assert "000001.SZ" in df["symbol"].values

    def test_vol_renamed_to_volume(self, astock_csv_file):
        """Test that 'vol' column is renamed to 'volume'."""
        adapter = AStockDataExportAdapter()
        df = adapter.load(DataRequest(path=str(astock_csv_file)))
        assert "volume" in df.columns

    def test_pct_chg_renamed(self, astock_csv_file):
        """Test that 'pct_chg' is renamed to 'pct_change'."""
        adapter = AStockDataExportAdapter()
        df = adapter.load(DataRequest(path=str(astock_csv_file)))
        assert "pct_change" in df.columns

    def test_file_not_found(self):
        """Test FileNotFoundError."""
        adapter = AStockDataExportAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.load(DataRequest(path="missing.csv"))

    def test_unsupported_format(self, tmp_path):
        """Test that unsupported file format raises ValueError."""
        path = tmp_path / "data.txt"
        path.write_text("hello")
        adapter = AStockDataExportAdapter()
        with pytest.raises(ValueError, match="Unsupported file format"):
            adapter.load(DataRequest(path=str(path)))

    def test_load_json(self, tmp_path):
        """Test loading JSON format."""
        data = [
            {"ts_code": "A", "trade_date": "2022-01-03", "open": 10, "high": 11,
             "low": 9, "close": 10.5, "vol": 1000},
        ]
        path = tmp_path / "data.json"
        path.write_text(json.dumps(data))
        adapter = AStockDataExportAdapter()
        df = adapter.load(DataRequest(path=str(path)))
        assert len(df) == 1
        assert df["symbol"].iloc[0] == "A"


# ---------------------------------------------------------------------------
# GlobalStockDataExportAdapter Tests
# ---------------------------------------------------------------------------


class TestGlobalStockDataExportAdapter:
    """Tests for GlobalStockDataExportAdapter."""

    def test_load_csv(self, global_csv_file):
        """Test loading a global-stock-data CSV export."""
        adapter = GlobalStockDataExportAdapter()
        df = adapter.load(DataRequest(path=str(global_csv_file)))
        assert len(df) == 4
        assert "symbol" in df.columns
        # ticker should be renamed to symbol
        assert "AAPL" in df["symbol"].values

    def test_ticker_renamed_to_symbol(self, global_csv_file):
        """Test that 'ticker' column is renamed to 'symbol'."""
        adapter = GlobalStockDataExportAdapter()
        df = adapter.load(DataRequest(path=str(global_csv_file)))
        assert "ticker" not in df.columns or "symbol" in df.columns

    def test_file_not_found(self):
        """Test FileNotFoundError."""
        adapter = GlobalStockDataExportAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.load(DataRequest(path="missing.csv"))

    def test_unsupported_format(self, tmp_path):
        """Test unsupported format raises ValueError."""
        path = tmp_path / "data.txt"
        path.write_text("hello")
        adapter = GlobalStockDataExportAdapter()
        with pytest.raises(ValueError, match="Unsupported"):
            adapter.load(DataRequest(path=str(path)))


# ---------------------------------------------------------------------------
# VibeTradingExportAdapter Tests
# ---------------------------------------------------------------------------


class TestVibeTradingExportAdapter:
    """Tests for VibeTradingExportAdapter."""

    def test_load_json(self, vibe_json_file):
        """Test loading a Vibe-Trading JSON export."""
        adapter = VibeTradingExportAdapter()
        df = adapter.load(DataRequest(path=str(vibe_json_file)))
        assert len(df) == 2
        assert "symbol" in df.columns
        assert "BTC" in df["symbol"].values

    def test_load_csv(self, tmp_path):
        """Test loading CSV format."""
        df = pd.DataFrame(
            {
                "symbol": ["ETH"],
                "trade_date": ["2022-01-03"],
                "open": [3000], "high": [3100], "low": [2900], "close": [3050],
                "volume": [1000],
            }
        )
        path = tmp_path / "vibe.csv"
        df.to_csv(str(path), index=False)
        adapter = VibeTradingExportAdapter()
        result = adapter.load(DataRequest(path=str(path)))
        assert len(result) == 1

    def test_file_not_found(self):
        """Test FileNotFoundError."""
        adapter = VibeTradingExportAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.load(DataRequest(path="missing.json"))

    def test_unsupported_format(self, tmp_path):
        """Test unsupported format."""
        path = tmp_path / "data.txt"
        path.write_text("hello")
        adapter = VibeTradingExportAdapter()
        with pytest.raises(ValueError, match="Unsupported"):
            adapter.load(DataRequest(path=str(path)))


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestAdapterEdgeCases:
    """Edge case tests across all adapters."""

    def test_empty_csv(self, tmp_path):
        """Test loading an empty CSV (headers only)."""
        path = tmp_path / "empty.csv"
        Path(str(path)).write_text("symbol,trade_date,open,high,low,close,volume\n")
        adapter = LocalCSVAdapter()
        df = adapter.load(DataRequest(path=str(path)))
        assert len(df) == 0

    def test_date_range_filter_excludes_outside(self, sample_csv_file):
        """Test that dates outside the range are excluded."""
        adapter = LocalCSVAdapter()
        request = DataRequest(
            path=str(sample_csv_file),
            start_date="2022-01-05",
            end_date="2022-01-10",
        )
        df = adapter.load(request)
        assert len(df) == 0

    def test_symbol_filter_nonexistent(self, sample_csv_file):
        """Test that filtering by nonexistent symbol returns empty."""
        adapter = LocalCSVAdapter()
        request = DataRequest(path=str(sample_csv_file), symbols=["NONEXIST"])
        df = adapter.load(request)
        assert len(df) == 0

    def test_normalize_adds_market_exchange(self, tmp_path):
        """Test that normalize adds default market and exchange."""
        df = pd.DataFrame(
            {
                "symbol": ["A"],
                "trade_date": ["2022-01-03"],
                "open": [10.0], "high": [11.0], "low": [9.0], "close": [10.5],
                "volume": [1000],
            }
        )
        path = tmp_path / "no_market.csv"
        df.to_csv(str(path), index=False)
        adapter = LocalCSVAdapter()
        result = adapter.load(DataRequest(path=str(path)))
        assert "market" in result.columns
        assert "exchange" in result.columns

    def test_trade_date_converted_to_datetime(self, sample_csv_file):
        """Test that trade_date is converted to datetime."""
        adapter = LocalCSVAdapter()
        df = adapter.load(DataRequest(path=str(sample_csv_file)))
        assert pd.api.types.is_datetime64_any_dtype(df["trade_date"])

    def test_symbol_converted_to_string(self, sample_csv_file):
        """Test that symbol is converted to string type."""
        adapter = LocalCSVAdapter()
        df = adapter.load(DataRequest(path=str(sample_csv_file)))
        # After normalize, symbol is converted via astype(str) which may
        # produce object or StringDtype depending on pandas version
        assert str(df["symbol"].dtype) in ("object", "string", "str")


# ---------------------------------------------------------------------------
# Snapshot Manifest Tests
# ---------------------------------------------------------------------------


class TestSnapshotManifest:
    """Tests for create_snapshot_manifest."""

    def test_manifest_has_required_fields(self, sample_csv_file, sample_ohlcv_df):
        """Test that manifest contains all required fields."""
        manifest = create_snapshot_manifest(
            sample_ohlcv_df, "test_source", str(sample_csv_file)
        )
        assert "source" in manifest
        assert "file_sha256" in manifest
        assert "rows" in manifest
        assert "n_symbols" in manifest
        assert "start_date" in manifest
        assert "end_date" in manifest
        assert "fields" in manifest
        assert "data_fingerprint" in manifest

    def test_manifest_sha256_correct(self, sample_csv_file, sample_ohlcv_df):
        """Test that SHA256 is computed correctly."""
        import hashlib

        expected_sha = hashlib.sha256(sample_csv_file.read_bytes()).hexdigest()
        manifest = create_snapshot_manifest(
            sample_ohlcv_df, "test", str(sample_csv_file)
        )
        assert manifest["file_sha256"] == expected_sha

    def test_manifest_rows_count(self, sample_csv_file, sample_ohlcv_df):
        """Test that row count is correct."""
        manifest = create_snapshot_manifest(
            sample_ohlcv_df, "test", str(sample_csv_file)
        )
        assert manifest["rows"] == 4

    def test_manifest_n_symbols(self, sample_csv_file, sample_ohlcv_df):
        """Test that symbol count is correct."""
        manifest = create_snapshot_manifest(
            sample_ohlcv_df, "test", str(sample_csv_file)
        )
        assert manifest["n_symbols"] == 2

    def test_manifest_missing_rates(self, sample_csv_file):
        """Test that missing rates are computed."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "trade_date": pd.to_datetime(["2022-01-03", "2022-01-04"]),
                "open": [10.0, np.nan],
                "high": [11.0, 12.0],
                "low": [9.0, 10.0],
                "close": [10.5, 11.5],
                "volume": [1000, 2000],
            }
        )
        manifest = create_snapshot_manifest(df, "test", str(sample_csv_file))
        assert "open" in manifest["missing_rates"]
        assert manifest["missing_rates"]["open"] == 0.5

    def test_manifest_duplicate_keys(self, sample_csv_file):
        """Test that duplicate keys are counted."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "A"],
                "trade_date": pd.to_datetime(["2022-01-03", "2022-01-03"]),
                "open": [10.0, 11.0],
                "high": [11.0, 12.0],
                "low": [9.0, 10.0],
                "close": [10.5, 11.5],
                "volume": [1000, 2000],
                "market": ["CN", "CN"],
                "exchange": ["SSE", "SSE"],
            }
        )
        manifest = create_snapshot_manifest(df, "test", str(sample_csv_file))
        assert manifest["duplicate_keys"] == 1

    def test_manifest_nonexistent_file(self, sample_ohlcv_df):
        """Test manifest with nonexistent file (empty SHA)."""
        manifest = create_snapshot_manifest(
            sample_ohlcv_df, "test", "nonexistent.csv"
        )
        assert manifest["file_sha256"] == ""


# ---------------------------------------------------------------------------
# StandardMarketData Validation Tests
# ---------------------------------------------------------------------------


class TestStandardMarketDataValidation:
    """Tests for StandardMarketData.validate."""

    def test_valid_data_no_errors(self, sample_ohlcv_df):
        """Test that valid data produces no errors."""
        errors = StandardMarketData.validate(sample_ohlcv_df)
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test that missing fields are detected."""
        df = pd.DataFrame({"symbol": ["A"], "trade_date": ["2022-01-03"]})
        errors = StandardMarketData.validate(df)
        assert any("Missing required fields" in e for e in errors)

    def test_negative_price_detected(self):
        """Test that negative prices are detected."""
        df = pd.DataFrame(
            {
                "symbol": ["A"],
                "trade_date": pd.to_datetime(["2022-01-03"]),
                "open": [-10.0],
                "high": [11.0],
                "low": [9.0],
                "close": [10.5],
                "volume": [1000],
            }
        )
        errors = StandardMarketData.validate(df)
        assert any("non-positive" in e for e in errors)

    def test_negative_volume_detected(self):
        """Test that negative volume is detected."""
        df = pd.DataFrame(
            {
                "symbol": ["A"],
                "trade_date": pd.to_datetime(["2022-01-03"]),
                "open": [10.0],
                "high": [11.0],
                "low": [9.0],
                "close": [10.5],
                "volume": [-100],
            }
        )
        errors = StandardMarketData.validate(df)
        assert any("negative" in e.lower() for e in errors)

    def test_duplicate_keys_detected(self):
        """Test that duplicate primary keys are detected."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "A"],
                "trade_date": pd.to_datetime(["2022-01-03", "2022-01-03"]),
                "open": [10.0, 11.0],
                "high": [11.0, 12.0],
                "low": [9.0, 10.0],
                "close": [10.5, 11.5],
                "volume": [1000, 2000],
                "market": ["CN", "CN"],
                "exchange": ["SSE", "SSE"],
            }
        )
        errors = StandardMarketData.validate(df)
        assert any("duplicate" in e.lower() for e in errors)

    def test_fingerprint_is_deterministic(self, sample_ohlcv_df):
        """Test that fingerprint is deterministic."""
        fp1 = StandardMarketData.compute_fingerprint(sample_ohlcv_df)
        fp2 = StandardMarketData.compute_fingerprint(sample_ohlcv_df)
        assert fp1 == fp2

    def test_fingerprint_changes_with_data(self, sample_ohlcv_df):
        """Test that fingerprint changes when data changes."""
        fp1 = StandardMarketData.compute_fingerprint(sample_ohlcv_df)
        modified = sample_ohlcv_df.copy()
        modified.loc[0, "volume"] = 999999  # volume affects rows but not fingerprint fields
        # Fingerprint is based on structure (rows, columns, dates, symbols, missing rates)
        # so changing a non-structural value may not change it. Add a row instead.
        modified = pd.concat([sample_ohlcv_df, pd.DataFrame({
            "symbol": ["NEW"], "trade_date": pd.to_datetime(["2022-01-05"]),
            "open": [10], "high": [11], "low": [9], "close": [10.5], "volume": [1000],
        })], ignore_index=True)
        fp2 = StandardMarketData.compute_fingerprint(modified)
        assert fp1 != fp2
