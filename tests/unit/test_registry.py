"""Tests for factor registry and deduplication."""

from cogalpha_mvp.factors.registry import FactorMetadata, FactorRegistry
from cogalpha_mvp.factors.seed_factors import register_seed_factors


class TestFactorRegistry:
    """Tests for factor registry."""

    def test_register_factor(self):
        """Test registering a single factor."""
        registry = FactorRegistry()
        factor = FactorMetadata(
            factor_id="test_001",
            name="test_factor",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="20-day moving average for trend identification",
        )
        registry.register(factor)
        assert registry.count == 1

    def test_register_duplicate_rejected(self):
        """Test that duplicate factor IDs are rejected."""
        registry = FactorRegistry()
        factor = FactorMetadata(
            factor_id="dup_001",
            name="dup_factor",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="Duplicate test factor for trend identification",
        )
        registry.register(factor)
        registry.register(factor)  # Same ID
        assert registry.count == 1

    def test_register_structural_duplicate(self):
        """Test that structurally identical factors are deduped."""
        registry = FactorRegistry()
        f1 = FactorMetadata(
            factor_id="struct_001",
            name="struct_factor_a",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="20-day moving average for trend identification",
        )
        f2 = FactorMetadata(
            factor_id="struct_002",
            name="struct_factor_b",
            agent_id="Agent_02",
            level=2,
            expression="ts_mean(close, 20)",  # Same expression
            description="Another 20-day moving average for trend identification",
        )
        registry.register(f1)
        registry.register(f2)
        assert registry.count == 1, "Structurally identical factors should be deduped"

    def test_get_by_id(self):
        """Test getting factor by ID."""
        registry = FactorRegistry()
        factor = FactorMetadata(
            factor_id="get_001",
            name="get_factor",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 20)",
            description="Test factor for trend identification purposes",
        )
        registry.register(factor)
        retrieved = registry.get("get_001")
        assert retrieved is not None
        assert retrieved.factor_id == "get_001"

    def test_get_nonexistent(self):
        """Test getting a non-existent factor returns None."""
        registry = FactorRegistry()
        assert registry.get("nonexistent") is None

    def test_filter_by_level(self):
        """Test filtering factors by level."""
        registry = FactorRegistry()
        register_seed_factors(registry)
        level1 = registry.filter_by_level(1)
        assert len(level1) == 3  # 3 agents per level
        level7 = registry.filter_by_level(7)
        assert len(level7) == 3

    def test_all_factors(self):
        """Test getting all factors."""
        registry = FactorRegistry()
        register_seed_factors(registry)
        all_factors = registry.all_factors()
        assert len(all_factors) == 21

    def test_clear(self):
        """Test clearing the registry."""
        registry = FactorRegistry()
        register_seed_factors(registry)
        registry.clear()
        assert registry.count == 0

    def test_evaluate_factor(self):
        """Test evaluating a factor against data."""
        import numpy as np
        import pandas as pd

        registry = FactorRegistry()
        factor = FactorMetadata(
            factor_id="eval_001",
            name="eval_factor",
            agent_id="Agent_01",
            level=1,
            expression="ts_mean(close, 5)",
            description="Test factor for evaluation",
        )
        registry.register(factor)

        dates = pd.bdate_range("2020-01-01", "2020-03-31")
        rng = np.random.default_rng(42)
        data = pd.DataFrame(
            {
                "symbol": "TEST",
                "trade_date": dates,
                "open": 100,
                "high": 101,
                "low": 99,
                "close": 100 + rng.normal(0, 1, len(dates)).cumsum(),
                "volume": rng.integers(1e6, 5e7, len(dates)),
            }
        )
        result = registry.evaluate_factor("eval_001", data)
        assert len(result) == len(data)
        assert "factor_value" in result.columns

    def test_evaluate_all(self):
        """Test evaluating all factors."""
        import numpy as np
        import pandas as pd

        registry = FactorRegistry()
        register_seed_factors(registry)

        dates = pd.bdate_range("2020-01-01", "2020-03-31")
        rng = np.random.default_rng(42)
        records = []
        for sym in ["A", "B", "C"]:
            prices = 100 + rng.normal(0, 1, len(dates)).cumsum()
            for d, p in zip(dates, prices, strict=False):
                records.append(
                    {
                        "symbol": sym,
                        "trade_date": d,
                        "open": p,
                        "high": p * 1.01,
                        "low": p * 0.99,
                        "close": p,
                        "volume": int(rng.integers(1e6, 5e7)),
                    }
                )
        data = pd.DataFrame(records)

        results = registry.evaluate_all(data)
        assert len(results) > 0

    def test_passed_factors(self):
        """Test getting passed factors."""
        registry = FactorRegistry()
        f1 = FactorMetadata(
            factor_id="pass_001",
            name="f1",
            agent_id="A1",
            level=1,
            expression="ts_mean(close, 20)",
            description="Test factor for trend identification",
        )
        f1.review_status = "passed"
        f2 = FactorMetadata(
            factor_id="pass_002",
            name="f2",
            agent_id="A2",
            level=1,
            expression="ts_mean(close, 30)",
            description="Test factor for trend identification variant",
        )
        f2.review_status = "rejected"
        registry.register(f1)
        registry.register(f2)

        passed = registry.passed_factors()
        assert len(passed) == 1
        assert passed[0].factor_id == "pass_001"

    def test_structural_dedup(self):
        """Test structural dedup removes duplicates."""
        registry = FactorRegistry()
        f1 = FactorMetadata(
            factor_id="sd_001",
            name="f1",
            agent_id="A1",
            level=1,
            expression="ts_mean(close, 20)",
            description="Test factor for trend identification",
        )
        f2 = FactorMetadata(
            factor_id="sd_002",
            name="f2",
            agent_id="A2",
            level=2,
            expression="ts_mean(close, 20)",  # Same hash
            description="Another test factor for trend identification",
        )
        # Register both without auto-dedup by using different IDs
        # The register method auto-dedups, so we need to test structural_dedup separately
        registry.register(f1)
        # f2 has same expression hash, so it won't be registered
        registry.register(f2)
        assert registry.count == 1

    def test_count_property(self):
        """Test count property."""
        registry = FactorRegistry()
        assert registry.count == 0
        register_seed_factors(registry)
        assert registry.count == 21

    def test_filter_by_level_nonexistent(self):
        """Test filtering by nonexistent level returns empty."""
        registry = FactorRegistry()
        register_seed_factors(registry)
        result = registry.filter_by_level(99)
        assert len(result) == 0
