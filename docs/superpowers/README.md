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
- Public read endpoints use backend cache headers and validation-versioned `ETag`s. `POST /api/waitlist` is no-store and
  application-rate-limited.
- Server-kit scripts live under `server-kit/` and include bootstrap, optional `cloudflared` install, deploy, user service
  enablement, health check, and debug helpers.

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
| `specs/2026-07-01-localization-quality-language-expansion-design.md` | Future-facing | Phase 8 localization add-on for EN/RU copy polish, ES/DE launch scope, and deferred AR/ZH research. |
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
