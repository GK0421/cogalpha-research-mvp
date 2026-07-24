"""Report service for generating and retrieving reports."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..persistence.database import Database
from ..persistence.repositories import ArtifactRepository

logger = logging.getLogger(__name__)


class ReportService:
    """Application service for report management."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        with self.db.session() as session:
            repo = ArtifactRepository(session)
            return [
                {
                    "id": a.id,
                    "run_id": a.run_id,
                    "artifact_type": a.artifact_type,
                    "name": a.name,
                    "relative_path": a.relative_path,
                    "sha256": a.sha256,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in repo.list_by_run(run_id)
            ]

    def get_report_path(self, run_id: str, reports_dir: Path) -> Path | None:
        """Get the HTML report path for a run."""
        report_path = reports_dir / run_id / "report.html"
        return report_path if report_path.exists() else None

    def get_summary(self, run_id: str, runs_dir: Path) -> dict[str, Any] | None:
        """Get run summary JSON."""
        summary_path = runs_dir / run_id / "summary.json"
        if summary_path.exists():
            return json.loads(summary_path.read_text(encoding="utf-8"))
        return None

    def get_factor_metrics(self, run_id: str, runs_dir: Path) -> list[dict[str, Any]]:
        """Get factor metrics CSV as list of dicts."""
        csv_path = runs_dir / run_id / "factor_metrics.csv"
        if csv_path.exists():
            import csv

            with open(csv_path, encoding="utf-8") as f:
                return list(csv.DictReader(f))
        return []

    def get_portfolio_results(self, run_id: str, runs_dir: Path) -> dict[str, Any]:
        """Get portfolio backtest results."""
        summary = self.get_summary(run_id, runs_dir)
        if summary and "portfolio" in summary:
            return summary["portfolio"]
        return {}
