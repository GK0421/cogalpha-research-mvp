"""Pipeline runner - orchestrates the full research workflow.

Workflow:
  1. Data loading & snapshot
  2. Normalization & validation
  3. Train/OOS isolation
  4. Factor registration & computation
  5. Quality checking
  6. IC/RankIC evaluation
  7. Qualified/elite factor selection
  8. Deduplication
  9. OOS validation
  10. Portfolio backtest
  11. Report generation
"""

from __future__ import annotations

import hashlib
import json
import logging
import platform
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from cogalpha_mvp.config import Config
from cogalpha_mvp.data.adapters import SyntheticDataAdapter, create_snapshot_manifest
from cogalpha_mvp.domain.data_contract import DataRequest, MarketDataAdapter, StandardMarketData
from cogalpha_mvp.domain.sample_boundary import (
    LeakageGuard,
    OutOfSampleDataLoader,
    SampleBoundary,
    TrainDataLoader,
)
from cogalpha_mvp.evaluation.dedup import FactorDeduplicator
from cogalpha_mvp.evaluation.metrics import compute_all_metrics
from cogalpha_mvp.evaluation.scorer import FactorScorer
from cogalpha_mvp.factors.registry import FactorRegistry
from cogalpha_mvp.factors.seed_factors import register_seed_factors
from cogalpha_mvp.logging_config import setup_logging
from cogalpha_mvp.portfolio.backtest import BacktestEngine
from cogalpha_mvp.quality.pipeline import QualityPipeline
from cogalpha_mvp.reporting.reporter import ReportGenerator

logger = logging.getLogger("cogalpha_mvp")


class PipelineRunner:
    """Orchestrates the full CogAlpha research pipeline."""

    def __init__(self, config: Config):
        self.config = config
        self.registry = FactorRegistry()
        self.boundary = SampleBoundary.from_config(config)
        self.leakage_guard = LeakageGuard(self.boundary)

        # Set up output directory
        run_id = config.run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")
        self.config.run_id = run_id
        self.output_dir = Path(config.output_dir) / run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging
        log_file = self.output_dir / "pipeline.log"
        setup_logging(config.log_level, log_file, run_id)

    def run_all(self, use_synthetic: bool = True, data_path: str = "") -> dict:
        """Run the complete pipeline end-to-end.

        Args:
            use_synthetic: If True, generate synthetic data. Otherwise load from path.
            data_path: Path to data file (if not synthetic).

        Returns:
            Summary dictionary with all results.
        """
        logger.info("=" * 60)
        logger.info("CogAlpha Research MVP - Pipeline Start")
        logger.info("Run ID: %s", self.config.run_id)
        logger.info("=" * 60)

        # Save config snapshot
        self.config.snapshot(self.output_dir / "config_snapshot.yaml")

        # Save environment info
        self._save_environment()

        # Step 1: Load data
        data = self._load_data(use_synthetic, data_path)

        # Step 2: Validate & normalize
        data = self._validate_data(data)

        # Step 3: Sample isolation
        train_data, oos_data = self._split_data(data)

        # Step 4: Register factors
        self._register_factors()

        # Step 5: Quality checking
        quality_results = self._quality_check(train_data)

        # Step 6: Evaluate factors
        train_metrics, factor_values = self._evaluate_factors(train_data)

        # Step 7: Score & classify
        scoring_results = self._score_factors(train_metrics)

        # Step 8: Dedup
        dedup_results = self._dedup(train_metrics, factor_values, scoring_results)

        # Step 9: OOS validation
        oos_metrics = self._oos_validation(oos_data, dedup_results)

        # Step 10: Portfolio backtest
        portfolio_results = self._backtest(factor_values, train_data)

        # Step 11: Report
        report_path = self._generate_report(
            data,
            quality_results,
            train_metrics,
            scoring_results,
            dedup_results,
            oos_metrics,
            portfolio_results,
        )

        # Generate SHA256SUMS
        self._generate_sha256sums()

        summary = {
            "run_id": self.config.run_id,
            "report_path": str(report_path),
            "n_factors": self.registry.count,
            "n_passed_quality": sum(1 for r in quality_results if r.get("passed")),
            "n_elite": sum(1 for r in scoring_results.values() if r["status"] == "elite"),
            "n_qualified": sum(1 for r in scoring_results.values() if r["status"] == "qualified"),
            "n_after_dedup": dedup_results.get("after", 0),
            "train_period": f"{self.config.data.train_start} to {self.config.data.train_end}",
            "oos_period": f"{self.config.data.oos_start} to {self.config.data.oos_end}",
            "disclaimer": "RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING",
        }

        logger.info("=" * 60)
        logger.info("Pipeline Complete!")
        logger.info("Report: %s", report_path)
        logger.info("=" * 60)

        return summary

    def _save_environment(self) -> None:
        """Save environment information."""
        env_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "timestamp": datetime.now().isoformat(),
            "package_version": "0.1.0",
        }
        path = self.output_dir / "environment.json"
        path.write_text(json.dumps(env_info, indent=2), encoding="utf-8")

    def _load_data(self, use_synthetic: bool, data_path: str) -> pd.DataFrame:
        """Step 1: Load market data."""
        logger.info("Step 1: Loading data...")

        if use_synthetic or not data_path:
            adapter: MarketDataAdapter = SyntheticDataAdapter()
            request = DataRequest(
                start_date=self.config.data.full_start,
                end_date=self.config.data.full_end,
            )
            data = adapter.load(request)
            source = "synthetic"
        else:
            from cogalpha_mvp.data.adapters import LocalCSVAdapter, LocalParquetAdapter

            adapter = LocalParquetAdapter() if data_path.endswith(".parquet") else LocalCSVAdapter()
            request = DataRequest(
                path=data_path,
                start_date=self.config.data.full_start,
                end_date=self.config.data.full_end,
            )
            data = adapter.load(request)
            source = f"file:{data_path}"

        # Create snapshot manifest
        manifest = create_snapshot_manifest(data, source, data_path or "synthetic")
        manifest_path = self.output_dir / "data_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        logger.info("Data loaded: %d rows, %d symbols", len(data), data["symbol"].nunique())
        return data

    def _validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Step 2: Validate and normalize data."""
        logger.info("Step 2: Validating data...")
        data = StandardMarketData.normalize(data)
        errors = StandardMarketData.validate(data)
        if errors:
            for e in errors:
                logger.warning("Data validation: %s", e)
        logger.info("Data validation complete (errors: %d)", len(errors))
        return data

    def _split_data(self, data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Step 3: Split data into train and OOS."""
        logger.info("Step 3: Splitting data into train/OOS...")
        self.boundary.validate()

        train_loader = TrainDataLoader(self.boundary)
        oos_loader = OutOfSampleDataLoader(self.boundary)

        train_data = train_loader.load(data)
        oos_data = oos_loader.load(data)

        # Verify no leakage
        self.leakage_guard.check_train_oos_fingerprints(
            train_loader.fingerprint,
            oos_loader.fingerprint,
        )

        # Save run manifest
        run_manifest = {
            "train_fingerprint": train_loader.fingerprint,
            "oos_fingerprint": oos_loader.fingerprint,
            "train_rows": len(train_data),
            "oos_rows": len(oos_data),
            "train_symbols": int(train_data["symbol"].nunique()),
            "oos_symbols": int(oos_data["symbol"].nunique()),
        }
        path = self.output_dir / "run_manifest.json"
        path.write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")

        return train_data, oos_data

    def _register_factors(self) -> None:
        """Step 4: Register seed factors."""
        logger.info("Step 4: Registering seed factors...")
        n = register_seed_factors(self.registry)
        logger.info("Registered %d seed factors", n)

    def _quality_check(self, train_data: pd.DataFrame) -> list[dict]:
        """Step 5: Run quality checks on all factors."""
        logger.info("Step 5: Quality checking...")
        pipeline = QualityPipeline(self.config.quality)
        results = []

        quality_dir = self.output_dir / "quality"
        quality_dir.mkdir(exist_ok=True)

        for factor in self.registry.all_factors():
            result = pipeline.check(factor, train_data)
            factor.review_status = "passed" if result.passed else "rejected"
            factor.rejection_reason = result.error
            results.append(result.to_dict())

        # Save quality results
        import pandas as pd

        df = pd.DataFrame(results)
        df.to_csv(str(quality_dir / "factor_quality.csv"), index=False, encoding="utf-8-sig")

        n_passed = sum(1 for r in results if r["passed"])
        logger.info("Quality check: %d/%d passed", n_passed, len(results))

        return results

    def _evaluate_factors(self, train_data: pd.DataFrame) -> tuple[dict, dict]:
        """Step 6: Evaluate factors on training data."""
        logger.info("Step 6: Evaluating factors...")
        train_metrics: dict[str, dict] = {}
        factor_values: dict[str, pd.DataFrame] = {}

        train_dir = self.output_dir / "train"
        train_dir.mkdir(exist_ok=True)

        passed_factors = self.registry.passed_factors()
        for factor in passed_factors:
            logger.info("  Evaluating %s...", factor.factor_id)
            try:
                values = self.registry.evaluate_factor(factor.factor_id, train_data)
                factor_values[factor.factor_id] = values

                metrics = compute_all_metrics(
                    values,
                    train_data,
                    factor.factor_id,
                    forward_period=self.config.factors.forward_period,
                )
                factor.train_metrics = metrics.to_dict()
                train_metrics[factor.factor_id] = metrics.to_dict()
            except Exception as e:
                logger.error("  Failed to evaluate %s: %s", factor.factor_id, e)

        # Save train metrics to CSV
        if train_metrics:
            pd.DataFrame(list(train_metrics.values())).to_csv(
                str(train_dir / "train_metrics.csv"), index=False, encoding="utf-8-sig"
            )

        logger.info("Evaluated %d factors", len(train_metrics))
        return train_metrics, factor_values

    def _score_factors(self, train_metrics: dict[str, dict]) -> dict[str, dict]:
        """Step 7: Score and classify factors."""
        logger.info("Step 7: Scoring factors...")
        from cogalpha_mvp.evaluation.metrics import FactorMetrics

        scorer = FactorScorer(self.config.factors)

        # Convert dicts back to FactorMetrics
        metrics_objects: dict[str, FactorMetrics] = {}
        for fid, m_dict in train_metrics.items():
            m = FactorMetrics()
            for k, v in m_dict.items():
                if hasattr(m, k):
                    setattr(m, k, v)
            metrics_objects[fid] = m

        results = scorer.score_all(metrics_objects)

        # Convert back to serializable
        scoring_results: dict[str, dict] = {}
        for fid, r in results.items():
            scoring_results[fid] = {
                "status": r["status"],
                "composite_score": r["composite_score"],
                "metrics": r["metrics"].to_dict(),
            }

        return scoring_results

    def _dedup(
        self,
        train_metrics: dict,
        factor_values: dict,
        scoring_results: dict,
    ) -> dict:
        """Step 8: Deduplicate factors."""
        logger.info("Step 8: Deduplicating factors...")
        dedup_dir = self.output_dir / "dedup"
        dedup_dir.mkdir(exist_ok=True)

        deduplicator = FactorDeduplicator(self.config.dedup)

        # Get passed factors
        passed_factors = self.registry.passed_factors()
        n_before = len(passed_factors)

        # Build composite scores dict
        scores = {fid: r["composite_score"] for fid, r in scoring_results.items()}
        coverage = {fid: r["metrics"].get("coverage", 0.0) for fid, r in scoring_results.items()}
        turnover = {fid: r["metrics"].get("turnover", 0.0) for fid, r in scoring_results.items()}

        unique_factors, removed = deduplicator.dedup(
            passed_factors,
            factor_values,
            scores,
            coverage,
            turnover,
        )

        result = {
            "before": n_before,
            "after": len(unique_factors),
            "removed": len(removed),
            "removed_ids": removed,
        }

        import pandas as pd

        pd.DataFrame([result]).to_csv(
            str(dedup_dir / "dedup_results.csv"), index=False, encoding="utf-8-sig"
        )

        # Save elite factors info
        elite_dir = self.output_dir / "elite_factors"
        elite_dir.mkdir(exist_ok=True)
        elite_factors = [
            scoring_results[f.factor_id]
            for f in unique_factors
            if f.factor_id in scoring_results and scoring_results[f.factor_id]["status"] == "elite"
        ]
        if elite_factors:
            import pandas as pd

            pd.DataFrame(elite_factors).to_csv(
                str(elite_dir / "elite_factors.csv"), index=False, encoding="utf-8-sig"
            )

        logger.info("Dedup: %d -> %d (removed %d)", n_before, len(unique_factors), len(removed))
        return result

    def _oos_validation(self, oos_data: pd.DataFrame, dedup_results: dict) -> dict[str, dict]:
        """Step 9: Out-of-sample validation."""
        logger.info("Step 9: OOS validation...")
        self.leakage_guard.mark_oos_loaded()

        oos_dir = self.output_dir / "oos"
        oos_dir.mkdir(exist_ok=True)

        oos_metrics: dict[str, dict] = {}
        passed_factors = self.registry.passed_factors()

        for factor in passed_factors:
            try:
                values = self.registry.evaluate_factor(factor.factor_id, oos_data)
                metrics = compute_all_metrics(
                    values,
                    oos_data,
                    factor.factor_id,
                    forward_period=self.config.factors.forward_period,
                )

                # Compute decay from train to OOS
                train_ic = factor.train_metrics.get("ic_mean", 0.0)
                oos_ic = metrics.ic_mean
                decay = (train_ic - oos_ic) / abs(train_ic) if train_ic != 0 else 0.0

                # Sign consistency
                train_ic_sign = 1 if train_ic >= 0 else -1
                oos_ic_sign = 1 if oos_ic >= 0 else -1
                sign_consistent = train_ic_sign == oos_ic_sign

                oos_metrics[factor.factor_id] = {
                    **metrics.to_dict(),
                    "train_ic": train_ic,
                    "oos_ic": oos_ic,
                    "decay_ratio": float(decay),
                    "sign_consistent": sign_consistent,
                }
            except Exception as e:
                logger.error("OOS evaluation failed for %s: %s", factor.factor_id, e)

        import pandas as pd

        if oos_metrics:
            pd.DataFrame(list(oos_metrics.values())).to_csv(
                str(oos_dir / "oos_metrics.csv"), index=False, encoding="utf-8-sig"
            )

        logger.info("OOS validation complete: %d factors", len(oos_metrics))
        return oos_metrics

    def _backtest(self, factor_values: dict, train_data: pd.DataFrame) -> dict:
        """Step 10: Portfolio backtest."""
        logger.info("Step 10: Portfolio backtest...")
        engine = BacktestEngine(self.config.portfolio)
        results: dict[str, dict] = {}

        # Use the first available factor for demo
        if factor_values:
            fid = next(iter(factor_values.keys()))
            values = factor_values[fid]

            for strategy in ["top_quantile", "long_short", "equal_weight"]:
                try:
                    result = engine.run(values, train_data, strategy=strategy)
                    results[strategy] = result.to_dict()
                except Exception as e:
                    logger.error("Backtest failed for %s: %s", strategy, e)

        # Save portfolio results to CSV
        portfolio_dir = self.output_dir / "portfolio"
        portfolio_dir.mkdir(exist_ok=True)
        if results:
            pd.DataFrame(list(results.values())).to_csv(
                str(portfolio_dir / "portfolio_results.csv"), index=False, encoding="utf-8-sig"
            )

        # Create charts directory (charts are embedded in HTML report)
        charts_dir = self.output_dir / "charts"
        charts_dir.mkdir(exist_ok=True)

        logger.info("Backtest complete: %d strategies", len(results))
        return results

    def _generate_report(
        self,
        data: pd.DataFrame,
        quality_results: list[dict],
        train_metrics: dict[str, dict],
        scoring_results: dict[str, dict],
        dedup_results: dict,
        oos_metrics: dict[str, dict],
        portfolio_results: dict,
    ) -> Path:
        """Step 11: Generate reports."""
        logger.info("Step 11: Generating reports...")

        data_summary = {
            "rows": len(data),
            "n_symbols": int(data["symbol"].nunique()),
            "start_date": str(data["trade_date"].min()),
            "end_date": str(data["trade_date"].max()),
            "data_fingerprint": StandardMarketData.compute_fingerprint(data),
        }

        reporter = ReportGenerator(self.config, self.output_dir)
        report_path = reporter.generate_full_report(
            data_summary=data_summary,
            quality_results=quality_results,
            train_metrics=train_metrics,
            scoring_results=scoring_results,
            dedup_results=dedup_results,
            oos_metrics=oos_metrics,
            portfolio_results=portfolio_results,
        )

        return report_path

    def _generate_sha256sums(self) -> None:
        """Generate SHA256SUMS.txt for all output files."""
        sha_path = self.output_dir / "SHA256SUMS.txt"
        lines = []

        for f in sorted(self.output_dir.rglob("*")):
            if f.is_file() and f.name != "SHA256SUMS.txt":
                sha = hashlib.sha256(f.read_bytes()).hexdigest()
                rel = f.relative_to(self.output_dir)
                lines.append(f"{sha}  {rel}")

        sha_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("SHA256SUMS generated: %d files", len(lines))
