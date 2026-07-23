"""Factor deduplication - structural and numerical."""

from __future__ import annotations

import logging

import pandas as pd

from cogalpha_mvp.config import DedupConfig
from cogalpha_mvp.factors.registry import FactorMetadata

logger = logging.getLogger("cogalpha_mvp")


class FactorDeduplicator:
    """Removes duplicate factors using two layers:

    1. Structural dedup: Based on expression hash (AST/parse tree).
    2. Numerical dedup: Based on factor value correlation.

    Does NOT use OOS performance for dedup decisions.
    """

    def __init__(self, config: DedupConfig):
        self.config = config

    def structural_dedup(
        self,
        factors: list[FactorMetadata],
    ) -> tuple[list[FactorMetadata], list[str]]:
        """Remove structurally duplicate factors.

        Args:
            factors: List of factor metadata.

        Returns:
            Tuple of (unique_factors, removed_factor_ids).
        """
        seen_hashes: dict[str, str] = {}
        unique: list[FactorMetadata] = []
        removed: list[str] = []

        for factor in factors:
            if factor.expression_hash in seen_hashes:
                removed.append(factor.factor_id)
                logger.info(
                    "Structural dedup: removing %s (duplicate of %s)",
                    factor.factor_id,
                    seen_hashes[factor.expression_hash],
                )
            else:
                seen_hashes[factor.expression_hash] = factor.factor_id
                unique.append(factor)

        return unique, removed

    def numerical_dedup(
        self,
        factors: list[FactorMetadata],
        factor_values: dict[str, pd.DataFrame],
        composite_scores: dict[str, float],
        coverage: dict[str, float] | None = None,
        turnover: dict[str, float] | None = None,
    ) -> tuple[list[FactorMetadata], list[str]]:
        """Remove numerically correlated factors.

        For each cluster of highly correlated factors, keep the one with:
        1. Highest composite score
        2. Lower expression complexity
        3. Higher coverage
        4. Lower turnover

        Args:
            factors: List of factor metadata.
            factor_values: Dictionary mapping factor_id to factor value DataFrame.
            composite_scores: Dictionary mapping factor_id to composite score.
            coverage: Optional coverage dict.
            turnover: Optional turnover dict.

        Returns:
            Tuple of (deduplicated_factors, removed_factor_ids).
        """
        if coverage is None:
            coverage = {}
        if turnover is None:
            turnover = {}

        # Build factor value matrix
        # Pivot each factor's values to [date x symbol]
        factor_series: dict[str, pd.Series] = {}
        for fid in [f.factor_id for f in factors]:
            if fid not in factor_values:
                continue
            df = factor_values[fid]
            if df.empty:
                continue
            # Average across symbols per date
            series = df.groupby("trade_date")["factor_value"].mean()
            factor_series[fid] = series

        if len(factor_series) < 2:
            return factors, []

        # Build correlation matrix
        series_df = pd.DataFrame(factor_series)
        corr_matrix = series_df.corr()

        # Cluster correlated factors
        threshold = self.config.absolute_correlation_threshold
        removed: set[str] = set()
        factor_ids = [f.factor_id for f in factors]

        for i, fid_i in enumerate(factor_ids):
            if fid_i in removed or fid_i not in corr_matrix.columns:
                continue

            # Find correlated cluster
            cluster = [fid_i]
            for j in range(i + 1, len(factor_ids)):
                fid_j = factor_ids[j]
                if fid_j in removed or fid_j not in corr_matrix.columns:
                    continue

                corr = corr_matrix.loc[fid_i, fid_j]
                if pd.notna(corr) and abs(corr) >= threshold:
                    cluster.append(fid_j)

            if len(cluster) > 1:
                # Keep the best factor in the cluster
                best = self._select_best(cluster, factors, composite_scores, coverage, turnover)
                for fid in cluster:
                    if fid != best:
                        removed.add(fid)
                        logger.info(
                            "Numerical dedup: removing %s (correlated with %s, keeping %s)",
                            fid,
                            best,
                            best,
                        )

        unique = [f for f in factors if f.factor_id not in removed]
        return unique, list(removed)

    def _select_best(
        self,
        cluster: list[str],
        factors: list[FactorMetadata],
        scores: dict[str, float],
        coverage: dict[str, float],
        turnover: dict[str, float],
    ) -> str:
        """Select the best factor from a correlated cluster.

        Priority:
        1. Highest composite score
        2. Lower expression complexity
        3. Higher coverage
        4. Lower turnover
        """
        factor_map = {f.factor_id: f for f in factors}

        def sort_key(fid: str) -> tuple:
            f = factor_map.get(fid)
            score = scores.get(fid, 0.0)
            complexity = len(f.expression) if f else 999
            cov = coverage.get(fid, 0.0)
            turn = turnover.get(fid, 1.0)
            # Higher score is better, lower complexity is better,
            # higher coverage is better, lower turnover is better
            return (-score, complexity, -cov, turn)

        return min(cluster, key=sort_key)

    def dedup(
        self,
        factors: list[FactorMetadata],
        factor_values: dict[str, pd.DataFrame] | None = None,
        composite_scores: dict[str, float] | None = None,
        coverage: dict[str, float] | None = None,
        turnover: dict[str, float] | None = None,
    ) -> tuple[list[FactorMetadata], list[str]]:
        """Run both structural and numerical deduplication.

        Args:
            factors: List of factor metadata.
            factor_values: Optional factor values for numerical dedup.
            composite_scores: Optional scores for numerical dedup.
            coverage: Optional coverage dict.
            turnover: Optional turnover dict.

        Returns:
            Tuple of (deduplicated_factors, all_removed_ids).
        """
        all_removed: list[str] = []

        # Structural dedup first
        if self.config.structural_dedup:
            factors, removed = self.structural_dedup(factors)
            all_removed.extend(removed)

        # Numerical dedup second
        if self.config.numerical_dedup and factor_values and composite_scores:
            factors, removed = self.numerical_dedup(
                factors, factor_values, composite_scores, coverage, turnover
            )
            all_removed.extend(removed)

        logger.info(
            "Dedup complete: %d factors remaining, %d removed", len(factors), len(all_removed)
        )
        return factors, all_removed
