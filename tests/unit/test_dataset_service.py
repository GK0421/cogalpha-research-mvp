"""Tests for dataset service file operations."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from cogalpha_mvp.application import DatasetService, ProjectService
from cogalpha_mvp.persistence.database import Database
from cogalpha_mvp.product.paths import WorkspaceManager


@pytest.fixture
def services():
    tmpdir = tempfile.mkdtemp()
    os.environ["COGALPHA_HOME"] = tmpdir
    ws = WorkspaceManager()
    ws.initialize()
    db = Database(ws)
    db.create_tables()
    yield {
        "project": ProjectService(db),
        "dataset": DatasetService(db),
        "db": db,
        "ws": ws,
    }
    db.drop_tables()


def _create_test_csv(path: Path) -> Path:
    """Create a small test CSV file."""
    df = pd.DataFrame(
        {
            "symbol": ["000001", "000001", "000002", "000002"],
            "trade_date": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"],
            "open": [10.0, 10.5, 20.0, 20.5],
            "high": [10.5, 11.0, 20.5, 21.0],
            "low": [9.8, 10.2, 19.5, 20.0],
            "close": [10.2, 10.8, 20.2, 20.8],
            "volume": [1000, 1200, 2000, 2200],
        }
    )
    df.to_csv(path, index=False)
    return path


class TestDatasetUpload:
    def test_upload_csv(self, services):
        proj = services["project"].create_project(name="Test")
        csv_data = b"symbol,trade_date,open,high,low,close,volume\n000001,2024-01-01,10,10.5,9.8,10.2,1000\n"

        ds = services["dataset"].upload_dataset(
            project_id=proj["id"],
            filename="test.csv",
            file_data=csv_data,
            storage_dir=Path(tempfile.mkdtemp()),
        )
        assert ds["name"] == "test.csv"
        assert ds["source_type"] == "csv"
        assert ds["row_count"] == 1

    def test_upload_invalid_extension(self, services):
        proj = services["project"].create_project(name="Test")
        with pytest.raises(ValueError, match="Unsupported"):
            services["dataset"].upload_dataset(
                project_id=proj["id"],
                filename="test.txt",
                file_data=b"data",
                storage_dir=Path(tempfile.mkdtemp()),
            )

    def test_upload_too_large(self, services):
        proj = services["project"].create_project(name="Test")
        # Create data > 500MB limit
        with pytest.raises(ValueError, match="too large"):
            services["dataset"].upload_dataset(
                project_id=proj["id"],
                filename="test.csv",
                file_data=b"x" * (501 * 1024 * 1024),
                storage_dir=Path(tempfile.mkdtemp()),
            )

    def test_register_local(self, services):
        proj = services["project"].create_project(name="Test")
        csv_path = _create_test_csv(Path(tempfile.mkdtemp()) / "local.csv")

        ds = services["dataset"].register_local(
            project_id=proj["id"],
            name="local_data",
            file_path=str(csv_path),
        )
        assert ds["name"] == "local_data"
        assert ds["row_count"] == 4
        assert ds["symbol_count"] == 2

    def test_register_local_not_found(self, services):
        proj = services["project"].create_project(name="Test")
        with pytest.raises(FileNotFoundError):
            services["dataset"].register_local(
                project_id=proj["id"],
                name="missing",
                file_path="/nonexistent/path.csv",
            )

    def test_validate_dataset(self, services):
        proj = services["project"].create_project(name="Test")
        csv_path = _create_test_csv(Path(tempfile.mkdtemp()) / "test.csv")
        ds = services["dataset"].register_local(
            project_id=proj["id"],
            name="test",
            file_path=str(csv_path),
        )

        result = services["dataset"].validate_dataset(ds["id"])
        assert result["status"] == "valid"
        assert result["row_count"] == 4
        assert result["symbol_count"] == 2

    def test_preview_dataset(self, services):
        proj = services["project"].create_project(name="Test")
        csv_path = _create_test_csv(Path(tempfile.mkdtemp()) / "test.csv")
        ds = services["dataset"].register_local(
            project_id=proj["id"],
            name="test",
            file_path=str(csv_path),
        )

        preview = services["dataset"].preview_dataset(ds["id"], n_rows=2)
        assert preview["n_rows"] == 2
        assert "symbol" in preview["columns"]

    def test_delete_dataset_with_file(self, services):
        proj = services["project"].create_project(name="Test")
        storage_dir = Path(tempfile.mkdtemp())
        csv_data = b"symbol,close\n000001,10.0\n"
        ds = services["dataset"].upload_dataset(
            project_id=proj["id"],
            filename="test.csv",
            file_data=csv_data,
            storage_dir=storage_dir,
        )

        result = services["dataset"].delete_dataset(ds["id"], delete_file=True)
        assert result is True
        assert services["dataset"].get_dataset(ds["id"]) is None

    def test_get_dataset_not_found(self, services):
        assert services["dataset"].get_dataset("nonexistent") is None

    def test_validate_dataset_not_found(self, services):
        with pytest.raises(ValueError):
            services["dataset"].validate_dataset("nonexistent")

    def test_preview_dataset_not_found(self, services):
        with pytest.raises(ValueError):
            services["dataset"].preview_dataset("nonexistent")
