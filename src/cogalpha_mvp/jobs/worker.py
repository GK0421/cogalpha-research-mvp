"""Background job worker that executes research pipelines."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..application.run_service import RunService
from ..config import Config
from ..pipeline.runner import PipelineRunner
from .models import STAGE_PROGRESS, JobStage

logger = logging.getLogger(__name__)


class JobWorker:
    """Worker that executes research pipeline runs."""

    # Map pipeline steps to job stages
    STEP_TO_STAGE = {
        "save_environment": JobStage.INITIALIZING,
        "load_data": JobStage.LOADING_DATA,
        "validate_data": JobStage.VALIDATING_DATA,
        "register_factors": JobStage.CALCULATING_FACTORS,
        "quality_check": JobStage.QUALITY_CHECKING,
        "evaluate_factors": JobStage.TRAIN_EVALUATING,
        "score_factors": JobStage.TRAIN_EVALUATING,
        "dedup": JobStage.DEDUPLICATING,
        "oos_validation": JobStage.OOS_EVALUATING,
        "backtest": JobStage.BACKTESTING,
        "generate_report": JobStage.REPORTING,
    }

    def __init__(
        self,
        run_service: RunService,
        workspace_root: Path,
    ) -> None:
        self.run_service = run_service
        self.workspace_root = workspace_root
        self._cancelled: set[str] = set()

    def execute_run(
        self,
        run_id: str,
        config: Config,
        use_synthetic: bool = False,
    ) -> dict[str, Any]:
        """Execute a research run. Returns summary dict."""
        try:
            self._update_stage(run_id, JobStage.INITIALIZING)
            self.run_service.update_run_status(
                run_id, status="running", progress=0.0, current_stage="INITIALIZING"
            )

            # Create pipeline runner
            runner = PipelineRunner(config)

            # Run the pipeline
            self._update_stage(run_id, JobStage.LOADING_DATA)
            summary = runner.run_all(use_synthetic=use_synthetic)

            self._update_stage(run_id, JobStage.FINALIZING)
            self.run_service.update_run_status(
                run_id,
                status="succeeded",
                progress=100.0,
                current_stage="FINALIZING",
                result_path=str(Path(config.output_dir) / config.run_id),
            )

            return summary

        except Exception as e:
            logger.error("Run %s failed: %s", run_id, e)
            self.run_service.update_run_status(
                run_id,
                status="failed",
                error_code=type(e).__name__,
                error_message=str(e),
            )
            raise

    def request_cancel(self, run_id: str) -> None:
        """Request cancellation of a run."""
        self._cancelled.add(run_id)
        self.run_service.update_run_status(run_id, status="cancel_requested")

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self._cancelled

    def _update_stage(self, run_id: str, stage: JobStage) -> None:
        progress = STAGE_PROGRESS.get(stage, 0.0)
        self.run_service.update_run_status(
            run_id,
            status="running",
            progress=progress,
            current_stage=stage.value,
        )
        logger.info("Run %s -> stage: %s (%.0f%%)", run_id, stage.value, progress)
