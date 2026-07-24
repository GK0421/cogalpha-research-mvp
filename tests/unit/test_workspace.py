"""Tests for workspace and paths."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from cogalpha_mvp.product.paths import WorkspaceManager, get_default_home, get_workspace_root


class TestWorkspaceManager:
    def test_initialize(self):
        tmpdir = tempfile.mkdtemp()
        os.environ["COGALPHA_HOME"] = tmpdir
        ws = WorkspaceManager()
        ws.initialize()

        assert ws.root.exists()
        for subdir in ws.SUBDIRS:
            assert (ws.root / subdir).exists()

    def test_is_initialized(self):
        tmpdir = tempfile.mkdtemp()
        os.environ["COGALPHA_HOME"] = tmpdir
        ws = WorkspaceManager()
        assert not ws.is_initialized()
        ws.initialize()
        assert ws.is_initialized()

    def test_db_path(self):
        tmpdir = tempfile.mkdtemp()
        os.environ["COGALPHA_HOME"] = tmpdir
        ws = WorkspaceManager()
        assert ws.db_path == ws.root / "metadata" / "cogalpha.db"

    def test_properties(self):
        tmpdir = tempfile.mkdtemp()
        os.environ["COGALPHA_HOME"] = tmpdir
        ws = WorkspaceManager()
        assert ws.projects_dir == ws.root / "projects"
        assert ws.datasets_dir == ws.root / "datasets"
        assert ws.runs_dir == ws.root / "runs"
        assert ws.reports_dir == ws.root / "reports"
        assert ws.cache_dir == ws.root / "cache"
        assert ws.config_dir == ws.root / "config"

    def test_get_info(self):
        tmpdir = tempfile.mkdtemp()
        os.environ["COGALPHA_HOME"] = tmpdir
        ws = WorkspaceManager()
        info = ws.get_info()
        assert "root" in info
        assert "db_path" in info
        assert "platform" in info

    def test_idempotent(self):
        tmpdir = tempfile.mkdtemp()
        os.environ["COGALPHA_HOME"] = tmpdir
        ws = WorkspaceManager()
        ws.initialize()
        ws.initialize()  # should not error
        assert ws.is_initialized()


class TestPathFunctions:
    def test_get_default_home_env(self):
        os.environ["COGALPHA_HOME"] = "/tmp/test_cogalpha"
        assert get_default_home() == Path("/tmp/test_cogalpha")

    def test_get_workspace_root_env(self):
        os.environ["COGALPHA_DATA_DIR"] = "/tmp/test_data"
        assert get_workspace_root() == Path("/tmp/test_data")
