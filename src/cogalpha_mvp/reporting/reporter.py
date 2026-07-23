"""Report generator - HTML, CSV, JSON output.

All HTML reports are self-contained with relative resource paths.
No dependency on developer's local absolute paths.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from cogalpha_mvp.config import Config

logger = logging.getLogger("cogalpha_mvp")


class ReportGenerator:
    """Generates HTML, CSV, and JSON reports for a research run."""

    def __init__(self, config: Config, output_dir: str | Path):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_full_report(
        self,
        data_summary: dict,
        quality_results: list[dict],
        train_metrics: dict[str, dict],
        scoring_results: dict[str, dict],
        dedup_results: dict,
        oos_metrics: dict[str, dict] | None = None,
        portfolio_results: dict | None = None,
    ) -> Path:
        """Generate the complete HTML report.

        Args:
            data_summary: Data manifest summary.
            quality_results: Quality check results list.
            train_metrics: Training metrics per factor.
            scoring_results: Scoring results per factor.
            dedup_results: Deduplication results.
            oos_metrics: OOS metrics per factor (optional).
            portfolio_results: Portfolio backtest results (optional).

        Returns:
            Path to the generated HTML report.
        """
        if oos_metrics is None:
            oos_metrics = {}
        if portfolio_results is None:
            portfolio_results = {}

        n_elite = sum(1 for r in scoring_results.values() if r["status"] == "elite")
        n_qualified = sum(1 for r in scoring_results.values() if r["status"] == "qualified")
        n_rejected = sum(1 for r in scoring_results.values() if r["status"] == "rejected")
        n_passed_quality = sum(1 for r in quality_results if r.get("passed"))

        html = self._build_html(
            data_summary=data_summary,
            quality_results=quality_results,
            train_metrics=train_metrics,
            scoring_results=scoring_results,
            dedup_results=dedup_results,
            oos_metrics=oos_metrics,
            portfolio_results=portfolio_results,
            n_elite=n_elite,
            n_qualified=n_qualified,
            n_rejected=n_rejected,
            n_passed_quality=n_passed_quality,
        )

        report_path = self.output_dir / "report.html"
        report_path.write_text(html, encoding="utf-8")
        logger.info("HTML report generated: %s", report_path)

        # Also generate JSON summary
        summary = {
            "run_id": self.config.run_id,
            "generated_at": datetime.now().isoformat(),
            "data_summary": data_summary,
            "quality": {
                "total": len(quality_results),
                "passed": n_passed_quality,
                "failed": len(quality_results) - n_passed_quality,
            },
            "scoring": {
                "elite": n_elite,
                "qualified": n_qualified,
                "rejected": n_rejected,
            },
            "dedup": dedup_results,
            "oos": {k: v for k, v in oos_metrics.items()},
            "portfolio": portfolio_results,
            "disclaimer": "RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING",
        }

        summary_path = self.output_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

        return report_path

    def _build_html(self, **kwargs) -> str:
        """Build the HTML report content."""
        data = kwargs["data_summary"]
        n_elite = kwargs["n_elite"]
        n_qualified = kwargs["n_qualified"]
        n_rejected = kwargs["n_rejected"]
        n_passed = kwargs["n_passed_quality"]
        portfolio = kwargs.get("portfolio_results", {})

        portfolio_html = ""
        if portfolio:
            portfolio_html = "<h2>[CHART] Portfolio Results</h2><table border='1' cellpadding='5'>"
            for strategy, result in portfolio.items():
                if isinstance(result, dict):
                    portfolio_html += f"<tr><th>{strategy}</th><td>"
                    for k, v in result.items():
                        if k != "disclaimer":
                            portfolio_html += f"<b>{k}</b>: {v:.4f}<br>"
                    portfolio_html += "</td></tr>"
            portfolio_html += "</table>"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CogAlpha Research MVP Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 10px; }}
        h2 {{ color: #16213e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th {{ background: #16213e; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border: 1px solid #ddd; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .metric {{ display: inline-block; background: #e3f2fd; padding: 10px 20px; margin: 5px; border-radius: 4px; }}
        .disclaimer {{ background: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; font-weight: bold; }}
        .elite {{ color: #d4af37; font-weight: bold; }}
        .qualified {{ color: #28a745; }}
        .rejected {{ color: #dc3545; }}
    </style>
</head>
<body>
<div class="container">
    <h1>[LAB] CogAlpha Research MVP Report</h1>
    <p><b>Run ID:</b> {self.config.run_id or "N/A"}</p>
    <p><b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <div class="disclaimer">
        [!] RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING<br>
        This report is for research and educational purposes only.
        It does NOT constitute investment advice and does NOT imply any real trading capability.
    </div>

    <h2>[CLIP] Data Summary</h2>
    <table border="1" cellpadding="5">
        <tr><th>Field</th><th>Value</th></tr>
        <tr><td>Rows</td><td>{data.get("rows", "N/A")}</td></tr>
        <tr><td>Symbols</td><td>{data.get("n_symbols", "N/A")}</td></tr>
        <tr><td>Date Range</td><td>{data.get("start_date", "N/A")} to {data.get("end_date", "N/A")}</td></tr>
        <tr><td>Training Period</td><td>{self.config.data.train_start} to {self.config.data.train_end}</td></tr>
        <tr><td>OOS Period</td><td>{self.config.data.oos_start} to {self.config.data.oos_end}</td></tr>
        <tr><td>Data Fingerprint</td><td>{str(data.get("data_fingerprint", "N/A"))[:32]}...</td></tr>
    </table>

    <h2>[SEARCH] Quality Check Results</h2>
    <div class="metric">Total: {len(kwargs["quality_results"])}</div>
    <div class="metric qualified">Passed: {n_passed}</div>
    <div class="metric rejected">Failed: {len(kwargs["quality_results"]) - n_passed}</div>

    <h2>[CHART] Factor Scoring</h2>
    <div class="metric elite">Elite: {n_elite}</div>
    <div class="metric qualified">Qualified: {n_qualified}</div>
    <div class="metric rejected">Rejected: {n_rejected}</div>

    <h2>[SYNC] Deduplication</h2>
    <p>Factors before dedup: {kwargs["dedup_results"].get("before", "N/A")}</p>
    <p>Factors after dedup: {kwargs["dedup_results"].get("after", "N/A")}</p>
    <p>Removed: {kwargs["dedup_results"].get("removed", "N/A")}</p>

    {portfolio_html}

    <h2>[!] Known Limitations</h2>
    <ul>
        <li>This MVP uses synthetic data for demonstration. Results are NOT indicative of real market performance.</li>
        <li>No survivorship-bias-free universe snapshots are implemented.</li>
        <li>No point-in-time fundamentals data is included.</li>
        <li>Multi-testing bias and data mining bias are present but not corrected.</li>
        <li>This is NOT a live trading system. No orders are executed.</li>
    </ul>

    <hr>
    <p><small>CogAlpha Research MVP v0.1.0 | MIT License | RESEARCH_BACKTEST_ONLY</small></p>
</div>
</body>
</html>"""
        return html

    def save_factor_report(
        self,
        factors: list[dict],
        filename: str = "factor_report.csv",
    ) -> Path:
        """Save factor report as CSV."""
        path = self.output_dir / filename
        df = pd.DataFrame(factors)
        df.to_csv(str(path), index=False, encoding="utf-8-sig")
        return path
