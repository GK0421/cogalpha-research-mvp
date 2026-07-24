"""Tests for job system."""

from __future__ import annotations

import os
import tempfile

import pytest

from cogalpha_mvp.application import ProjectService, RunService
from cogalpha_mvp.jobs.events import JobEvent
from cogalpha_mvp.jobs.models import STAGE_PROGRESS, JobStage
from cogalpha_mvp.jobs.recovery import recover_runs
from cogalpha_mvp.persistence.database import Database
from cogalpha_mvp.product.paths import WorkspaceManager


@pytest.fixture
def db():
    tmpdir = tempfile.mkdtemp()
    os.environ["COGALPHA_HOME"] = tmpdir
    ws = WorkspaceManager()
    ws.initialize()
    database = Database(ws)
    database.create_tables()
    yield database
    database.drop_tables()


class TestJobStage:
    def test_stage_values(self):
        assert JobStage.INITIALIZING.value == "INITIALIZING"
        assert JobStage.REPORTING.value == "REPORTING"
        assert JobStage.FINALIZING.value == "FINALIZING"

    def test_stage_progress(self):
        assert STAGE_PROGRESS[JobStage.INITIALIZING] == 0.0
        assert STAGE_PROGRESS[JobStage.LOADING_DATA] == 5.0
        assert STAGE_PROGRESS[JobStage.FINALIZING] == 100.0
        # Monotonically increasing
        stages = list(STAGE_PROGRESS.keys())
        for i in range(1, len(stages)):
            assert STAGE_PROGRESS[stages[i]] >= STAGE_PROGRESS[stages[i - 1]]


class TestJobEvent:
    def test_to_dict(self):
        event = JobEvent(
            run_id="run-1",
            stage="LOADING_DATA",
            message="Loading dataset",
        )
        d = event.to_dict()
        assert d["run_id"] == "run-1"
        assert d["stage"] == "LOADING_DATA"
        assert d["level"] == "INFO"
        assert "timestamp" in d

    def test_to_json(self):
        event = JobEvent(
            run_id="run-1",
            stage="INITIALIZING",
            message="Starting",
        )
        import json

        parsed = json.loads(event.to_json())
        assert parsed["run_id"] == "run-1"

    def test_with_data(self):
        event = JobEvent(
            run_id="run-1",
            stage="QUALITY_CHECKING",
            message="Checked 21 factors",
            data={"passed": 19, "failed": 2},
        )
        assert event.data["passed"] == 19


class TestRecovery:
    def test_recover_no_interrupted(self, db):
        run_svc = RunService(db)
        recovered = recover_runs(run_svc)
        assert len(recovered) == 0

    def test_recover_interrupted(self, db):
        proj_svc = ProjectService(db)
        p = proj_svc.create_project(name="Test")
        run_svc = RunService(db)
        run = run_svc.create_run(project_id=p["id"])
        run_svc.update_run_status(run["id"], status="running")

        recovered = recover_runs(run_svc)
        assert len(recovered) == 1

        # Check that it's now marked interrupted
        updated = run_svc.get_run(run["id"])
        assert updated["status"] == "interrupted"
