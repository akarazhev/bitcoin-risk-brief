# Canonical Risk Methodology Design

**Goal:** align Bitcoin Risk Brief risk math and price-risk levels with the canonical Bitcoin methodology used by `crypto-scout-analytics`.

## Scope

This pass makes the mini-product methodologically consistent at the calculation layer:

- Use HLC3 price, EMA365 trend deviation, 30-day realized volatility, and turnover as `ln(volume / market_cap)`.
- Use robust rolling z-scores with a 1460-day window, 365-day minimum, and clipping to `[-6, 6]`.
- Use canonical weights: `0.60 trend + 0.25 volatility + 0.15 turnover` when turnover is enabled, and `0.70 trend + 0.30 volatility` when turnover is disabled.
- Build risk levels by solving hypothetical prices through the same risk function, not by applying a heuristic multiplier to the current price.
- Recompute risk over the accumulated persisted OHLCV history plus the latest CoinGecko refresh rows, so daily refreshes do not discard older context after a backfill.

## Explicit Non-Goals

Full data-source parity is not included in this pass. The mini-product will still use CoinGecko-derived OHLCV rows and persisted local history. It will not yet copy the early 2010-2013 BTC CSV history, full source stitch validation, or manual audit workflow from `crypto-scout-analytics`.

## API Compatibility

`GET /api/risk/levels` keeps returning `data` as an array of `{ risk, price_usd }` for the frontend. Methodology metadata moves into `meta`, including the current price, current risk, turnover mode, risk step, and methodology version.

## Data Flow

1. Collector fetches current CoinGecko rows.
2. Collector writes refreshed OHLCV rows.
3. Collector loads all persisted OHLCV rows.
4. Collector calculates risk over the full merged history.
5. Collector writes risk rows, validation metadata, and the latest brief snapshot.
6. Backend level endpoint loads source OHLCV rows and calculates risk levels through the canonical solver.

## Risks

With only 365 days of CoinGecko data, early points remain neutral because robust z-scores require 365 observations. The all-time backfill path is still the correct way to populate enough context for useful canonical outputs.
