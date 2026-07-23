# Data Contract

## Minimum Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `symbol` | string | non-null | Stock ticker symbol |
| `trade_date` | date | non-null | Trading date (timezone-naive or UTC) |
| `open` | float | > 0 | Opening price |
| `high` | float | > 0 | High price |
| `low` | float | > 0 | Low price |
| `close` | float | > 0 | Closing price |
| `volume` | float | >= 0 | Trading volume |

## Recommended Extension Fields

| Field | Type | Description |
|-------|------|-------------|
| `exchange` | string | Exchange code |
| `market` | string | Market identifier (CN, US, HK) |
| `currency` | string | Currency code |
| `amount` | float | Trading amount |
| `turnover` | float | Turnover rate |
| `adj_factor` | float | Adjustment factor |
| `list_date` | date | Listing date |
| `delist_date` | date | Delisting date |
| `is_st` | bool | ST/*ST flag |
| `is_limit_up` | bool | Limit up flag |
| `is_limit_down` | bool | Limit down flag |
| `is_suspended` | bool | Suspension flag |
| `source` | string | Data source |
| `source_symbol` | string | Original symbol in source |
| `fetched_at` | datetime | Fetch timestamp |
| `data_version` | string | Data version tag |

## Primary Key

The primary key is: `market + exchange + symbol + trade_date`

- No duplicate primary keys are allowed
- No cross-stock filling is allowed
- No future-record filling is allowed
- Volume is not filled by default
- Price missing rows are deleted by default

## Data Layers

```
raw         -> Original immutable snapshot (never modified)
normalized  -> Field, code, and type standardized
features    -> Factor values and derived variables
```

## Raw Snapshot Manifest

Each raw data load produces a manifest with:
- Data source
- Fetch timestamp
- File SHA256
- Row count
- Symbol count
- Date range
- Field list
- Missing rates per field
- Duplicate key count

## Column Name Normalization

The system automatically normalizes common column name variations:

| Source | Normalized |
|--------|-----------|
| `ts_code` | `symbol` |
| `code` | `symbol` |
| `ticker` | `symbol` |
| `date` | `trade_date` |
| `datetime` | `trade_date` |
| `vol` | `volume` |
| `amt` | `amount` |
| `pct_chg` | `pct_change` |

## Supported File Formats

- CSV (`.csv`)
- Parquet (`.parquet`)
- JSON (`.json`) - for export adapters

## Data Isolation Rules

1. Training and OOS periods must not overlap
2. Factor generation, parameter selection, and dedup only use training data
3. OOS data is only loaded during final validation
4. Training objects must not hold OOS DataFrame references
5. SHA256 fingerprints are computed independently for train and OOS data
