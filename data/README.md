# Data Directory

This directory stores market data for the CogAlpha Research MVP.

## Structure

```
data/
├── raw/         # Original immutable snapshots (never modified)
├── normalized/  # Standardized data (fields, codes, types)
└── features/    # Factor values and derived variables
```

## Important Notes

- **Never commit real market data to Git.** The `.gitignore` excludes all data files.
- Only small synthetic test data may be committed.
- Raw snapshots must record: data source, fetch time, file SHA256, row count,
  symbol count, date range, fields, missing rate, and duplicate primary key count.
- Use `python -m cogalpha_mvp.cli generate-demo-data` to create synthetic data.
- Use `python -m cogalpha_mvp.cli ingest --config configs/research.yaml` to import
  real CSV or Parquet files.

## Data Contract

See `docs/data_contract.md` for the full data contract specification.

Required fields: `symbol`, `trade_date`, `open`, `high`, `low`, `close`, `volume`

Recommended extension fields: `exchange`, `market`, `currency`, `amount`, `turnover`,
`adj_factor`, `list_date`, `delist_date`, `is_st`, `is_limit_up`, `is_limit_down`,
`is_suspended`, `source`, `source_symbol`, `fetched_at`, `data_version`
