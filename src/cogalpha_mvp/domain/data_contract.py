"""Standard data contract for market data.

Defines the minimum required fields, recommended extension fields,
and the DataRequest protocol used by all adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd

# Minimum required OHLCV fields
REQUIRED_FIELDS = ["symbol", "trade_date", "open", "high", "low", "close", "volume"]

# Recommended extension fields
RECOMMENDED_FIELDS = [
    "exchange",
    "market",
    "currency",
    "amount",
    "turnover",
    "adj_factor",
    "list_date",
    "delist_date",
    "is_st",
    "is_limit_up",
    "is_limit_down",
    "is_suspended",
    "source",
    "source_symbol",
    "fetched_at",
    "data_version",
]


@dataclass
class DataRequest:
    """Request object for loading market data.

    Attributes:
        path: File path for local adapters.
        start_date: Start date (inclusive) in YYYY-MM-DD format.
        end_date: End date (inclusive) in YYYY-MM-DD format.
        symbols: Optional list of symbols to filter. None = all.
        fields: Optional list of fields to select. None = all standard fields.
    """

    path: str = ""
    start_date: str = ""
    end_date: str = ""
    symbols: list[str] | None = None
    fields: list[str] | None = None


class MarketDataAdapter(Protocol):
    """Protocol for all market data adapters."""

    def load(self, request: DataRequest) -> pd.DataFrame:
        """Load market data according to the request.

        Args:
            request: Data request specifying path, date range, symbols.

        Returns:
            DataFrame with at least REQUIRED_FIELDS columns.
        """
        ...


class StandardMarketData:
    """Validator and normalizer for standard market data."""

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """Validate a DataFrame against the standard data contract.

        Returns:
            List of validation error messages. Empty list means valid.
        """
        errors: list[str] = []

        # Check required fields
        missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
        if missing:
            errors.append(f"Missing required fields: {missing}")

        if errors:
            return errors

        # Check data types
        if not pd.api.types.is_string_dtype(df["symbol"]):
            errors.append("symbol must be string type")

        # Check OHLC are positive
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                vals = df[col].dropna()
                if (vals <= 0).any():
                    errors.append(f"{col} contains non-positive values")

        # Check volume non-negative
        if "volume" in df.columns:
            vals = df["volume"].dropna()
            if (vals < 0).any():
                errors.append("volume contains negative values")

        # Check for duplicate primary keys
        if "trade_date" in df.columns and "symbol" in df.columns:
            market_col = "market" if "market" in df.columns else None
            exchange_col = "exchange" if "exchange" in df.columns else None
            key_cols = [c for c in [market_col, exchange_col, "symbol", "trade_date"] if c]
            dup_count = df.duplicated(subset=key_cols).sum()
            if dup_count > 0:
                errors.append(f"Found {dup_count} duplicate primary keys")

        # OHLC logical relationships
        for _, row in df.iterrows():
            o, h, lo, c = row.get("open"), row.get("high"), row.get("low"), row.get("close")
            if all(pd.notna(v) for v in [o, h, lo, c]) and (h < max(o, lo, c) or lo > min(o, h, c)):
                errors.append(
                    f"OHLC logic violation for {row.get('symbol')} on {row.get('trade_date')}"
                )
                break

        return errors

    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and types to standard contract.

        Args:
            df: Raw DataFrame.

        Returns:
            Normalized DataFrame.
        """
        df = df.copy()

        # Standardize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()

        # Common rename mappings
        rename_map = {
            "ts_code": "symbol",
            "code": "symbol",
            "ticker": "symbol",
            "date": "trade_date",
            "datetime": "trade_date",
            "vol": "volume",
            "amt": "amount",
            "pct_chg": "pct_change",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Ensure trade_date is datetime
        if "trade_date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["trade_date"])

        # Ensure symbol is string
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].astype(str)

        # Add default market/exchange if missing
        if "market" not in df.columns:
            df["market"] = "CN"
        if "exchange" not in df.columns:
            df["exchange"] = "UNKNOWN"

        return df

    @staticmethod
    def compute_fingerprint(df: pd.DataFrame) -> str:
        """Compute a SHA256 fingerprint of the data for audit purposes.

        Args:
            df: DataFrame to fingerprint.

        Returns:
            Hex digest string.
        """
        import hashlib
        import json

        info = {
            "rows": len(df),
            "columns": list(df.columns),
            "start_date": str(df["trade_date"].min()) if "trade_date" in df.columns else None,
            "end_date": str(df["trade_date"].max()) if "trade_date" in df.columns else None,
            "n_symbols": df["symbol"].nunique() if "symbol" in df.columns else 0,
            "missing_rates": {
                col: float(df[col].isna().mean()) for col in df.columns if df[col].isna().any()
            },
        }
        content = json.dumps(info, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
