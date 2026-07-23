# Upstream Repository Review

## 1. GK0421/cogalpha-factor-mining-clean

- **URL:** https://github.com/GK0421/cogalpha-factor-mining-clean
- **License:** MIT
- **Description:** CogAlpha Factor Mining - Clean MVP (Stage18 OOS validation pipeline)
- **Relationship:** Predecessor project. This MVP is an independent rebuild.
- **Reusable concepts:** Direction correction, low-memory evaluation, composite scoring, family deduplication
- **Not copied:** No code was directly copied. All implementations are clean-room.

## 2. simonlin1212/global-stock-data

- **URL:** https://github.com/simonlin1212/global-stock-data
- **Reviewed for:** Data normalization patterns, market coverage conventions
- **Relationship:** External reference for data adapter design
- **Not copied:** No code. Only interface design patterns were noted.

## 3. simonlin1212/a-stock-data

- **URL:** https://github.com/simonlin1212/a-stock-data
- **Reviewed for:** A-share data field conventions (ts_code, trade_date, vol, amount)
- **Relationship:** External reference for A-share data format
- **Not copied:** No code. Only field naming conventions were noted.

## 4. HKUDS/Vibe-Trading

- **URL:** https://github.com/HKUDS/Vibe-Trading
- **Reviewed for:** Architectural patterns for trading system design
- **Relationship:** External reference for architecture
- **Not copied:** No code. Only architectural ideas were noted.

## Summary

All four repositories were reviewed in read-only mode. No code was copied.
The CogAlpha Research MVP is a clean-room implementation based on publicly documented
interfaces and architectural concepts. The CogAlpha Operations Manual (PDF) served as
the primary design reference.
