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
