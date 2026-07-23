"""Integration test: data loading to factor evaluation."""

import pandas as pd

from cogalpha_mvp.data.adapters import SyntheticDataAdapter
from cogalpha_mvp.domain.data_contract import DataRequest, StandardMarketData
from cogalpha_mvp.domain.sample_boundary import (
    OutOfSampleDataLoader,
    SampleBoundary,
    TrainDataLoader,
)
from cogalpha_mvp.evaluation.metrics import compute_all_metrics
from cogalpha_mvp.factors.dsl import FactorInterpreter
from cogalpha_mvp.factors.seed_factors import get_all_seed_factors
from cogalpha_mvp.quality.pipeline import QualityPipeline


class TestDataToFactorIntegration:
    """Test the flow from data loading to factor evaluation."""

    def test_full_flow_single_factor(self):
        """Test loading data, splitting, computing factor, evaluating."""
        # 1. Load synthetic data
        adapter = SyntheticDataAdapter()
        request = DataRequest(start_date="2020-01-01", end_date="2021-12-31")
        raw_data = adapter.load(request)

        # 2. Validate (minor OHLC issues are acceptable as warnings)
        errors = StandardMarketData.validate(raw_data)
        assert len(errors) < len(raw_data) * 0.01, f"Too many validation errors: {len(errors)}"

        # 3. Split train/OOS
        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2020-12-31",
            oos_start="2021-01-01",
            oos_end="2021-12-31",
        )
        boundary.validate()
        train_loader = TrainDataLoader(boundary)
        oos_loader = OutOfSampleDataLoader(boundary)
        train_data = train_loader.load(raw_data)
        oos_data = oos_loader.load(raw_data)

        assert len(train_data) > 0
        assert len(oos_data) > 0
        assert train_data["trade_date"].max() <= pd.Timestamp("2020-12-31")
        assert oos_data["trade_date"].min() >= pd.Timestamp("2021-01-01")

        # 4. Compute a factor on training data
        interpreter = FactorInterpreter()
        factors = get_all_seed_factors()
        factor = factors[0]
        factor_values = interpreter.evaluate(factor.expression, train_data)
        assert len(factor_values) > 0
        assert "factor_value" in factor_values.columns

        # 5. Quality check
        quality = QualityPipeline()
        q_result = quality.check(factor, train_data)
        # At least it should not crash; may pass or fail
        assert q_result is not None

        # 6. Evaluate metrics
        metrics = compute_all_metrics(factor_values, train_data, factor.factor_id)
        assert metrics is not None
        assert metrics.factor_id == factor.factor_id


class TestFactorToReportIntegration:
    """Test the flow from factor evaluation to report data."""

    def test_multiple_factors_evaluation(self):
        """Test evaluating multiple factors."""
        adapter = SyntheticDataAdapter()
        request = DataRequest(start_date="2020-01-01", end_date="2021-12-31")
        raw_data = adapter.load(request)

        boundary = SampleBoundary(
            train_start="2020-01-01",
            train_end="2020-12-31",
            oos_start="2021-01-01",
            oos_end="2021-12-31",
        )
        train_loader = TrainDataLoader(boundary)
        train_data = train_loader.load(raw_data)

        interpreter = FactorInterpreter()
        factors = get_all_seed_factors()

        results = []
        for f in factors[:5]:  # Test first 5
            fv = interpreter.evaluate(f.expression, train_data)
            metrics = compute_all_metrics(fv, train_data, f.factor_id)
            results.append((f, metrics))

        assert len(results) == 5
        for f, m in results:
            assert m.factor_id == f.factor_id
