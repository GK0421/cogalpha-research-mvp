"""Factor registry - manages factor definitions and metadata."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from cogalpha_mvp.factors.dsl import FactorDefinition, FactorInterpreter

logger = logging.getLogger("cogalpha_mvp")


@dataclass
class FactorMetadata:
    """Complete metadata for a registered factor.

    Attributes:
        factor_id: Unique identifier.
        name: Human-readable name.
        agent_id: Owning agent ID.
        level: Agent hierarchy level (1-7).
        expression: DSL expression string.
        direction: +1 or -1.
        description: Economic rationale.
        parameters: Parameter dictionary.
        source: Origin ("seed", "llm", "mutation", "crossover").
        created_at: Creation timestamp.
        expression_hash: SHA256 of normalized expression.
        review_status: "pending", "passed", "rejected".
        train_metrics: Training period metrics.
        oos_metrics: OOS period metrics.
        rejection_reason: Reason if rejected.
    """

    factor_id: str
    name: str
    agent_id: str
    level: int
    expression: str
    direction: int = 1
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    source: str = "seed"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expression_hash: str = ""
    review_status: str = "pending"
    train_metrics: dict[str, float] = field(default_factory=dict)
    oos_metrics: dict[str, float] = field(default_factory=dict)
    rejection_reason: str = ""

    def __post_init__(self):
        if not self.expression_hash:
            defn = FactorDefinition(
                name=self.name,
                agent_id=self.agent_id,
                expression=self.expression,
                direction=self.direction,
                description=self.description,
                parameters=self.parameters,
                source=self.source,
            )
            self.expression_hash = defn.expression_hash()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "factor_id": self.factor_id,
            "name": self.name,
            "agent_id": self.agent_id,
            "level": self.level,
            "expression": self.expression,
            "direction": self.direction,
            "description": self.description,
            "parameters": self.parameters,
            "source": self.source,
            "created_at": self.created_at,
            "expression_hash": self.expression_hash,
            "review_status": self.review_status,
            "train_metrics": self.train_metrics,
            "oos_metrics": self.oos_metrics,
            "rejection_reason": self.rejection_reason,
        }


class FactorRegistry:
    """Registry for managing factor definitions.

    Supports:
    - Registration of new factors
    - Structural deduplication (by expression hash)
    - Factor lookup by ID
    - Batch evaluation
    """

    def __init__(self):
        self._factors: dict[str, FactorMetadata] = {}
        self._hash_index: dict[str, str] = {}  # expression_hash -> factor_id
        self._interpreter = FactorInterpreter()

    def register(self, metadata: FactorMetadata) -> bool:
        """Register a new factor.

        Returns:
            True if registered, False if duplicate (same expression hash).
        """
        if metadata.expression_hash in self._hash_index:
            existing_id = self._hash_index[metadata.expression_hash]
            logger.info(
                "Factor '%s' is a structural duplicate of '%s' (hash=%s)",
                metadata.name,
                existing_id,
                metadata.expression_hash[:16],
            )
            return False

        self._factors[metadata.factor_id] = metadata
        self._hash_index[metadata.expression_hash] = metadata.factor_id
        logger.info(
            "Registered factor '%s' (id=%s, agent=%s, level=%d)",
            metadata.name,
            metadata.factor_id,
            metadata.agent_id,
            metadata.level,
        )
        return True

    def get(self, factor_id: str) -> FactorMetadata | None:
        """Get a factor by ID."""
        return self._factors.get(factor_id)

    def all_factors(self) -> list[FactorMetadata]:
        """Get all registered factors."""
        return list(self._factors.values())

    def passed_factors(self) -> list[FactorMetadata]:
        """Get factors that passed quality checks."""
        return [f for f in self._factors.values() if f.review_status == "passed"]

    def evaluate_factor(
        self,
        factor_id: str,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Evaluate a single factor against market data.

        Args:
            factor_id: Factor to evaluate.
            data: Market data DataFrame.

        Returns:
            DataFrame with [symbol, trade_date, factor_value].
        """
        factor = self._factors[factor_id]
        result = self._interpreter.evaluate(factor.expression, data)
        # Apply direction
        result["factor_value"] = result["factor_value"] * factor.direction
        return result

    def evaluate_all(self, data: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Evaluate all registered factors.

        Returns:
            Dictionary mapping factor_id to result DataFrame.
        """
        results = {}
        for factor_id in self._factors:
            try:
                results[factor_id] = self.evaluate_factor(factor_id, data)
            except Exception as e:
                logger.error("Failed to evaluate factor %s: %s", factor_id, e)
        return results

    @property
    def count(self) -> int:
        """Number of registered factors."""
        return len(self._factors)

    def filter_by_level(self, level: int) -> list[FactorMetadata]:
        """Get all factors at a given level."""
        return [f for f in self._factors.values() if f.level == level]

    def clear(self) -> None:
        """Remove all factors from the registry."""
        self._factors.clear()
        self._hash_index.clear()

    def structural_dedup(self) -> list[str]:
        """Remove structurally duplicate factors.

        Returns:
            List of removed factor IDs.
        """
        seen_hashes: dict[str, str] = {}
        removed: list[str] = []

        for factor_id, factor in list(self._factors.items()):
            if factor.expression_hash in seen_hashes:
                removed.append(factor_id)
                del self._factors[factor_id]
            else:
                seen_hashes[factor.expression_hash] = factor_id

        logger.info("Structural dedup removed %d duplicates", len(removed))
        return removed
