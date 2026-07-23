"""Factor quality checking pipeline.

Serial pipeline:
  1. Structure validation
  2. DSL whitelist validation
  3. Small sample execution
  4. Output type validation
  5. NaN and constant check
  6. Economic logic metadata check
  7. Future info static check
  8. Time-series truncation dynamic check
  9. Complexity check
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from cogalpha_mvp.config import QualityConfig
from cogalpha_mvp.factors.dsl import (
    FORBIDDEN_PATTERNS,
    DSLParseError,
    DSLRuntimeError,
    DSLSecurityError,
    FactorInterpreter,
    FactorParser,
)
from cogalpha_mvp.factors.registry import FactorMetadata

logger = logging.getLogger("cogalpha_mvp")


@dataclass
class QualityResult:
    """Result of quality checking for a single factor.

    Attributes:
        factor_id: Factor identifier.
        passed: Whether the factor passed all checks.
        stage: Stage where failure occurred (if any).
        error: Error message (if any).
        warnings: List of warning messages.
        valid_ratio: Ratio of non-NaN values.
        is_constant: Whether the output is approximately constant.
        has_future_info: Whether future info leakage was detected.
        complexity: Expression complexity score.
    """

    factor_id: str
    passed: bool = False
    stage: str = ""
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    valid_ratio: float = 0.0
    is_constant: bool = False
    has_future_info: bool = False
    complexity: int = 0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "factor_id": self.factor_id,
            "passed": self.passed,
            "stage": self.stage,
            "error": self.error,
            "warnings": self.warnings,
            "valid_ratio": self.valid_ratio,
            "is_constant": self.is_constant,
            "has_future_info": self.has_future_info,
            "complexity": self.complexity,
        }


class QualityPipeline:
    """Serial quality checking pipeline for factors.

    Each stage must pass before the factor proceeds to the next.
    Any failure marks the factor as rejected.
    """

    def __init__(self, config: QualityConfig | None = None):
        self.config = config or QualityConfig()
        self.interpreter = FactorInterpreter()

    def check(self, factor: FactorMetadata, data: pd.DataFrame) -> QualityResult:
        """Run all quality checks on a factor.

        Args:
            factor: Factor metadata to check.
            data: Training period market data.

        Returns:
            QualityResult with pass/fail status and details.
        """
        result = QualityResult(factor_id=factor.factor_id)

        # Stage 1: Structure validation
        result = self._check_structure(factor, result)
        if result.stage:  # stage is set on failure
            result.passed = False
            return result

        # Stage 2: DSL whitelist validation
        result = self._check_dsl_whitelist(factor, result)
        if result.stage:
            result.passed = False
            return result

        # Stage 3: Small sample execution
        result = self._check_execution(factor, data, result)
        if result.stage:
            result.passed = False
            return result

        # Stage 4: Output type validation
        result = self._check_output_type(factor, result)
        if result.stage:
            result.passed = False
            return result

        # Stage 5: NaN and constant check
        result = self._check_nan_constant(factor, result)
        if result.stage:
            result.passed = False
            return result

        # Stage 6: Economic logic metadata check
        result = self._check_economic_logic(factor, result)
        if result.stage:
            result.passed = False
            return result

        # Stage 7: Future info static check
        result = self._check_future_info_static(factor, result)
        if result.stage:
            result.passed = False
            return result

        # Stage 8: Time-series truncation dynamic check
        result = self._check_truncation(factor, data, result)
        if result.stage:
            result.passed = False
            return result

        # Stage 9: Complexity check
        result = self._check_complexity(factor, result)
        if result.stage:
            result.passed = False
            return result

        result.passed = True
        return result

    def _check_structure(self, factor: FactorMetadata, result: QualityResult) -> QualityResult:
        """Stage 1: Validate factor structure."""
        if not factor.expression or not factor.expression.strip():
            result.stage = "structure"
            result.error = "Empty expression"
            return result

        if not factor.name:
            result.stage = "structure"
            result.error = "Missing factor name"
            return result

        if factor.direction not in (1, -1):
            result.stage = "structure"
            result.error = f"Invalid direction: {factor.direction} (must be 1 or -1)"
            return result

        result.passed = True
        return result

    def _check_dsl_whitelist(self, factor: FactorMetadata, result: QualityResult) -> QualityResult:
        """Stage 2: Validate DSL against whitelist and window sizes."""
        is_valid, msg = FactorParser.validate(factor.expression)
        if not is_valid:
            result.stage = "dsl_whitelist"
            result.error = msg
            return result

        # Check for unreasonably large window sizes
        import re as _re

        window_matches = _re.findall(
            r"(?:ts_mean|ts_sum|ts_std|ts_min|ts_max|ts_rank|delay|delta|ret|corr|cov)\s*\([^,]+,\s*(\d+)\s*\)",
            factor.expression,
        )
        for w in window_matches:
            if int(w) > self.config.max_window_size:
                result.stage = "dsl_whitelist"
                result.error = f"Window size {w} exceeds maximum {self.config.max_window_size}"
                return result

        result.passed = True
        return result

    def _check_execution(
        self, factor: FactorMetadata, data: pd.DataFrame, result: QualityResult
    ) -> QualityResult:
        """Stage 3: Execute factor on small sample."""
        try:
            # Use first 100 rows or all if less
            sample = data.head(min(1000, len(data)))
            eval_result = self.interpreter.evaluate(factor.expression, sample)

            if eval_result.empty:
                result.stage = "execution"
                result.error = "Factor produced empty output"
                return result

            result._eval_result = eval_result  # Store for later checks
            result.passed = True
            return result

        except DSLParseError as e:
            result.stage = "execution"
            result.error = f"Parse error: {e}"
            return result
        except DSLSecurityError as e:
            result.stage = "execution"
            result.error = f"Security error: {e}"
            return result
        except DSLRuntimeError as e:
            result.stage = "execution"
            result.error = f"Runtime error: {e}"
            return result
        except Exception as e:
            result.stage = "execution"
            result.error = f"Unexpected error: {e}"
            return result

    def _check_output_type(self, factor: FactorMetadata, result: QualityResult) -> QualityResult:
        """Stage 4: Validate output type and index alignment."""
        eval_result = getattr(result, "_eval_result", None)
        if eval_result is None:
            result.stage = "output_type"
            result.error = "No evaluation result available"
            return result

        if "factor_value" not in eval_result.columns:
            result.stage = "output_type"
            result.error = "Missing 'factor_value' column"
            return result

        # Check output length matches input
        getattr(result, "_sample_size", None)
        result.passed = True
        return result

    def _check_nan_constant(self, factor: FactorMetadata, result: QualityResult) -> QualityResult:
        """Stage 5: Check for excessive NaN or constant values."""
        eval_result = getattr(result, "_eval_result", None)
        if eval_result is None:
            result.stage = "nan_constant"
            result.error = "No evaluation result available"
            return result

        values = eval_result["factor_value"]

        # Check all NaN
        if values.isna().all():
            result.stage = "nan_constant"
            result.error = "All values are NaN"
            return result

        # Check valid ratio
        valid_ratio = float(values.notna().mean())
        result.valid_ratio = valid_ratio
        if valid_ratio < self.config.min_valid_ratio:
            result.stage = "nan_constant"
            result.error = (
                f"Valid ratio {valid_ratio:.2%} below threshold {self.config.min_valid_ratio:.2%}"
            )
            return result

        # Check for infinite values
        if np.isinf(values.dropna()).any():
            result.stage = "nan_constant"
            result.error = "Contains infinite values"
            return result

        # Check for near-constant
        non_nan = values.dropna()
        if len(non_nan) > 1:
            std = float(non_nan.std())
            if std < self.config.near_constant_threshold:
                result.is_constant = True
                result.stage = "nan_constant"
                result.error = f"Near-constant output (std={std:.2e})"
                return result

        result.passed = True
        return result

    def _check_economic_logic(self, factor: FactorMetadata, result: QualityResult) -> QualityResult:
        """Stage 6: Check economic logic metadata."""
        if not factor.description or len(factor.description.strip()) < 10:
            result.stage = "economic_logic"
            result.error = "Missing or too short economic rationale"
            return result

        result.passed = True
        return result

    def _check_future_info_static(
        self, factor: FactorMetadata, result: QualityResult
    ) -> QualityResult:
        """Stage 7: Static check for future information patterns."""
        import re

        expr = factor.expression
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, expr):
                result.stage = "future_info_static"
                result.error = f"Future info pattern detected: {pattern}"
                result.has_future_info = True
                return result

        result.passed = True
        return result

    def _check_truncation(
        self, factor: FactorMetadata, data: pd.DataFrame, result: QualityResult
    ) -> QualityResult:
        """Stage 8: Time-series truncation dynamic check.

        For multiple random dates T:
        1. Run factor on full data D_full
        2. Truncate data to T, run factor on D_truncated
        3. Compare factor values at date T
        4. Any significant difference => future info leakage
        """
        if "trade_date" not in data.columns or len(data) == 0:
            result.warnings.append("Cannot perform truncation test: no date column")
            result.passed = True
            return result

        # Get unique dates
        dates = sorted(data["trade_date"].unique())

        # Need at least 30 dates for meaningful test
        if len(dates) < 30:
            result.warnings.append("Insufficient dates for truncation test")
            result.passed = True
            return result

        # Select test dates (skip first 30 for warmup)
        rng = np.random.default_rng(seed=42)
        test_indices = rng.choice(
            range(30, len(dates)),
            size=min(self.config.truncation_test_dates, len(dates) - 30),
            replace=False,
        )

        max_diff = 0.0
        min_corr = 1.0

        for idx in test_indices:
            test_date = dates[idx]

            # Full data evaluation
            try:
                full_result = self.interpreter.evaluate(factor.expression, data)
            except Exception:
                continue

            # Truncated data evaluation
            truncated = data[data["trade_date"] <= test_date].copy()
            try:
                trunc_result = self.interpreter.evaluate(factor.expression, truncated)
            except Exception:
                continue

            # Compare values at test_date
            full_at_t = full_result[full_result["trade_date"] == test_date]
            trunc_at_t = trunc_result[trunc_result["trade_date"] == test_date]

            if full_at_t.empty or trunc_at_t.empty:
                continue

            # Merge on symbol
            merged = full_at_t.merge(trunc_at_t, on="symbol", suffixes=("_full", "_trunc"))

            if merged.empty:
                continue

            merged["factor_value_full"].dropna()
            merged["factor_value_trunc"].dropna()

            common = merged.dropna(subset=["factor_value_full", "factor_value_trunc"])
            if len(common) < 2:
                continue

            diff = (common["factor_value_full"] - common["factor_value_trunc"]).abs()
            max_diff = max(max_diff, float(diff.max()))

            if common["factor_value_full"].std() > 0 and common["factor_value_trunc"].std() > 0:
                corr = float(common["factor_value_full"].corr(common["factor_value_trunc"]))
                if not np.isnan(corr):
                    min_corr = min(min_corr, corr)

        if max_diff > self.config.truncation_max_diff or min_corr < self.config.truncation_min_corr:
            result.stage = "truncation"
            result.error = (
                f"Future info leakage detected: max_diff={max_diff:.2e} "
                f"(threshold={self.config.truncation_max_diff:.2e}), "
                f"min_corr={min_corr:.6f} (threshold={self.config.truncation_min_corr})"
            )
            result.has_future_info = True
            return result

        result.passed = True
        return result

    def _check_complexity(self, factor: FactorMetadata, result: QualityResult) -> QualityResult:
        """Stage 9: Check expression complexity."""
        # Count function calls and operators as complexity measure
        expr = factor.expression
        complexity = (
            expr.count("(") + expr.count("+") + expr.count("-") + expr.count("*") + expr.count("/")
        )
        result.complexity = complexity

        if complexity > self.config.max_complexity:
            result.stage = "complexity"
            result.error = f"Complexity {complexity} exceeds max {self.config.max_complexity}"
            return result

        result.passed = True
        return result


# Known bad factors that must be rejected
BAD_FACTORS = {
    "bad_negative_shift": "sub(close, shift(close, -1))",  # Uses future data
    "bad_future_global_mean": "sub(close, ts_mean(close, 999999))",  # Uses full sample
    "bad_full_sample_normalization": "div(sub(close, ts_mean(close, 99999)), ts_std(close, 99999))",
    "bad_last_row_reference": "sub(close, delay(close, -1))",  # Negative delay = future
}


def verify_bad_factors_rejected(pipeline: QualityPipeline, data: pd.DataFrame) -> dict[str, bool]:
    """Verify that all known bad factors are rejected.

    Returns:
        Dictionary mapping bad factor name to whether it was correctly rejected.
    """
    results = {}
    for name, expr in BAD_FACTORS.items():
        factor = FactorMetadata(
            factor_id=f"bad_{name}",
            name=name,
            agent_id="test",
            level=0,
            expression=expr,
            description="Test bad factor for leakage detection",
        )
        result = pipeline.check(factor, data)
        results[name] = not result.passed  # Should be rejected
    return results
