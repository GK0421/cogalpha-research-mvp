"""Tests for configuration management."""

import pytest

from cogalpha_mvp.config import Config


class TestConfig:
    """Tests for configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.data.train_start == "2011-01-01"
        assert config.data.train_end == "2019-12-31"
        assert config.data.oos_start == "2020-01-01"
        assert config.data.oos_end == "2025-12-31"
        assert config.factors.qualified_score_threshold == 0.65
        assert config.factors.elite_score_threshold == 0.80
        assert config.dedup.absolute_correlation_threshold == 0.85

    def test_validate_boundaries(self):
        """Test boundary validation."""
        config = Config()
        config.data.validate_boundaries()  # Should not raise

    def test_validate_boundaries_overlap(self):
        """Test that overlapping boundaries raise error."""
        config = Config()
        config.data.train_end = "2021-06-30"
        config.data.oos_start = "2021-01-01"
        with pytest.raises(AssertionError):
            config.data.validate_boundaries()

    def test_from_yaml(self):
        """Test loading config from YAML file."""
        import os
        import tempfile

        import yaml

        yaml_content = {
            "data": {
                "train_start": "2020-01-01",
                "train_end": "2022-12-31",
                "oos_start": "2023-01-01",
                "oos_end": "2024-12-31",
            },
            "factors": {
                "qualified_score_threshold": 0.60,
                "elite_score_threshold": 0.75,
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            path = f.name
        try:
            config = Config.from_yaml(path)
            assert config.data.train_start == "2020-01-01"
            assert config.factors.qualified_score_threshold == 0.60
        finally:
            os.unlink(path)

    def test_research_only_flag(self):
        """Test that portfolio config has transaction cost settings."""
        config = Config()
        assert config.portfolio.transaction_cost_bps > 0
        assert config.portfolio.slippage_bps > 0
