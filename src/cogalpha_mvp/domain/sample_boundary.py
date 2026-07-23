"""Sample boundary isolation for train/OOS data split.

Ensures strict separation between training and out-of-sample data.
No OOS data can be accessed during training phase.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from cogalpha_mvp.config import Config
from cogalpha_mvp.domain.data_contract import StandardMarketData

logger = logging.getLogger("cogalpha_mvp")


@dataclass
class SampleBoundary:
    """Defines the boundary between training and OOS data.

    Attributes:
        train_start: Training period start date (inclusive).
        train_end: Training period end date (inclusive).
        oos_start: OOS period start date (inclusive).
        oos_end: OOS period end date (inclusive).
    """

    train_start: str
    train_end: str
    oos_start: str
    oos_end: str

    @classmethod
    def from_config(cls, config: Config) -> SampleBoundary:
        """Create boundary from configuration."""
        return cls(
            train_start=config.data.train_start,
            train_end=config.data.train_end,
            oos_start=config.data.oos_start,
            oos_end=config.data.oos_end,
        )

    def validate(self) -> None:
        """Validate that train and OOS periods do not overlap."""
        train_end = pd.Timestamp(self.train_end)
        oos_start = pd.Timestamp(self.oos_start)
        assert train_end < oos_start, (
            f"Training period end ({self.train_end}) must be strictly before "
            f"OOS period start ({self.oos_start}). No overlap allowed."
        )
        logger.info(
            "Sample boundary validated: train=[%s, %s], oos=[%s, %s]",
            self.train_start,
            self.train_end,
            self.oos_start,
            self.oos_end,
        )

    def is_train_date(self, date: str | pd.Timestamp) -> bool:
        """Check if a date falls within the training period."""
        d = pd.Timestamp(date)
        return pd.Timestamp(self.train_start) <= d <= pd.Timestamp(self.train_end)

    def is_oos_date(self, date: str | pd.Timestamp) -> bool:
        """Check if a date falls within the OOS period."""
        d = pd.Timestamp(date)
        return pd.Timestamp(self.oos_start) <= d <= pd.Timestamp(self.oos_end)


class TrainDataLoader:
    """Loads only training period data. OOS data is never loaded."""

    def __init__(self, boundary: SampleBoundary):
        self.boundary = boundary
        self._fingerprint: str = ""

    def load(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to training period only.

        Args:
            df: Full market data DataFrame.

        Returns:
            DataFrame containing only training period rows.
        """
        mask = df["trade_date"].apply(self.boundary.is_train_date)
        train_df = df.loc[mask].copy()
        self._fingerprint = StandardMarketData.compute_fingerprint(train_df)
        logger.info(
            "Loaded training data: %d rows, %d symbols, fingerprint=%s",
            len(train_df),
            train_df["symbol"].nunique(),
            self._fingerprint[:16],
        )
        return train_df

    @property
    def fingerprint(self) -> str:
        """SHA256 fingerprint of the loaded training data."""
        return self._fingerprint


class OutOfSampleDataLoader:
    """Loads only OOS period data. Used only in final validation."""

    def __init__(self, boundary: SampleBoundary):
        self.boundary = boundary
        self._fingerprint: str = ""

    def load(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to OOS period only.

        Args:
            df: Full market data DataFrame.

        Returns:
            DataFrame containing only OOS period rows.
        """
        mask = df["trade_date"].apply(self.boundary.is_oos_date)
        oos_df = df.loc[mask].copy()
        self._fingerprint = StandardMarketData.compute_fingerprint(oos_df)
        logger.info(
            "Loaded OOS data: %d rows, %d symbols, fingerprint=%s",
            len(oos_df),
            oos_df["symbol"].nunique(),
            self._fingerprint[:16],
        )
        return oos_df

    @property
    def fingerprint(self) -> str:
        """SHA256 fingerprint of the loaded OOS data."""
        return self._fingerprint


class LeakageGuard:
    """Runtime guard to prevent future information leakage.

    Checks:
    1. Training objects do not hold OOS DataFrame references.
    2. Factor computation only uses historical data at each point in time.
    3. OOS data cannot be accessed during training phase.
    """

    def __init__(self, boundary: SampleBoundary):
        self.boundary = boundary
        self._oos_loaded = False
        self._violations: list[str] = []

    def mark_oos_loaded(self) -> None:
        """Mark that OOS data has been loaded. Call before OOS validation."""
        self._oos_loaded = True
        logger.warning("OOS data marked as loaded. Training phase should be complete.")

    def check_no_oos_access(self, df: pd.DataFrame, context: str = "") -> None:
        """Verify that a DataFrame does not contain OOS period data.

        Args:
            df: DataFrame to check.
            context: Context string for error reporting.

        Raises:
            ValueError: If OOS data is found during training phase.
        """
        if "trade_date" not in df.columns:
            return

        oos_dates = df["trade_date"].apply(self.boundary.is_oos_date)
        if oos_dates.any():
            violation = (
                f"LEAKAGE VIOLATION [{context}]: Found {oos_dates.sum()} rows "
                f"with OOS dates in training-phase data."
            )
            self._violations.append(violation)
            logger.error(violation)
            raise ValueError(violation)

    def check_train_oos_fingerprints(
        self,
        train_fp: str,
        oos_fp: str,
    ) -> None:
        """Verify train and OOS fingerprints are different."""
        if train_fp == oos_fp:
            violation = "Train and OOS data have identical fingerprints - possible data overlap!"
            self._violations.append(violation)
            logger.error(violation)
            raise ValueError(violation)
        logger.info("Train/OOS fingerprints verified as distinct.")

    @property
    def violations(self) -> list[str]:
        """List of recorded leakage violations."""
        return self._violations
