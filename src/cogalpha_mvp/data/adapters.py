"""Data adapters for loading market data from various sources.

All adapters implement the MarketDataAdapter protocol and output
the standard data contract with at least REQUIRED_FIELDS.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from cogalpha_mvp.domain.data_contract import DataRequest, StandardMarketData

logger = logging.getLogger("cogalpha_mvp")


class LocalCSVAdapter:
    """Adapter for loading market data from local CSV files."""

    def load(self, request: DataRequest) -> pd.DataFrame:
        """Load data from a CSV file.

        Args:
            request: Data request with path pointing to a CSV file.

        Returns:
            Normalized DataFrame with standard fields.
        """
        path = Path(request.path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        logger.info("Loading CSV from %s", path)
        df = pd.read_csv(str(path))
        df = StandardMarketData.normalize(df)
        df = self._filter(df, request)
        return df

    def _filter(self, df: pd.DataFrame, request: DataRequest) -> pd.DataFrame:
        """Apply date and symbol filters from request."""
        if request.start_date:
            df = df[df["trade_date"] >= pd.Timestamp(request.start_date)]
        if request.end_date:
            df = df[df["trade_date"] <= pd.Timestamp(request.end_date)]
        if request.symbols:
            df = df[df["symbol"].isin(request.symbols)]
        return df


class LocalParquetAdapter:
    """Adapter for loading market data from local Parquet files."""

    def load(self, request: DataRequest) -> pd.DataFrame:
        """Load data from a Parquet file.

        Args:
            request: Data request with path pointing to a Parquet file.

        Returns:
            Normalized DataFrame with standard fields.
        """
        path = Path(request.path)
        if not path.exists():
            raise FileNotFoundError(f"Parquet file not found: {path}")

        logger.info("Loading Parquet from %s", path)
        df = pd.read_parquet(str(path))
        df = StandardMarketData.normalize(df)
        df = self._filter(df, request)
        return df

    def _filter(self, df: pd.DataFrame, request: DataRequest) -> pd.DataFrame:
        if request.start_date:
            df = df[df["trade_date"] >= pd.Timestamp(request.start_date)]
        if request.end_date:
            df = df[df["trade_date"] <= pd.Timestamp(request.end_date)]
        if request.symbols:
            df = df[df["symbol"].isin(request.symbols)]
        return df


class SyntheticDataAdapter:
    """Adapter that generates synthetic market data for testing and demos.

    Produces deterministic data using a fixed random seed.
    """

    def load(self, request: DataRequest) -> pd.DataFrame:
        """Generate synthetic market data.

        Args:
            request: Data request. Uses start_date, end_date for date range.
                     If path is provided, it's used as a seed hint.

        Returns:
            DataFrame with standard OHLCV fields.
        """
        start = (
            pd.Timestamp(request.start_date) if request.start_date else pd.Timestamp("2020-01-01")
        )
        end = pd.Timestamp(request.end_date) if request.end_date else pd.Timestamp("2023-12-31")

        n_symbols = 50
        symbols = [f"S{i:03d}" for i in range(n_symbols)]

        # Generate trading dates (business days)
        dates = pd.bdate_range(start=start, end=end)

        records = []
        rng = np.random.default_rng(seed=42)

        for sym in symbols:
            # Each stock has a different starting price and drift
            base_price = float(rng.uniform(10, 100))
            drift = float(rng.uniform(-0.0005, 0.001))
            vol = float(rng.uniform(0.01, 0.03))

            price = base_price
            for date in dates:
                ret = rng.normal(drift, vol)
                new_price = max(price * (1 + ret), 0.01)

                op = price * (1 + rng.normal(0, 0.003))
                cl = new_price
                # Ensure high >= max(open, close) and low <= min(open, close)
                high = max(op, cl) * (1 + abs(rng.normal(0, 0.005)))
                low = min(op, cl) * (1 - abs(rng.normal(0, 0.005)))
                volume = int(rng.uniform(1e6, 5e7))

                records.append(
                    {
                        "symbol": sym,
                        "trade_date": date,
                        "open": round(op, 4),
                        "high": round(high, 4),
                        "low": round(low, 4),
                        "close": round(cl, 4),
                        "volume": volume,
                        "amount": round(volume * cl, 2),
                        "market": "CN",
                        "exchange": "SYNTH",
                        "source": "synthetic",
                        "fetched_at": "2020-01-01T00:00:00",  # Fixed for determinism
                        "data_version": "synthetic-v1",
                    }
                )
                price = new_price

        df = pd.DataFrame(records)
        logger.info(
            "Generated synthetic data: %d rows, %d symbols, %s to %s",
            len(df),
            df["symbol"].nunique(),
            start.date(),
            end.date(),
        )
        return df


class AStockDataExportAdapter:
    """Adapter for importing data exported from a-stock-data tools.

    Only reads already-exported CSV/JSON/Parquet files. Does not
    directly call any public API.
    """

    def load(self, request: DataRequest) -> pd.DataFrame:
        """Load data from an a-stock-data export file.

        Expected fields: ts_code, trade_date, open, high, low, close, vol, amount
        """
        path = Path(request.path)
        if not path.exists():
            raise FileNotFoundError(f"Export file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(str(path))
        elif suffix == ".parquet":
            df = pd.read_parquet(str(path))
        elif suffix == ".json":
            df = pd.read_json(str(path))
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        df = StandardMarketData.normalize(df)

        # a-stock-data specific normalizations
        if "pct_chg" in df.columns:
            df["pct_change"] = df["pct_chg"]
        if "vol" in df.columns and "volume" not in df.columns:
            df["volume"] = df["vol"]

        df = self._filter(df, request)
        return df

    def _filter(self, df: pd.DataFrame, request: DataRequest) -> pd.DataFrame:
        if request.start_date:
            df = df[df["trade_date"] >= pd.Timestamp(request.start_date)]
        if request.end_date:
            df = df[df["trade_date"] <= pd.Timestamp(request.end_date)]
        if request.symbols:
            df = df[df["symbol"].isin(request.symbols)]
        return df


class GlobalStockDataExportAdapter:
    """Adapter for importing data exported from global-stock-data tools.

    Only reads already-exported CSV/JSON/Parquet files.
    """

    def load(self, request: DataRequest) -> pd.DataFrame:
        """Load data from a global-stock-data export file."""
        path = Path(request.path)
        if not path.exists():
            raise FileNotFoundError(f"Export file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(str(path))
        elif suffix == ".parquet":
            df = pd.read_parquet(str(path))
        elif suffix == ".json":
            df = pd.read_json(str(path))
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        df = StandardMarketData.normalize(df)

        # global-stock-data specific: may use 'ticker' instead of 'symbol'
        if "ticker" in df.columns and "symbol" not in df.columns:
            df["symbol"] = df["ticker"]

        df = self._filter(df, request)
        return df

    def _filter(self, df: pd.DataFrame, request: DataRequest) -> pd.DataFrame:
        if request.start_date:
            df = df[df["trade_date"] >= pd.Timestamp(request.start_date)]
        if request.end_date:
            df = df[df["trade_date"] <= pd.Timestamp(request.end_date)]
        if request.symbols:
            df = df[df["symbol"].isin(request.symbols)]
        return df


class VibeTradingExportAdapter:
    """Adapter for importing data exported from Vibe-Trading tools.

    Only reads already-exported CSV/JSON/Parquet files.
    """

    def load(self, request: DataRequest) -> pd.DataFrame:
        """Load data from a Vibe-Trading export file."""
        path = Path(request.path)
        if not path.exists():
            raise FileNotFoundError(f"Export file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(str(path))
        elif suffix == ".parquet":
            df = pd.read_parquet(str(path))
        elif suffix == ".json":
            df = pd.read_json(str(path))
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        df = StandardMarketData.normalize(df)
        df = self._filter(df, request)
        return df

    def _filter(self, df: pd.DataFrame, request: DataRequest) -> pd.DataFrame:
        if request.start_date:
            df = df[df["trade_date"] >= pd.Timestamp(request.start_date)]
        if request.end_date:
            df = df[df["trade_date"] <= pd.Timestamp(request.end_date)]
        if request.symbols:
            df = df[df["symbol"].isin(request.symbols)]
        return df


def create_snapshot_manifest(
    df: pd.DataFrame,
    source: str,
    file_path: str | Path,
) -> dict:
    """Create a raw data snapshot manifest for audit purposes.

    Args:
        df: The raw data DataFrame.
        source: Source description string.
        file_path: Path to the source file.

    Returns:
        Manifest dictionary with metadata and fingerprint.
    """
    path = Path(file_path)
    file_sha = ""
    if path.exists():
        sha256 = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        file_sha = sha256.hexdigest()

    manifest = {
        "source": source,
        "file_path": str(path),
        "file_sha256": file_sha,
        "fetched_at": datetime.now().isoformat(),
        "rows": len(df),
        "n_symbols": df["symbol"].nunique() if "symbol" in df.columns else 0,
        "start_date": str(df["trade_date"].min()) if "trade_date" in df.columns else None,
        "end_date": str(df["trade_date"].max()) if "trade_date" in df.columns else None,
        "fields": list(df.columns),
        "missing_rates": {
            col: float(df[col].isna().mean()) for col in df.columns if df[col].isna().any()
        },
        "duplicate_keys": 0,
        "data_fingerprint": StandardMarketData.compute_fingerprint(df),
    }

    # Count duplicate keys
    key_cols = [c for c in ["market", "exchange", "symbol", "trade_date"] if c in df.columns]
    if key_cols:
        manifest["duplicate_keys"] = int(df.duplicated(subset=key_cols).sum())

    return manifest
