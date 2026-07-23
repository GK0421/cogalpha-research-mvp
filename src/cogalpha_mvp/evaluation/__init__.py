"""Evaluation layer - IC, RankIC, factor scoring, and deduplication."""

from cogalpha_mvp.evaluation.dedup import FactorDeduplicator
from cogalpha_mvp.evaluation.metrics import (
    FactorMetrics,
    compute_all_metrics,
    compute_ic,
    compute_icir,
    compute_rank_ic,
    compute_rank_icir,
)
from cogalpha_mvp.evaluation.scorer import FactorScorer

__all__ = [
    "FactorDeduplicator",
    "FactorMetrics",
    "FactorScorer",
    "compute_all_metrics",
    "compute_ic",
    "compute_icir",
    "compute_rank_ic",
    "compute_rank_icir",
]
