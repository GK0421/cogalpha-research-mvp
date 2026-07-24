"""Tests for application services."""

from __future__ import annotations

import os
import tempfile

import pytest

from cogalpha_mvp.application import (
    DatasetService,
    FactorService,
    ProjectService,
    RunService,
    SettingsService,
)
from cogalpha_mvp.persistence.database import Database
from cogalpha_mvp.product.paths import WorkspaceManager


@pytest.fixture
def services():
    """Create all services with a temporary database."""
    tmpdir = tempfile.mkdtemp()
    os.environ["COGALPHA_HOME"] = tmpdir
    ws = WorkspaceManager()
    ws.initialize()
    db = Database(ws)
    db.create_tables()

    yield {
        "project": ProjectService(db),
        "dataset": DatasetService(db),
        "factor": FactorService(db),
        "run": RunService(db),
        "settings": SettingsService(db),
        "db": db,
    }
    db.drop_tables()


class TestProjectService:
    def test_create_and_get(self, services):
        svc = services["project"]
        p = svc.create_project(name="Test", description="desc")
        assert p["name"] == "Test"
        assert p["status"] == "active"

        fetched = svc.get_project(p["id"])
        assert fetched is not None
        assert fetched["name"] == "Test"

    def test_list_projects(self, services):
        svc = services["project"]
        svc.create_project(name="A")
        svc.create_project(name="B")
        assert len(svc.list_projects()) == 2

    def test_update_project(self, services):
        svc = services["project"]
        p = svc.create_project(name="Old")
        updated = svc.update_project(p["id"], name="New")
        assert updated["name"] == "New"

    def test_delete_project(self, services):
        svc = services["project"]
        p = svc.create_project(name="Test")
        assert svc.delete_project(p["id"]) is True
        # Soft delete - still exists but not in list
        assert svc.get_project(p["id"]) is not None
        assert len(svc.list_projects()) == 0


class TestFactorService:
    def test_validate_expression_valid(self, services):
        svc = services["factor"]
        result = svc.validate_expression("ts_rank(close, 20)")
        assert result["valid"] is True
        assert len(result["hash"]) > 0

    def test_validate_expression_invalid(self, services):
        svc = services["factor"]
        result = svc.validate_expression("exec('import os')")
        assert result["valid"] is False
        assert "Forbidden" in result["error"] or "forbidden" in result["error"].lower()

    def test_create_factor(self, services):
        proj_svc = services["project"]
        p = proj_svc.create_project(name="Test")

        fac_svc = services["factor"]
        f = fac_svc.create_factor(
            project_id=p["id"],
            name="Momentum",
            expression="ts_rank(close, 20)",
            agent_id="Agent_01",
        )
        assert f["name"] == "Momentum"
        assert f["validation_status"] == "valid"

    def test_seed_factors(self, services):
        proj_svc = services["project"]
        p = proj_svc.create_project(name="Test")

        fac_svc = services["factor"]
        factors = fac_svc.seed_project_factors(p["id"])
        assert len(factors) == 21

        listed = fac_svc.list_factors(p["id"])
        assert len(listed) == 21

    def test_generate_with_llm_no_key(self, services):
        svc = services["factor"]
        result = svc.generate_with_llm(
            project_id="dummy",
            provider="none",
            api_key="",
        )
        assert result["status"] == "LLM_PROVIDER_NOT_CONFIGURED"


class TestRunService:
    def test_create_and_get_run(self, services):
        proj_svc = services["project"]
        p = proj_svc.create_project(name="Test")

        run_svc = services["run"]
        run = run_svc.create_run(project_id=p["id"])
        assert run["status"] == "pending"

        fetched = run_svc.get_run(run["id"])
        assert fetched is not None

    def test_update_run_status(self, services):
        proj_svc = services["project"]
        p = proj_svc.create_project(name="Test")

        run_svc = services["run"]
        run = run_svc.create_run(project_id=p["id"])
        updated = run_svc.update_run_status(
            run["id"], status="running", progress=50.0, current_stage="LOADING_DATA"
        )
        assert updated["status"] == "running"
        assert updated["progress"] == 50.0

    def test_cancel_run(self, services):
        proj_svc = services["project"]
        p = proj_svc.create_project(name="Test")

        run_svc = services["run"]
        run = run_svc.create_run(project_id=p["id"])
        run_svc.update_run_status(run["id"], status="running")
        cancelled = run_svc.cancel_run(run["id"])
        assert cancelled["status"] == "cancel_requested"

    def test_rerun(self, services):
        proj_svc = services["project"]
        p = proj_svc.create_project(name="Test")

        run_svc = services["run"]
        run = run_svc.create_run(project_id=p["id"])
        new_run = run_svc.rerun(run["id"])
        assert new_run is not None
        assert new_run["id"] != run["id"]

    def test_recover_interrupted(self, services):
        proj_svc = services["project"]
        p = proj_svc.create_project(name="Test")

        run_svc = services["run"]
        run = run_svc.create_run(project_id=p["id"])
        run_svc.update_run_status(run["id"], status="running")

        recovered = run_svc.recover_interrupted()
        assert len(recovered) == 1


class TestSettingsService:
    def test_get_all(self, services):
        svc = services["settings"]
        svc.initialize_defaults()
        settings = svc.get_all()
        assert "api.host" in settings
        assert settings["api.host"] == "127.0.0.1"

    def test_set_and_get(self, services):
        svc = services["settings"]
        svc.set("test.key", "test_value")
        assert svc.get("test.key") == "test_value"

    def test_update_multiple(self, services):
        svc = services["settings"]
        svc.update({"key1": "val1", "key2": "val2"})
        assert svc.get("key1") == "val1"
        assert svc.get("key2") == "val2"

    def test_llm_config(self, services):
        svc = services["settings"]
        svc.initialize_defaults()
        config = svc.get_llm_config()
        assert config["enabled"] is False
        assert config["provider"] == "none"
