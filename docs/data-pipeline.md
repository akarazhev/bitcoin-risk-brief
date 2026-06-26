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

### Scheduled Collector

The long-running `data-collector` service schedules the same refresh/import flow once per day using UTC cron settings:

- `SCHEDULE_CRON_HOUR`, default `1`
- `SCHEDULE_CRON_MINUTE`, default `0`

## CoinMarketCap Delta Fetch

The collector uses the official CoinMarketCap OHLCV Historical endpoint:

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

## Delta Validation

Remote deltas must exactly match the requested date range.

The collector rejects a remote delta when:

- a requested day is missing;
- an unexpected date is returned;
- dates are out of order;
- the merged CSV would contain gaps or invalid source rows.

When validation fails, the CSV is not rewritten.

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
