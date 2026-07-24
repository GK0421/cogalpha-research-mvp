"""Tests for API endpoints."""

from __future__ import annotations

import os
import tempfile

import pytest
from apps.api.main import create_app, reset_state
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with a temporary workspace."""
    tmpdir = tempfile.mkdtemp()
    os.environ["COGALPHA_HOME"] = tmpdir

    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_state()


class TestHealth:
    def test_health(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "CogAlpha" in data["product"]

    def test_version(self, client):
        r = client.get("/api/v1/version")
        assert r.status_code == 200
        assert "version" in r.json()

    def test_capabilities(self, client):
        r = client.get("/api/v1/capabilities")
        assert r.status_code == 200
        data = r.json()
        assert data["research_only"] is True
        assert data["trading_enabled"] is False
        assert data["seed_factors_count"] == 21

    def test_workspace_info(self, client):
        r = client.get("/api/v1/workspace-info")
        assert r.status_code == 200
        assert "root" in r.json()


class TestProjects:
    def test_create_project(self, client):
        r = client.post("/api/v1/projects", json={"name": "Test"})
        assert r.status_code == 201
        assert r.json()["name"] == "Test"

    def test_list_projects(self, client):
        client.post("/api/v1/projects", json={"name": "A"})
        client.post("/api/v1/projects", json={"name": "B"})
        r = client.get("/api/v1/projects")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_project(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.get(f"/api/v1/projects/{pid}")
        assert r.status_code == 200
        assert r.json()["name"] == "Test"

    def test_get_project_not_found(self, client):
        r = client.get("/api/v1/projects/nonexistent")
        assert r.status_code == 404

    def test_update_project(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Old"})
        pid = create_r.json()["id"]
        r = client.patch(f"/api/v1/projects/{pid}", json={"name": "New"})
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    def test_delete_project_no_confirm(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.delete(f"/api/v1/projects/{pid}")
        assert r.status_code == 400

    def test_delete_project_with_confirm(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.delete(f"/api/v1/projects/{pid}?confirm=true")
        assert r.status_code == 200


class TestFactors:
    def test_seed_factors(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.post(f"/api/v1/projects/{pid}/factors/seed")
        assert r.status_code == 200
        assert len(r.json()) == 21

    def test_list_factors(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        client.post(f"/api/v1/projects/{pid}/factors/seed")
        r = client.get(f"/api/v1/projects/{pid}/factors")
        assert r.status_code == 200
        assert len(r.json()) == 21

    def test_validate_expression_valid(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.post(
            f"/api/v1/projects/{pid}/factors/validate",
            json={"expression": "ts_rank(close, 20)"},
        )
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_validate_expression_invalid(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.post(
            f"/api/v1/projects/{pid}/factors/validate",
            json={"expression": "exec('hack')"},
        )
        assert r.status_code == 200
        assert r.json()["valid"] is False

    def test_create_factor(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.post(
            f"/api/v1/projects/{pid}/factors",
            json={
                "name": "My Factor",
                "expression": "close / open",
                "agent_id": "Agent_01",
                "level": 1,
            },
        )
        assert r.status_code == 201
        assert r.json()["name"] == "My Factor"
        assert r.json()["validation_status"] == "valid"

    def test_create_factor_invalid_expression(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.post(
            f"/api/v1/projects/{pid}/factors",
            json={"name": "Bad", "expression": "exec('hack')"},
        )
        assert r.status_code == 400


class TestRuns:
    def test_create_run(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        r = client.post(f"/api/v1/projects/{pid}/runs", json={"run_type": "full"})
        assert r.status_code == 201
        assert r.json()["status"] == "pending"

    def test_get_run(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        run_r = client.post(f"/api/v1/projects/{pid}/runs", json={})
        run_id = run_r.json()["id"]
        r = client.get(f"/api/v1/runs/{run_id}")
        assert r.status_code == 200

    def test_list_runs(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        client.post(f"/api/v1/projects/{pid}/runs", json={})
        r = client.get(f"/api/v1/projects/{pid}/runs")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_rerun(self, client):
        create_r = client.post("/api/v1/projects", json={"name": "Test"})
        pid = create_r.json()["id"]
        run_r = client.post(f"/api/v1/projects/{pid}/runs", json={})
        run_id = run_r.json()["id"]
        r = client.post(f"/api/v1/runs/{run_id}/rerun")
        assert r.status_code == 201
        assert r.json()["id"] != run_id


class TestSettings:
    def test_get_settings(self, client):
        r = client.get("/api/v1/settings")
        assert r.status_code == 200
        assert "api.host" in r.json()

    def test_update_settings(self, client):
        r = client.patch("/api/v1/settings", json={"updates": {"test.key": "val"}})
        assert r.status_code == 200
        assert r.json()["test.key"] == "val"

    def test_llm_config(self, client):
        r = client.get("/api/v1/settings/llm")
        assert r.status_code == 200
        assert r.json()["enabled"] is False
