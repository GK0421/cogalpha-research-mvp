"""Configuration management for CogAlpha Research MVP.

All paths are handled via pathlib.Path. No hardcoded absolute paths.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DataConfig:
    """Data layer configuration."""

    full_start: str = "2011-01-01"
    full_end: str = "2025-12-31"
    train_start: str = "2011-01-01"
    train_end: str = "2019-12-31"
    oos_start: str = "2020-01-01"
    oos_end: str = "2025-12-31"
    raw_dir: str = "data/raw"
    normalized_dir: str = "data/normalized"
    features_dir: str = "data/features"

    def validate_boundaries(self) -> None:
        """Ensure train and OOS periods do not overlap."""
        assert self.train_start < self.train_end, "train_start must be before train_end"
        assert self.oos_start < self.oos_end, "oos_start must be before oos_end"
        assert self.train_end <= self.oos_start, (
            f"train_end ({self.train_end}) must be <= oos_start ({self.oos_start})"
        )


@dataclass
class FactorConfig:
    """Factor evaluation configuration."""

    qualified_score_threshold: float = 0.65
    elite_score_threshold: float = 0.80
    min_ic_qualified: float = 0.005
    min_icir_qualified: float = 0.05
    min_rankic_qualified: float = 0.005
    min_rankicir_qualified: float = 0.05
    min_ic_elite: float = 0.01
    min_icir_elite: float = 0.10
    min_rankic_elite: float = 0.01
    min_rankicir_elite: float = 0.10
    return_label: str = "next_1d_return"
    forward_period: int = 1


@dataclass
class DedupConfig:
    """Deduplication configuration."""

    absolute_correlation_threshold: float = 0.85
    structural_dedup: bool = True
    numerical_dedup: bool = True


@dataclass
class PortfolioConfig:
    """Portfolio backtest configuration."""

    top_quantile: float = 0.2
    bottom_quantile: float = 0.2
    rebalance: str = "weekly"
    transaction_cost_bps: float = 10.0
    slippage_bps: float = 5.0
    max_single_weight: float = 0.05


@dataclass
class QualityConfig:
    """Quality checking configuration."""

    min_valid_ratio: float = 0.5
    max_nan_ratio: float = 0.5
    near_constant_threshold: float = 1e-8
    truncation_test_dates: int = 10
    truncation_max_diff: float = 1e-10
    truncation_min_corr: float = 0.9999
    max_complexity: int = 100
    max_window_size: int = 500


@dataclass
class GenerationConfig:
    """LLM generation configuration."""

    enabled: bool = False
    mode: str = "concrete"
    temperature_range: dict[str, list[float]] = field(
        default_factory=lambda: {
            "mild": [0.1, 0.3],
            "moderate": [0.3, 0.5],
            "creative": [0.5, 0.7],
            "divergent": [0.7, 0.9],
            "concrete": [0.5, 0.7],
        }
    )
    max_concurrent_requests: int = 5
    max_retry_on_error: int = 3
    timeout: int = 60


@dataclass
class Config:
    """Master configuration object."""

    data: DataConfig = field(default_factory=DataConfig)
    factors: FactorConfig = field(default_factory=FactorConfig)
    dedup: DedupConfig = field(default_factory=DedupConfig)
    portfolio: PortfolioConfig = field(default_factory=PortfolioConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    seed: int = 42
    output_dir: str = "results"
    log_level: str = "INFO"
    run_id: str = ""
    _source_path: str = ""

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load configuration from a YAML file."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        cfg = cls()
        cfg._source_path = str(path.resolve())

        if "data" in raw:
            for k, v in raw["data"].items():
                if hasattr(cfg.data, k):
                    setattr(cfg.data, k, v)

        if "factors" in raw:
            for k, v in raw["factors"].items():
                if hasattr(cfg.factors, k):
                    setattr(cfg.factors, k, v)

        if "dedup" in raw:
            for k, v in raw["dedup"].items():
                if hasattr(cfg.dedup, k):
                    setattr(cfg.dedup, k, v)

        if "portfolio" in raw:
            for k, v in raw["portfolio"].items():
                if hasattr(cfg.portfolio, k):
                    setattr(cfg.portfolio, k, v)

        if "quality" in raw:
            for k, v in raw["quality"].items():
                if hasattr(cfg.quality, k):
                    setattr(cfg.quality, k, v)

        if "generation" in raw:
            for k, v in raw["generation"].items():
                if hasattr(cfg.generation, k):
                    setattr(cfg.generation, k, v)

        if "seed" in raw:
            cfg.seed = raw["seed"]
        if "output_dir" in raw:
            cfg.output_dir = raw["output_dir"]
        if "log_level" in raw:
            cfg.log_level = raw["log_level"]
        if "run_id" in raw:
            cfg.run_id = raw["run_id"]

        cfg.data.validate_boundaries()
        return cfg

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to a dictionary."""
        return {
            "data": self.data.__dict__,
            "factors": self.factors.__dict__,
            "dedup": self.dedup.__dict__,
            "portfolio": self.portfolio.__dict__,
            "quality": self.quality.__dict__,
            "generation": self.generation.__dict__,
            "seed": self.seed,
            "output_dir": self.output_dir,
            "log_level": self.log_level,
            "run_id": self.run_id,
        }

    def snapshot(self, output_path: str | Path) -> None:
        """Save a configuration snapshot for reproducibility."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)

    def fingerprint(self) -> str:
        """Compute a SHA256 fingerprint of the configuration."""
        content = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


def load_config(path: str | Path) -> Config:
    """Convenience function to load configuration."""
    return Config.from_yaml(path)
