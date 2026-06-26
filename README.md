# Bitcoin Risk Brief

Standalone EN/RU mini-product for testing demand around a daily Bitcoin risk signal.

## What It Includes

- TimescaleDB for BTC OHLCV, risk history, validation state, and brief snapshots.
- Python collector for one-time backfill and daily scheduled refresh.
- FastAPI backend with read-only risk/brief endpoints.
- React + Vite frontend with ECharts visualizations and EN/RU copy.
- `podman-compose` orchestration.

## Quick Start

```bash
cp .env.example .env
./scripts/manage.sh validate
./scripts/manage.sh start
./scripts/manage.sh migrate
./scripts/manage.sh backfill
```

Open: `http://localhost:3001`

## Commands

```bash
./scripts/manage.sh start       # build and start services
./scripts/manage.sh migrate     # apply idempotent bootstrap schema to an existing DB
./scripts/manage.sh stop        # stop services
./scripts/manage.sh logs        # follow logs
./scripts/manage.sh backfill    # fetch configured all-time BTC history once
./scripts/manage.sh run-now     # rolling refresh
./scripts/manage.sh test-python # local unit tests for risk and collector transform
```

## API

- `GET /api/health`
- `GET /api/risk/latest`
- `GET /api/risk/history?limit=2000`
- `GET /api/risk/levels`
- `GET /api/brief/latest`
- `POST /api/waitlist` with `{ "contact": "user@example.com", "locale": "en", "source": "landing" }`


## Risk Methodology

Risk uses `crypto-scout-canonical-v1`, aligned with `crypto-scout-analytics`: HLC3 price, EMA365 trend deviation, 30-day realized volatility, turnover as `ln(volume / market_cap)`, robust rolling z-scores with a 1460-day window and 365-day minimum, and canonical weights of `0.60/0.25/0.15` when turnover is enabled. `/api/risk/levels` solves target prices through the same risk function at `0.025` risk increments.

Canonical backfill now loads local BTC CSV history from `collector/btc-csv` for `2010-07-13` through `2013-12-31`, merges it with CoinGecko later history, validates the source stitch, and stores stitch diagnostics in `btc_risk_validation.validation_json`. If there is no source overlap and no explicit manual audit signoff, turnover is disabled while price-based features remain provisional. Daily refreshes recalculate risk over persisted OHLCV history plus the latest CoinGecko rows, so a successful all-time backfill keeps providing long context.

## Data Source Notes

The collector uses CoinGecko `coins/bitcoin/market_chart`. `COINGECKO_BACKFILL_DAYS=max` is intended for an all-history bootstrap where the active CoinGecko plan permits it. For lower tiers, set `COINGECKO_BACKFILL_DAYS=365` or use an API key with the allowed history range.

## Product Scope

This repo deliberately excludes auth, billing, broad chart catalogs, and alert delivery. It exists to validate whether users want a focused daily BTC risk product before expanding.

## Waitlist Storage

The frontend waitlist form stores leads in PostgreSQL via `POST /api/waitlist`. The backend accepts email addresses and Telegram handles, normalizes contacts to avoid duplicates, and stores locale/source metadata in `waitlist_leads`. This does not send notifications yet.
