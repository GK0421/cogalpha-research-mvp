"""Tests for factor scorer."""

import numpy as np

from cogalpha_mvp.config import FactorConfig
from cogalpha_mvp.evaluation.metrics import FactorMetrics
from cogalpha_mvp.evaluation.scorer import FactorScorer


def make_metrics(
    factor_id: str = "test",
    ic_mean: float = 0.01,
    icir: float = 0.1,
    rankic_mean: float = 0.01,
    rankicir: float = 0.1,
    positive_ic_ratio: float = 0.55,
    coverage: float = 0.95,
    turnover: float = 0.3,
    n_valid_dates: int = 200,
) -> FactorMetrics:
    """Create a FactorMetrics instance with the actual field names."""
    return FactorMetrics(
        factor_id=factor_id,
        ic_mean=ic_mean,
        ic_std=abs(icir) if icir != 0 else 0.01,
        icir=icir,
        rankic_mean=rankic_mean,
        rankic_std=abs(rankicir) if rankicir != 0 else 0.01,
        rankicir=rankicir,
        n_valid_dates=n_valid_dates,
        positive_ic_ratio=positive_ic_ratio,
        coverage=coverage,
        turnover=turnover,
    )


class TestFactorScorer:
    """Tests for factor scoring and classification."""

    def test_elite_factor(self):
        """Test that a strong factor is classified as elite or qualified."""
        scorer = FactorScorer(FactorConfig())
        good = make_metrics(
            factor_id="elite", ic_mean=0.02, icir=0.2, rankic_mean=0.02, rankicir=0.2
        )
        # Include a weaker factor so percentile ranking works
        weak = make_metrics(
            factor_id="weak", ic_mean=0.001, icir=0.01, rankic_mean=0.001, rankicir=0.01
        )
        all_metrics = [good, weak]
        score = scorer.compute_composite_score(good, all_metrics)
        classification = scorer.classify(good, score)
        assert classification in ("elite", "qualified"), (
            f"Expected elite/qualified, got {classification} (score={score})"
        )
        assert score > 0

    def test_rejected_factor(self):
        """Test that a poor factor is rejected."""
        scorer = FactorScorer(FactorConfig())
        good = make_metrics(
            factor_id="good", ic_mean=0.02, icir=0.2, rankic_mean=0.02, rankicir=0.2
        )
        bad = make_metrics(
            factor_id="reject",
            ic_mean=0.0001,
            icir=0.001,
            rankic_mean=0.0001,
            rankicir=0.001,
            positive_ic_ratio=0.5,
            turnover=0.9,
        )
        all_metrics = [good, bad]
        score = scorer.compute_composite_score(bad, all_metrics)
        classification = scorer.classify(bad, score)
        assert classification == "rejected"

    def test_composite_score_ordering(self):
        """Test that better metrics produce higher scores."""
        scorer = FactorScorer(FactorConfig())
        good = make_metrics(
            factor_id="good", ic_mean=0.02, icir=0.2, rankic_mean=0.02, rankicir=0.2
        )
        bad = make_metrics(
            factor_id="bad", ic_mean=0.001, icir=0.01, rankic_mean=0.001, rankicir=0.01
        )
        all_metrics = [good, bad]
        good_score = scorer.compute_composite_score(good, all_metrics)
        bad_score = scorer.compute_composite_score(bad, all_metrics)
        assert good_score > bad_score

    def test_score_in_range(self):
        """Test that composite score is in [0, 1]."""
        scorer = FactorScorer(FactorConfig())
        rng = np.random.default_rng(42)
        metrics_list = []
        for i in range(10):
            m = make_metrics(
                factor_id=f"rand_{i}",
                ic_mean=rng.normal(0, 0.02),
                icir=rng.normal(0, 0.1),
                rankic_mean=rng.normal(0, 0.02),
                rankicir=rng.normal(0, 0.1),
            )
            metrics_list.append(m)

        for m in metrics_list:
            score = scorer.compute_composite_score(m, metrics_list)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for {m.factor_id}"
