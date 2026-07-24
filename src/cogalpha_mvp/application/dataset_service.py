"""Dataset management service."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

from ..persistence.database import Database
from ..persistence.repositories import DatasetQualityStatus, DatasetRepository

logger = logging.getLogger(__name__)

# Security: allowed file extensions
_ALLOWED_EXTENSIONS = {".csv", ".parquet"}
# Security: max file size (default 500MB)
_MAX_FILE_SIZE = 500 * 1024 * 1024
# Security: dangerous CSV formula prefixes
_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path components
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = re.sub(r"[^\w\.\-]", "_", filename)
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[: 200 - len(ext)] + ext
    return filename


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _check_path_traversal(path: str) -> bool:
    """Check if path contains path traversal attempts."""
    if ".." in path or path.startswith("/"):
        return True
    return False


def _sanitize_csv_value(value: str) -> str:
    """Sanitize CSV cell values to prevent formula injection."""
    if isinstance(value, str) and value.startswith(_DANGEROUS_PREFIXES):
        return "'" + value
    return value


class DatasetService:
    """Application service for dataset management."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def upload_dataset(
        self,
        project_id: str,
        filename: str,
        file_data: bytes,
        storage_dir: Path,
    ) -> dict[str, Any]:
        """Upload a dataset file."""
        # Security checks
        ext = Path(filename).suffix.lower()
        if ext not in _ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Allowed: {_ALLOWED_EXTENSIONS}")

        if len(file_data) > _MAX_FILE_SIZE:
            raise ValueError(f"File too large: {len(file_data)} bytes. Max: {_MAX_FILE_SIZE}")

        safe_name = _sanitize_filename(filename)
        if _check_path_traversal(safe_name):
            raise ValueError("Invalid filename")

        storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = storage_dir / safe_name
        file_path.write_bytes(file_data)

        sha256 = _compute_sha256(file_path)

        # Parse data to get metadata
        metadata = self._extract_metadata(file_path, ext)

        with self.db.session() as session:
            repo = DatasetRepository(session)
            ds = repo.create(
                project_id=project_id,
                name=safe_name,
                source_type=ext.lstrip("."),
                original_filename=filename,
                stored_path=str(file_path),
                sha256=sha256,
                row_count=metadata["row_count"],
                symbol_count=metadata["symbol_count"],
                start_date=metadata["start_date"],
                end_date=metadata["end_date"],
            )
            return self._to_dict(ds)

    def register_local(
        self,
        project_id: str,
        name: str,
        file_path: str,
    ) -> dict[str, Any]:
        """Register a local file as a dataset (without copying)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext not in _ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        sha256 = _compute_sha256(path)
        metadata = self._extract_metadata(path, ext)

        with self.db.session() as session:
            repo = DatasetRepository(session)
            ds = repo.create(
                project_id=project_id,
                name=name,
                source_type=ext.lstrip("."),
                original_filename=path.name,
                stored_path=str(path),
                sha256=sha256,
                row_count=metadata["row_count"],
                symbol_count=metadata["symbol_count"],
                start_date=metadata["start_date"],
                end_date=metadata["end_date"],
            )
            return self._to_dict(ds)

    def list_datasets(self, project_id: str) -> list[dict[str, Any]]:
        with self.db.session() as session:
            repo = DatasetRepository(session)
            return [self._to_dict(d) for d in repo.list_by_project(project_id)]

    def get_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        with self.db.session() as session:
            repo = DatasetRepository(session)
            ds = repo.get(dataset_id)
            return self._to_dict(ds) if ds else None

    def delete_dataset(self, dataset_id: str, delete_file: bool = False) -> bool:
        with self.db.session() as session:
            repo = DatasetRepository(session)
            ds = repo.get(dataset_id)
            if ds is None:
                return False
            if delete_file and ds.stored_path:
                try:
                    Path(ds.stored_path).unlink(missing_ok=True)
                except OSError:
                    logger.warning("Failed to delete file: %s", ds.stored_path)
            repo.delete(dataset_id)
            return True

    def validate_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Validate dataset and return quality report."""
        with self.db.session() as session:
            repo = DatasetRepository(session)
            ds = repo.get(dataset_id)
            if ds is None:
                raise ValueError(f"Dataset not found: {dataset_id}")

            file_path = Path(ds.stored_path)
            if not file_path.exists():
                repo.update(
                    dataset_id,
                    quality_status=DatasetQualityStatus.INVALID,
                    quality_report=json.dumps({"error": "File not found"}),
                )
                return {"status": "invalid", "error": "File not found"}

            try:
                quality = self._compute_quality(file_path, ds.source_type)
                repo.update(
                    dataset_id,
                    quality_status=DatasetQualityStatus.VALID,
                    quality_report=json.dumps(quality),
                )
                return quality
            except Exception as e:
                logger.error("Dataset validation failed: %s", e)
                repo.update(
                    dataset_id,
                    quality_status=DatasetQualityStatus.INVALID,
                    quality_report=json.dumps({"error": str(e)}),
                )
                return {"status": "invalid", "error": str(e)}

    def preview_dataset(self, dataset_id: str, n_rows: int = 50) -> dict[str, Any]:
        """Preview first n_rows of a dataset."""
        with self.db.session() as session:
            repo = DatasetRepository(session)
            ds = repo.get(dataset_id)
            if ds is None:
                raise ValueError(f"Dataset not found: {dataset_id}")

            file_path = Path(ds.stored_path)
            if ds.source_type == "csv":
                df = pd.read_csv(file_path, nrows=n_rows)
            else:
                df = pd.read_parquet(file_path).head(n_rows)

            return {
                "columns": list(df.columns),
                "rows": df.head(n_rows).to_dict(orient="records"),
                "n_rows": len(df),
            }

    def _extract_metadata(self, file_path: Path, ext: str) -> dict[str, Any]:
        """Extract metadata from data file."""
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_parquet(file_path)

        row_count = len(df)
        symbol_col = (
            "symbol" if "symbol" in df.columns else "ticker" if "ticker" in df.columns else None
        )
        symbol_count = int(df[symbol_col].nunique()) if symbol_col else 0

        date_col = (
            "trade_date" if "trade_date" in df.columns else "date" if "date" in df.columns else None
        )
        if date_col and date_col in df.columns:
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
            start_date = str(dates.min().date()) if len(dates) > 0 else ""
            end_date = str(dates.max().date()) if len(dates) > 0 else ""
        else:
            start_date = ""
            end_date = ""

        return {
            "row_count": row_count,
            "symbol_count": symbol_count,
            "start_date": start_date,
            "end_date": end_date,
        }

    def _compute_quality(self, file_path: Path, source_type: str) -> dict[str, Any]:
        """Compute data quality report."""
        if source_type == "csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_parquet(file_path)

        required = {"open", "high", "low", "close", "volume"}
        actual = set(df.columns.str.lower())
        missing = required - actual

        date_col = "trade_date" if "trade_date" in df.columns else "date"
        symbol_col = "symbol" if "symbol" in df.columns else "ticker"

        # Missing rate
        missing_rates = {}
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                missing_rates[col] = float(df[col].isna().mean())

        # Duplicates
        dup_count = 0
        if date_col in df.columns and symbol_col in df.columns:
            dup_count = int(df.duplicated(subset=[symbol_col, date_col]).sum())

        # OHLC anomalies
        ohlc_anomalies = 0
        if all(c in df.columns for c in ["open", "high", "low", "close"]):
            ohlc_anomalies = int(((df["high"] < df["low"]) | (df["high"] < df["open"])).sum())

        return {
            "status": "valid" if not missing else "invalid",
            "missing_fields": list(missing),
            "row_count": len(df),
            "symbol_count": int(df[symbol_col].nunique()) if symbol_col in df.columns else 0,
            "missing_rates": missing_rates,
            "duplicate_keys": dup_count,
            "ohlc_anomalies": ohlc_anomalies,
        }

    @staticmethod
    def _to_dict(ds: Any) -> dict[str, Any]:
        return {
            "id": ds.id,
            "project_id": ds.project_id,
            "name": ds.name,
            "source_type": ds.source_type,
            "original_filename": ds.original_filename,
            "stored_path": ds.stored_path,
            "sha256": ds.sha256,
            "row_count": ds.row_count,
            "symbol_count": ds.symbol_count,
            "start_date": ds.start_date,
            "end_date": ds.end_date,
            "schema_version": ds.schema_version,
            "quality_status": ds.quality_status.value
            if hasattr(ds.quality_status, "value")
            else str(ds.quality_status),
            "quality_report": json.loads(ds.quality_report) if ds.quality_report else {},
            "created_at": ds.created_at.isoformat() if ds.created_at else None,
        }
