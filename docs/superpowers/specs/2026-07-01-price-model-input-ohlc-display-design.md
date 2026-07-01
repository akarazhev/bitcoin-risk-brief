# Price Model Input OHLC Display Design

> Status: future-facing UI/API polish. Last reviewed 2026-07-01. This does not change
> `crypto-scout-canonical-v1`; it clarifies how the latest completed daily candle is displayed in the first viewport.

## Goal

Make the `BTC price model input` block more transparent by showing the model price together with the daily low and high
that contributed to the latest risk observation.

The user should be able to see that the risk value is based on a completed daily candle, not an unexplained live spot
price.

## Current Behavior

`/api/risk/latest` returns `price_usd`, and the frontend renders it under `BTC price model input`.

In the current backend, `price_usd` is serialized from `btc_risk_daily.price_hlc3`. That value is the HLC3 model price:

```text
HLC3 = (high + low + close) / 3
```

The latest daily open, high, low, close, volume, market cap, and circulating supply already exist in
`btc_ohlcv_daily`, but `/api/risk/latest` does not currently return the daily high or low values.

## Recommended UI

Replace the single value in the first metrics strip with a compact grouped display:

```text
BTC price model input

Model price    Low        High
$58,948        $58,xxx    $61,xxx
```

English labels:

- `Model price`
- `Low`
- `High`

Russian labels:

- `Цена модели`
- `Мин.`
- `Макс.`

Use `High` and `Low`, not `high shadow` or `low shadow`. Candle shadow or wick terminology would be misleading here
because the product is not showing wick length; it is showing the daily candle's absolute high and low.

## API Shape

Keep `price_usd` as a backwards-compatible alias for the existing HLC3 model price.

Add explicit fields to the latest risk payload:

```json
{
  "data": {
    "price_usd": 58948.0,
    "model_price_usd": 58948.0,
    "low_usd": 58000.0,
    "high_usd": 61584.0
  }
}
```

`model_price_usd` makes the meaning clear for new clients. `price_usd` remains so the current frontend, brief builder,
and existing API consumers do not break.

The daily low and high must come from the same completed daily candle as the latest risk timestamp. Do not mix a live
intraday high/low with a completed daily risk value.

## Data Flow

The backend should build the latest response by joining or pairing:

- latest row from `btc_risk_daily`;
- matching row from `btc_ohlcv_daily` by timestamp.

If the matching OHLCV row is missing, the API can still return the risk point with `model_price_usd` and `price_usd`, but
the frontend should hide the Low/High sub-values rather than showing zeroes or stale values.

## Frontend Behavior

The first metric card should remain compact and scannable:

- title centered or visually aligned over the three values;
- three fixed-width value groups on desktop;
- responsive wrapping or a two-row grid on small mobile screens;
- no overlap with the updated/readiness and risk-change cells;
- no extra explanation text in the first viewport.

The methodology section can continue to explain that the model price is HLC3.

## Non-Goals

This design does not include:

- changing the risk formula;
- adding 1h or 4h candles;
- showing live intraday values;
- adding `Close` to the first-viewport metric group;
- showing upper/lower wick length;
- changing `/api/risk/history` unless a later chart or API use case needs historical OHLC display.

## Testing

Implementation should include:

- backend test that `/api/risk/latest` or its repository helper pairs latest risk with the matching OHLCV row;
- backend fallback test for a missing OHLCV match;
- frontend test that renders `Model price`, `Low`, and `High` when fields are present;
- frontend test that does not render empty or misleading Low/High values when fields are missing;
- API reference update for the new fields;
- browser/mobile smoke pass to confirm the metrics strip does not overflow.

## Phase Fit

This belongs in Phase 8 launch polish because it improves first-viewport clarity before active traffic without changing
the methodology or broadening the product into a dashboard.

It should not block launch if the current single-value display is accepted, but if implemented before launch it should be
verified together with the browser/device QA pass.
