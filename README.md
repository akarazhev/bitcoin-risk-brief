# Bitcoin Risk Brief

Bitcoin Risk Brief is a standalone EN/RU mini-product for validating demand around a focused daily Bitcoin risk signal. It collects canonical BTC/USD daily data, computes a `crypto-scout-canonical-v1` risk metric, exposes read-only API endpoints, renders risk charts and risk levels, and stores waitlist leads in PostgreSQL.

## Current Status

Bitcoin Risk Brief is locally implementation-complete for the current pre-traffic hardening items: scheduled public
CoinMarketCap CSV refresh, public payload cache warmup, USB Update And Install Kit V2, and first-viewport
model-price/OHLC display polish. These are local repository states, not proof that production has been updated.

The public pilot hostname exists at `https://bitcoinriskbrief.minihub.app` and has historical smoke-test evidence.
However, the latest documented public snapshot on 2026-07-05 showed public `/api/readiness` returning HTTP 503 because
production BTC data was stale (`latest_date: 2026-06-30`, `data_age_days: 4`, `max_age_days: 2`). Do not treat the
project as publicly launched until public `/api/readiness` returns HTTP 200 again and the remaining production
operations gates are completed or explicitly accepted.

Production deployment is unavailable from this workspace. Local changes made after the current production snapshot still
require operator deployment or update verification on the selected production path under
`/srv/projects/bitcoin-risk-brief`, or an explicitly chosen replacement path.

External production tasks still required before treating the pilot as publicly launched:

- Restore fresh production data and verify public `/api/readiness` returns HTTP 200.
- Deploy and verify the scheduled public CoinMarketCap refresh and public cache warmup on the production host.
- Prepare a real USB kit v2 package and run the backup-gated production update wrapper, or verify the selected deployment
  path another way.
- Configure scheduled backups for TimescaleDB data and the canonical BTC CSV, copy them off-server, and run a restore
  drill.
- Configure alerts on `/api/readiness`, stale data after the nightly update window, and collector failures.
- Run a deliberate waitlist smoke test and verify server-side storage with no cached response.
- Capture production import provenance outside the repository.
- Complete browser/device and focused accessibility checks on the public hostname.
- Decide whether the current Cloudflare Free-plan edge subset is enough for first traffic or whether to upgrade for
  managed WAF and broader API burst-rate-limit entitlement.
- Run the first traffic test only after freshness and accepted launch gates allow it.

## Product Surface

- Daily BTC risk metric from `0.0` to `1.0`.
- Stable states: `low`, `neutral`, `high`.
- Historical risk chart.
- Risk-level price ladder at `0.025` risk increments.
- Latest completed daily candle context: `Model price` is the HLC3 value; `Low` and `High` are daily candle values when
  the matching OHLCV row exists. These fields are not live spot-price ticks or close-only pricing.
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
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
./scripts/manage.sh test-python # backend and collector unit tests
```

## Operational Notes

- `warm-public-cache` warms the standard public read payloads through normal GET routes against a local or private
  origin after readiness is healthy. Production latency benefit still requires deployment, fresh readiness, and
  post-deploy operator execution.
- USB Update And Install Kit V2 packages a filtered project snapshot and update wrapper for the selected local-server
  deployment path. It does not include production secrets, container images, dependency caches, backups, or a full
  offline package mirror. Production benefit still requires preparing a real USB package and running the backup-gated
  update on the production host.

## Development Workflow

Use `AGENTS.md` as the agent-facing source for repository rules. For human-driven work with Codex, use this sequence:

1. Define the change in concrete terms: expected behavior, affected area, constraints, and verification commands.
2. For ambiguous or multi-step work, ask Codex to use `/plan` before implementation.
3. For longer implementation sessions, set a `/goal` with clear completion criteria.
4. Expect Codex to apply relevant Superpowers skills before implementation, such as planning, test-driven development,
   systematic debugging, verification, or code-review workflows.
5. Review the diff while work is in progress, especially if multiple files or services are touched. Avoid running
   parallel Codex threads against the same files.
6. Before accepting the work, require the relevant checks:
   - Python/backend/collector changes: `./scripts/manage.sh test-python`
   - Frontend behavior or build changes: `npm test --prefix frontend` and `npm run build --prefix frontend`
   - Compose or operational changes: `./scripts/manage.sh validate`
   - Documentation-only changes: targeted diff/read review is enough; runtime tests are not required.
7. Use `/review` before finalizing substantial diffs or PR-ready work, then address confirmed findings and rerun the
   relevant checks.

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

Scheduled collector runs target the last completed UTC day. With an empty `COINMARKETCAP_API_KEY`, a stale canonical
CSV is refreshed through the public CoinMarketCap download path first; if the CSV is already current, the collector
imports the existing CSV and recomputes risk. The optional official API refresh is used only when an API key is
configured, and manual `import-cmc-csv` remains the operator fallback when public automation is unavailable.

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
