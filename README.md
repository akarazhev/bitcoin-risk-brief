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
./scripts/manage.sh backfill    # import canonical local BTC CSV once
./scripts/manage.sh run-now     # refresh BTC CSV from CMC if configured, then import
./scripts/manage.sh test-python # local unit tests for risk and collector transform
```

## API

- `GET /api/health`
- `GET /api/readiness`
- `GET /api/risk/latest`
- `GET /api/risk/history?limit=2000`
- `GET /api/risk/levels`
- `GET /api/brief/latest`
- `POST /api/waitlist` with `{ "contact": "user@example.com", "locale": "en", "source": "landing" }`


## Risk Methodology

Risk uses `crypto-scout-canonical-v1`, aligned with `crypto-scout-analytics`: HLC3 price, EMA365 trend deviation, 30-day realized volatility, turnover as `ln(volume / market_cap)`, robust rolling z-scores with a 1460-day window and 365-day minimum, and canonical weights of `0.60/0.25/0.15` when turnover is enabled. `/api/risk/levels` solves target prices through the same risk function at `0.025` risk increments.

The canonical source is `collector/btc-csv/btc_usd_daily.csv`, currently covering daily BTC/USD rows from `2010-07-13` onward. `./scripts/manage.sh backfill` imports the whole CSV into TimescaleDB and recalculates every risk row. `./scripts/manage.sh run-now` and the scheduled collector first try to fetch missing completed UTC days from CoinMarketCap OHLCV Historical, append them to the host-mounted CSV, then import the full CSV and recalculate risk. If `COINMARKETCAP_API_KEY` is empty, remote refresh is skipped and the existing CSV is still imported.

## Data Source Notes

The collector uses the official CoinMarketCap OHLCV Historical API (`/v2/cryptocurrency/ohlcv/historical`, `id=1`, `time_period=daily`) only for daily deltas after the local CSV tail. The CSV is bind-mounted into the `data-collector` container at `/app/collector/btc-csv`, so scheduled container runs update the repository copy instead of an ephemeral image file.

## Production Readiness

Use `.env.production.example` for deploy configuration and `docs/production-readiness.md` for the release checklist. The backend exposes `/api/readiness` for deployment probes and alerting.

## Product Scope

This repo deliberately excludes auth, billing, broad chart catalogs, and alert delivery. It exists to validate whether users want a focused daily BTC risk product before expanding.

## Waitlist Storage

The frontend waitlist form stores leads in PostgreSQL via `POST /api/waitlist`. The backend accepts email addresses and Telegram handles, normalizes contacts to avoid duplicates, and stores locale/source metadata in `waitlist_leads`. This does not send notifications yet.
