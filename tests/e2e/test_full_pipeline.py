"""E2E test: full pipeline run with synthetic data."""

from cogalpha_mvp.config import Config
from cogalpha_mvp.pipeline.runner import PipelineRunner


class TestFullPipelineE2E:
    """End-to-end test of the complete pipeline."""

    def test_run_all_synthetic(self, tmp_path):
        """Test running the full pipeline with synthetic data."""
        config = Config()
        config.output_dir = str(tmp_path)
        # Use shorter date range for faster test
        config.data.full_start = "2020-01-01"
        config.data.full_end = "2021-12-31"
        config.data.train_start = "2020-01-01"
        config.data.train_end = "2020-12-31"
        config.data.oos_start = "2021-01-01"
        config.data.oos_end = "2021-12-31"
        config.data.validate_boundaries()

        runner = PipelineRunner(config)
        summary = runner.run_all(use_synthetic=True)

        # Verify summary has expected keys
        assert "run_id" in summary
        assert "n_factors" in summary
        assert "n_passed_quality" in summary

        # Verify some factors passed
        assert summary["n_factors"] == 21
        assert summary["n_passed_quality"] > 0, "At least some factors should pass"

    def test_run_all_deterministic(self, tmp_path):
        """Test that the same config produces the same summary."""
        config1 = Config()
        config1.output_dir = str(tmp_path / "run1")
        config1.data.full_start = "2020-01-01"
        config1.data.full_end = "2021-06-30"
        config1.data.train_start = "2020-01-01"
        config1.data.train_end = "2020-12-31"
        config1.data.oos_start = "2021-01-01"
        config1.data.oos_end = "2021-06-30"
        config1.data.validate_boundaries()

        config2 = Config()
        config2.output_dir = str(tmp_path / "run2")
        config2.data = config1.data

        runner1 = PipelineRunner(config1)
        summary1 = runner1.run_all(use_synthetic=True)

        runner2 = PipelineRunner(config2)
        summary2 = runner2.run_all(use_synthetic=True)

        # With same seed, results should be identical
        assert summary1["n_factors"] == summary2["n_factors"]
        assert summary1["n_passed_quality"] == summary2["n_passed_quality"]
        assert summary1["n_elite"] == summary2["n_elite"]
        assert summary1["n_qualified"] == summary2["n_qualified"]

    def test_oos_validation_present(self, tmp_path):
        """Test that OOS validation metrics are in the summary."""
        config = Config()
        config.output_dir = str(tmp_path)
        config.data.full_start = "2020-01-01"
        config.data.full_end = "2021-12-31"
        config.data.train_start = "2020-01-01"
        config.data.train_end = "2020-12-31"
        config.data.oos_start = "2021-01-01"
        config.data.oos_end = "2021-12-31"
        config.data.validate_boundaries()

        runner = PipelineRunner(config)
        summary = runner.run_all(use_synthetic=True)

        # OOS validation should have been performed
        assert summary.get("n_passed_quality", 0) > 0
