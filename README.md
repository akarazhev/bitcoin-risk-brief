# Bitcoin Risk Brief

Bitcoin Risk Brief is a standalone seven-locale mini-product for validating demand around a focused daily Bitcoin risk signal. It collects canonical BTC/USD daily data, computes a `crypto-scout-canonical-v1.1` risk metric, exposes read-only API endpoints, renders risk charts and risk levels, and stores waitlist leads in PostgreSQL.

## Current Status

Bitcoin Risk Brief is online at `https://bitcoinriskbrief.minihub.app/` and is in a small operator-watched pilot. The
2026-07-15 watched first-traffic observation completed for that pilot with `first_traffic_status=completed`. This is not
a broad public launch, paid launch, commercial-readiness claim, full WCAG/legal accessibility approval, broader
monitoring claim, or broader direct import provenance claim.

Current local repo state before this docs cleanup was verified as `HEAD=origin/main=a62216b`, with local tag
`first-traffic-pilot-evidence-2026-07-15` pointing at the same commit. The final launch snapshot was created and
validated outside Git before first traffic with basename `launch-snapshot-20260715T121952Z.json`; local tag
`final-launch-snapshot-evidence-2026-07-15` points at `aa2ac6a`.

First-traffic public evidence recorded on 2026-07-15:

- `GET /api/health`, `GET /api/readiness`, and `GET /api/risk/latest` passed.
- Readiness was current for the window: `latest_date=2026-07-14`, `covered_end=2026-07-14`, `row_count=5846`,
  `data_fresh=true`, freshness policy `max_age_days=2`, and `Cache-Control: no-store`.
- Latest risk was `0.2694028326125623`, `risk_state=low`, with cache/version headers present.
- The watched homepage observation loaded the public page, showed current risk/readiness and two visible chart canvases.
- No production waitlist POST was performed or claimed during the first-traffic run.

Current repository-local BTC CSV evidence tails at `2026-07-14`; tag
`btc-csv-through-2026-07-14-evidence-2026-07-15` points at `e204acc`. Repository CSV evidence supports the small-pilot
snapshot but does not replace broader direct production source/archive provenance.

The detailed evidence history has moved to [Production Evidence Log](docs/production-evidence-log.md). The current gate
register is [Production Readiness](docs/production-readiness.md).

Still external/operator before broader public launch:

- Recheck public `/api/readiness` and `/api/risk/latest` during future pilot windows and after production updates, and
  keep scheduled public-download-first refresh evidence current on the production host.
- Keep USB deploy/update evidence current on future production updates, including project revision, health/readiness
  checks, and backup-gated mode when a fresh pre-update database dump is required.
- Keep the accepted small-pilot monitoring coverage active: Cloudflare Tunnel Health Alert plus external public homepage
  availability monitoring. Dedicated external `/api/health` and `/api/readiness` freshness monitors, stale-data
  after-window alerting, collector-failure alerts, backup freshness alerts, and explicit alert delivery evidence remain
  pending before broader launch.
- Keep the 2026-07-15 fresh manual backup/off-server copy evidence available with the final launch snapshot and
  first-traffic evidence. Recurring scheduled backups, recurring off-server copies, and backup freshness monitoring are
  deferred until after the initial operator-watched pilot. Restore drill remains deferred until a separate staging or
  intentionally empty restore target exists.
- Capture direct broader-launch production import source/archive provenance outside the repository, including source
  snapshot, manifest, `sha256`, retrieval metadata, row count, covered range, expected tail, validation/readiness output,
  and cache evidence. Public readiness/latest-risk plus the BTC CSV evidence tag support the small-pilot snapshot, but a
  broader real production packet and direct production validation/import metadata remain pending.
- Preserve the final sanitized launch snapshot packet evidence separately from first-traffic evidence. Dedicated API
  monitoring, alert delivery proof, broader direct import provenance, and a true screen-reader/manual assistive-tech pass
  remain broader-launch limitations.
- Keep public-host privacy/terms/disclaimer and SEO/social metadata verification current after future deployments, and
  continue post-traffic feedback review plus broader governance, accessibility, and operational evidence gates.
- Keep the current Cloudflare Free-plan-compatible subset limited to a small operator-watched pilot; defer managed WAF
  and broader API burst-rate-limit controls until broader traffic or observed abuse risk.

Current first-traffic status:

1. Keep the created and validated final sanitized launch snapshot packet evidence available outside Git; do not treat it
   as the first-traffic observation itself.
2. The 2026-07-15 watched first-traffic observation completed after operator approval from the continuation request;
   `first_traffic_status=completed` for the small pilot.
3. Keep future pilot-window public readiness/latest-risk checks current, especially after future production updates.
4. Keep accepted limitations explicit: broader direct import provenance, dedicated API monitoring, alert delivery proof,
   restore drill, true screen-reader/manual assistive-tech evidence, full WCAG/legal accessibility, and broader launch
   claims remain unclaimed.

## Product Surface

- Daily BTC risk metric from `0.0` to `1.0`.
- Stable states: `low`, `neutral`, `high`.
- Historical risk chart, shown as a two-year public UI window.
- Risk-level price ladder at `0.025` risk increments.
- Latest completed daily candle context: `Model price` is the HLC3 value; `Low` and `High` are daily candle values when
  the matching OHLCV row exists. These fields are not live spot-price ticks or close-only pricing.
- Daily brief payload in English, Russian, Simplified Chinese, German, French, Spanish, and Arabic.
- Waitlist form for email or Telegram handles.
- Compact privacy/terms/disclaimer note near the waitlist, verified in the 2026-07-11 public browser smoke.
- Readiness endpoint for deployment probes and alerts.

## Architecture

| Service | Stack | Purpose |
| --- | --- | --- |
| `timescaledb` | TimescaleDB/PostgreSQL | BTC OHLCV, risk rows, validation state, brief snapshots, waitlist leads |
| `data-collector` | Python, asyncpg, APScheduler, httpx | Daily CSV refresh, full CSV import, risk recomputation |
| `backend` | FastAPI, asyncpg | API, readiness, waitlist storage, risk and brief reads |
| `frontend` | React, Vite, ECharts, nginx | Public seven-locale interface and API proxy |

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
  offline package mirror. A 2026-07-11 backup-gated USB production update verification is recorded for commit
  `86cb2dad889baf24a7464a105bbe2224f75b14ef`; future production updates still need current sanitized evidence for the
  selected revision, health/readiness checks, backup-gated mode when required, and no secrets staged.

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
- [Pilot Learning Loop](docs/pilot-learning-loop.md)
- [Marketing and Growth](docs/marketing-and-growth.md)
- [Ubuntu and Cloudflare Tunnel Deployment](docs/deploy-ubuntu-cloudflare.md)
- [Production Readiness](docs/production-readiness.md)
- [Production Evidence Log](docs/production-evidence-log.md)
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
- `GET /api/risk/history?limit=730`
- `GET /api/risk/levels`
- `GET /api/brief/latest`
- `POST /api/waitlist`

Detailed response shapes are documented in [API Reference](docs/api-reference.md).

## Risk Methodology

Risk uses `crypto-scout-canonical-v1.1`, aligned with `crypto-scout-analytics`: HLC3 price, EMA365 trend deviation, 30-day realized volatility, turnover as `ln(volume / market_cap)`, robust rolling z-scores with a 1460-day window and 365-day minimum, and canonical weights of `0.60/0.25/0.15` when turnover is enabled.

Risk levels are solved through the same risk model at `0.025` risk increments. They are scenario outputs, not trading instructions. The API keeps the full `0.00` to `1.00` ladder; the public chart displays the practical `0.20` to `0.80` window so extreme solver endpoints do not dominate the price scale.

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
- `VITE_TURNSTILE_SITE_KEY` to the public sitekey in the operator-controlled Managed-widget record
- `TURNSTILE_SECRET` to the matching private secret in operator-controlled storage
- `TURNSTILE_HOSTNAMES=bitcoinriskbrief.minihub.app`

The site key is a frontend build input and the secret is backend runtime configuration. Do not commit either value. The
Turnstile integration has not yet been USB-deployed or production-validated; before that operator-run update, edit the
server `.env` and use `bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app`. The server `.env` is
preserved by the update process and excluded from the USB kit.

## Disclaimer

Bitcoin Risk Brief is an analytics and research product. It is not financial advice, investment advice, or a trading recommendation.
