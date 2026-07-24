"""Research run management service."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..persistence.database import Database
from ..persistence.models import RunStatus, RunType
from ..persistence.repositories import RunRepository

logger = logging.getLogger(__name__)


class RunService:
    """Application service for research run management."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_run(
        self,
        project_id: str,
        dataset_id: str | None = None,
        run_type: str = "full",
        config: dict | None = None,
    ) -> dict[str, Any]:
        with self.db.session() as session:
            repo = RunRepository(session)
            run = repo.create(
                project_id=project_id,
                dataset_id=dataset_id,
                run_type=RunType(run_type)
                if run_type in [r.value for r in RunType]
                else RunType.FULL,
                config_snapshot=config,
            )
            return self._to_dict(run)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self.db.session() as session:
            repo = RunRepository(session)
            run = repo.get(run_id)
            return self._to_dict(run) if run else None

    def list_runs(self, project_id: str) -> list[dict[str, Any]]:
        with self.db.session() as session:
            repo = RunRepository(session)
            return [self._to_dict(r) for r in repo.list_by_project(project_id)]

    def update_run_status(
        self,
        run_id: str,
        status: str,
        progress: float | None = None,
        current_stage: str = "",
        error_code: str = "",
        error_message: str = "",
        result_path: str = "",
    ) -> dict[str, Any] | None:
        with self.db.session() as session:
            repo = RunRepository(session)
            kwargs: dict[str, Any] = {"status": RunStatus(status)}
            if progress is not None:
                kwargs["progress"] = progress
            if current_stage:
                kwargs["current_stage"] = current_stage
            if error_code:
                kwargs["error_code"] = error_code
            if error_message:
                kwargs["error_message"] = error_message
            if result_path:
                kwargs["result_path"] = result_path
            if status in ("succeeded", "failed", "cancelled", "interrupted"):
                from datetime import datetime

                kwargs["finished_at"] = datetime.utcnow()
            if status == "running":
                from datetime import datetime

                kwargs["started_at"] = datetime.utcnow()
            run = repo.update(run_id, **kwargs)
            return self._to_dict(run) if run else None

    def cancel_run(self, run_id: str) -> dict[str, Any] | None:
        return self.update_run_status(run_id, status="cancel_requested")

    def rerun(self, run_id: str) -> dict[str, Any] | None:
        """Create a new run with the same configuration."""
        with self.db.session() as session:
            repo = RunRepository(session)
            old_run = repo.get(run_id)
            if old_run is None:
                return None
            config = json.loads(old_run.config_snapshot) if old_run.config_snapshot else {}
            new_run = repo.create(
                project_id=old_run.project_id,
                dataset_id=old_run.dataset_id,
                run_type=RunType(old_run.run_type)
                if isinstance(old_run.run_type, str)
                else old_run.run_type,
                config_snapshot=config,
            )
            return self._to_dict(new_run)

    def recover_interrupted(self) -> list[str]:
        """Mark interrupted runs and return their IDs."""
        with self.db.session() as session:
            repo = RunRepository(session)
            interrupted = repo.list_interrupted()
            ids = []
            for run in interrupted:
                repo.update(run.id, status=RunStatus.INTERRUPTED)
                ids.append(run.id)
            return ids

    @staticmethod
    def _to_dict(run: Any) -> dict[str, Any]:
        return {
            "id": run.id,
            "project_id": run.project_id,
            "dataset_id": run.dataset_id,
            "run_type": run.run_type.value if hasattr(run.run_type, "value") else str(run.run_type),
            "status": run.status.value if hasattr(run.status, "value") else str(run.status),
            "progress": run.progress,
            "current_stage": run.current_stage,
            "config_snapshot": json.loads(run.config_snapshot) if run.config_snapshot else {},
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "error_code": run.error_code,
            "error_message": run.error_message,
            "result_path": run.result_path,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
