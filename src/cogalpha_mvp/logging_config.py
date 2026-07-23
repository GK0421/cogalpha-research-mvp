"""Logging configuration for CogAlpha Research MVP."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: str | Path | None = None,
    run_id: str = "",
) -> logging.Logger:
    """Configure and return the root logger for the project.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path to a log file. If provided, logs are written there.
        run_id: Run identifier for log context.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("cogalpha_mvp")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    if run_id:
        logger = logging.LoggerAdapter(logger, {"run_id": run_id})

    return logger
