"""Unit tests for reporting and logging modules."""

from __future__ import annotations

import json

import pytest
import yaml

from cogalpha_mvp.config import Config
from cogalpha_mvp.logging_config import setup_logging
from cogalpha_mvp.reporting.reporter import ReportGenerator


@pytest.fixture
def minimal_config(tmp_path):
    """Create a minimal config for testing."""
    config_data = {
        "data": {
            "full_start": "2022-01-03",
            "full_end": "2022-03-31",
            "train_start": "2022-01-03",
            "train_end": "2022-02-28",
            "oos_start": "2022-03-01",
            "oos_end": "2022-03-31",
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
        "dedup": {"correlation_threshold": 0.85, "structural_dedup_enabled": True},
        "generation": {"enabled": False},
        "seed": 42,
        "output_dir": str(tmp_path / "report_test"),
        "log_level": "WARNING",
        "run_id": "test_report_001",
    }
    config_path = tmp_path / "test_config.yaml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    return Config.from_yaml(str(config_path))


class TestReportGenerator:
    """Tests for ReportGenerator."""

    def test_generate_full_report(self, minimal_config, tmp_path):
        """Test that full report generation works."""
        output_dir = tmp_path / "report_output" / "test_report_001"
        output_dir.mkdir(parents=True, exist_ok=True)

        reporter = ReportGenerator(minimal_config, output_dir)
        report_path = reporter.generate_full_report(
            data_summary={
                "rows": 100,
                "n_symbols": 5,
                "start_date": "2022-01-03",
                "end_date": "2022-03-31",
                "data_fingerprint": "abc123",
            },
            quality_results=[{"factor_id": "f1", "passed": True, "stage": "", "error": ""}],
            train_metrics={"f1": {"ic_mean": 0.05, "icir": 0.5, "rankic_mean": 0.04}},
            scoring_results={
                "f1": {"status": "qualified", "composite_score": 0.7, "metrics": {"ic_mean": 0.05}}
            },
            dedup_results={"before": 1, "after": 1, "removed": 0, "removed_ids": []},
            oos_metrics={"f1": {"ic_mean": 0.03, "decay_ratio": 0.4, "sign_consistent": True}},
            portfolio_results={"long_short": {"annual_return": 0.1, "sharpe_ratio": 1.2}},
        )

        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "CogAlpha" in content
        assert "RESEARCH_BACKTEST_ONLY" in content

    def test_report_contains_disclaimer(self, minimal_config, tmp_path):
        """Test that report contains the research-only disclaimer."""
        output_dir = tmp_path / "report_output2" / "test_report_001"
        output_dir.mkdir(parents=True, exist_ok=True)

        reporter = ReportGenerator(minimal_config, output_dir)
        report_path = reporter.generate_full_report(
            data_summary={
                "rows": 100,
                "n_symbols": 5,
                "start_date": "2022-01-03",
                "end_date": "2022-03-31",
                "data_fingerprint": "abc123",
            },
            quality_results=[],
            train_metrics={},
            scoring_results={},
            dedup_results={"before": 0, "after": 0, "removed": 0, "removed_ids": []},
            oos_metrics={},
            portfolio_results={},
        )

        content = report_path.read_text(encoding="utf-8")
        assert "NO_LIVE_TRADING" in content

    def test_report_summary_json(self, minimal_config, tmp_path):
        """Test that summary.json is generated."""
        output_dir = tmp_path / "report_output3" / "test_report_001"
        output_dir.mkdir(parents=True, exist_ok=True)

        reporter = ReportGenerator(minimal_config, output_dir)
        reporter.generate_full_report(
            data_summary={
                "rows": 100,
                "n_symbols": 5,
                "start_date": "2022-01-03",
                "end_date": "2022-03-31",
                "data_fingerprint": "abc123",
            },
            quality_results=[],
            train_metrics={},
            scoring_results={},
            dedup_results={"before": 0, "after": 0, "removed": 0, "removed_ids": []},
            oos_metrics={},
            portfolio_results={},
        )

        summary_path = output_dir / "summary.json"
        assert summary_path.exists()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert "disclaimer" in summary


class TestLoggingConfig:
    """Tests for logging configuration."""

    def test_setup_logging_creates_log_file(self, tmp_path):
        """Test that setup_logging creates a log file."""
        log_file = tmp_path / "test.log"
        setup_logging("DEBUG", log_file, "test_run")
        assert log_file.exists()

    def test_setup_logging_warning_level(self, tmp_path):
        """Test that WARNING level works."""
        log_file = tmp_path / "test_warn.log"
        setup_logging("WARNING", log_file, "test_run_warn")
        assert log_file.exists()

    def test_setup_logging_info_level(self, tmp_path):
        """Test that INFO level works."""
        log_file = tmp_path / "test_info.log"
        setup_logging("INFO", log_file, "test_run_info")
        assert log_file.exists()
