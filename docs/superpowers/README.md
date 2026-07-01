# Superpowers Docs Index

This directory is an implementation-history archive for agent-assisted specs and plans. It is not the primary runtime
documentation source. For current behavior, use the core docs in `docs/README.md`.

Unchecked boxes inside files marked completed, historical, or superseded are original plan tracking, not current TODOs.

Last reviewed: 2026-07-01.

## Current Implementation Summary

- The product is a four-service Podman Compose stack: TimescaleDB, `data-collector`, FastAPI `backend`, and React/Vite
  `frontend`.
- `collector/btc-csv/btc_usd_daily.csv` is the canonical BTC/USD source. CoinGecko runtime collection has been removed.
- Supported refresh paths are `backfill`, `run-now` with optional CoinMarketCap API key, automatic public
  `download-cmc-csv`, and manual staged `import-cmc-csv`.
- Every import recalculates the full risk series, writes validation and brief snapshots, and deletes derived database
  rows after the CSV tail.
- The public frontend fetches readiness, latest risk, history, levels, brief, and waitlist endpoints. It renders
  readiness/freshness, methodology metadata, no-advice disclaimer, and nearest `0.35`/`0.65` threshold callouts.
- `price_usd` in the latest risk payload is the HLC3 model price; a planned UI/API polish pass may expose daily `Low`
  and `High` next to an explicit `Model price` label.
- Public read endpoints use backend cache headers and validation-versioned `ETag`s. `POST /api/waitlist` is no-store and
  application-rate-limited.
- Server-kit scripts live under `server-kit/` and include bootstrap, optional `cloudflared` install, deploy, user service
  enablement, health check, and debug helpers.
- USB kit v2 is planned as a reproducible workstation-side packaging flow plus a server-side backup-before-update gate;
  it is not a full offline deployment artifact.
- A final documentation and portfolio presentation pass is planned after implementation freeze; it is for a private or
  portfolio repository, not an open-source community launch.
- A launch operations and governance checklist is planned for privacy/terms, waitlist handling, credential ownership,
  resource monitoring, accessibility, metadata, data-source terms, dependency maintenance, and incident response.
- A release feedback and operational evidence checklist is planned to capture decision memory, first-user feedback,
  contact handling, dependency-license review, and launch/restore evidence without creating a new product phase.
- Deferred Phase 9 gates are planned for email/Telegram outreach, paid beta or license experiments, account recovery,
  synthetic journey monitoring, and public trust artifacts.

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
| `specs/2026-07-01-public-payload-cache-warmup-precompute-design.md` | Future-facing | Phase 5/8 performance hardening for first-load cache warmup and expensive payload precompute. |
| `specs/2026-07-01-price-model-input-ohlc-display-design.md` | Future-facing | Phase 8 UI/API polish for showing Model price, daily Low, and daily High in the first metrics strip. |
| `specs/2026-07-01-launch-operations-governance-checklist-design.md` | Future-facing | Phase 7/8 launch completeness checklist for privacy, waitlist handling, ownership, monitoring, maintenance, accessibility, metadata, and incident response. |
| `specs/2026-07-01-release-feedback-operational-evidence-design.md` | Future-facing | Phase 8 launch completeness add-on for release notes, decision log, first-user feedback, support contact, dependency-license review, and launch/restore evidence. |
| `specs/2026-07-01-email-paid-beta-trust-gates-design.md` | Future-facing | Phase 9 readiness gates before recurring outreach, first payments, license experiments, account recovery reliance, synthetic monitoring, or broader trust claims. |
| `specs/2026-07-01-documentation-portfolio-presentation-design.md` | Future-facing | Phase 8 final documentation and private/portfolio repository presentation pass after implementation freeze. |
| `specs/2026-07-01-localization-quality-language-expansion-design.md` | Future-facing | Phase 8 localization add-on for EN/RU copy polish, ES/DE launch scope, and deferred AR/ZH research. |
| `specs/2026-07-01-scheduled-public-cmc-refresh-design.md` | Future-facing | Phase 6/7 operational hardening for nightly no-key public CoinMarketCap refresh. |
| `specs/2026-07-01-usb-update-install-kit-v2-design.md` | Future-facing | Phase 6/7 operational hardening for reproducible USB preparation, install/update flows, and backup-before-update. |
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

## Reading Rule

When a superpowers file conflicts with `docs/data-pipeline.md`, `docs/architecture.md`, `docs/api-reference.md`,
`docs/operations.md`, `docs/production-readiness.md`, or the code, treat the core docs and code as authoritative.
