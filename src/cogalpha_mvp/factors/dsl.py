"""Factor DSL - Safe expression parser and interpreter.

NO exec(), eval(), or compile() is used. The DSL is parsed into
an AST and interpreted by a custom tree-walking interpreter.

Supported operators (whitelist):
  open, high, low, close, volume, amount,
  delay, delta, ret, ts_mean, ts_sum, ts_std, ts_min, ts_max,
  ts_rank, corr, cov, rank, zscore, winsorize,
  abs, sign, log1p, sqrt, clip,
  add, sub, mul, div, min, max, where

Forbidden:
  shift (negative), lead, future, tail (future endpoint),
  iloc[-1], file access, network access, system calls,
  dynamic imports, reflection, arbitrary attribute chains
"""

from __future__ import annotations

import ast
import hashlib
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

import numpy as np
import pandas as pd

logger = logging.getLogger("cogalpha_mvp")

# Whitelist of allowed DSL function names
DSL_FUNCTIONS = {
    "delay",
    "delta",
    "ret",
    "ts_mean",
    "ts_sum",
    "ts_std",
    "ts_min",
    "ts_max",
    "ts_rank",
    "corr",
    "cov",
    "rank",
    "zscore",
    "winsorize",
    "abs",
    "sign",
    "log1p",
    "sqrt",
    "clip",
    "add",
    "sub",
    "mul",
    "div",
    "min",
    "max",
    "where",
}

# Whitelist of allowed data field names
DSL_FIELDS = {"open", "high", "low", "close", "volume", "amount"}

# Forbidden patterns (checked at parse time)
FORBIDDEN_PATTERNS = [
    r"\.shift\s*\(\s*-\d",  # negative shift
    r"\.lead\s*\(",
    r"\.future\s*\(",
    r"\.tail\s*\(",
    r"iloc\s*\[\s*-\d*\s*\]",
    r"__import__",
    r"exec\s*\(",
    r"eval\s*\(",
    r"compile\s*\(",
    r"subprocess",
    r"os\.system",
    r"open\s*\(",
    r"import\s+",
    r"getattr\s*\(",
    r"setattr\s*\(",
]


class DSLParseError(Exception):
    """Raised when DSL expression cannot be parsed."""


class DSLSecurityError(Exception):
    """Raised when DSL expression contains forbidden patterns."""


class DSLRuntimeError(Exception):
    """Raised when DSL expression fails during evaluation."""


@dataclass
class FactorDefinition:
    """A factor definition in structured DSL format.

    Attributes:
        name: Human-readable factor name.
        agent_id: Owning agent ID (e.g., "Agent_01").
        expression: DSL expression string.
        direction: +1 or -1, indicating expected factor direction.
        description: Economic rationale description.
        parameters: Dictionary of parameter values.
        source: "seed" or "llm" or "mutation" or "crossover".
    """

    name: str
    agent_id: str
    expression: str
    direction: int = 1
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    source: str = "seed"

    def expression_hash(self) -> str:
        """Compute SHA256 hash of the normalized expression."""
        normalized = re.sub(r"\s+", "", self.expression.lower())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "expression": self.expression,
            "direction": self.direction,
            "description": self.description,
            "parameters": self.parameters,
            "source": self.source,
            "expression_hash": self.expression_hash(),
        }


class FactorParser:
    """Parses DSL expressions into Python AST for validation.

    Does NOT use eval(). Uses ast.parse() to validate syntax
    and check for security violations.
    """

    @staticmethod
    def validate(expression: str) -> tuple[bool, str]:
        """Validate a DSL expression.

        Args:
            expression: DSL expression string.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not expression or not expression.strip():
            return False, "Empty expression"

        # Check for forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, expression):
                return False, f"Forbidden pattern detected: {pattern}"

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        # Walk the AST to validate nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    if func.id not in DSL_FUNCTIONS and func.id not in DSL_FIELDS:
                        return False, f"Unknown function: {func.id}"
                elif isinstance(func, ast.Attribute):
                    return False, f"Attribute access not allowed: {ast.dump(func)}"

            elif isinstance(node, ast.Name):
                if (
                    node.id not in DSL_FUNCTIONS
                    and node.id not in DSL_FIELDS
                    and node.id not in {"True", "False", "None"}
                ):
                    return False, f"Unknown identifier: {node.id}"

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                return False, "Import statements are forbidden"

            elif isinstance(node, ast.Attribute):
                # Allow attribute access for method calls only if whitelisted
                return False, f"Attribute access not allowed: {ast.dump(node)}"

        return True, ""

    @staticmethod
    def parse(expression: str) -> ast.AST:
        """Parse expression and return AST. Raises on error."""
        is_valid, msg = FactorParser.validate(expression)
        if not is_valid:
            raise DSLParseError(msg)
        return ast.parse(expression, mode="eval")


class FactorInterpreter:
    """Interprets validated DSL expressions against market data.

    Implements a tree-walking interpreter for the DSL.
    All operations are cross-sectional (per symbol) time-series operations.
    """

    # Implementation of DSL functions
    @staticmethod
    def _delay(series: pd.Series, n: int) -> pd.Series:
        """Shift series by n periods (lag). n must be positive."""
        if n < 0:
            raise DSLRuntimeError("delay with negative n is forbidden (future info)")
        return series.shift(n)

    @staticmethod
    def _delta(series: pd.Series, n: int = 1) -> pd.Series:
        """Difference: series - delay(series, n)."""
        return series.diff(n)

    @staticmethod
    def _ret(series: pd.Series, n: int = 1) -> pd.Series:
        """Return: (series - delay(series, n)) / delay(series, n)."""
        delayed = series.shift(n)
        return (series - delayed) / (delayed.replace(0, np.nan))

    @staticmethod
    def _ts_mean(series: pd.Series, n: int) -> pd.Series:
        """Rolling mean over n periods."""
        return series.rolling(window=n, min_periods=1).mean()

    @staticmethod
    def _ts_sum(series: pd.Series, n: int) -> pd.Series:
        """Rolling sum over n periods."""
        return series.rolling(window=n, min_periods=1).sum()

    @staticmethod
    def _ts_std(series: pd.Series, n: int) -> pd.Series:
        """Rolling standard deviation over n periods."""
        return series.rolling(window=n, min_periods=1).std()

    @staticmethod
    def _ts_min(series: pd.Series, n: int) -> pd.Series:
        """Rolling minimum over n periods."""
        return series.rolling(window=n, min_periods=1).min()

    @staticmethod
    def _ts_max(series: pd.Series, n: int) -> pd.Series:
        """Rolling maximum over n periods."""
        return series.rolling(window=n, min_periods=1).max()

    @staticmethod
    def _ts_rank(series: pd.Series, n: int) -> pd.Series:
        """Rolling rank (percentile) over n periods."""
        return series.rolling(window=n, min_periods=1).rank(pct=True)

    @staticmethod
    def _corr(s1: pd.Series, s2: pd.Series, n: int) -> pd.Series:
        """Rolling correlation between two series over n periods."""
        return s1.rolling(window=n, min_periods=2).corr(s2)

    @staticmethod
    def _cov(s1: pd.Series, s2: pd.Series, n: int) -> pd.Series:
        """Rolling covariance between two series over n periods."""
        return s1.rolling(window=n, min_periods=2).cov(s2)

    @staticmethod
    def _rank(series: pd.Series) -> pd.Series:
        """Cross-sectional rank (percentile)."""
        return series.rank(pct=True)

    @staticmethod
    def _zscore(series: pd.Series) -> pd.Series:
        """Cross-sectional z-score."""
        std = series.std()
        if std == 0 or pd.isna(std):
            return series * 0
        return (series - series.mean()) / std

    @staticmethod
    def _winsorize(series: pd.Series, n_std: float = 3.0) -> pd.Series:
        """Winsorize at n_std standard deviations."""
        mean = series.mean()
        std = series.std()
        if std == 0 or pd.isna(std):
            return series
        lower = mean - n_std * std
        upper = mean + n_std * std
        return series.clip(lower, upper)

    @staticmethod
    def _abs(series: pd.Series) -> pd.Series:
        return series.abs()

    @staticmethod
    def _sign(series: pd.Series) -> pd.Series:
        return pd.Series(np.sign(series), index=series.index)

    @staticmethod
    def _log1p(series: pd.Series) -> pd.Series:
        return pd.Series(np.log1p(series.abs()) * np.sign(series), index=series.index)

    @staticmethod
    def _sqrt(series: pd.Series) -> pd.Series:
        return pd.Series(np.sqrt(series.abs()) * np.sign(series), index=series.index)

    @staticmethod
    def _clip(series: pd.Series, lower: float, upper: float) -> pd.Series:
        return series.clip(lower, upper)

    @staticmethod
    def _add(a, b):
        return a + b

    @staticmethod
    def _sub(a, b):
        return a - b

    @staticmethod
    def _mul(a, b):
        return a * b

    @staticmethod
    def _div(a, b):
        if hasattr(b, "replace"):
            return a / b.replace(0, np.nan)
        return a / (b if b != 0 else np.nan)

    @staticmethod
    def _min(a, b):
        return pd.Series(np.minimum(a, b), index=getattr(a, "index", None))

    @staticmethod
    def _max(a, b):
        return pd.Series(np.maximum(a, b), index=getattr(a, "index", None))

    @staticmethod
    def _where(cond, a, b):
        return pd.Series(np.where(cond, a, b), index=getattr(cond, "index", None))

    # Map function names to implementations
    _FUNCS: ClassVar[dict[str, Callable]] = {}

    @classmethod
    def _init_funcs(cls) -> None:
        """Initialize function lookup table."""
        cls._FUNCS = {
            "delay": cls._delay,
            "delta": cls._delta,
            "ret": cls._ret,
            "ts_mean": cls._ts_mean,
            "ts_sum": cls._ts_sum,
            "ts_std": cls._ts_std,
            "ts_min": cls._ts_min,
            "ts_max": cls._ts_max,
            "ts_rank": cls._ts_rank,
            "corr": cls._corr,
            "cov": cls._cov,
            "rank": cls._rank,
            "zscore": cls._zscore,
            "winsorize": cls._winsorize,
            "abs": cls._abs,
            "sign": cls._sign,
            "log1p": cls._log1p,
            "sqrt": cls._sqrt,
            "clip": cls._clip,
            "add": cls._add,
            "sub": cls._sub,
            "mul": cls._mul,
            "div": cls._div,
            "min": cls._min,
            "max": cls._max,
            "where": cls._where,
        }

    def __init__(self):
        if not self._FUNCS:
            self._init_funcs()

    def evaluate(
        self,
        expression: str,
        data: pd.DataFrame,
        symbol_col: str = "symbol",
        date_col: str = "trade_date",
    ) -> pd.DataFrame:
        """Evaluate a DSL expression against market data.

        Computes the factor for each symbol independently, producing
        a cross-sectional factor value for each (symbol, date) pair.

        Args:
            expression: Validated DSL expression.
            data: Market data DataFrame with at least OHLCV columns.
            symbol_col: Column name for symbol.
            date_col: Column name for trade date.

        Returns:
            DataFrame with columns [symbol, trade_date, factor_value].
        """
        # Parse expression
        is_valid, msg = FactorParser.validate(expression)
        if not is_valid:
            raise DSLParseError(f"Invalid expression: {msg}")

        tree = ast.parse(expression, mode="eval")

        results = []
        for sym, group in data.groupby(symbol_col):
            group = group.sort_values(date_col).reset_index(drop=True)
            try:
                value = self._eval_node(tree.body, group)
                if isinstance(value, (int, float)):
                    value = pd.Series(value, index=group.index)
                result_df = pd.DataFrame(
                    {
                        symbol_col: group[symbol_col],
                        date_col: group[date_col],
                        "factor_value": value,
                    }
                )
                results.append(result_df)
            except Exception as e:
                logger.warning("Factor evaluation failed for %s: %s", sym, e)
                result_df = pd.DataFrame(
                    {
                        symbol_col: group[symbol_col],
                        date_col: group[date_col],
                        "factor_value": np.nan,
                    }
                )
                results.append(result_df)

        return pd.concat(results, ignore_index=True)

    def _eval_node(self, node: ast.AST, data: pd.DataFrame) -> Any:
        """Recursively evaluate an AST node against data."""
        if isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Name):
            if node.id in DSL_FIELDS:
                if node.id in data.columns:
                    return data[node.id]
                raise DSLRuntimeError(f"Field '{node.id}' not in data columns")
            raise DSLRuntimeError(f"Unknown identifier: {node.id}")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, data)
            right = self._eval_node(node.right, data)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / (right.replace(0, np.nan) if hasattr(right, "replace") else right)
            elif isinstance(node.op, ast.Pow):
                return left**right
            else:
                raise DSLRuntimeError(f"Unsupported binary operator: {type(node.op)}")

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, data)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
            else:
                raise DSLRuntimeError(f"Unsupported unary operator: {type(node.op)}")

        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, data)
            for op, comp in zip(node.ops, node.comparators, strict=False):
                right = self._eval_node(comp, data)
                if isinstance(op, ast.Gt):
                    left = left > right
                elif isinstance(op, ast.Lt):
                    left = left < right
                elif isinstance(op, ast.GtE):
                    left = left >= right
                elif isinstance(op, ast.LtE):
                    left = left <= right
                elif isinstance(op, ast.Eq):
                    left = left == right
                elif isinstance(op, ast.NotEq):
                    left = left != right
                else:
                    raise DSLRuntimeError(f"Unsupported comparison: {type(op)}")
            return left

        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, data) for v in node.values]
            if isinstance(node.op, ast.And):
                result = values[0]
                for v in values[1:]:
                    result = result & v
                return result
            elif isinstance(node.op, ast.Or):
                result = values[0]
                for v in values[1:]:
                    result = result | v
                return result

        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name is None:
                raise DSLRuntimeError("Only named function calls are allowed")

            if func_name not in self._FUNCS:
                raise DSLRuntimeError(f"Unknown function: {func_name}")

            args = [self._eval_node(a, data) for a in node.args]
            func = self._FUNCS[func_name]
            return func(*args)

        else:
            raise DSLRuntimeError(f"Unsupported AST node type: {type(node).__name__}")
