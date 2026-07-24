"""Job recovery for interrupted runs."""

from __future__ import annotations

import logging

from ..application.run_service import RunService

logger = logging.getLogger(__name__)


def recover_runs(run_service: RunService) -> list[str]:
    """Recover interrupted runs on application startup."""
    interrupted_ids = run_service.recover_interrupted()
    if interrupted_ids:
        logger.info("Recovered %d interrupted runs: %s", len(interrupted_ids), interrupted_ids)
    return interrupted_ids
