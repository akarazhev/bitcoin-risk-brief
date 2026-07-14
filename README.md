# Bitcoin Risk Brief

Bitcoin Risk Brief is a standalone seven-locale mini-product for validating demand around a focused daily Bitcoin risk signal. It collects canonical BTC/USD daily data, computes a `crypto-scout-canonical-v1` risk metric, exposes read-only API endpoints, renders risk charts and risk levels, and stores waitlist leads in PostgreSQL.

## Current Status

Bitcoin Risk Brief is implementation-complete in this repository for the current local pre-traffic hardening items.
Repository files, commits, local tags, and recorded checks are implementation evidence; production readiness still
depends on recorded operator execution and public-host evidence. The project is still not publicly launched.

Local pre-deployment tooling and evidence completed in the repository:

- Scheduled public CoinMarketCap CSV refresh, local bundled BTC CSV evidence through 2026-07-09, and operator/manual CSV
  fallback workflows.
- Public payload cache warmup, USB Update And Install Kit V2, first-viewport model-price/OHLC display polish, local
  SEO/social metadata, and a local public privacy/terms/disclaimer note near the waitlist.
- Local public endpoint probe tooling for health/readiness/latest-risk assertions, local backup freshness/off-server copy
  checker tooling, local import provenance packet helper, and local launch snapshot packet helper for the final
  pre-traffic evidence window.
- Local Dependabot configuration, local dependency/license inventory evidence, local accessibility improvements/evidence,
  and local waitlist live-region/keyboard evidence.
- Latest local tooling evidence tag: `launch-snapshot-helper-local-evidence-2026-07-11` at commit
  `e1a4dc521343b8c48060358204ff5c9cfd7e1ecf`.

Repository-local bundled BTC CSV evidence recorded on 2026-07-11: commit
`8cbc6998c757f1ca1716277104e099b4705dfba9` is tagged
`btc-csv-through-2026-07-09-evidence-2026-07-11` and adds 11 canonical rows for 2026-06-29 through 2026-07-09 to
`collector/btc-csv/btc_usd_daily.csv`. The reviewed local incoming source was
`collector/btc-csv/incoming/coinmarketcap-public-btc-20260629-20260709.csv` with SHA-256
`38e9b0e8717013f217b93e7501aa3e216b1f989b52899cacff9e14c13f309d07`. This is local repository data evidence only; it
does not prove a production deployment, production database import, public-host freshness after this commit, full
production import provenance, launch readiness, or first traffic.

The public pilot hostname exists at `https://bitcoinriskbrief.minihub.app` and has evidence through 2026-07-12. The
2026-07-05 public `/api/readiness` HTTP 503 stale-data blocker is closed by later public evidence: 2026-07-07
post-deploy checks returned public readiness HTTP 200/fresh, the 2026-07-10 monitoring evidence recorded public
`/api/health`, `/api/readiness`, and `/api/risk/latest` healthy/current, and the 2026-07-11 backup-gated USB update
evidence recorded public readiness/latest checks passed. Latest recorded local public GET-only probe evidence is from
2026-07-12: public health/readiness/latest-risk checks passed with `latest_date=2026-07-11`, latest risk `0.2190`,
freshness policy `max_data_age_days:2`, and required cache headers present. This public probe does not prove external
monitor/provider configuration or alert delivery.

The 2026-07-12 AI-resolvable pre-traffic readiness sweep completed the remaining local/GET-only checks available from
this workspace without mutating production. Frontend unit tests passed 27 tests, the frontend production build passed,
the safe local mocked Playwright smoke passed 25 tests after local preview-server bind approval, and the approved public
GET-only probe passed for `/api/health`, `/api/readiness`, and `/api/risk/latest` with `latest_date=2026-07-11`, latest
risk `0.2190`, freshness policy `max_data_age_days:2`, and required cache headers present. The sweep did not deploy,
refresh/import data, call waitlist POST, change Cloudflare/routing, configure external providers, run first traffic, or
mutate production state.

The 2026-07-12 Launch Matrix / Accessibility / Public-Host QA pass recorded public desktop/mobile Chromium homepage
smoke, public-host axe automation, public metadata checks, visible privacy/disclaimer copy, and no waitlist POST. The
gate remains partial: manual keyboard, screen-reader/assistive-tech, physical-device/native browser, full WCAG/legal
accessibility, broader latency, fresh backup/off-server copy, direct import proof, launch snapshot, and first-traffic
evidence remain pending or unaccepted.

Backup-gated USB production update evidence recorded on 2026-07-11 targets commit
`86cb2dad889baf24a7464a105bbe2224f75b14ef` with evidence tag
`predeployment-readiness-reconciled-2026-07-11`. The server-reported update exit code was 0; the copied/off-server backup
freshness/checksum checker passed for timestamp basename `20260711T190355Z` as valid and fresh; public metadata/privacy
smoke passed; and desktop/mobile browser smoke passed without waitlist POSTs. No data refresh/import, external monitor
configuration, restore drill, launch snapshot, or first traffic is claimed by that evidence.

The 2026-07-08 browser-like waitlist smoke is closed for HTTP 201, no-store/no-cache headers, expected JSON response
shape, and aggregate-only server-side storage verification. The 2026-07-09 import provenance pass is partial, not
passed: public data/readiness/cache consistency aligned, but direct production source/archive proof and validation/import
metadata remain pending.

The 2026-07-12 sanitized support/contact and account recovery readiness evidence records the support email as created
and ready, the support contact category as a dedicated support mailbox with project-domain alias, deletion/unsubscribe
handling as manual requests through that dedicated support path, and the account recovery record as created outside Git
and current. Exact support addresses, provider details, account IDs, recovery text, private URLs, and secrets remain
outside Git.

The 2026-07-14 sanitized monitoring acceptance records the small operator-watched pilot monitoring blocker as
accepted/closed with limitation: Cloudflare Tunnel Health Alert is configured, a HetrixTools/external uptime monitor
provider category is recorded, and homepage availability monitoring is configured for the public homepage. This does not
claim full API readiness/freshness monitoring; dedicated external `/api/health` and `/api/readiness` monitors plus
explicit alert delivery evidence remain deferred before broader launch.

The project is still not publicly launched. Launch remains blocked by external/operational evidence gates, and public
readiness must be rechecked before any first traffic window because freshness is time-sensitive. Production host access
is unavailable from this workspace; future production updates still require operator deployment or update verification on
the selected production path, or an explicitly chosen replacement path.

Still external/operator before treating the pilot as publicly launched:

- Recheck public `/api/readiness` immediately before first traffic and keep scheduled public-download-first refresh
  evidence current on the production host.
- Keep USB deploy/update evidence current on future production updates, including project revision, health/readiness
  checks, and backup-gated mode when a fresh pre-update database dump is required.
- Keep the accepted small-pilot monitoring coverage active: Cloudflare Tunnel Health Alert plus external public homepage
  availability monitoring. Dedicated external `/api/health` and `/api/readiness` freshness monitors, stale-data
  after-window alerting, collector-failure alerts, backup freshness alerts, and explicit alert delivery evidence remain
  pending before broader launch.
- Create a fresh manual backup plus off-server copy before first traffic. Recurring scheduled backups, recurring
  off-server copies, and backup freshness monitoring are deferred until after the initial operator-watched pilot,
  conditional on the fresh manual backup/off-server copy passing before traffic. Restore drill remains deferred until a
  separate staging or intentionally empty restore target exists.
- Capture direct production import source/archive provenance outside the repository, including source snapshot, manifest,
  `sha256`, retrieval metadata, row count, covered range, expected tail, validation/readiness output, and cache evidence.
  The local `scripts/import_provenance_packet.py` helper is implemented/tested to build or validate sanitized manifests
  for future runs, but a real production packet and direct production validation/import metadata remain pending.
- Use `scripts/launch_snapshot_packet.py` during the final pre-traffic window to create or validate a sanitized local
  launch snapshot packet from already collected evidence. The helper is implemented/tested, but the actual launch
  snapshot packet, final pre-traffic public readiness evidence, production import provenance, fresh backup/off-server
  evidence, manual/native accessibility evidence, and first traffic remain pending. Dedicated API monitoring and alert
  delivery proof remain broader-launch limitations.
- Keep public-host privacy/terms/disclaimer and SEO/social metadata verification current after future deployments, and
  complete launch governance, browser/device, accessibility, release-feedback, and operational evidence gates.
- Keep the current Cloudflare Free-plan-compatible subset limited to a small operator-watched pilot; defer managed WAF
  and broader API burst-rate-limit controls until broader traffic or observed abuse risk.
- Capture the launch snapshot and run the first traffic test only after freshness and accepted launch gates allow it.

Recommended next production sequence before first traffic:

1. Complete the remaining operator-owned setup after the 2026-07-14 monitoring acceptance: fresh backup/off-server copy,
   manual/native accessibility checks, sanitized import proof, final public readiness/latest-risk checks, and final launch
   snapshot.
2. Deploy or update the selected production path, then record project revision, service status, health/readiness, and
   public-host metadata/privacy/accessibility smoke evidence.
3. Run the production refresh/import path and create the production import provenance packet from the real source,
   canonical output, validation/readiness, cache evidence, and deployment context.
4. Create a fresh backup, copy it off-server, run the backup freshness checker against both roots, and keep restore drill
   pending until a staging or intentionally empty restore target exists.
5. Keep the accepted small-pilot Tunnel health plus homepage monitor coverage active, run the public endpoint probe with
   the chosen freshness policy for final evidence, and defer dedicated external API monitors and alert delivery evidence
   to broader launch.
6. Verify public-host privacy/terms/disclaimer copy, SEO/social metadata, browser/device smoke, and the required manual
   keyboard, screen-reader/assistive-tech, and physical/native browser checks.
7. Create and validate the final sanitized launch snapshot packet from already collected evidence. Use
   [docs/launch-snapshot-evidence-packet-template.md](docs/launch-snapshot-evidence-packet-template.md) to prepare the
   packet outside Git first, then copy only sanitized final evidence into launch docs.
8. Run the operator-watched first traffic test only after all required blockers are completed, the final launch snapshot
   exists, and the only remaining limitations are the current accepted limitations, including the 2026-07-14 monitoring
   accepted limitation.

## Product Surface

- Daily BTC risk metric from `0.0` to `1.0`.
- Stable states: `low`, `neutral`, `high`.
- Historical risk chart.
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
