# Bitcoin Risk Brief

Bitcoin Risk Brief is a standalone EN/RU mini-product for validating demand around a focused daily Bitcoin risk signal. It collects canonical BTC/USD daily data, computes a `crypto-scout-canonical-v1` risk metric, exposes read-only API endpoints, renders risk charts and risk levels, and stores waitlist leads in PostgreSQL.

## Current Status

Bitcoin Risk Brief is implementation-complete in this repository for the current pre-traffic hardening items: scheduled
public CoinMarketCap CSV refresh, public payload cache warmup, USB Update And Install Kit V2, first-viewport
model-price/OHLC display polish, local SEO/social metadata, and a local public privacy/terms/disclaimer note near the
waitlist. Repository files, commits, local tags, and recorded checks are implementation evidence; production readiness
depends on recorded operator and public-host evidence.

The public pilot hostname exists at `https://bitcoinriskbrief.minihub.app` and has evidence through 2026-07-10. The
2026-07-05 public `/api/readiness` HTTP 503 stale-data blocker is closed by later public evidence: 2026-07-07
post-deploy checks returned public readiness HTTP 200/fresh, and the 2026-07-10 monitoring evidence recorded public
`/api/health`, `/api/readiness`, and `/api/risk/latest` healthy/current. Latest recorded public readiness evidence is
from 2026-07-10: HTTP 200, `status: ready`, `data_fresh: true`, `latest_date: 2026-07-09`,
`covered_end: 2026-07-09`, `data_age_days: 1`, `max_age_days: 2`, and `row_count: 5841`.

The 2026-07-08 browser-like waitlist smoke is closed for HTTP 201, no-store/no-cache headers, expected JSON response
shape, and aggregate-only server-side storage verification. The 2026-07-09 import provenance pass is partial, not
passed: public data/readiness/cache consistency aligned, but direct production source/archive proof and validation/import
metadata remain pending.

The project is still not publicly launched. Launch remains blocked by external/operational evidence gates, and public
readiness must be rechecked before any first traffic window because freshness is time-sensitive. Production host access
is unavailable from this workspace; future production updates still require operator deployment or update verification on
the selected production path, or an explicitly chosen replacement path.

External production tasks still required before treating the pilot as publicly launched:

- Recheck public `/api/readiness` immediately before first traffic and keep scheduled public-download-first refresh
  evidence current on the production host.
- Keep USB deploy/update evidence current on future production updates, including project revision, health/readiness
  checks, and backup-gated mode when a fresh pre-update database dump is required.
- Configure external monitors and alerts for `/api/health`, `/api/readiness`, stale data after the nightly update
  window, collector failures, Cloudflare Tunnel health, and alert delivery.
- Configure recurring scheduled backups, recurring off-server copies, and backup freshness monitoring; defer the restore
  drill until a separate staging or intentionally empty restore target exists.
- Capture direct production import source/archive provenance outside the repository, including source snapshot, manifest,
  `sha256`, retrieval metadata, row count, covered range, expected tail, validation/readiness output, and cache evidence.
- Verify the local privacy/terms/disclaimer note and SEO/social metadata on the public host, and complete launch
  governance, browser/device, accessibility, release-feedback, and operational evidence gates.
- Decide whether the current Cloudflare Free-plan edge subset is enough for first traffic or whether to upgrade for
  managed WAF and broader API burst-rate-limit entitlement.
- Capture the launch snapshot and run the first traffic test only after freshness and accepted launch gates allow it.

## Product Surface

- Daily BTC risk metric from `0.0` to `1.0`.
- Stable states: `low`, `neutral`, `high`.
- Historical risk chart.
- Risk-level price ladder at `0.025` risk increments.
- Latest completed daily candle context: `Model price` is the HLC3 value; `Low` and `High` are daily candle values when
  the matching OHLCV row exists. These fields are not live spot-price ticks or close-only pricing.
- Daily brief payload in English and Russian.
- Waitlist form for email or Telegram handles.
- Compact privacy/terms/disclaimer note near the waitlist, implemented locally and pending public-host verification.
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
  origin after readiness is healthy. Post-deploy public smoke has recorded fast Cloudflare HIT behavior after warmup, but
  operators must rerun or verify warmup after validation-version changes and must not use it to mask stale readiness.
- USB Update And Install Kit V2 packages a filtered project snapshot and update wrapper for the selected local-server
  deployment path. It does not include production secrets, container images, dependency caches, backups, or a full
  offline package mirror. A 2026-07-07 USB deploy verification is recorded; future production updates still need current
  sanitized evidence for the selected revision, health/readiness checks, backup-gated mode when required, and no secrets
  staged.

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
