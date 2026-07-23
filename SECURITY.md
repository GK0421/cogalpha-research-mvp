# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
privately by creating a security advisory on GitHub or contacting the
repository owner directly. Do not open a public issue.

## Security Measures

This project implements the following security measures:

### No Code Execution from LLM
- LLM outputs are never executed via `exec()`, `eval()`, or `compile()`.
- LLM can only output structured Factor DSL (JSON) which is parsed by a
  custom parser with a strict whitelist of operators.
- No `subprocess`, `os.system`, or dynamic imports are used to process
  LLM-generated content.

### Secret Management
- API keys are read from environment variables only.
- `.env` files are gitignored and never committed.
- `.env.example` contains only variable names, never real values.
- A pre-commit scan checks for common secret patterns.

### Data Isolation
- Training and out-of-sample data are strictly separated.
- No future information leakage is allowed in factor computation.
- Time-series truncation tests verify no look-ahead bias.

### No Live Trading
- This project does NOT implement order execution or broker connections.
- All backtests are research-only and clearly labeled as such.
