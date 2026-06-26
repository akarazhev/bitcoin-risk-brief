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
./scripts/manage.sh backfill
```

Open: `http://localhost:3001`

## Commands

```bash
./scripts/manage.sh start       # build and start services
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

## Data Source Notes

The collector uses CoinGecko `coins/bitcoin/market_chart`. `COINGECKO_BACKFILL_DAYS=max` is intended for an all-history bootstrap where the active CoinGecko plan permits it. For lower tiers, set `COINGECKO_BACKFILL_DAYS=365` or use an API key with the allowed history range.

## Product Scope

This repo deliberately excludes auth, billing, broad chart catalogs, and alert delivery. It exists to validate whether users want a focused daily BTC risk product before expanding.
