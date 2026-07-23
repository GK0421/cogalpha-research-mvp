"""Factor scorer - classifies factors as qualified or elite."""

from __future__ import annotations

import logging

import numpy as np

from cogalpha_mvp.config import FactorConfig
from cogalpha_mvp.evaluation.metrics import FactorMetrics

logger = logging.getLogger("cogalpha_mvp")


class FactorScorer:
    """Scores and classifies factors based on evaluation metrics.

    Classification:
    - Qualified: composite_score >= 0.65 AND meets minimum thresholds
    - Elite: composite_score >= 0.80 AND meets stricter thresholds
    - Rejected: otherwise
    """

    def __init__(self, config: FactorConfig):
        self.config = config

    def compute_composite_score(
        self, metrics: FactorMetrics, all_metrics: list[FactorMetrics]
    ) -> float:
        """Compute composite percentile score.

        The score is the average of percentile ranks across
        IC, ICIR, RankIC, RankICIR.

        Args:
            metrics: Metrics for this factor.
            all_metrics: All factors' metrics for percentile computation.

        Returns:
            Composite score in [0, 1].
        """
        if not all_metrics:
            return 0.0

        ics = np.array([m.ic_mean for m in all_metrics])
        icirs = np.array([m.icir for m in all_metrics])
        rankics = np.array([m.rankic_mean for m in all_metrics])
        rankicirs = np.array([m.rankicir for m in all_metrics])

        # Compute percentile ranks
        def pct_rank(arr: np.ndarray, val: float) -> float:
            if len(arr) <= 1:
                return 0.5
            return float((arr < val).sum() / (len(arr) - 1))

        p_ic = pct_rank(ics, metrics.ic_mean)
        p_icir = pct_rank(icirs, metrics.icir)
        p_rankic = pct_rank(rankics, metrics.rankic_mean)
        p_rankicir = pct_rank(rankicirs, metrics.rankicir)

        score = (p_ic + p_icir + p_rankic + p_rankicir) / 4.0
        return float(score)

    def classify(
        self,
        metrics: FactorMetrics,
        composite_score: float,
    ) -> str:
        """Classify a factor as elite, qualified, or rejected.

        Args:
            metrics: Factor metrics.
            composite_score: Composite percentile score.

        Returns:
            "elite", "qualified", or "rejected".
        """
        # Check elite thresholds
        if composite_score >= self.config.elite_score_threshold and (
            metrics.ic_mean >= self.config.min_ic_elite
            and metrics.icir >= self.config.min_icir_elite
            and metrics.rankic_mean >= self.config.min_rankic_elite
            and metrics.rankicir >= self.config.min_rankicir_elite
        ):
            return "elite"

        # Check qualified thresholds
        if composite_score >= self.config.qualified_score_threshold and (
            metrics.ic_mean >= self.config.min_ic_qualified
            and metrics.icir >= self.config.min_icir_qualified
            and metrics.rankic_mean >= self.config.min_rankic_qualified
            and metrics.rankicir >= self.config.min_rankicir_qualified
        ):
            return "qualified"

        return "rejected"

    def score_all(
        self,
        all_metrics: dict[str, FactorMetrics],
    ) -> dict[str, dict]:
        """Score and classify all factors.

        Args:
            all_metrics: Dictionary mapping factor_id to FactorMetrics.

        Returns:
            Dictionary mapping factor_id to classification info:
            {"status": str, "composite_score": float, "metrics": FactorMetrics}
        """
        metrics_list = list(all_metrics.values())

        results: dict[str, dict] = {}
        for factor_id, metrics in all_metrics.items():
            score = self.compute_composite_score(metrics, metrics_list)
            metrics.composite_score = score
            status = self.classify(metrics, score)
            results[factor_id] = {
                "status": status,
                "composite_score": score,
                "metrics": metrics,
            }

        n_elite = sum(1 for r in results.values() if r["status"] == "elite")
        n_qualified = sum(1 for r in results.values() if r["status"] == "qualified")
        n_rejected = sum(1 for r in results.values() if r["status"] == "rejected")

        logger.info(
            "Factor scoring: %d elite, %d qualified, %d rejected (total %d)",
            n_elite,
            n_qualified,
            n_rejected,
            len(results),
        )

        return results
