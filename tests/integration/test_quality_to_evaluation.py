"""Integration test: quality pipeline to evaluation."""

from cogalpha_mvp.config import DedupConfig, FactorConfig
from cogalpha_mvp.data.adapters import SyntheticDataAdapter
from cogalpha_mvp.domain.data_contract import DataRequest
from cogalpha_mvp.domain.sample_boundary import SampleBoundary, TrainDataLoader
from cogalpha_mvp.evaluation.dedup import FactorDeduplicator
from cogalpha_mvp.evaluation.metrics import compute_all_metrics
from cogalpha_mvp.evaluation.scorer import FactorScorer
from cogalpha_mvp.factors.dsl import FactorInterpreter
from cogalpha_mvp.factors.seed_factors import get_all_seed_factors
from cogalpha_mvp.quality.pipeline import QualityPipeline


class TestQualityToEvaluationIntegration:
    """Test quality pipeline followed by evaluation and scoring."""

    def test_quality_then_score(self):
        """Test that quality-checked factors are scored correctly."""
        # Setup
        adapter = SyntheticDataAdapter()
        request = DataRequest(start_date="2020-01-01", end_date="2021-12-31")
        raw_data = adapter.load(request)
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2020-12-31",
            oos_start="2021-01-01",
            oos_end="2021-12-31",
        )
        train_data = TrainDataLoader(boundary).load(raw_data)

        quality = QualityPipeline()
        interpreter = FactorInterpreter()
        scorer = FactorScorer(FactorConfig())
        factors = get_all_seed_factors()

        passed_factors = []
        for f in factors:
            qr = quality.check(f, train_data)
            if qr.passed:
                passed_factors.append(f)

        # At least some should pass
        assert len(passed_factors) > 0, "At least some seed factors should pass quality checks"

        # Evaluate and score
        all_metrics = {}
        for f in passed_factors:
            fv = interpreter.evaluate(f.expression, train_data)
            metrics = compute_all_metrics(fv, train_data, f.factor_id)
            all_metrics[f.factor_id] = metrics

        # Score all
        scored = scorer.score_all(all_metrics)
        assert len(scored) == len(passed_factors)

    def test_dedup_after_evaluation(self):
        """Test that dedup removes duplicates after evaluation."""
        dedup = FactorDeduplicator(DedupConfig())
        factors = get_all_seed_factors()

        # Check no structural duplicates among seed factors
        unique, removed = dedup.structural_dedup(factors)
        assert len(unique) == 21, "All 21 seed factors should be structurally unique"
        assert len(removed) == 0
