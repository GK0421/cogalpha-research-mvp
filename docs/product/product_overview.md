# CogAlpha Studio - Product Overview

**CogAlpha Studio** is a local-first, browser-based quantitative factor research workbench.

## Product Positioning

```
Local-first quantitative factor research workspace
```

## What It Does

CogAlpha Studio enables researchers to:
- Import and validate market data (CSV/Parquet)
- Define factors using a safe DSL (no code execution)
- Run quality checks, evaluation, and OOS validation
- Generate research reports with IC/ICIR metrics
- Backtest factor portfolios (research-only, no live trading)

## Key Characteristics

| Feature | Value |
|---------|-------|
| Installation | One command (Windows/Docker) |
| Data storage | Local SQLite + file system |
| Network | Localhost-only (127.0.0.1:8765) |
| LLM | Optional (works with zero API keys) |
| Telemetry | Disabled by default |
| Trading | NOT included (research only) |

## Architecture

```
Browser (React+TS+Vite)
    |
    v
FastAPI Backend (127.0.0.1:8765)
    |
    +-- SQLAlchemy + SQLite (metadata)
    +-- Background job manager (pipeline execution)
    +-- CogAlpha MVP core (factors, quality, evaluation, backtest)
```

## Version

Current: v0.2.1  
Package: `cogalpha_mvp`  
Product: CogAlpha Studio
