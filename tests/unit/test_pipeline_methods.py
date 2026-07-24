"""Fast unit tests for PipelineRunner methods (no full pipeline run).

Tests individual methods directly for coverage without the
performance cost of running the full pipeline end-to-end.
"""

from __future__ import annotations

import json

import pytest
import yaml

from cogalpha_mvp.config import Config
from cogalpha_mvp.pipeline.runner import PipelineRunner


@pytest.fixture
def fast_config(tmp_path):
    """Create a config with very short date range."""
    config_data = {
        "data": {
            "full_start": "2022-01-03",
            "full_end": "2022-01-31",
            "train_start": "2022-01-03",
            "train_end": "2022-01-21",
            "oos_start": "2022-01-24",
            "oos_end": "2022-01-31",
        },
        "factors": {
            "qualified_score_threshold": 0.0,
            "elite_score_threshold": 0.0,
            "min_ic_qualified": -999,
            "min_icir_qualified": -999,
            "min_rankic_qualified": -999,
            "min_rankicir_qualified": -999,
            "min_ic_elite": -999,
            "min_icir_elite": -999,
            "min_rankic_elite": -999,
            "min_rankicir_elite": -999,
            "forward_period": 1,
        },
        "portfolio": {
            "top_quantile": 0.2,
            "bottom_quantile": 0.2,
            "rebalance": "daily",
            "transaction_cost_bps": 10,
            "slippage_bps": 5,
            "max_single_weight": 0.05,
        },
        "quality": {
            "min_valid_ratio": 0.01,
            "max_nan_ratio": 0.99,
            "near_constant_threshold": 0.0,
            "truncation_test_dates": 1,
            "truncation_max_diff": 999,
            "truncation_min_corr": -1,
            "max_complexity": 1000,
        },
        "dedup": {"correlation_threshold": 0.99, "structural_dedup_enabled": True},
        "generation": {"enabled": False},
        "seed": 42,
        "output_dir": str(tmp_path / "fast_runner"),
        "log_level": "ERROR",
        "run_id": "unit_test",
    }
    config_path = tmp_path / "fast_config.yaml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    return Config.from_yaml(str(config_path))


@pytest.fixture
def runner(fast_config):
    return PipelineRunner(fast_config)


@pytest.fixture
def sample_data():
    """Small synthetic data for testing."""
    from cogalpha_mvp.data.adapters import SyntheticDataAdapter
    from cogalpha_mvp.domain.data_contract import DataRequest

    adapter = SyntheticDataAdapter()
    return adapter.load(DataRequest(start_date="2022-01-03", end_date="2022-01-31"))


class TestPipelineRunnerMethods:
    """Test individual PipelineRunner methods without full pipeline run."""

    def test_save_environment(self, runner):
        """Test _save_environment creates environment.json."""
        runner._save_environment()
        env_path = runner.output_dir / "environment.json"
        assert env_path.exists()
        env = json.loads(env_path.read_text())
        assert "python_version" in env
        assert "platform" in env

    def test_load_data_synthetic(self, runner):
        """Test _load_data with synthetic data."""
        data = runner._load_data(use_synthetic=True, data_path="")
        assert len(data) > 0
        assert "symbol" in data.columns
        assert "close" in data.columns
        # Check manifest was created
        assert (runner.output_dir / "data_manifest.json").exists()

    def test_validate_data(self, runner, sample_data):
        """Test _validate_data normalizes data."""
        validated = runner._validate_data(sample_data)
        assert "symbol" in validated.columns
        assert "trade_date" in validated.columns

    def test_split_data(self, runner, sample_data):
        """Test _split_data creates train and OOS sets."""
        train, oos = runner._split_data(sample_data)
        assert len(train) > 0
        assert len(oos) > 0
        # Check run manifest
        assert (runner.output_dir / "run_manifest.json").exists()

    def test_register_factors(self, runner):
        """Test _register_factors registers 21 seed factors."""
        runner._register_factors()
        assert runner.registry.count == 21

    def test_quality_check(self, runner, sample_data):
        """Test _quality_check returns results for all factors."""
        runner._register_factors()
        results = runner._quality_check(sample_data)
        assert len(results) == 21
        assert (runner.output_dir / "quality" / "factor_quality.csv").exists()

    def test_evaluate_factors(self, runner, sample_data):
        """Test _evaluate_factors returns metrics."""
        runner._register_factors()
        runner._quality_check(sample_data)
        metrics, values = runner._evaluate_factors(sample_data)
        assert isinstance(metrics, dict)
        assert isinstance(values, dict)

    def test_score_factors(self, runner, sample_data):
        """Test _score_factors classifies factors."""
        runner._register_factors()
        runner._quality_check(sample_data)
        train_metrics, _fv = runner._evaluate_factors(sample_data)
        scoring = runner._score_factors(train_metrics)
        assert isinstance(scoring, dict)

    def test_dedup(self, runner, sample_data):
        """Test _dedup removes correlated factors."""
        runner._register_factors()
        runner._quality_check(sample_data)
        train_metrics, factor_values = runner._evaluate_factors(sample_data)
        scoring = runner._score_factors(train_metrics)
        result = runner._dedup(train_metrics, factor_values, scoring)
        assert "before" in result
        assert "after" in result
        assert (runner.output_dir / "dedup" / "dedup_results.csv").exists()

    def test_oos_validation(self, runner, sample_data):
        """Test _oos_validation runs OOS evaluation."""
        runner._register_factors()
        runner._quality_check(sample_data)
        train_metrics, factor_values = runner._evaluate_factors(sample_data)
        scoring = runner._score_factors(train_metrics)
        dedup_result = runner._dedup(train_metrics, factor_values, scoring)
        oos_metrics = runner._oos_validation(sample_data, dedup_result)
        assert isinstance(oos_metrics, dict)
        assert (runner.output_dir / "oos" / "oos_metrics.csv").exists()

    def test_backtest(self, runner, sample_data):
        """Test _backtest runs portfolio strategies."""
        runner._register_factors()
        runner._quality_check(sample_data)
        _tm, factor_values = runner._evaluate_factors(sample_data)
        results = runner._backtest(factor_values, sample_data)
        assert isinstance(results, dict)
        assert (runner.output_dir / "portfolio" / "portfolio_results.csv").exists()

    def test_generate_report(self, runner, sample_data):
        """Test _generate_report creates HTML report."""
        report_path = runner._generate_report(
            data=sample_data,
            quality_results=[{"factor_id": "f1", "passed": True, "stage": "", "error": ""}],
            train_metrics={"f1": {"ic_mean": 0.05}},
            scoring_results={
                "f1": {"status": "qualified", "composite_score": 0.7, "metrics": {"ic_mean": 0.05}}
            },
            dedup_results={"before": 1, "after": 1, "removed": 0, "removed_ids": []},
            oos_metrics={"f1": {"ic_mean": 0.03}},
            portfolio_results={"long_short": {"annual_return": 0.1}},
        )
        assert report_path.exists()
        assert "RESEARCH_BACKTEST_ONLY" in report_path.read_text(encoding="utf-8")

    def test_generate_sha256sums(self, runner):
        """Test _generate_sha256sums creates hash file."""
        # Create a test file
        (runner.output_dir / "test.txt").write_text("test content")
        runner._generate_sha256sums()
        sha_path = runner.output_dir / "SHA256SUMS.txt"
        assert sha_path.exists()
        content = sha_path.read_text()
        assert "test.txt" in content
        assert len(content.split("\n")[0].split("  ")[0]) == 64
