# V0.2.0/V0.2.1 Security Report

**Date**: 2026-07-24  
**Version**: 0.2.1  

---

## Security Checklist

### Network Security
- [x] Default binding: 127.0.0.1:8765 (localhost only)
- [x] CORS restricted to localhost origins
- [x] No 0.0.0.0 binding by default
- [x] Docker ports bound to 127.0.0.1

### Authentication & Secrets
- [x] No API keys in source code
- [x] API keys stored in local .env (gitignored)
- [x] Keys never logged
- [x] No hardcoded passwords or tokens
- [x] .env.example has no real keys

### Code Security
- [x] No exec(), eval(), or compile() (safe DSL parser)
- [x] AST-based expression evaluation
- [x] Whitelisted functions and fields only
- [x] No SQL injection (SQLAlchemy ORM with parameterized queries)

### File Upload Security
- [x] Max file size: 500MB
- [x] Extension whitelist: .csv, .parquet only
- [x] Filename sanitization (no path traversal)
- [x] CSV formula injection prevention
- [x] SHA256 hash computed for uploaded files

### Docker Security
- [x] Non-root user (UID 1000)
- [x] No API keys in Docker images
- [x] No real data in Docker images
- [x] No PDF in Docker images
- [x] Health checks configured

### Data Security
- [x] No real market data in git
- [x] No PDF files in git
- [x] No .env in git
- [x] No results/runs in git
- [x] Data directory gitignored

### Telemetry & Privacy
- [x] Telemetry DISABLED by default
- [x] No analytics collected
- [x] No crash reports sent
- [x] No external calls without user action

### Research Safety
- [x] RESEARCH_BACKTEST_ONLY label throughout
- [x] NO_LIVE_TRADING label throughout
- [x] No brokerage API integration
- [x] No order execution capability
- [x] Training/OOS data strictly separated

### CI Security
- [x] pip-audit in security workflow
- [x] Secret scanning in CI
- [x] Large file detection in CI
- [x] Default permissions: contents: read

## Secret Scan Results

```
Scanned: all tracked files
Patterns: API keys, passwords, tokens, private keys
Result: NO SECRETS FOUND
```

## Dependency Audit

```
pip-audit: No known vulnerabilities in installed packages
```
