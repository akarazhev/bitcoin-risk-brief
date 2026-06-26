# CoinMarketCap CSV Source Design

**Goal:** make `collector/btc-csv/btc_usd_daily.csv` the canonical Bitcoin OHLCV source and use the official CoinMarketCap API only for daily delta updates.

## Source Strategy

The collector will no longer use CoinGecko. `btc_usd_daily.csv` is the durable local source of truth. On every scheduled run the collector will:

1. Load and validate `collector/btc-csv/btc_usd_daily.csv`.
2. If `COINMARKETCAP_API_KEY` is set, request missing completed UTC days from CoinMarketCap `GET /v2/cryptocurrency/ohlcv/historical` with `id=1`, `time_period=daily`, and `convert=USD`.
3. Merge fetched rows into the CSV by date, replacing duplicate dates with the newest API row.
4. Re-read the CSV, import all rows into TimescaleDB, and recalculate risk over the full local history.
5. Write validation metadata and the daily brief.

If no API key is configured, the scheduled run still imports the existing CSV and recalculates risk. It logs that remote refresh was skipped.

## Container Requirement

`podman-compose` must mount `./collector/btc-csv` into the data-collector container. Without that bind mount, a container can update only its own ephemeral copy of the CSV.

## Removed Integration

CoinGecko collector runtime, config, tests, and compose env variables are removed. Historical docs may mention previous CoinGecko decisions, but runnable collector code must not depend on CoinGecko.

## Failure Behavior

If the CMC API fails, the collector does not corrupt the CSV. The existing CSV remains the canonical source and the run fails visibly. If the API returns no missing dates, the collector imports the current CSV without modification.
