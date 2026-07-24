# Privacy and Security

## Data Location

All data is stored locally:
- Metadata: `~/.cogalpha/cogalpha.db` (SQLite)
- Run results: `~/.cogalpha/runs/`
- Reports: `~/.cogalpha/reports/`
- Logs: `~/.cogalpha/logs/`

No data is sent to external servers.

## Network Binding

CogAlpha Studio binds to `127.0.0.1:8765` only. It is NOT accessible
from other machines on the network by default.

## Telemetry

Telemetry is **DISABLED** by default. No usage data, crash reports, or
analytics are collected or transmitted.

## API Keys

- API keys (LLM providers) are stored in local `.env` file only
- `.env` is gitignored and never committed
- Keys are never logged or transmitted except to the LLM provider you configure
- The product works fully without any API keys

## File Upload Security

- Maximum file size: 500MB
- Allowed extensions: `.csv`, `.parquet` only
- Filename sanitization prevents path traversal
- CSV formula injection prevention (strips `=`, `+`, `-`, `@` from cell starts)

## Research-Only

CogAlpha Studio is a **research tool**. It does NOT:
- Execute real trades
- Connect to brokerage APIs
- Provide investment advice
- Guarantee any returns

All backtest results are simulated and for research purposes only.

## RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING

These labels appear throughout the product to remind users that
all results are research simulations.
