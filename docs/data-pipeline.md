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

### Automatic Public CoinMarketCap CSV Download

```bash
./scripts/manage.sh download-cmc-csv 2026-06-28
```

The optional argument is the UTC date the merged canonical CSV must cover through. If omitted, the collector targets the
last completed UTC day.

This command fetches missing Bitcoin daily rows after the canonical CSV tail from CoinMarketCap's public historical-data
JSON endpoint, filters the returned window down to the requested range, writes a staged CSV under
`collector/btc-csv/incoming/`, and then runs the same validated CSV import used by `import-cmc-csv`.

The public endpoint is not the official paid API contract. Treat this path as best-effort automation: if CoinMarketCap
changes or blocks the endpoint, the command fails before rewriting the canonical CSV and operators should use the manual
downloaded CSV workflow or the official API-key refresh path.

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

The long-running `data-collector` service schedules a refresh/import flow once per day using UTC cron settings:

- `SCHEDULE_CRON_HOUR`, default `1`
- `SCHEDULE_CRON_MINUTE`, default `0`

Each scheduled run targets the last completed UTC day. If the canonical CSV already covers that target, the collector
imports the existing CSV, recomputes risk, writes validation and brief data, and removes stale derived rows.

If the CSV is stale, the scheduled path uses public CoinMarketCap download first. A successful public download is staged
under `collector/btc-csv/incoming/`, validated as a contiguous range, merged into the canonical CSV, imported into
TimescaleDB, and used for risk recomputation. If the public download fails and `COINMARKETCAP_API_KEY` is configured,
the scheduled run falls back to the optional official API delta refresh. With no API key, the public-download failure is
visible in collector logs and the canonical CSV remains unchanged.

Manual `import-cmc-csv` remains the operator fallback when public automation and any configured API fallback are
unavailable. See
[Scheduled Public CoinMarketCap Refresh Design](superpowers/specs/2026-07-01-scheduled-public-cmc-refresh-design.md).

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

The API path is an optional convenience path. `run-now` uses it when a key is configured, and scheduled runs use it only
as fallback after public download failure when a key is configured. Production-pilot operation must not depend on a paid
CoinMarketCap account being available.

## Public And Downloaded CSV Intake

Production-pilot operation supports an operator-downloaded CSV from the public CoinMarketCap Bitcoin historical data
page:

```text
https://coinmarketcap.com/currencies/bitcoin/historical-data/
```

The preferred no-key workflow is `./scripts/manage.sh download-cmc-csv`, which uses the public historical-data JSON that
the page uses to render and download CSV data. It only writes a staged CSV after the endpoint returns a complete
contiguous range.

The manual fallback is still supported: the operator downloads the CSV, stages it under `collector/btc-csv/incoming/`,
and runs `./scripts/manage.sh import-cmc-csv`.

The public/downloaded CSV intake:

- stages automatic downloads under `collector/btc-csv/incoming/`;
- accepts an explicit staged CSV file path for manual downloads;
- normalizes supported CoinMarketCap historical-data columns into the canonical local CSV schema;
- rejects missing or incompatible required columns and ignores unsupported extra columns;
- rejects partial files, duplicate dates, date gaps, and non-daily rows;
- preserves the existing canonical CSV when validation fails;
- atomically replaces `collector/btc-csv/btc_usd_daily.csv` only after validation succeeds;
- runs the same database import, risk recomputation, and readiness checks as the current CSV-backed flow.

The API delta refresh remains available for environments that have an API key, but the documented production-pilot path
is valid with only the public/manual CSV workflows.

## Import Provenance And Source Archive

Production-pilot imports should keep sanitized import evidence outside the repository. The local helper
`scripts/import_provenance_packet.py` can create or validate a sanitized JSON manifest from local source/canonical CSVs
and supplied evidence-file paths, but it is tooling only; a real production packet still has to be captured by the
operator outside the project checkout for each production import. Store the packet in an
operator-controlled archive or off-server backup location, not under the project checkout, Git history, dependency
caches, browser profiles, or ad hoc workstation downloads.

The evidence packet should include:

- manifest id and UTC import timestamp;
- operator or automation identity;
- git commit and command used;
- source type: `automatic_public_cmc`, `manual_cmc_csv`, `optional_cmc_api`, `restore`, or `correction`;
- source URL, download page, backup path, or other retrieval method;
- local staged source path and archived source snapshot path when practical;
- source file `sha256`, byte size, row count, and covered start/end dates;
- expected tail date requested by the import;
- canonical CSV path and `sha256` after import;
- validation row count, covered end, source strategy, and methodology version;
- readiness payload after import;
- latest risk date/value and latest brief timestamp when available;
- `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version` for a standard public endpoint after import;
- collector log summary and related launch, restore, or correction note path if any.

Use [docs/import-provenance-evidence-packet-template.md](import-provenance-evidence-packet-template.md) to collect these
fields in a copy outside Git before copying only sanitized final outcomes into launch docs. The template is not
production import evidence and does not replace the outside-repository source/archive packet.

Do not store `.env` values, API keys, Cloudflare tokens, waitlist contacts, raw analytics, browser profiles, private
account exports, or other PII in provenance artifacts. Manifests may include local file paths or operator names, so
review and redact them before external sharing. These artifacts support launch evidence, restore drills, bad-data
correction notes, and future methodology research; they are not a public audit product.

## Delta Validation

Remote deltas, public downloads, and downloaded CSV imports must exactly match the intended date range.

The collector rejects a remote delta, public download, or downloaded CSV import when:

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
