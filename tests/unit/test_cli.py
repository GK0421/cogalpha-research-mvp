"""Comprehensive tests for the CLI module.

Tests all 11 CLI commands including success paths, failure exit codes,
option handling, and output verification.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cogalpha_mvp.cli import main


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def demo_config(tmp_path):
    """Create a demo config file for testing."""
    config_data = {
        "data": {
            "full_start": "2022-01-01",
            "full_end": "2022-03-31",
            "train_start": "2022-01-01",
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
        "seed": 42,
        "output_dir": str(tmp_path / "results"),
        "log_level": "WARNING",
    }
    config_path = tmp_path / "test_config.yaml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    return config_path


class TestCLIVersion:
    """Test version display."""

    def test_version_flag(self, runner):
        """Test --version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help_flag(self, runner):
        """Test --help flag."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "doctor" in result.output
        assert "demo" in result.output
        assert "run-all" in result.output


class TestCLIDoctor:
    """Test the doctor command."""

    def test_doctor_success(self, runner):
        """Test doctor command runs and reports environment."""
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "Environment Check" in result.output
        assert "Python" in result.output
        assert "pandas" in result.output

    def test_doctor_shows_api_keys(self, runner):
        """Test doctor shows API key status."""
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "ANTHROPIC_API_KEY" in result.output
        assert "OPENAI_API_KEY" in result.output


class TestCLIInit:
    """Test the init command."""

    def test_init_creates_directories(self, runner, tmp_path):
        """Test init creates project structure."""
        output_dir = str(tmp_path / "test_init")
        result = runner.invoke(main, ["init", "--output-dir", output_dir])
        assert result.exit_code == 0
        assert (tmp_path / "test_init" / "data" / "raw").exists()
        assert (tmp_path / "test_init" / "configs").exists()
        assert (tmp_path / "test_init" / "configs" / "research.yaml").exists()

    def test_init_config_has_correct_dates(self, runner, tmp_path):
        """Test init creates config with spec-correct dates."""
        output_dir = str(tmp_path / "test_init2")
        result = runner.invoke(main, ["init", "--output-dir", output_dir])
        assert result.exit_code == 0
        config_path = tmp_path / "test_init2" / "configs" / "research.yaml"
        with config_path.open() as f:
            cfg = yaml.safe_load(f)
        assert cfg["data"]["train_start"] == "2011-01-01"
        assert cfg["data"]["train_end"] == "2019-12-31"
        assert cfg["data"]["oos_start"] == "2020-01-01"
        assert cfg["data"]["oos_end"] == "2025-12-31"


class TestCLIGenerateDemoData:
    """Test the generate-demo-data command."""

    def test_generate_demo_data(self, runner, tmp_path):
        """Test generating demo data."""
        output_file = str(tmp_path / "demo.csv")
        result = runner.invoke(
            main,
            [
                "generate-demo-data",
                "--output", output_file,
                "--start-date", "2022-01-01",
                "--end-date", "2022-06-30",
            ],
        )
        assert result.exit_code == 0
        assert Path(output_file).exists()
        assert "Generated" in result.output

    def test_generate_demo_data_creates_parent_dir(self, runner, tmp_path):
        """Test that parent directories are created."""
        output_file = str(tmp_path / "nested" / "dir" / "demo.csv")
        result = runner.invoke(
            main,
            ["generate-demo-data", "--output", output_file],
        )
        assert result.exit_code == 0
        assert Path(output_file).exists()


class TestCLIIngest:
    """Test the ingest command."""

    def test_ingest_success(self, runner, demo_config):
        """Test ingest command with valid config."""
        result = runner.invoke(
            main,
            ["ingest", "--config", str(demo_config), "--seed", "123"],
        )
        assert result.exit_code == 0
        assert "Data ingestion complete" in result.output

    def test_ingest_with_run_id(self, runner, demo_config):
        """Test ingest with custom run ID."""
        result = runner.invoke(
            main,
            ["ingest", "--config", str(demo_config), "--run-id", "test_run_001"],
        )
        assert result.exit_code == 0

    def test_ingest_missing_config(self, runner):
        """Test ingest with missing config file exits non-zero."""
        result = runner.invoke(main, ["ingest", "--config", "nonexistent.yaml"])
        assert result.exit_code != 0


class TestCLIValidateData:
    """Test the validate-data command."""

    def test_validate_data_success(self, runner, demo_config):
        """Test validate-data command."""
        result = runner.invoke(
            main,
            ["validate-data", "--config", str(demo_config)],
        )
        assert result.exit_code == 0
        assert "Data validation complete" in result.output

    def test_validate_data_missing_config(self, runner):
        """Test validate-data with missing config."""
        result = runner.invoke(main, ["validate-data", "--config", "missing.yaml"])
        assert result.exit_code != 0


class TestCLIEvaluate:
    """Test the evaluate command."""

    def test_evaluate_success(self, runner, demo_config):
        """Test evaluate command."""
        result = runner.invoke(
            main,
            ["evaluate", "--config", str(demo_config), "--seed", "42"],
        )
        assert result.exit_code == 0
        assert "Factor evaluation complete" in result.output


class TestCLIOOS:
    """Test the oos command."""

    def test_oos_success(self, runner, demo_config):
        """Test oos command."""
        result = runner.invoke(
            main,
            ["oos", "--config", str(demo_config)],
        )
        assert result.exit_code == 0
        assert "OOS validation complete" in result.output


class TestCLIBacktest:
    """Test the backtest command."""

    def test_backtest_success(self, runner, demo_config):
        """Test backtest command."""
        result = runner.invoke(
            main,
            ["backtest", "--config", str(demo_config)],
        )
        assert result.exit_code == 0
        assert "Backtest complete" in result.output


class TestCLIReport:
    """Test the report command."""

    def test_report_success(self, runner, demo_config):
        """Test report command."""
        result = runner.invoke(
            main,
            ["report", "--config", str(demo_config)],
        )
        assert result.exit_code == 0
        assert "Report generated" in result.output


class TestCLIRunAll:
    """Test the run-all command."""

    @pytest.mark.slow
    def test_run_all_with_demo_config(self, runner, demo_config, tmp_path):
        """Test run-all command with a real config."""
        output_dir = str(tmp_path / "run_all_results")
        result = runner.invoke(
            main,
            [
                "run-all",
                "--config", str(demo_config),
                "--output-dir", output_dir,
                "--seed", "42",
                "--log-level", "WARNING",
            ],
        )
        assert result.exit_code == 0
        assert "Pipeline Complete" in result.output
        # Verify output files
        result_dirs = list(Path(output_dir).iterdir())
        assert len(result_dirs) > 0
        run_dir = result_dirs[0]
        assert (run_dir / "report.html").exists()
        assert (run_dir / "summary.json").exists()
        assert (run_dir / "SHA256SUMS.txt").exists()

    @pytest.mark.slow
    def test_run_all_default_config(self, runner, tmp_path):
        """Test run-all falls back to default config."""
        output_dir = str(tmp_path / "default_results")
        result = runner.invoke(
            main,
            [
                "run-all",
                "--output-dir", output_dir,
                "--log-level", "WARNING",
            ],
        )
        assert result.exit_code == 0
        assert "Pipeline Complete" in result.output


class TestCLIDemo:
    """Test the demo command."""

    @pytest.mark.slow
    def test_demo_success(self, runner, tmp_path):
        """Test demo command runs full pipeline."""
        output_dir = str(tmp_path / "demo_results")
        result = runner.invoke(
            main,
            ["demo", "--output-dir", output_dir, "--log-level", "WARNING"],
        )
        assert result.exit_code == 0
        assert "Demo Complete" in result.output
        assert "RESEARCH_BACKTEST_ONLY" in result.output
        assert "n_factors: 21" in result.output

    @pytest.mark.slow
    def test_demo_report_path(self, runner, tmp_path):
        """Test demo outputs a valid report path."""
        output_dir = str(tmp_path / "demo_results2")
        result = runner.invoke(
            main,
            ["demo", "--output-dir", output_dir, "--log-level", "WARNING"],
        )
        assert result.exit_code == 0
        assert "[DOC] Report:" in result.output
        # Extract path and verify file exists
        report_line = next(line for line in result.output.split("\n") if "[DOC] Report:" in line)
        report_path = report_line.split("[DOC] Report:")[1].strip()
        assert Path(report_path).exists()


class TestCLIExitCodes:
    """Test that commands return proper exit codes."""

    def test_doctor_exit_zero(self, runner):
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0

    def test_init_exit_zero(self, runner, tmp_path):
        result = runner.invoke(main, ["init", "--output-dir", str(tmp_path / "x")])
        assert result.exit_code == 0

    def test_generate_demo_data_exit_zero(self, runner, tmp_path):
        result = runner.invoke(
            main, ["generate-demo-data", "--output", str(tmp_path / "d.csv")]
        )
        assert result.exit_code == 0

    def test_missing_config_returns_nonzero(self, runner):
        """All commands requiring --config should fail with missing config."""
        for cmd in ["ingest", "validate-data", "evaluate", "oos", "backtest", "report"]:
            result = runner.invoke(main, [cmd, "--config", "nonexistent.yaml"])
            assert result.exit_code != 0, f"{cmd} should fail with missing config"
