"""Persistent job manager for background research tasks."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from ..application.run_service import RunService
from ..config import Config
from ..persistence.database import Database
from .worker import JobWorker

logger = logging.getLogger(__name__)


class JobManager:
    """Manages background research jobs with persistence."""

    def __init__(
        self,
        db: Database,
        workspace_root: Path,
        max_concurrent: int = 1,
    ) -> None:
        self.db = db
        self.workspace_root = workspace_root
        self.max_concurrent = max_concurrent
        self.run_service = RunService(db)
        self.worker = JobWorker(self.run_service, workspace_root)
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()
        self._active_runs: set[str] = set()

    def start_run(
        self,
        run_id: str,
        config: Config,
        use_synthetic: bool = False,
    ) -> bool:
        """Start a research run in background thread."""
        with self._lock:
            if len(self._active_runs) >= self.max_concurrent:
                logger.warning("Max concurrent runs reached, queuing run %s", run_id)
                self.run_service.update_run_status(run_id, status="queued")
                return False

            if run_id in self._active_runs:
                logger.warning("Run %s already active", run_id)
                return False

            self._active_runs.add(run_id)

        thread = threading.Thread(
            target=self._run_job,
            args=(run_id, config, use_synthetic),
            daemon=True,
        )
        self._threads[run_id] = thread
        thread.start()
        return True

    def cancel_run(self, run_id: str) -> bool:
        """Request cancellation of a run."""
        self.worker.request_cancel(run_id)
        return True

    def get_active_count(self) -> int:
        return len(self._active_runs)

    def recover_interrupted(self) -> list[str]:
        """Recover interrupted runs on startup."""
        return self.run_service.recover_interrupted()

    def _run_job(
        self,
        run_id: str,
        config: Config,
        use_synthetic: bool,
    ) -> None:
        """Thread target for running a job."""
        try:
            self.worker.execute_run(run_id, config, use_synthetic)
        except Exception as e:
            logger.error("Job %s failed: %s", run_id, e)
        finally:
            with self._lock:
                self._active_runs.discard(run_id)
                self._threads.pop(run_id, None)
