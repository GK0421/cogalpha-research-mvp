# Data Import Guide

## Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | UTF-8 encoding |
| Parquet | `.parquet` | Columnar format |

## Required Columns

| Column | Type | Description |
|--------|------|-------------|
| symbol | string | Stock code (e.g., "000001") |
| trade_date | string/date | Trading date (YYYY-MM-DD) |
| open | float | Opening price |
| high | float | Highest price |
| low | float | Lowest price |
| close | float | Closing price |
| volume | float/int | Trading volume |

## Upload via UI

1. Open project -> Datasets tab
2. Click **Upload**
3. Select file
4. System validates columns and row count
5. Dataset appears in list with quality metrics

## Register Local File

For large files already on disk:

```bash
curl -X POST http://127.0.0.1:8765/api/projects/{id}/datasets/register-local \
  -H "Content-Type: application/json" \
  -d '{"name": "my_data", "file_path": "/path/to/data.csv"}'
```

## Security

- Max file size: 500MB
- Allowed extensions: .csv, .parquet only
- Filename sanitization (no path traversal)
- CSV formula injection prevention (=, +, -, @ stripped from cell starts)

## Validation

After upload, the system checks:
- Required columns present
- Date format valid
- No duplicate (symbol, date) pairs
- Missing value rates per column
- Symbol count and date range

## Synthetic Data

For testing without real data:

```powershell
python -m cogalpha_mvp.cli generate-demo-data
```

This creates 100 symbols x 252 days of synthetic OHLCV data.
