"""Product paths and workspace management."""

from __future__ import annotations

import os
import platform
from pathlib import Path


def get_default_home() -> Path:
    """Get default CogAlpha home directory."""
    env_home = os.environ.get("COGALPHA_HOME")
    if env_home:
        return Path(env_home)
    return Path.home() / ".cogalpha"


def get_workspace_root() -> Path:
    """Get workspace root, respecting env overrides."""
    env_data = os.environ.get("COGALPHA_DATA_DIR")
    if env_data:
        return Path(env_data)
    return get_default_home()


def get_log_dir() -> Path:
    """Get log directory."""
    env_log = os.environ.get("COGALPHA_LOG_DIR")
    if env_log:
        return Path(env_log)
    return get_workspace_root() / "logs"


class WorkspaceManager:
    """Manage local workspace initialization."""

    SUBDIRS = [
        "config",
        "metadata",
        "projects",
        "datasets",
        "runs",
        "reports",
        "logs",
        "cache",
    ]

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or get_workspace_root()

    @property
    def db_path(self) -> Path:
        return self.root / "metadata" / "cogalpha.db"

    @property
    def projects_dir(self) -> Path:
        return self.root / "projects"

    @property
    def datasets_dir(self) -> Path:
        return self.root / "datasets"

    @property
    def runs_dir(self) -> Path:
        return self.root / "runs"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def logs_dir(self) -> Path:
        return get_log_dir() if get_log_dir() != self.root / "logs" else self.root / "logs"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    def initialize(self) -> None:
        """Initialize workspace directories. Idempotent."""
        self.root.mkdir(parents=True, exist_ok=True)
        for subdir in self.SUBDIRS:
            (self.root / subdir).mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        """Check if workspace is initialized."""
        return self.root.exists() and self.db_path.parent.exists()

    def get_info(self) -> dict[str, str]:
        """Get workspace info dict."""
        return {
            "root": str(self.root),
            "db_path": str(self.db_path),
            "projects_dir": str(self.projects_dir),
            "datasets_dir": str(self.datasets_dir),
            "runs_dir": str(self.runs_dir),
            "reports_dir": str(self.reports_dir),
            "logs_dir": str(self.logs_dir),
            "cache_dir": str(self.cache_dir),
            "platform": platform.system(),
            "python_path": str(Path(os.executable) if hasattr(os, "executable") else ""),
        }
