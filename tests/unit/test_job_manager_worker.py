"""Tests for job manager and worker."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from cogalpha_mvp.application import ProjectService, RunService
from cogalpha_mvp.jobs.manager import JobManager
from cogalpha_mvp.jobs.worker import JobWorker
from cogalpha_mvp.persistence.database import Database
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
    }
    db.drop_tables()


class TestJobManager:
    def test_create_and_recover(self, db_setup):
        mgr = JobManager(db_setup["db"], db_setup["ws"].root, max_concurrent=1)
        assert mgr.get_active_count() == 0

        # Recover should work with no interrupted runs
        recovered = mgr.recover_interrupted()
        assert recovered == []

    def test_recover_with_interrupted(self, db_setup):
        proj = db_setup["project_svc"].create_project(name="Test")
        run = db_setup["run_svc"].create_run(project_id=proj["id"])
        db_setup["run_svc"].update_run_status(run["id"], status="running")

        mgr = JobManager(db_setup["db"], db_setup["ws"].root, max_concurrent=1)
        recovered = mgr.recover_interrupted()
        assert len(recovered) == 1

        # Verify run is now interrupted
        updated = db_setup["run_svc"].get_run(run["id"])
        assert updated["status"] == "interrupted"

    def test_cancel_nonexistent_run(self, db_setup):
        mgr = JobManager(db_setup["db"], db_setup["ws"].root, max_concurrent=1)
        # Cancel should not raise even for nonexistent run
        result = mgr.cancel_run("nonexistent")
        assert result is True

    def test_max_concurrent(self, db_setup):
        mgr = JobManager(db_setup["db"], db_setup["ws"].root, max_concurrent=1)
        assert mgr.max_concurrent == 1


class TestJobWorker:
    def test_worker_creation(self, db_setup):
        run_svc = db_setup["run_svc"]
        worker = JobWorker(run_svc, db_setup["ws"].root)
        assert worker.workspace_root == db_setup["ws"].root
        assert len(worker.STEP_TO_STAGE) == 11

    def test_is_cancelled(self, db_setup):
        run_svc = db_setup["run_svc"]
        worker = JobWorker(run_svc, db_setup["ws"].root)
        assert not worker.is_cancelled("nonexistent")
        worker.request_cancel("test-run")
        assert worker.is_cancelled("test-run")

    def test_execute_run_failure(self, db_setup):
        """Test that a run with invalid config fails gracefully."""
        proj = db_setup["project_svc"].create_project(name="Test")
        run = db_setup["run_svc"].create_run(project_id=proj["id"])

        worker = JobWorker(db_setup["run_svc"], db_setup["ws"].root)

        # Mock config that will cause an error
        mock_config = MagicMock()
        mock_config.output_dir = "/nonexistent"
        mock_config.run_id = run["id"]

        with patch("cogalpha_mvp.jobs.worker.PipelineRunner") as mock_runner_cls:
            mock_runner = MagicMock()
            mock_runner.run_all.side_effect = RuntimeError("Test error")
            mock_runner_cls.return_value = mock_runner

            with pytest.raises(RuntimeError, match="Test error"):
                worker.execute_run(run["id"], mock_config)

        # Verify run status was updated to failed
        updated = db_setup["run_svc"].get_run(run["id"])
        assert updated["status"] == "failed"
        assert "Test error" in updated["error_message"]
