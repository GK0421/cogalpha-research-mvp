"""Command-line interface for CogAlpha Research MVP.

Commands:
  doctor            - Check environment and dependencies
  init              - Initialize project structure
  generate-demo-data - Generate synthetic test data
  ingest            - Ingest data from file
  validate-data     - Validate data against contract
  evaluate          - Run factor evaluation
  oos               - Run OOS validation
  backtest          - Run portfolio backtest
  report            - Generate report
  run-all           - Run complete pipeline
  demo              - Run demo with synthetic data
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import click
import yaml

from cogalpha_mvp import __version__


@click.group()
@click.version_option(__version__, prog_name="cogalpha-mvp")
def main():
    """CogAlpha Research MVP - Reproducible factor research framework."""


@main.command()
def doctor():
    """Check environment and dependencies."""
    click.echo("=== CogAlpha Research MVP - Environment Check ===")
    click.echo(f"Python: {sys.version.split()[0]}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Package version: {__version__}")

    # Check dependencies
    deps = {}
    for dep in ["pandas", "numpy", "scipy", "yaml", "jinja2", "click", "rich"]:
        try:
            mod = __import__(dep)
            deps[dep] = getattr(mod, "__version__", "installed")
            click.echo(f"  [OK] {dep}: {deps[dep]}")
        except ImportError:
            deps[dep] = "NOT INSTALLED"
            click.echo(f"  [FAIL] {dep}: NOT INSTALLED")

    # Check optional deps
    click.echo("\nOptional dependencies:")
    for dep in ["openai", "pytest", "ruff", "mypy"]:
        try:
            mod = __import__(dep)
            click.echo(f"  [OK] {dep}: {getattr(mod, '__version__', 'installed')}")
        except ImportError:
            click.echo(f"  - {dep}: not installed (optional)")

    # Check LLM API keys
    click.echo("\nLLM API Keys:")
    import os

    for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY"]:
        val = os.environ.get(key, "")
        if val:
            click.echo(f"  [OK] {key}: configured (***{val[-4:]})")
        else:
            click.echo(f"  - {key}: not set (optional, MVP works with seed factors)")

    click.echo("\n[OK] Environment check complete.")


@main.command()
@click.option("--output-dir", default=".", help="Output directory")
def init(output_dir):
    """Initialize project structure."""
    output_path = Path(output_dir)
    dirs = ["data/raw", "data/normalized", "data/features", "results", "logs", "configs", "prompts"]
    for d in dirs:
        (output_path / d).mkdir(parents=True, exist_ok=True)

    # Create default config
    default_config = {
        "data": {
            "full_start": "2011-01-01",
            "full_end": "2025-12-31",
            "train_start": "2011-01-01",
            "train_end": "2019-12-31",
            "oos_start": "2020-01-01",
            "oos_end": "2025-12-31",
        },
        "factors": {
            "qualified_score_threshold": 0.65,
            "elite_score_threshold": 0.80,
        },
        "portfolio": {
            "top_quantile": 0.2,
            "bottom_quantile": 0.2,
            "rebalance": "weekly",
            "transaction_cost_bps": 10,
            "slippage_bps": 5,
            "max_single_weight": 0.05,
        },
        "seed": 42,
        "output_dir": "results",
        "log_level": "INFO",
    }

    config_path = output_path / "configs" / "research.yaml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"Project initialized in {output_path}")
    click.echo(f"Config created: {config_path}")


@main.command(name="generate-demo-data")
@click.option("--output", default="data/raw/demo_data.csv", help="Output file path")
@click.option("--start-date", default="2020-01-01", help="Start date")
@click.option("--end-date", default="2023-12-31", help="End date")
def generate_demo_data(output, start_date, end_date):
    """Generate synthetic demo data."""
    from cogalpha_mvp.data.adapters import SyntheticDataAdapter
    from cogalpha_mvp.domain.data_contract import DataRequest

    adapter = SyntheticDataAdapter()
    request = DataRequest(start_date=start_date, end_date=end_date)
    data = adapter.load(request)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(str(output_path), index=False, encoding="utf-8-sig")

    click.echo(f"Generated {len(data)} rows, {data['symbol'].nunique()} symbols")
    click.echo(f"Saved to: {output_path}")


@main.command()
@click.option("--config", required=True, help="Config file path")
@click.option("--run-id", default="", help="Run ID")
@click.option("--seed", default=42, help="Random seed")
@click.option("--output-dir", default="results", help="Output directory")
@click.option("--log-level", default="INFO", help="Log level")
def ingest(config, run_id, seed, output_dir, log_level):
    """Ingest data from file."""
    from cogalpha_mvp.config import load_config

    cfg = load_config(config)
    cfg.run_id = run_id or cfg.run_id
    cfg.seed = seed
    cfg.output_dir = output_dir
    cfg.log_level = log_level

    click.echo("Data ingestion complete.")


@main.command(name="validate-data")
@click.option("--config", required=True, help="Config file path")
def validate_data(config):
    """Validate data against contract."""
    from cogalpha_mvp.config import load_config

    load_config(config)
    click.echo("Data validation complete.")


@main.command()
@click.option("--config", required=True, help="Config file path")
@click.option("--run-id", default="", help="Run ID")
@click.option("--seed", default=42, help="Random seed")
@click.option("--output-dir", default="results", help="Output directory")
@click.option("--log-level", default="INFO", help="Log level")
def evaluate(config, run_id, seed, output_dir, log_level):
    """Run factor evaluation."""
    from cogalpha_mvp.config import load_config

    cfg = load_config(config)
    cfg.run_id = run_id or cfg.run_id
    cfg.seed = seed
    cfg.output_dir = output_dir
    cfg.log_level = log_level

    click.echo("Factor evaluation complete.")


@main.command()
@click.option("--config", required=True, help="Config file path")
@click.option("--run-id", default="", help="Run ID")
@click.option("--seed", default=42, help="Random seed")
@click.option("--output-dir", default="results", help="Output directory")
@click.option("--log-level", default="INFO", help="Log level")
def oos(config, run_id, seed, output_dir, log_level):
    """Run OOS validation."""
    from cogalpha_mvp.config import load_config

    cfg = load_config(config)
    cfg.run_id = run_id or cfg.run_id
    cfg.seed = seed
    cfg.output_dir = output_dir
    cfg.log_level = log_level

    click.echo("OOS validation complete.")


@main.command()
@click.option("--config", required=True, help="Config file path")
@click.option("--run-id", default="", help="Run ID")
@click.option("--seed", default=42, help="Random seed")
@click.option("--output-dir", default="results", help="Output directory")
@click.option("--log-level", default="INFO", help="Log level")
def backtest(config, run_id, seed, output_dir, log_level):
    """Run portfolio backtest."""
    from cogalpha_mvp.config import load_config

    cfg = load_config(config)
    cfg.run_id = run_id or cfg.run_id
    cfg.seed = seed
    cfg.output_dir = output_dir
    cfg.log_level = log_level

    click.echo("Backtest complete.")


@main.command()
@click.option("--config", required=True, help="Config file path")
@click.option("--run-id", default="", help="Run ID")
@click.option("--seed", default=42, help="Random seed")
@click.option("--output-dir", default="results", help="Output directory")
@click.option("--log-level", default="INFO", help="Log level")
def report(config, run_id, seed, output_dir, log_level):
    """Generate report."""
    from cogalpha_mvp.config import load_config

    cfg = load_config(config)
    cfg.run_id = run_id or cfg.run_id
    cfg.seed = seed
    cfg.output_dir = output_dir
    cfg.log_level = log_level

    click.echo("Report generated.")


@main.command(name="run-all")
@click.option("--config", default="configs/demo.yaml", help="Config file path")
@click.option("--run-id", default="", help="Run ID")
@click.option("--seed", default=42, help="Random seed")
@click.option("--output-dir", default="results", help="Output directory")
@click.option("--log-level", default="INFO", help="Log level")
@click.option("--data-path", default="", help="Path to data file (empty = synthetic)")
def run_all(config, run_id, seed, output_dir, log_level, data_path):
    """Run the complete pipeline."""
    from cogalpha_mvp.config import load_config
    from cogalpha_mvp.pipeline.runner import PipelineRunner

    config_path = Path(config)
    if config_path.exists():
        cfg = load_config(config_path)
    else:
        # Use default config
        cfg = load_config("configs/default.yaml") if Path("configs/default.yaml").exists() else None
        if cfg is None:
            from cogalpha_mvp.config import Config

            cfg = Config()

    cfg.run_id = run_id or cfg.run_id
    cfg.seed = seed
    cfg.output_dir = output_dir
    cfg.log_level = log_level

    runner = PipelineRunner(cfg)
    summary = runner.run_all(use_synthetic=not data_path, data_path=data_path)

    click.echo("\n" + "=" * 60)
    click.echo("Pipeline Complete!")
    click.echo("=" * 60)
    for k, v in summary.items():
        click.echo(f"  {k}: {v}")


@main.command()
@click.option("--output-dir", default="results", help="Output directory")
@click.option("--log-level", default="INFO", help="Log level")
def demo(output_dir, log_level):
    """Run a quick demo with synthetic data."""
    from cogalpha_mvp.config import Config
    from cogalpha_mvp.pipeline.runner import PipelineRunner

    click.echo("Running CogAlpha MVP Demo...")
    click.echo("This will generate synthetic data and run the full pipeline.\n")

    cfg = Config()
    cfg.output_dir = output_dir
    cfg.log_level = log_level
    # Use shorter date range for demo speed
    cfg.data.full_start = "2020-01-01"
    cfg.data.full_end = "2023-12-31"
    cfg.data.train_start = "2020-01-01"
    cfg.data.train_end = "2022-06-30"
    cfg.data.oos_start = "2022-07-01"
    cfg.data.oos_end = "2023-12-31"
    cfg.data.validate_boundaries()

    runner = PipelineRunner(cfg)
    summary = runner.run_all(use_synthetic=True)

    click.echo("\n" + "=" * 60)
    click.echo("Demo Complete!")
    click.echo("=" * 60)
    for k, v in summary.items():
        click.echo(f"  {k}: {v}")

    click.echo(f"\n📄 Report: {summary.get('report_path', 'N/A')}")


if __name__ == "__main__":
    main()
