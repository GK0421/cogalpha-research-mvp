# Getting Started

## 1. Start Studio

```powershell
scripts\start_studio.ps1
```

Browser opens at `http://127.0.0.1:8765`.

## 2. Create a Project

1. Click **Projects** in navigation
2. Click **New Project**
3. Enter name (e.g., "My First Research")
4. Click **Create**

## 3. Import Data

1. Open your project
2. Go to **Datasets** tab
3. Click **Upload CSV**
4. Select a CSV file with columns: `symbol, trade_date, open, high, low, close, volume`
5. Wait for validation

Or use synthetic data:
```powershell
python -m cogalpha_mvp.cli generate-demo-data
```

## 4. Explore Factors

1. Go to **Factor Lab**
2. Browse 21 built-in seed factors
3. Try the DSL validator with expressions like:
   - `ts_rank(close, 20)`
   - `mean(volume, 5) / mean(volume, 20)`
   - `delay(close, 1) / close - 1`

## 5. Run Research

1. Go to **Runs**
2. Click **New Run**
3. Select your project and dataset
4. Click **Start**
5. Watch progress in real-time

## 6. View Results

1. Open the completed run
2. Check factor metrics (IC, RankIC, ICIR)
3. View portfolio backtest results
4. Download HTML report

## Next Steps

- [Data Import Guide](data_import_guide.md)
- [Factor Lab Guide](factor_lab_guide.md)
- [Research Run Guide](research_run_guide.md)
- [Result Interpretation](result_interpretation.md)
