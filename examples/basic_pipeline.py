# Example: Basic Pipeline
"""Run the basic CogAlpha pipeline with synthetic data."""

from cogalpha_mvp.config import Config
from cogalpha_mvp.pipeline.runner import PipelineRunner


def main():
    config = Config()
    # Use shorter date range for demo
    config.data.full_start = "2020-01-01"
    config.data.full_end = "2023-12-31"
    config.data.train_start = "2020-01-01"
    config.data.train_end = "2022-06-30"
    config.data.oos_start = "2022-07-01"
    config.data.oos_end = "2023-12-31"
    config.data.validate_boundaries()

    runner = PipelineRunner(config)
    summary = runner.run_all(use_synthetic=True)

    print("\n=== Pipeline Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
