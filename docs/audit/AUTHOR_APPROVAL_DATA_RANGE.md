# AUTHOR_APPROVAL: Data Range Deviation

**Document ID**: CogAlpha-APPROVAL-001  
**Date**: 2026-07-24  
**Project**: CogAlpha Research MVP v0.1.1  
**Approver**: 郭恺  

---

## AUTHOR_APPROVAL

本人批准CogAlpha Research MVP v0.1.1使用当前真实数据的实际覆盖范围：

实际训练期：2015-01-01-2019-12-31  
实际样本外期：2020-01-01-2025-12-31

该区间偏离原始2011-2019训练期设定，原因是当前真实数据不包含2011-2014年。  
本批准仅适用于MVP工程验证，不代表原始长期样本研究设计已经完整复现。

批准人：郭恺  
批准日期：2026-07-24

---

## Deviation Disclosure

### 1. Configuration Target Range

| Parameter | Configured Value | Source |
|-----------|-----------------|--------|
| `full_start` | 2011-01-01 | `configs/default.yaml` |
| `full_end` | 2025-12-31 | `configs/default.yaml` |
| `train_start` | 2011-01-01 | `configs/default.yaml` |
| `train_end` | 2019-12-31 | `configs/default.yaml` |
| `oos_start` | 2020-01-01 | `configs/default.yaml` |
| `oos_end` | 2025-12-31 | `configs/default.yaml` |

### 2. Data Actual Coverage Range

| Parameter | Actual Value | Source |
|-----------|-------------|--------|
| Earliest date in data | 2015-01-05 | `stock_daily_master.parquet` (10.7M rows) |
| Total symbols | 5,401 | `stock_daily_master.parquet` |
| Total rows | 10,700,000+ | `stock_daily_master.parquet` |
| Sampled symbols | 100 | `data/raw/real_astock_sample.csv` |
| Sampled rows | 266,222 | `data/raw/real_astock_sample.csv` |
| Sampled unique dates | 2,663 | `data/raw/real_astock_sample.csv` |
| Sampled date range | 2015-01-05 to 2025-12-31 | `data/raw/real_astock_sample.csv` |

### 3. Actual Computation Range

| Parameter | Value | Notes |
|-----------|-------|-------|
| Train period used | 2015-01-01 to 2019-12-31 | Configured 2011-2019, but data starts ~2014 |
| OOS period used | 2020-01-01 to 2025-12-31 | Matches configuration |
| Forward period | 1 day | For IC calculation |

### 4. Missing Records (2011-2014)

| Year Range | Status | Impact |
|------------|--------|--------|
| 2011-01-01 to 2014-12-31 | No data available in source parquet | 4 years of training data missing |
| Estimated missing trading days | ~960 (240 days/year x 4 years) | Conservative estimate |
| Estimated missing records (sampled) | ~96,000 (100 symbols x 960 days) | Based on sampled 100 symbols |
| Actual train rows used | 121,896 | `results/real_data_run_001/run_manifest.json` |
| Actual OOS rows used | 144,326 | `results/real_data_run_001/run_manifest.json` |

### 5. Data Loader Behavior on Empty Ranges

The `LocalCSVAdapter` loads data within the requested date range. When the
requested range includes dates not present in the data file (e.g., 2011-01-01
when data starts at 2014), the adapter silently returns only the rows that
exist within the intersection of the requested range and the available data.

**This means**: A configuration requesting `train_start: "2011-01-01"` with
data starting at 2014 will produce a training set starting at 2014, not 2011,
without any warning or error.

This behavior is documented in the adapter's `load()` method:
- Filters by `trade_date >= start_date AND trade_date <= end_date`
- No assertion or warning if the resulting date range is shorter than requested
- The `run_manifest.json` records the actual min/max dates of loaded data

### 6. Research Impact Assessment

| Dimension | Impact |
|-----------|--------|
| Training sample length | Reduced from 9 years to 5 years (44% reduction) |
| Market state coverage | Missing 2011-2014 bull-to-bear transition |
| Factor stability assessment | Weaker with shorter history |
| Parameter sensitivity | Higher sensitivity to 2015-2019 market conditions |
| Comparability with original spec | NOT strictly comparable |

### 7. Conclusion

This deviation does NOT invalidate the MVP engineering deliverable. The
pipeline, quality checks, evaluation, dedup, OOS validation, backtest, and
reporting all function correctly. However, research conclusions drawn from
this data range should not be presented as equivalent to the original
2011-2019 training specification.

Future work: Acquire A-stock data covering 2011-2014 to enable full
compliance with the original date range specification.
