"""Tests for persistence layer (database, models, repositories)."""

from __future__ import annotations

import os
import tempfile

import pytest

from cogalpha_mvp.persistence.database import Database
from cogalpha_mvp.persistence.models import (
    FactorOrigin,
    FactorValidationStatus,
    ProjectStatus,
    RunStatus,
    RunType,
)
from cogalpha_mvp.persistence.repositories import (
    ArtifactRepository,
    DatasetRepository,
    FactorRepository,
    ProjectRepository,
    RunRepository,
    SettingRepository,
)
from cogalpha_mvp.product.paths import WorkspaceManager


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    tmpdir = tempfile.mkdtemp()
    os.environ["COGALPHA_HOME"] = tmpdir
    ws = WorkspaceManager()
    ws.initialize()
    database = Database(ws)
    database.create_tables()
    yield database
    database.drop_tables()


class TestProjectRepository:
    def test_create_project(self, db):
        with db.session() as session:
            repo = ProjectRepository(session)
            p = repo.create(name="Test", description="desc")
            assert p.id is not None
            assert p.name == "Test"
            assert p.description == "desc"
            assert p.status == ProjectStatus.ACTIVE

    def test_get_project(self, db):
        with db.session() as session:
            repo = ProjectRepository(session)
            p = repo.create(name="Test")
            fetched = repo.get(p.id)
            assert fetched is not None
            assert fetched.name == "Test"

    def test_get_nonexistent(self, db):
        with db.session() as session:
            repo = ProjectRepository(session)
            assert repo.get("nonexistent") is None

    def test_list_all(self, db):
        with db.session() as session:
            repo = ProjectRepository(session)
            repo.create(name="A")
            repo.create(name="B")
            assert len(repo.list_all()) == 2

    def test_update_project(self, db):
        with db.session() as session:
            repo = ProjectRepository(session)
            p = repo.create(name="Old")
            updated = repo.update(p.id, name="New")
            assert updated.name == "New"

    def test_soft_delete(self, db):
        with db.session() as session:
            repo = ProjectRepository(session)
            p = repo.create(name="Test")
            assert repo.delete(p.id) is True
            assert repo.get(p.id) is not None  # still exists
            assert repo.get(p.id).status == ProjectStatus.DELETED
            assert len(repo.list_all()) == 0  # not in active list

    def test_permanent_delete(self, db):
        with db.session() as session:
            repo = ProjectRepository(session)
            p = repo.create(name="Test")
            assert repo.delete(p.id, permanent=True) is True
            assert repo.get(p.id) is None


class TestDatasetRepository:
    def test_create_dataset(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            ds_repo = DatasetRepository(session)
            ds = ds_repo.create(project_id=p.id, name="data.csv", row_count=1000)
            assert ds.id is not None
            assert ds.name == "data.csv"
            assert ds.row_count == 1000

    def test_list_by_project(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            ds_repo = DatasetRepository(session)
            ds_repo.create(project_id=p.id, name="a.csv")
            ds_repo.create(project_id=p.id, name="b.csv")
            assert len(ds_repo.list_by_project(p.id)) == 2

    def test_delete_dataset(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            ds_repo = DatasetRepository(session)
            ds = ds_repo.create(project_id=p.id, name="data.csv")
            assert ds_repo.delete(ds.id) is True
            assert ds_repo.get(ds.id) is None


class TestFactorRepository:
    def test_create_factor(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            fac_repo = FactorRepository(session)
            f = fac_repo.create(
                project_id=p.id,
                name="Momentum",
                expression="ts_rank(close, 20)",
                agent_id="Agent_01",
                level=1,
            )
            assert f.id is not None
            assert f.name == "Momentum"
            assert f.origin == FactorOrigin.SEED
            assert f.validation_status == FactorValidationStatus.PENDING

    def test_list_by_project(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            fac_repo = FactorRepository(session)
            fac_repo.create(project_id=p.id, name="A", expression="close")
            fac_repo.create(project_id=p.id, name="B", expression="open")
            assert len(fac_repo.list_by_project(p.id)) == 2

    def test_update_factor(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            fac_repo = FactorRepository(session)
            f = fac_repo.create(project_id=p.id, name="Old", expression="close")
            updated = fac_repo.update(f.id, name="New")
            assert updated.name == "New"


class TestRunRepository:
    def test_create_run(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            run_repo = RunRepository(session)
            run = run_repo.create(project_id=p.id)
            assert run.id is not None
            assert run.status == RunStatus.PENDING
            assert run.run_type == RunType.FULL

    def test_update_run_status(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            run_repo = RunRepository(session)
            run = run_repo.create(project_id=p.id)
            updated = run_repo.update(run.id, status=RunStatus.RUNNING, progress=50.0)
            assert updated.status == RunStatus.RUNNING
            assert updated.progress == 50.0

    def test_list_interrupted(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")

            run_repo = RunRepository(session)
            r1 = run_repo.create(project_id=p.id)
            run_repo.update(r1.id, status=RunStatus.RUNNING)
            r2 = run_repo.create(project_id=p.id)
            run_repo.update(r2.id, status=RunStatus.SUCCEEDED)

            interrupted = run_repo.list_interrupted()
            assert len(interrupted) == 1
            assert interrupted[0].id == r1.id


class TestSettingRepository:
    def test_set_and_get(self, db):
        with db.session() as session:
            repo = SettingRepository(session)
            repo.set("key1", "value1")
            assert repo.get("key1") == "value1"

    def test_get_default(self, db):
        with db.session() as session:
            repo = SettingRepository(session)
            assert repo.get("nonexistent", "default") == "default"

    def test_update_existing(self, db):
        with db.session() as session:
            repo = SettingRepository(session)
            repo.set("key", "val1")
            repo.set("key", "val2")
            assert repo.get("key") == "val2"

    def test_get_all(self, db):
        with db.session() as session:
            repo = SettingRepository(session)
            repo.set("a", "1")
            repo.set("b", "2")
            all_settings = repo.get_all()
            assert all_settings["a"] == "1"
            assert all_settings["b"] == "2"

    def test_delete(self, db):
        with db.session() as session:
            repo = SettingRepository(session)
            repo.set("key", "val")
            assert repo.delete("key") is True
            assert repo.get("key") == ""


class TestArtifactRepository:
    def test_create_and_list(self, db):
        with db.session() as session:
            proj_repo = ProjectRepository(session)
            p = proj_repo.create(name="Test")
            run_repo = RunRepository(session)
            run = run_repo.create(project_id=p.id)

            art_repo = ArtifactRepository(session)
            art_repo.create(run_id=run.id, artifact_type="report", name="report.html")
            art_repo.create(run_id=run.id, artifact_type="metrics", name="metrics.csv")

            artifacts = art_repo.list_by_run(run.id)
            assert len(artifacts) == 2
