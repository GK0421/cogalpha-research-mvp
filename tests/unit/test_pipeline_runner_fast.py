"""Fast unit test for PipelineRunner that covers runner.py.

Uses a very short date range (1 month) for speed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cogalpha_mvp.config import Config
from cogalpha_mvp.pipeline.runner import PipelineRunner


@pytest.fixture
def fast_config(tmp_path):
    """Create a config with very short date range (1 month) for fast testing."""
    config_data = {
        "data": {
            "full_start": "2022-01-03",
            "full_end": "2022-01-31",
            "train_start": "2022-01-03",
            "train_end": "2022-01-21",
            "oos_start": "2022-01-24",
            "oos_end": "2022-01-31",
            "raw_dir": "data/raw",
            "normalized_dir": "data/normalized",
            "features_dir": "data/features",
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
        "dedup": {
            "correlation_threshold": 0.99,
            "structural_dedup_enabled": True,
        },
        "generation": {"enabled": False},
        "seed": 42,
        "output_dir": str(tmp_path / "fast_pipeline"),
        "log_level": "ERROR",
        "run_id": "fast_test",
    }
    config_path = tmp_path / "fast_config.yaml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    return Config.from_yaml(str(config_path))


class TestPipelineRunnerFast:
    """Fast test for PipelineRunner with 1-month data range."""

    @pytest.mark.slow
    def test_run_all_fast(self, fast_config):
        """Test run_all with very short date range."""
        runner = PipelineRunner(fast_config)
        summary = runner.run_all(use_synthetic=True)

        assert summary["run_id"] == "fast_test"
        assert summary["n_factors"] == 21
        assert "RESEARCH_BACKTEST_ONLY" in summary["disclaimer"]

        # Verify output directory
        output_dir = Path(fast_config.output_dir) / "fast_test"
        assert (output_dir / "report.html").exists()
        assert (output_dir / "SHA256SUMS.txt").exists()
        assert (output_dir / "environment.json").exists()
        assert (output_dir / "data_manifest.json").exists()
        assert (output_dir / "run_manifest.json").exists()
        assert (output_dir / "config_snapshot.yaml").exists()
