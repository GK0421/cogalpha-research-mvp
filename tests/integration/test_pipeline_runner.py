"""Integration test that exercises the full PipelineRunner with minimal data.

This test covers pipeline/runner.py, portfolio/backtest.py,
reporting/reporter.py, and logging_config.py in a single run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from cogalpha_mvp.config import Config
from cogalpha_mvp.pipeline.runner import PipelineRunner


@pytest.fixture
def minimal_config(tmp_path):
    """Create a config with a very short date range for fast testing."""
    config_data = {
        "data": {
            "full_start": "2022-01-03",
            "full_end": "2022-03-31",
            "train_start": "2022-01-03",
            "train_end": "2022-02-28",
            "oos_start": "2022-03-01",
            "oos_end": "2022-03-31",
            "raw_dir": "data/raw",
            "normalized_dir": "data/normalized",
            "features_dir": "data/features",
        },
        "factors": {
            "qualified_score_threshold": 0.65,
            "elite_score_threshold": 0.80,
            "min_ic_qualified": 0.005,
            "min_icir_qualified": 0.05,
            "min_rankic_qualified": 0.005,
            "min_rankicir_qualified": 0.05,
            "min_ic_elite": 0.01,
            "min_icir_elite": 0.10,
            "min_rankic_elite": 0.01,
            "min_rankicir_elite": 0.10,
            "forward_period": 1,
        },
        "portfolio": {
            "top_quantile": 0.2,
            "bottom_quantile": 0.2,
            "rebalance": "weekly",
            "transaction_cost_bps": 10,
            "slippage_bps": 5,
            "max_single_weight": 0.05,
        },
        "quality": {
            "min_valid_ratio": 0.3,
            "max_nan_ratio": 0.7,
            "near_constant_threshold": 1.0e-8,
            "truncation_test_dates": 5,
            "truncation_max_diff": 1.0e-10,
            "truncation_min_corr": 0.9999,
            "max_complexity": 100,
        },
        "dedup": {
            "correlation_threshold": 0.85,
            "structural_dedup_enabled": True,
        },
        "generation": {
            "enabled": False,
        },
        "seed": 42,
        "output_dir": str(tmp_path / "pipeline_test"),
        "log_level": "WARNING",
        "run_id": "test_run_001",
    }
    config_path = tmp_path / "test_config.yaml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    return Config.from_yaml(str(config_path))


class TestPipelineRunnerIntegration:
    """Integration test for PipelineRunner - covers runner, backtest, reporter."""

    @pytest.mark.slow
    def test_run_all_synthetic(self, minimal_config):
        """Test that run_all completes successfully with synthetic data."""
        runner = PipelineRunner(minimal_config)
        summary = runner.run_all(use_synthetic=True)

        assert summary["run_id"] == "test_run_001"
        assert summary["n_factors"] > 0
        assert summary["disclaimer"] == "RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING"

    @pytest.mark.slow
    def test_run_all_output_files(self, minimal_config):
        """Test that all required output files are generated."""
        runner = PipelineRunner(minimal_config)
        runner.run_all(use_synthetic=True)

        output_dir = Path(minimal_config.output_dir) / "test_run_001"

        # Check report
        assert (output_dir / "report.html").exists()
        # Check summary JSON (reporter generates)
        assert (output_dir / "summary.json").exists()
        # Check SHA256SUMS
        assert (output_dir / "SHA256SUMS.txt").exists()
        # Check config snapshot
        assert (output_dir / "config_snapshot.yaml").exists()
        # Check environment info
        assert (output_dir / "environment.json").exists()
        # Check data manifest
        assert (output_dir / "data_manifest.json").exists()
        # Check run manifest
        assert (output_dir / "run_manifest.json").exists()
        # Check quality results
        assert (output_dir / "quality" / "factor_quality.csv").exists()
        # Check train metrics
        assert (output_dir / "train" / "train_metrics.csv").exists()
        # Check dedup results
        assert (output_dir / "dedup" / "dedup_results.csv").exists()
        # Check OOS metrics
        assert (output_dir / "oos" / "oos_metrics.csv").exists()
        # Check portfolio results
        assert (output_dir / "portfolio" / "portfolio_results.csv").exists()
        # Check charts directory
        assert (output_dir / "charts").is_dir()

    @pytest.mark.slow
    def test_run_all_report_content(self, minimal_config):
        """Test that the HTML report contains expected sections."""
        runner = PipelineRunner(minimal_config)
        summary = runner.run_all(use_synthetic=True)

        report_path = Path(summary["report_path"])
        content = report_path.read_text(encoding="utf-8")

        assert "CogAlpha" in content
        assert "RESEARCH_BACKTEST_ONLY" in content
        assert "NO_LIVE_TRADING" in content

    @pytest.mark.slow
    def test_run_all_summary_json(self, minimal_config):
        """Test that summary.json contains required fields."""
        runner = PipelineRunner(minimal_config)
        runner.run_all(use_synthetic=True)

        summary_path = Path(minimal_config.output_dir) / "test_run_001" / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

        assert "run_id" in summary
        assert "n_factors" in summary
        assert "disclaimer" in summary
        assert "RESEARCH_BACKTEST_ONLY" in summary["disclaimer"]

    @pytest.mark.slow
    def test_run_all_sha256sums_valid(self, minimal_config):
        """Test that SHA256SUMS.txt contains valid hashes."""
        runner = PipelineRunner(minimal_config)
        runner.run_all(use_synthetic=True)

        sha_path = Path(minimal_config.output_dir) / "test_run_001" / "SHA256SUMS.txt"
        lines = sha_path.read_text(encoding="utf-8").strip().split("\n")

        assert len(lines) > 0
        for line in lines:
            parts = line.split("  ", 1)
            assert len(parts) == 2
            sha, _filename = parts
            assert len(sha) == 64  # SHA256 hex digest

    @pytest.mark.slow
    def test_run_all_environment_info(self, minimal_config):
        """Test that environment.json contains Python version."""
        runner = PipelineRunner(minimal_config)
        runner.run_all(use_synthetic=True)

        env_path = Path(minimal_config.output_dir) / "test_run_001" / "environment.json"
        env = json.loads(env_path.read_text(encoding="utf-8"))

        assert "python_version" in env
        assert "platform" in env
        assert "timestamp" in env

    @pytest.mark.slow
    def test_run_all_data_manifest(self, minimal_config):
        """Test that data_manifest.json has required fields."""
        runner = PipelineRunner(minimal_config)
        runner.run_all(use_synthetic=True)

        manifest_path = Path(minimal_config.output_dir) / "test_run_001" / "data_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert "source" in manifest
        assert "rows" in manifest
        assert "n_symbols" in manifest
        assert "data_fingerprint" in manifest

    @pytest.mark.slow
    def test_run_all_quality_csv(self, minimal_config):
        """Test that quality CSV has factor results."""
        runner = PipelineRunner(minimal_config)
        runner.run_all(use_synthetic=True)

        quality_path = Path(minimal_config.output_dir) / "test_run_001" / "quality" / "factor_quality.csv"
        df = pd.read_csv(str(quality_path))
        assert len(df) > 0
        assert "passed" in df.columns

    @pytest.mark.slow
    def test_run_all_with_csv_file(self, minimal_config, tmp_path):
        """Test run_all loading from a CSV file."""
        # Generate a small CSV file
        from cogalpha_mvp.data.adapters import SyntheticDataAdapter
        from cogalpha_mvp.domain.data_contract import DataRequest

        adapter = SyntheticDataAdapter()
        data = adapter.load(DataRequest(start_date="2022-01-03", end_date="2022-03-31"))
        csv_path = tmp_path / "test_data.csv"
        data.to_csv(str(csv_path), index=False)

        runner = PipelineRunner(minimal_config)
        summary = runner.run_all(use_synthetic=False, data_path=str(csv_path))

        assert summary["n_factors"] > 0
