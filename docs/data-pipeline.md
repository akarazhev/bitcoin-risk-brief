# Data Pipeline

## Canonical Source

The canonical local source is:

```text
collector/btc-csv/btc_usd_daily.csv
```

The file stores daily BTC/USD rows with CoinMarketCap-style columns:

```text
timeOpen;timeClose;timeHigh;timeLow;open;high;low;close;volume;marketCap;circulatingSupply;timestamp
```

The collector loads this CSV as the source of truth. The database is treated as a derived store and is rebuilt from the full CSV during each import.

## Refresh Modes

### Backfill

```bash
./scripts/manage.sh backfill
```

Backfill imports the current CSV without network access and recomputes all risk rows.

### Run Now

```bash
./scripts/manage.sh run-now
```

Run-now attempts a remote refresh when `COINMARKETCAP_API_KEY` is set. If no key is present, it skips remote refresh and imports the current CSV.

### Downloaded CoinMarketCap CSV Import

```bash
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv 2026-06-28
```

The first argument is a CSV downloaded from the public CoinMarketCap Bitcoin historical data page and staged under
`collector/btc-csv/incoming/`. The optional second argument is the UTC date the merged canonical CSV must cover through;
operators normally set it to the last completed UTC day.

The import command validates the downloaded file, atomically replaces the canonical CSV only after validation succeeds,
imports the full canonical CSV into TimescaleDB, recomputes risk, writes validation metadata and the daily brief, and
removes derived database rows after the CSV tail.

### Scheduled Collector

The long-running `data-collector` service schedules the same refresh/import flow once per day using UTC cron settings:

- `SCHEDULE_CRON_HOUR`, default `1`
- `SCHEDULE_CRON_MINUTE`, default `0`

## Optional CoinMarketCap API Delta Fetch

When an API key is configured, the collector uses the official CoinMarketCap OHLCV Historical endpoint:

```text
/v2/cryptocurrency/ohlcv/historical
```

Runtime parameters:

- `id=1` for Bitcoin
- `time_period=daily`
- `convert=USD` by default
- `time_start` is the day after the CSV tail
- `time_end` is the last completed UTC day

Transient HTTP/request errors are retried with exponential backoff. Permanent HTTP errors fail fast.

The API path is an optional convenience path. Production-pilot operation must not depend on a paid CoinMarketCap account
being available.

## Downloaded CSV Intake

Production-pilot operation supports an operator-downloaded CSV from the public CoinMarketCap Bitcoin historical data
page:

```text
https://coinmarketcap.com/currencies/bitcoin/historical-data/
```

This is a manual operator workflow, not page scraping. The operator downloads the CSV, stages it under
`collector/btc-csv/incoming/`, and runs `./scripts/manage.sh import-cmc-csv`.

The downloaded CSV intake:

- accepts an explicit staged CSV file path;
- normalizes supported CoinMarketCap historical-data columns into the canonical local CSV schema;
- rejects missing or incompatible required columns and ignores unsupported extra columns;
- rejects partial files, duplicate dates, date gaps, and non-daily rows;
- preserves the existing canonical CSV when validation fails;
- atomically replaces `collector/btc-csv/btc_usd_daily.csv` only after validation succeeds;
- runs the same database import, risk recomputation, and readiness checks as the current CSV-backed flow.

The API delta refresh remains available for environments that have an API key, but the documented production-pilot path
is valid with only the downloaded CSV.

## Delta Validation

Remote deltas and downloaded CSV imports must exactly match the intended date range.

The collector rejects a remote delta or downloaded CSV import when:

- a requested day is missing;
- an unexpected date is returned;
- dates are out of order;
- the merged CSV would contain gaps or invalid source rows.

When validation fails, the canonical CSV is not rewritten.

## CSV Write Safety

CSV writes use atomic replacement:

1. Write a temporary file next to the canonical CSV.
2. Complete and close the temporary file.
3. Replace the canonical CSV with `os.replace`.
4. Remove the temporary file if an exception occurs before replacement.

This prevents partial CSV writes from becoming canonical.

## Database Import

Each import writes:

- all OHLCV source rows into `btc_ohlcv_daily`;
- all computed risk rows into `btc_risk_daily`;
- latest validation metadata into `btc_risk_validation`;
- latest brief payload into `brief_snapshots`.

Rows after the CSV tail are deleted from `btc_ohlcv_daily`, `btc_risk_daily`, and `brief_snapshots` so older mixed-source data cannot remain visible.

## Readiness Relationship

`/api/readiness` depends on pipeline output. It returns HTTP 200 only when:

- latest risk data exists;
- validation data exists;
- validation row count is positive;
- risk range validation passed;
- validation source is `coinmarketcap_csv`;
- latest risk timestamp matches validation coverage end;
- latest risk data is within `DATA_FRESHNESS_MAX_AGE_DAYS`.
