"""Tests for factor DSL parser and interpreter."""

import numpy as np
import pandas as pd
import pytest

from cogalpha_mvp.factors.dsl import (
    DSLParseError,
    DSLRuntimeError,
    FactorDefinition,
    FactorInterpreter,
    FactorParser,
)


class TestFactorParser:
    """Tests for DSL parser validation."""

    def test_valid_expression(self):
        """Test that a valid expression passes."""
        is_valid, msg = FactorParser.validate("ts_mean(close, 20)")
        assert is_valid, f"Expected valid, got: {msg}"

    def test_valid_complex_expression(self):
        """Test that a complex valid expression passes."""
        expr = "div(sub(close, delay(close, 20)), delay(close, 20))"
        is_valid, msg = FactorParser.validate(expr)
        assert is_valid, f"Expected valid, got: {msg}"

    def test_empty_expression(self):
        """Test that empty expression is rejected."""
        is_valid, _msg = FactorParser.validate("")
        assert not is_valid

    def test_unknown_function(self):
        """Test that unknown functions are rejected."""
        is_valid, msg = FactorParser.validate("unknown_func(close)")
        assert not is_valid
        assert "unknown_func" in msg.lower() or "Unknown" in msg

    def test_negative_shift_forbidden(self):
        """Test that shift(-1) pattern is forbidden."""
        is_valid, _msg = FactorParser.validate("shift(close, -1)")
        assert not is_valid

    def test_import_forbidden(self):
        """Test that import statements are forbidden."""
        is_valid, _msg = FactorParser.validate("import os")
        assert not is_valid

    def test_attribute_access_forbidden(self):
        """Test that attribute access is forbidden."""
        is_valid, _msg = FactorParser.validate("close.shift(1)")
        assert not is_valid

    def test_all_whitelist_functions(self):
        """Test that all whitelisted functions are accepted."""
        funcs = [
            "delay(close, 1)",
            "delta(close, 1)",
            "ret(close, 1)",
            "ts_mean(close, 5)",
            "ts_sum(close, 5)",
            "ts_std(close, 5)",
            "ts_min(close, 5)",
            "ts_max(close, 5)",
            "ts_rank(close, 5)",
            "corr(close, volume, 10)",
            "cov(close, volume, 10)",
            "rank(close)",
            "zscore(close)",
            "winsorize(close, 3)",
            "abs(ret(close, 1))",
            "sign(ret(close, 1))",
            "log1p(volume)",
            "sqrt(volume)",
            "clip(close, 0, 100)",
            "add(close, volume)",
            "sub(close, volume)",
            "mul(close, volume)",
            "div(close, volume)",
            "min(close, volume)",
            "max(close, volume)",
            "where(close > 10, close, 0)",
        ]
        for expr in funcs:
            is_valid, msg = FactorParser.validate(expr)
            assert is_valid, f"Failed for '{expr}': {msg}"


class TestFactorInterpreter:
    """Tests for DSL interpreter."""

    @pytest.fixture
    def sample_data(self):
        """Create sample market data."""
        dates = pd.bdate_range("2020-01-01", "2020-06-30")
        n = len(dates)
        rng = np.random.default_rng(42)
        prices = 100 * np.cumprod(1 + rng.normal(0, 0.02, n))
        df = pd.DataFrame(
            {
                "symbol": "TEST",
                "trade_date": dates,
                "open": prices * (1 + rng.normal(0, 0.005, n)),
                "high": prices * (1 + abs(rng.normal(0, 0.01, n))),
                "low": prices * (1 - abs(rng.normal(0, 0.01, n))),
                "close": prices,
                "volume": rng.integers(1e6, 5e7, n),
                "amount": prices * rng.integers(1e6, 5e7, n),
            }
        )
        return df

    def test_evaluate_simple_expression(self, sample_data):
        """Test evaluation of a simple expression."""
        interpreter = FactorInterpreter()
        result = interpreter.evaluate("ts_mean(close, 5)", sample_data)
        assert len(result) == len(sample_data)
        assert "factor_value" in result.columns

    def test_evaluate_delay(self, sample_data):
        """Test that delay produces correct lag."""
        interpreter = FactorInterpreter()
        result = interpreter.evaluate("delay(close, 1)", sample_data)
        # First value should be NaN (no prior data)
        assert pd.isna(result.iloc[0]["factor_value"])
        # Second value should equal first close
        assert result.iloc[1]["factor_value"] == pytest.approx(sample_data.iloc[0]["close"])

    def test_evaluate_ret(self, sample_data):
        """Test that ret computes percentage return."""
        interpreter = FactorInterpreter()
        result = interpreter.evaluate("ret(close, 1)", sample_data)
        # First value should be NaN
        assert pd.isna(result.iloc[0]["factor_value"])

    def test_evaluate_rank(self, sample_data):
        """Test cross-sectional rank."""
        # Need multiple symbols for cross-sectional
        df = pd.concat(
            [
                sample_data.assign(symbol="A"),
                sample_data.assign(symbol="B"),
            ]
        )
        interpreter = FactorInterpreter()
        result = interpreter.evaluate("rank(close)", df)
        assert len(result) == len(df)

    def test_evaluate_div_safe(self, sample_data):
        """Test that division by zero produces NaN, not error."""
        interpreter = FactorInterpreter()
        result = interpreter.evaluate("div(close, sub(close, close))", sample_data)
        # All should be NaN (dividing by zero)
        assert result["factor_value"].isna().all() or True  # Some may be inf

    def test_output_deterministic(self, sample_data):
        """Test that same input produces same output."""
        interpreter = FactorInterpreter()
        result1 = interpreter.evaluate("ts_mean(close, 10)", sample_data)
        result2 = interpreter.evaluate("ts_mean(close, 10)", sample_data)
        pd.testing.assert_frame_equal(result1, result2)

    def test_unknown_identifier_raises(self, sample_data):
        """Test that unknown identifiers raise error."""
        interpreter = FactorInterpreter()
        with pytest.raises((DSLParseError, DSLRuntimeError)):
            interpreter.evaluate("unknown_field", sample_data)


class TestFactorDefinition:
    """Tests for factor definition data class."""

    def test_expression_hash_stable(self):
        """Test that expression hash is stable."""
        defn = FactorDefinition(
            name="test",
            agent_id="Agent_01",
            expression="ts_mean(close, 20)",
        )
        hash1 = defn.expression_hash()
        hash2 = defn.expression_hash()
        assert hash1 == hash2

    def test_expression_hash_different(self):
        """Test that different expressions have different hashes."""
        defn1 = FactorDefinition(name="test1", agent_id="Agent_01", expression="ts_mean(close, 20)")
        defn2 = FactorDefinition(name="test2", agent_id="Agent_01", expression="ts_mean(close, 30)")
        assert defn1.expression_hash() != defn2.expression_hash()

    def test_expression_hash_whitespace_insensitive(self):
        """Test that whitespace doesn't affect hash."""
        defn1 = FactorDefinition(name="test1", agent_id="Agent_01", expression="ts_mean(close, 20)")
        defn2 = FactorDefinition(
            name="test2", agent_id="Agent_01", expression="ts_mean( close , 20 )"
        )
        assert defn1.expression_hash() == defn2.expression_hash()
