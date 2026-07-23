# Factor Protocol

## Safe DSL Design

The factor DSL is designed to be **safe by construction**:
- No `exec()`, `eval()`, or `compile()` is ever used
- Expressions are parsed by Python's `ast` module for validation
- A custom tree-walking interpreter evaluates expressions
- Only whitelisted functions and fields are allowed

## Whitelisted Functions

### Time-Series Functions (per-symbol, chronological)

| Function | Description | Example |
|----------|-------------|---------|
| `delay(series, n)` | Lag by n periods | `delay(close, 1)` |
| `delta(series, n)` | Difference over n periods | `delta(close, 5)` |
| `ret(series, n)` | Percentage return over n periods | `ret(close, 1)` |
| `ts_mean(series, n)` | Rolling mean | `ts_mean(close, 20)` |
| `ts_sum(series, n)` | Rolling sum | `ts_sum(volume, 10)` |
| `ts_std(series, n)` | Rolling std | `ts_std(ret(close,1), 20)` |
| `ts_min(series, n)` | Rolling min | `ts_min(close, 20)` |
| `ts_max(series, n)` | Rolling max | `ts_max(close, 60)` |
| `ts_rank(series, n)` | Rolling percentile rank | `ts_rank(close, 20)` |
| `corr(s1, s2, n)` | Rolling correlation | `corr(close, volume, 20)` |
| `cov(s1, s2, n)` | Rolling covariance | `cov(close, volume, 20)` |

### Cross-Sectional Functions

| Function | Description | Example |
|----------|-------------|---------|
| `rank(series)` | Cross-sectional percentile rank | `rank(close)` |
| `zscore(series)` | Cross-sectional z-score | `zscore(volume)` |
| `winsorize(series, n_std)` | Clip at n std | `winsorize(close, 3)` |

### Mathematical Functions

| Function | Description |
|----------|-------------|
| `abs(series)` | Absolute value |
| `sign(series)` | Sign function |
| `log1p(series)` | log(1+|x|) * sign(x) |
| `sqrt(series)` | sqrt(|x|) * sign(x) |
| `clip(series, lower, upper)` | Clip values |

### Arithmetic Operators

| Function | Description |
|----------|-------------|
| `add(a, b)` | Addition |
| `sub(a, b)` | Subtraction |
| `mul(a, b)` | Multiplication |
| `div(a, b)` | Safe division (0 -> NaN) |
| `min(a, b)` | Element-wise minimum |
| `max(a, b)` | Element-wise maximum |
| `where(cond, a, b)` | Conditional selection |

## Allowed Data Fields

- `open`, `high`, `low`, `close`, `volume`, `amount`

## Forbidden Patterns

The following are **strictly forbidden** and will cause rejection:

- Negative shift (`shift(-n)`) - uses future data
- `lead`, `future` - future references
- `tail()` - future endpoint access
- `iloc[-1]` - full-sample endpoint reference
- File access, network access, system calls
- Dynamic imports, reflection, arbitrary attribute chains
- `exec()`, `eval()`, `compile()`

## Factor Metadata

Every factor has:

| Field | Description |
|-------|-------------|
| `factor_id` | Unique identifier |
| `name` | Human-readable name |
| `agent_id` | Owning agent |
| `level` | Hierarchy level (1-7) |
| `expression` | DSL expression string |
| `direction` | +1 or -1 |
| `description` | Economic rationale |
| `parameters` | Parameter dictionary |
| `source` | Origin (seed/llm/mutation/crossover) |
| `expression_hash` | SHA256 of normalized expression |
| `review_status` | pending/passed/rejected |
| `train_metrics` | Training period metrics |
| `oos_metrics` | OOS period metrics |

## LLM Integration (Optional)

When an LLM API key is available:
- LLM outputs structured JSON (Factor DSL), never Python code
- JSON Schema validation is performed
- Concurrent requests with rate limiting
- Exponential backoff for 429/5xx errors
- No API keys are logged

Without an API key:
- 21 built-in seed factors are used
- `LLM_GENERATION_DISABLED` is logged
- No error or crash
