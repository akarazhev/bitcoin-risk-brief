# Canonical Risk Methodology Design

> Status: completed. Last reviewed 2026-06-30. The methodology and risk-level solver are implemented, but the
> CoinGecko data-flow notes from the original design are superseded by the canonical CoinMarketCap CSV source.

**Goal:** align Bitcoin Risk Brief risk math and price-risk levels with the canonical Bitcoin methodology used by `crypto-scout-analytics`.

## Scope

This pass makes the mini-product methodologically consistent at the calculation layer:

- Use HLC3 price, EMA365 trend deviation, 30-day realized volatility, and turnover as `ln(volume / market_cap)`.
- Use robust rolling z-scores with a 1460-day window, 365-day minimum, and clipping to `[-6, 6]`.
- Use canonical weights: `0.60 trend + 0.25 volatility + 0.15 turnover` when turnover is enabled, and `0.70 trend + 0.30 volatility` when turnover is disabled.
- Build risk levels by solving hypothetical prices through the same risk function, not by applying a heuristic multiplier to the current price.
- Recompute risk over the full canonical CSV-backed OHLCV history on each import, so daily refreshes do not discard older
  context after a backfill.

## Explicit Non-Goals

Full data-source parity was addressed by replacing runtime CoinGecko collection with the canonical CoinMarketCap-style
BTC CSV. Current runtime behavior is documented in `docs/data-pipeline.md`.

## API Compatibility

`GET /api/risk/levels` keeps returning `data` as an array of `{ risk, price_usd }` for the frontend. Methodology metadata moves into `meta`, including the current price, current risk, turnover mode, risk step, and methodology version.

## Data Flow

1. Collector loads `collector/btc-csv/btc_usd_daily.csv`.
2. Optional refresh paths merge missing completed UTC days into the CSV only after contiguous-range validation.
3. Collector imports the full CSV into TimescaleDB.
4. Collector calculates risk over the full canonical history.
5. Collector writes risk rows, validation metadata, and the latest brief snapshot.
6. Backend level endpoint loads source OHLCV rows and calculates risk levels through the canonical solver.

## Risks

The canonical CSV must remain contiguous and long enough for robust z-score history. If the CSV is truncated or stale,
readiness and validation should fail before the public page treats the signal as current.
