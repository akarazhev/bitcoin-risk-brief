# Bitcoin Risk Brief

Bitcoin Risk Brief is a standalone EN/RU mini-product for validating demand around a focused daily Bitcoin risk signal. It collects canonical BTC/USD daily data, computes a `crypto-scout-canonical-v1` risk metric, exposes read-only API endpoints, renders risk charts and risk levels, and stores waitlist leads in PostgreSQL.

## Current Status

The product now has a live production-pilot hostname at `https://bitcoinriskbrief.minihub.app`. As of 2026-07-01,
public GET smoke checks through Cloudflare pass for health, readiness, latest risk, and conditional `ETag`
revalidation. The local stack has also been verified with containerized `run-now`, readiness checks, security headers,
full Python tests, frontend tests, frontend build, compose validation, and API smoke checks.

External production tasks still required before treating the pilot as publicly launched:

- Confirm the production host runbook, `.env`, and data-refresh workflow are the documented source of truth.
- Configure scheduled backups for TimescaleDB data and the canonical BTC CSV, copy them off-server, and run a restore drill.
- Configure alerts on `/api/readiness` and collector failures.
- Complete a short browser/device pass on the public hostname.
- Run a deliberate waitlist smoke test and first traffic test.
- Decide whether the current Cloudflare Free-plan edge subset is enough for launch or whether to upgrade for managed WAF
  and broader API burst-rate-limit entitlement.

## Product Surface

- Daily BTC risk metric from `0.0` to `1.0`.
- Stable states: `low`, `neutral`, `high`.
- Historical risk chart.
- Risk-level price ladder at `0.025` risk increments.
- Daily brief payload in English and Russian.
- Waitlist form for email or Telegram handles.
- Readiness endpoint for deployment probes and alerts.

## Architecture

| Service | Stack | Purpose |
| --- | --- | --- |
| `timescaledb` | TimescaleDB/PostgreSQL | BTC OHLCV, risk rows, validation state, brief snapshots, waitlist leads |
| `data-collector` | Python, asyncpg, APScheduler, httpx | Daily CSV refresh, full CSV import, risk recomputation |
| `backend` | FastAPI, asyncpg | API, readiness, waitlist storage, risk and brief reads |
| `frontend` | React, Vite, ECharts, nginx | Public EN/RU interface and API proxy |

The stack is orchestrated with `podman-compose`.

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
./scripts/manage.sh migrate     # apply idempotent schema to an existing DB
./scripts/manage.sh stop        # stop services
./scripts/manage.sh logs        # follow logs
./scripts/manage.sh backfill    # import canonical local BTC CSV once
./scripts/manage.sh run-now     # refresh BTC CSV from CMC if configured, then import
./scripts/manage.sh download-cmc-csv 2026-06-28
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv 2026-06-28
./scripts/manage.sh test-python # backend and collector unit tests
```

## Documentation

- [Documentation Index](docs/README.md)
- [Architecture](docs/architecture.md)
- [Data Pipeline](docs/data-pipeline.md)
- [Risk Methodology](docs/risk-methodology.md)
- [API Reference](docs/api-reference.md)
- [Waitlist](docs/waitlist.md)
- [Security and Privacy](docs/security-and-privacy.md)
- [Operations](docs/operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](docs/deploy-ubuntu-cloudflare.md)
- [Production Readiness](docs/production-readiness.md)
- [Testing and Quality](docs/testing-and-quality.md)

## Data Source

The canonical source is `collector/btc-csv/btc_usd_daily.csv`. The collector treats this file as durable local source of truth. Operators can refresh it without a paid API account by running `./scripts/manage.sh download-cmc-csv`, which fetches missing Bitcoin rows from CoinMarketCap's public historical-data endpoint, stages a CSV under `collector/btc-csv/incoming/`, validates it, and imports it. If that public endpoint is unavailable, operators can still stage a CSV downloaded from the CoinMarketCap page and run `./scripts/manage.sh import-cmc-csv`.

If `COINMARKETCAP_API_KEY` is configured, scheduled collector runs can also fetch missing completed UTC days from the official CoinMarketCap OHLCV Historical endpoint. If the key is empty, remote API refresh is skipped and the current CSV is still imported and used for risk recomputation.

## API Overview

- `GET /api/health`
- `GET /api/readiness`
- `GET /api/risk/latest`
- `GET /api/risk/history?limit=2000`
- `GET /api/risk/levels`
- `GET /api/brief/latest`
- `POST /api/waitlist`

Detailed response shapes are documented in [API Reference](docs/api-reference.md).

## Risk Methodology

Risk uses `crypto-scout-canonical-v1`, aligned with `crypto-scout-analytics`: HLC3 price, EMA365 trend deviation, 30-day realized volatility, turnover as `ln(volume / market_cap)`, robust rolling z-scores with a 1460-day window and 365-day minimum, and canonical weights of `0.60/0.25/0.15` when turnover is enabled.

Risk levels are solved through the same risk model at `0.025` risk increments. They are scenario outputs, not trading instructions.

## Production Configuration

Use `.env.production.example` as the production template. Do not deploy with `.env.example` defaults.

Production must set at least:

- `APP_ENV=production`
- `DB_PASSWORD` to a long random secret
- `CORS_ORIGINS` to the public HTTPS origin
- `COINMARKETCAP_API_KEY` only if the optional API refresh path is used; otherwise leave it empty and use the automatic or manual public CSV workflow
- `DATA_FRESHNESS_MAX_AGE_DAYS` to the accepted freshness threshold
- `WAITLIST_RATE_LIMIT_PER_HOUR` to the expected traffic profile
- `FRONTEND_BIND_IP=127.0.0.1` when Cloudflare Tunnel is the only public ingress

## Disclaimer

Bitcoin Risk Brief is an analytics and research product. It is not financial advice, investment advice, or a trading recommendation.
