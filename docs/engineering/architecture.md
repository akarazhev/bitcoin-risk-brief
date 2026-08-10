# Architecture

Bitcoin Risk Brief is a compact four-service product built for validating demand for a daily BTC risk signal.

## Service Topology

| Service | Stack | Responsibilities |
| --- | --- | --- |
| `timescaledb` | TimescaleDB/PostgreSQL | Stores canonical OHLCV rows, computed risk rows, validation status, brief snapshots, waitlist leads, and Telegram publication claims. |
| `data-collector` | Python, asyncpg, APScheduler, httpx | Updates the BTC CSV when possible, imports the full CSV, computes risk, writes validation data, schedules daily runs, and can publish ready daily output to the Telegram channel. |
| `backend` | FastAPI, asyncpg | Serves health/readiness, risk, risk levels, brief, and waitlist endpoints. |
| `frontend` | React, Vite, ECharts, nginx | Renders the product UI and proxies `/api/*` requests to the backend. |

All services run under `podman-compose.yml` on the `app-network` bridge network.

## Runtime Flow

1. The collector reads `collector/btc-csv/btc_usd_daily.csv`.
2. If an operator runs `download-cmc-csv`, the collector fetches missing rows from CoinMarketCap's public historical-data endpoint, stages a CSV, validates it, and merges it only when the result is contiguous.
3. If an operator runs `import-cmc-csv`, the collector validates the staged CoinMarketCap historical CSV and merges it into the canonical CSV only when the result is contiguous.
4. If running in refresh mode and `COINMARKETCAP_API_KEY` is set, it asks CoinMarketCap for missing completed UTC days after the CSV tail.
5. Public downloads, downloaded rows, and API-fetched deltas must exactly match the expected contiguous daily date range.
6. Valid rows are merged into the CSV with atomic file replacement.
7. The full CSV is imported into TimescaleDB.
8. The risk series is recomputed from the full canonical source history.
9. Validation metadata and a latest brief snapshot are written.
10. When Telegram publication is configured, the collector publishes only after the import output is ready and records the result in the publication ledger.
11. Rows after the CSV tail are deleted from OHLCV, risk, and brief tables to prevent stale mixed-source data.
12. The backend serves API reads from TimescaleDB.
13. The frontend displays current risk, risk history, risk levels, brief text, and waitlist capture.

## Repository Layout

```text
backend/                 FastAPI application and risk methodology code
collector/               Python collector, downloaded/API CSV refresh, database writer, BTC CSV source
collector/btc-csv/       Canonical BTC/USD daily CSV
frontend/                React/Vite UI and nginx config
migrations/              Idempotent PostgreSQL/TimescaleDB schema
scripts/manage.sh        Local service/test helper
podman-compose.yml       Local multi-service orchestration
docs/                    Product, operations, methodology, API, and deployment docs
```

## Database Tables

| Table | Purpose |
| --- | --- |
| `btc_ohlcv_daily` | Canonical daily BTC OHLCV rows imported from CSV. |
| `btc_risk_daily` | One computed risk row per canonical source date. |
| `btc_risk_validation` | Latest validation summary and JSON diagnostics. |
| `brief_snapshots` | Latest daily brief payloads. |
| `risk_level_snapshots` | Latest persisted public risk-level payloads served by `/api/risk/levels`. |
| `waitlist_leads` | Normalized email or Telegram waitlist contacts. |
| `telegram_posts` | One claim per covered date for channel publication, confirmed with Telegram's returned message ID. |

`btc_ohlcv_daily` and `btc_risk_daily` are TimescaleDB hypertables keyed by `timestamp`.

`telegram_posts` rows begin as unconfirmed claims with `message_id` and `posted_at` set to `NULL`. A successful
Telegram response stores the message ID and confirmation time. A definitive Telegram rejection releases an
unconfirmed claim; an ambiguous delivery result retains it to prefer a missed post over a duplicate.

## Public Entry Point

The frontend nginx container is the public local entry point on `127.0.0.1:3001` by default. It serves static assets and proxies `/api/*` to the backend service.

Baseline security headers are added at the nginx entrypoint and on backend API responses.
