"""Tests for seed factors."""

import numpy as np
import pandas as pd
import pytest

from cogalpha_mvp.factors.dsl import FactorInterpreter, FactorParser
from cogalpha_mvp.factors.registry import FactorRegistry
from cogalpha_mvp.factors.seed_factors import (
    get_all_seed_factors,
    register_seed_factors,
)


class TestSeedFactors:
    """Tests for 21 seed factors."""

    def test_count_21(self):
        """Test that exactly 21 seed factors are generated."""
        factors = get_all_seed_factors()
        assert len(factors) == 21, f"Expected 21, got {len(factors)}"

    def test_all_expressions_valid(self):
        """Test that all seed factor expressions are valid DSL."""
        factors = get_all_seed_factors()
        for f in factors:
            is_valid, msg = FactorParser.validate(f.expression)
            assert is_valid, (
                f"Seed factor {f.factor_id} ({f.name}) has invalid expression: {msg}\nExpression: {f.expression}"
            )

    def test_all_agents_represented(self):
        """Test that all 21 agents have at least one seed factor."""
        factors = get_all_seed_factors()
        agent_ids = {f.agent_id for f in factors}
        assert len(agent_ids) == 21, f"Expected 21 agents, got {len(agent_ids)}"

    def test_all_levels_represented(self):
        """Test that all 7 levels have seed factors."""
        factors = get_all_seed_factors()
        levels = {f.level for f in factors}
        assert levels == {1, 2, 3, 4, 5, 6, 7}, f"Expected levels 1-7, got {sorted(levels)}"

    def test_direction_valid(self):
        """Test that all factors have valid direction."""
        factors = get_all_seed_factors()
        for f in factors:
            assert f.direction in (1, -1), f"Invalid direction {f.direction} for {f.factor_id}"

    def test_description_not_empty(self):
        """Test that all factors have non-empty descriptions."""
        factors = get_all_seed_factors()
        for f in factors:
            assert len(f.description) > 10, f"Description too short for {f.factor_id}"

    @pytest.fixture
    def sample_data(self):
        """Create sample market data for evaluation."""
        dates = pd.bdate_range("2020-01-01", "2020-06-30")
        n = len(dates)
        rng = np.random.default_rng(42)
        records = []
        for sym in ["A", "B", "C", "D", "E"]:
            prices = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
            for i, date in enumerate(dates):
                records.append(
                    {
                        "symbol": sym,
                        "trade_date": date,
                        "open": prices[i] * (1 + rng.normal(0, 0.005)),
                        "high": prices[i] * (1 + abs(rng.normal(0, 0.01))),
                        "low": prices[i] * (1 - abs(rng.normal(0, 0.01))),
                        "close": prices[i],
                        "volume": rng.integers(1e6, 5e7),
                        "amount": prices[i] * rng.integers(1e6, 5e7),
                    }
                )
        return pd.DataFrame(records)

    def test_all_factors_evaluable(self, sample_data):
        """Test that all 21 seed factors can be evaluated without errors."""
        factors = get_all_seed_factors()
        interpreter = FactorInterpreter()
        for f in factors:
            result = interpreter.evaluate(f.expression, sample_data)
            assert len(result) > 0, f"Factor {f.factor_id} produced empty result"
            assert "factor_value" in result.columns

    def test_registry_registration(self):
        """Test that all seed factors register correctly."""
        registry = FactorRegistry()
        count = register_seed_factors(registry)
        assert count == 21, f"Expected 21 registered, got {count}"
        assert registry.count == 21

    def test_registry_dedup(self):
        """Test that registering same factors twice doesn't create duplicates."""
        registry = FactorRegistry()
        register_seed_factors(registry)
        register_seed_factors(registry)  # Register again
        assert registry.count == 21, "Duplicate registration should be rejected"
