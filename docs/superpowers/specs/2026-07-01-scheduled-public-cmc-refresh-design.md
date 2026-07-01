# Scheduled Public CoinMarketCap Refresh Design

> Status: future-facing operational hardening. Last reviewed 2026-07-01. This should be implemented before active traffic
> if the production pilot is expected to run autonomously without a `COINMARKETCAP_API_KEY`.

## Goal

Make the production pilot refresh BTC CSV data automatically once per day at night without requiring a paid
CoinMarketCap API key.

The product already has:

- a canonical BTC CSV source at `collector/btc-csv/btc_usd_daily.csv`;
- a validated public CoinMarketCap download command, `./scripts/manage.sh download-cmc-csv`;
- a validated manual downloaded CSV import path;
- a daily `data-collector` scheduler.

The missing piece is the scheduled refresh strategy. The current scheduled collector path uses the optional API-key
refresh flow; when `COINMARKETCAP_API_KEY` is empty it imports the existing CSV and recomputes risk, but it does not yet
try the public CoinMarketCap download automatically.

## Roadmap Placement

This belongs in Phase 6/7 operational hardening before active traffic:

- Phase 6 should verify the production host uses the intended scheduled refresh mode.
- Phase 7 should alert when the scheduled refresh fails or readiness becomes stale after the daily update window.

It should not wait for post-launch learning, because daily data freshness is part of the core product promise.

## Recommended Scheduled Strategy

Use public CoinMarketCap download as the default scheduled no-key refresh path.

On each scheduled run:

1. Calculate the target end date as the last completed UTC day.
2. Read the canonical CSV tail.
3. If the CSV already covers the target date, import the existing CSV, recompute risk, write validation and brief data,
   and log `already_current`.
4. If the CSV is stale, try the public CoinMarketCap historical-data download for the missing contiguous range.
5. Stage the downloaded rows under `collector/btc-csv/incoming/`.
6. Validate the staged CSV exactly against the requested contiguous range.
7. Atomically replace the canonical CSV only after validation succeeds.
8. Import the full CSV into TimescaleDB, recompute all risk rows, write validation data and the daily brief, and delete
   derived database rows after the CSV tail.

## Fallback Order

The scheduled path should use this order:

1. Public CoinMarketCap historical-data download.
2. Optional official CoinMarketCap API delta refresh only when `COINMARKETCAP_API_KEY` is configured.
3. Manual downloaded CSV import by an operator.

The official API key remains optional. It should be a fallback or an environment-specific preference, not a
production-pilot requirement.

If both public download and optional API fallback fail, the collector must fail visibly without rewriting the canonical
CSV. The previous canonical CSV and database-derived rows remain the last trusted state until a later successful import.

## Configuration

Existing schedule settings remain valid:

- `SCHEDULE_CRON_HOUR`, default `1`;
- `SCHEDULE_CRON_MINUTE`, default `0`;
- scheduler timezone: UTC.

The design may add an explicit refresh-mode setting, for example:

- `REFRESH_MODE=public_cmc_first` for the production-pilot default;
- `REFRESH_MODE=api_first` for environments with a paid API contract;
- `REFRESH_MODE=csv_only` for offline import-only operation.

If no explicit setting is added, an empty `COINMARKETCAP_API_KEY` must still trigger public-download-first behavior on
scheduled runs.

## Observability

Collector logs should distinguish these states:

- `public_cmc_download_started`;
- `public_cmc_download_success`;
- `already_current`;
- `public_cmc_download_failed`;
- `api_fallback_started`;
- `api_fallback_success`;
- `csv_not_rewritten`;
- `scheduled_refresh_failed`.

Readiness should remain the production gate. If the data is stale after the expected daily update window, monitoring
should alert operators.

## Safety Rules

- Never compute risk from a partial or non-contiguous public download.
- Never rewrite `collector/btc-csv/btc_usd_daily.csv` until validation passes.
- Never include the current incomplete UTC day in the daily target range.
- Keep manual `import-cmc-csv` as the operator fallback.
- Treat the public CoinMarketCap endpoint as best-effort, because it is not the official paid API contract.

## Non-Goals

This design does not include:

- paid data dependencies;
- replacing the canonical CSV model;
- adding another market-data provider;
- intraday refresh;
- multi-asset refresh;
- an admin dashboard;
- notification delivery beyond existing readiness/collector alert expectations.

## Success Criteria

The scheduled refresh work is successful when:

- a production deployment with an empty `COINMARKETCAP_API_KEY` updates through the last completed UTC day automatically;
- a successful scheduled run updates the canonical CSV, TimescaleDB rows, risk validation, and brief snapshot;
- a failed public download leaves the canonical CSV unchanged and creates an observable failure;
- optional API fallback works only when configured;
- manual downloaded CSV import remains documented as the last fallback;
- `/api/readiness` reports fresh data after the nightly update window.
