# Risk Methodology

## Version

Current methodology version:

```text
crypto-scout-canonical-v1
```

The mini-product methodology is aligned with the canonical risk model from `crypto-scout-analytics` for the implemented BTC risk surface.

## Input Rows

Each daily input row must contain:

- date
- open
- high
- low
- close
- volume
- market cap
- circulating supply

Prices, market cap, and circulating supply must be positive. Rows are sorted by date and duplicate dates are rejected.

## Feature Construction

### HLC3 Price

The model price is:

```text
HLC3 = (high + low + close) / 3
```

When the model price is displayed in the product or API docs, label it as `Model price` or HLC3 rather than a generic
spot or close price. If daily high and low are displayed alongside it, `High` and `Low` refer to the same completed daily
candle used to compute HLC3.

### Trend Deviation

Trend deviation uses a 365-day EMA:

```text
trend_dev = ln(HLC3 / EMA365(HLC3))
```

### Volatility Regime

Volatility is the rolling population standard deviation of daily log returns:

```text
log_return[t] = ln(HLC3[t] / HLC3[t-1])
vol_regime = rolling_std(log_return, 30 days)
```

### Turnover

Turnover is enabled when valid market cap is available across the source rows:

```text
turnover = ln(volume / market_cap)
```

## Robust Z-Scores

Each feature is converted to a robust rolling z-score with:

- window: `1460` days
- minimum periods: `365` days
- center: median
- scale: `1.4826 * MAD + 1e-12`
- clipping: `[-6.0, 6.0]`

When a window has fewer than 365 valid observations, the z-score is `0.0`.

## Score Weights

When turnover is enabled:

| Feature | Weight |
| --- | ---: |
| trend deviation | `0.60` |
| volatility regime | `0.25` |
| turnover | `0.15` |

When turnover is disabled:

| Feature | Weight |
| --- | ---: |
| trend deviation | `0.70` |
| volatility regime | `0.30` |

## Risk Value

The score is mapped to risk with a sigmoid:

```text
risk = sigmoid(score)
```

The stored risk value is always expected to be in `[0.0, 1.0]`.

## Risk States

| Range | State |
| --- | --- |
| `< 0.35` | `low` |
| `>= 0.35` and `< 0.65` | `neutral` |
| `>= 0.65` | `high` |

## Risk Levels

`/api/risk/levels` solves hypothetical BTC prices for target risk values from `0.0` to `1.0` in `0.025` increments.

The solver:

1. builds a context from the full OHLCV history;
2. keeps non-price components fixed for the latest day;
3. solves prices that would move the trend component to each target risk;
4. verifies target prices through the same risk model.

The latest risk from `/api/risk/latest` and `meta.current_risk` from `/api/risk/levels` are expected to match when the database is consistent.

## Interpretation Limits

The risk metric and risk levels are analytics outputs. They are not financial advice, investment advice, or trading recommendations. Risk levels are scenario estimates based on the current methodology and input data quality.
