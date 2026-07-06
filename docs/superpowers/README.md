# Superpowers Docs Index

This directory is an implementation-history archive for agent-assisted specs and plans. It is not the primary runtime
documentation source. For current behavior, use the core docs in `docs/README.md`.

Unchecked boxes inside files marked completed, historical, or superseded are original plan tracking, not current TODOs.

Last reviewed: 2026-07-06.

## Current Implementation Summary

- The product is a four-service Podman Compose stack: TimescaleDB, `data-collector`, FastAPI `backend`, and React/Vite
  `frontend`.
- `collector/btc-csv/btc_usd_daily.csv` is the canonical BTC/USD source. CoinGecko runtime collection has been removed.
- Supported refresh paths are `backfill`, `run-now` with optional CoinMarketCap API key, scheduled public-download-first
  refresh, `download-cmc-csv`, and manual staged `import-cmc-csv`. Public production freshness remains blocked until
  `/api/readiness` returns HTTP 200 again.
- Every import recalculates the full risk series, writes validation and brief snapshots, and deletes derived database
  rows after the CSV tail.
- The public frontend fetches readiness, latest risk, history, levels, brief, and waitlist endpoints. It renders
  readiness/freshness, methodology metadata, no-advice disclaimer, and nearest `0.35`/`0.65` threshold callouts.
- The latest risk payload/display has local explicit model-price/OHLC polish: `model_price_usd` is the HLC3 model price,
  and nullable `low_usd`/`high_usd` expose daily candle bounds when the matching OHLCV row exists. Production visibility
  still requires deploy.
- Public read endpoints use backend cache headers and validation-versioned `ETag`s. `POST /api/waitlist` is no-store and
  application-rate-limited.
- Standard public read cache warmup is implemented locally for startup and the `warm-public-cache` operator command.
  Production benefit requires deploy, healthy readiness, local/private-origin execution, and post-deploy measurement.
- Server-kit scripts live under `server-kit/` and include bootstrap, optional `cloudflared` install, deploy, user service
  enablement, health check, debug helpers, and a USB update wrapper.
- USB kit v2 has local workstation packaging and a server-side backup-before-update gate in the repository; it is not a
  full offline deployment artifact and does not package secrets, backups, dependency caches, build output, container
  images, or package mirrors. Production use remains pending.
- The documentation and portfolio presentation pass is tracked by
  `plans/2026-07-06-documentation-portfolio-presentation-implementation.md`; it is for a private or portfolio
  repository, not an open-source community launch or launch-ready claim.
- A launch operations and governance checklist is planned for privacy/terms, waitlist handling, credential ownership,
  resource monitoring, accessibility, metadata, data-source terms, dependency maintenance, and incident response.
- A release feedback and operational evidence checklist is planned to capture decision memory, first-user feedback,
  contact handling, dependency-license review, and launch/restore evidence without creating a new product phase.
- A data correction and service-target policy is planned for bad CSV/import/risk incidents, correction notes, cache
  safety, freshness, RPO/RTO, and pilot downtime boundaries.
- Import provenance and source archive evidence is planned for production data imports: source snapshot, `sha256`,
  retrieval method, row count, covered range, validation/readiness output, and cache evidence.
- Deferred Phase 9 gates are planned for email/Telegram outreach, paid beta or license experiments, account recovery,
  synthetic journey monitoring, and public trust artifacts.
- A deferred API/DB change-management gate is planned for future migrations, API client work, paid access, widgets,
  agent integrations, and methodology-version changes.

## Status

| File | Status | Notes |
| --- | --- | --- |
| `specs/2026-06-26-bitcoin-risk-brief-design.md` | Completed | Baseline product design is implemented. Current operational details are in the core docs. |
| `specs/2026-06-26-canonical-risk-methodology-design.md` | Completed, partly superseded | Formula and solver are implemented; CoinGecko-specific data-flow notes are superseded by the CoinMarketCap CSV source. |
| `specs/2026-06-26-coinmarketcap-csv-source-design.md` | Completed | Current source strategy is implemented and extended by public/manual CSV intake. |
| `specs/2026-06-26-database-waitlist-design.md` | Completed | Waitlist storage, validation, and API behavior are implemented. |
| `specs/2026-06-26-full-bitcoin-risk-source-parity-design.md` | Superseded | Earlier CoinGecko/source-stitch design is replaced by the canonical CoinMarketCap CSV source. |
| `specs/2026-06-30-agent-access-demand-test-design.md` | Future-facing | Phase 9 agent-access and risk-signal licensing experiment; not part of the production-pilot gate. |
| `specs/2026-07-01-product-analytics-usage-attribution-design.md` | Future-facing | Phase 8/9 analytics track for source attribution, repeat-use measurement, and future API client usage. |
| `specs/2026-07-01-public-payload-cache-warmup-precompute-design.md` | Implemented locally, production deploy pending | Local evidence: `cache-warmup-local-complete-2026-07-05`. Production benefit still requires deploy, healthy readiness, and measurement. |
| `specs/2026-07-01-price-model-input-ohlc-display-design.md` | Implemented locally, production deploy pending | Local evidence: `price-model-ohlc-local-complete-2026-07-06`. Production visibility still requires deploy and public-hostname verification. |
| `specs/2026-07-01-launch-operations-governance-checklist-design.md` | Future-facing | Phase 7/8 launch completeness checklist for privacy, waitlist handling, ownership, monitoring, maintenance, accessibility, metadata, and incident response. |
| `specs/2026-07-01-release-feedback-operational-evidence-design.md` | Future-facing | Phase 8 launch completeness add-on for release notes, decision log, first-user feedback, support contact, dependency-license review, and launch/restore evidence. |
| `specs/2026-07-02-data-correction-service-targets-design.md` | Future-facing | Phase 7/8 operational readiness gate for bad-data correction flow, correction notes, cache safety, freshness, RPO/RTO, and pilot downtime boundaries. |
| `specs/2026-07-02-import-provenance-source-archive-design.md` | Future-facing | Phase 7/8 operational readiness gate for source snapshots, import manifests, hashes, retrieval metadata, validation/readiness output, and cache evidence. |
| `specs/2026-07-01-email-paid-beta-trust-gates-design.md` | Future-facing | Phase 9 readiness gates before recurring outreach, first payments, license experiments, account recovery reliance, synthetic monitoring, or broader trust claims. |
| `specs/2026-07-02-api-db-change-management-design.md` | Future-facing | Deferred Phase 9/change-readiness gate for API compatibility, DB migrations, rollback, contract tests, and future external client safety. |
| `specs/2026-07-01-documentation-portfolio-presentation-design.md` | Planned by implementation plan | Tracked by `plans/2026-07-06-documentation-portfolio-presentation-implementation.md`; do not mark complete until the docs pass is executed and verified. |
| `specs/2026-07-01-localization-quality-language-expansion-design.md` | Future-facing | Phase 8 localization add-on for EN/RU copy polish, ES/DE launch scope, and deferred AR/ZH research. |
| `specs/2026-07-01-scheduled-public-cmc-refresh-design.md` | Implemented locally, production freshness blocked | Scheduled no-key public CoinMarketCap refresh exists locally/documented, but current public readiness remains stale until operator action restores freshness. |
| `specs/2026-07-01-usb-update-install-kit-v2-design.md` | Implemented locally, production use pending | Phase 6/7 operational hardening for reproducible USB preparation, install/update flows, and backup-before-update. Production benefit still requires preparing a real USB kit and running the flow on the production host. |
| `specs/2026-07-01-risk-methodology-research-design.md` | Future-facing | Phase 10 research track; v1 remains the production metric until evidence supports a versioned v2. |
| `specs/2026-07-01-distribution-channel-research-design.md` | Future-facing | Phase 11 distribution track; evaluates PWA, Telegram Mini App, browser extensions, and conditional platform wrappers. |
| `specs/2026-06-30-usb-server-kit-design.md` | Completed in repository | Templates and scripts exist under `server-kit/`; USB copy remains an operator action. |
| `plans/2026-06-26-bitcoin-risk-brief-implementation.md` | Completed, historical | Some unchecked boxes reflect stale tracking, not current work. |
| `plans/2026-06-26-canonical-risk-methodology-implementation.md` | Completed, historical | Current code uses Python 3.13 in CI and canonical CMC CSV data. |
| `plans/2026-06-26-coinmarketcap-csv-source-implementation.md` | Completed | Tracks the CMC CSV-first implementation and stale-row cleanup. |
| `plans/2026-06-26-database-waitlist-implementation.md` | Completed, historical | Unchecked boxes are stale; implementation exists in backend, migration, frontend, and tests. |
| `plans/2026-06-26-full-bitcoin-risk-source-parity-implementation.md` | Superseded | CoinGecko-oriented plan is not a current implementation guide. |
| `plans/2026-06-29-public-coinmarketcap-download.md` | Completed | Implemented by `collector/collector/public_cmc_download.py` and `./scripts/manage.sh download-cmc-csv`. |
| `plans/2026-06-30-usb-server-kit.md` | Completed in repository, operator copy pending | Repository templates exist; physical USB staging is not committed state. |
| `plans/2026-07-02-production-pilot-agent-handoff.md` | Historical coordination plan | Task tracking has been reconciled into the core docs and later focused implementation plans; remaining production gates are tracked in `docs/production-readiness.md` and `docs/production-roadmap.md`. |
| `plans/2026-07-02-production-pilot-priority-implementation.md` | Historical coordination plan | Priority model remains useful context, but current status lives in the roadmap/readiness docs and the focused 2026-07-05/2026-07-06 plans below. |
| `plans/2026-07-05-public-payload-cache-warmup-implementation.md` | Implemented locally, production deploy pending | Local implementation is tagged `cache-warmup-local-complete-2026-07-05`; production freshness and warmup measurement remain pending. |
| `plans/2026-07-05-usb-update-install-kit-v2-implementation.md` | Implemented locally, production use pending | Local implementation is tagged `usb-kit-v2-local-complete-2026-07-05`; a real USB package and production-host update remain pending. |
| `plans/2026-07-05-price-model-input-ohlc-display-implementation.md` | Implemented locally, production deploy pending | Local implementation is tagged `price-model-ohlc-local-complete-2026-07-06`; production browser verification remains pending. |
| `plans/2026-07-06-documentation-portfolio-presentation-implementation.md` | Planned | Current plan for README/docs presentation alignment; status changes only after the scoped docs pass is executed and verified. |

## Reading Rule

When a superpowers file conflicts with `docs/data-pipeline.md`, `docs/architecture.md`, `docs/api-reference.md`,
`docs/operations.md`, `docs/production-readiness.md`, or the code, treat the core docs and code as authoritative.
