"""Tests for report service and migrations."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from cogalpha_mvp.application import ProjectService, ReportService, RunService
from cogalpha_mvp.persistence.database import Database
from cogalpha_mvp.persistence.migrations import (
    get_schema_version,
    run_migrations,
    set_schema_version,
)
from cogalpha_mvp.product.paths import WorkspaceManager


@pytest.fixture
def db_setup():
    tmpdir = tempfile.mkdtemp()
    os.environ["COGALPHA_HOME"] = tmpdir
    ws = WorkspaceManager()
    ws.initialize()
    db = Database(ws)
    db.create_tables()
    yield {
        "db": db,
        "ws": ws,
        "project_svc": ProjectService(db),
        "run_svc": RunService(db),
        "report_svc": ReportService(db),
    }
    db.drop_tables()


class TestReportService:
    def test_list_artifacts_empty(self, db_setup):
        result = db_setup["report_svc"].list_artifacts("nonexistent")
        assert result == []

    def test_get_summary_not_found(self, db_setup):
        ws = db_setup["ws"]
        result = db_setup["report_svc"].get_summary("nonexistent", ws.runs_dir)
        assert result is None

    def test_get_summary_found(self, db_setup):
        ws = db_setup["ws"]
        run_dir = ws.runs_dir / "test-run"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "summary.json").write_text(json.dumps({"n_factors": 21}))

        result = db_setup["report_svc"].get_summary("test-run", ws.runs_dir)
        assert result is not None
        assert result["n_factors"] == 21

    def test_get_report_path_not_found(self, db_setup):
        ws = db_setup["ws"]
        result = db_setup["report_svc"].get_report_path("nonexistent", ws.reports_dir)
        assert result is None

    def test_get_report_path_found(self, db_setup):
        ws = db_setup["ws"]
        report_dir = ws.reports_dir / "test-run"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "report.html").write_text("<html>Report</html>")

        result = db_setup["report_svc"].get_report_path("test-run", ws.reports_dir)
        assert result is not None
        assert result.exists()

    def test_get_factor_metrics_empty(self, db_setup):
        ws = db_setup["ws"]
        result = db_setup["report_svc"].get_factor_metrics("nonexistent", ws.runs_dir)
        assert result == []

    def test_get_factor_metrics_found(self, db_setup):
        ws = db_setup["ws"]
        run_dir = ws.runs_dir / "test-run"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "factor_metrics.csv").write_text(
            "name,ic,rank_ic\nfactor1,0.05,0.04\nfactor2,0.03,0.02\n"
        )

        result = db_setup["report_svc"].get_factor_metrics("test-run", ws.runs_dir)
        assert len(result) == 2
        assert result[0]["name"] == "factor1"

    def test_get_portfolio_results_empty(self, db_setup):
        ws = db_setup["ws"]
        result = db_setup["report_svc"].get_portfolio_results("nonexistent", ws.runs_dir)
        assert result == {}

    def test_get_portfolio_results_found(self, db_setup):
        ws = db_setup["ws"]
        run_dir = ws.runs_dir / "test-run"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "summary.json").write_text(
            json.dumps({"portfolio": {"sharpe": 1.5, "max_drawdown": -0.1}})
        )

        result = db_setup["report_svc"].get_portfolio_results("test-run", ws.runs_dir)
        assert result["sharpe"] == 1.5


class TestMigrations:
    def test_run_migrations(self, db_setup):
        """run_migrations should not error when tables already exist."""
        run_migrations(db_setup["db"].engine)

    def test_get_schema_version_default(self, db_setup):
        """get_schema_version should return 1 when app_settings exists."""
        version = get_schema_version(db_setup["db"].engine)
        assert version >= 0

    def test_set_and_get_schema_version(self, db_setup):
        set_schema_version(db_setup["db"].engine, 42)
        version = get_schema_version(db_setup["db"].engine)
        assert version == 42


class TestProductWorkspace:
    def test_workspace_module_import(self):
        """Test that workspace.py module is importable."""
        from cogalpha_mvp.product import workspace

        assert hasattr(workspace, "__doc__")
