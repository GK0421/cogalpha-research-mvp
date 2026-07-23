"""Tests for factor deduplication."""

import numpy as np
import pandas as pd

from cogalpha_mvp.config import DedupConfig
from cogalpha_mvp.evaluation.dedup import FactorDeduplicator
from cogalpha_mvp.factors.registry import FactorMetadata
from cogalpha_mvp.factors.seed_factors import get_all_seed_factors


class TestFactorDeduplication:
    """Tests for structural and numerical deduplication."""

    def test_structural_dedup_same_expression(self):
        """Test that identical expressions are deduped."""
        dedup = FactorDeduplicator(DedupConfig())
        f1 = FactorMetadata(
            factor_id="dedup_001",
            name="dedup_a",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="20-day moving average for trend identification",
        )
        f2 = FactorMetadata(
            factor_id="dedup_002",
            name="dedup_b",
            agent_id="Agent_02",
            level=2,
            expression="ts_mean(close, 20)",
            description="Another 20-day MA for trend identification",
        )
        unique, removed = dedup.structural_dedup([f1, f2])
        assert len(unique) == 1, "Same expression should be structural duplicate"
        assert len(removed) == 1

    def test_structural_dedup_different_expression(self):
        """Test that different expressions are not deduped."""
        dedup = FactorDeduplicator(DedupConfig())
        f1 = FactorMetadata(
            factor_id="dedup_003",
            name="dedup_c",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="20-day moving average for trend identification",
        )
        f2 = FactorMetadata(
            factor_id="dedup_004",
            name="dedup_d",
            agent_id="Agent_02",
            level=2,
            expression="ts_mean(close, 30)",
            description="30-day moving average for trend identification",
        )
        unique, _removed = dedup.structural_dedup([f1, f2])
        assert len(unique) == 2, "Different expressions should not be deduped"

    def test_numerical_dedup_identical_values(self):
        """Test that identical factor values are deduped."""
        dedup = FactorDeduplicator(DedupConfig())
        rng = np.random.default_rng(42)
        values = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"] * 10,
                "trade_date": pd.Timestamp("2020-01-01")
                + pd.Timedelta(days=0)
                + pd.to_timedelta(list(range(10)) * 3, unit="D"),
                "factor_value": rng.normal(0, 1, 30),
            }
        )
        factor_values = {"f1": values, "f2": values.copy()}
        scores = {"f1": 0.8, "f2": 0.8}
        factors = [
            FactorMetadata(
                factor_id="f1",
                name="f1",
                agent_id="A",
                level=1,
                expression="close",
                description="Test factor one",
            ),
            FactorMetadata(
                factor_id="f2",
                name="f2",
                agent_id="A",
                level=1,
                expression="open",
                description="Test factor two",
            ),
        ]
        unique, _removed = dedup.numerical_dedup(factors, factor_values, scores)
        assert len(unique) == 1, "Identical values should be numerical duplicates"

    def test_numerical_dedup_different_values(self):
        """Test that different factor values are not deduped."""
        dedup = FactorDeduplicator(DedupConfig())
        rng = np.random.default_rng(42)
        v1 = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"] * 10,
                "trade_date": pd.to_datetime("2020-01-01")
                + pd.to_timedelta(list(range(10)) * 3, unit="D"),
                "factor_value": rng.normal(0, 1, 30),
            }
        )
        v2 = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"] * 10,
                "trade_date": pd.to_datetime("2020-01-01")
                + pd.to_timedelta(list(range(10)) * 3, unit="D"),
                "factor_value": rng.normal(100, 1, 30),
            }
        )
        factor_values = {"f1": v1, "f2": v2}
        scores = {"f1": 0.8, "f2": 0.8}
        factors = [
            FactorMetadata(
                factor_id="f1",
                name="f1",
                agent_id="A",
                level=1,
                expression="close",
                description="Test factor one",
            ),
            FactorMetadata(
                factor_id="f2",
                name="f2",
                agent_id="A",
                level=1,
                expression="open",
                description="Test factor two",
            ),
        ]
        unique, _removed = dedup.numerical_dedup(factors, factor_values, scores)
        assert len(unique) == 2, "Different values should not be deduped"

    def test_seed_factors_not_duplicates(self):
        """Test that the 21 seed factors are not structurally duplicated."""
        factors = get_all_seed_factors()
        dedup = FactorDeduplicator(DedupConfig())
        unique, removed = dedup.structural_dedup(factors)
        assert len(unique) == 21, f"Expected 21 unique, got {len(unique)}"
        assert len(removed) == 0
