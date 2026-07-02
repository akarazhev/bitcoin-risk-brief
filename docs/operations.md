# Operations

## Local Environment

Create a local environment file:

```bash
cp .env.example .env
```

Validate compose:

```bash
./scripts/manage.sh validate
```

Start services:

```bash
./scripts/manage.sh start
```

Apply schema to an existing database:

```bash
./scripts/manage.sh migrate
```

For future schema changes beyond the current idempotent initial migration, use the API/DB change-management gate before
production deployment: add a new migration file, take a fresh backup, test migration on a fresh and existing database,
record rollback expectations, run smoke checks, and update API/security/operations docs when endpoint contracts,
retention, analytics, API client identity, or PII behavior changes.

Import the canonical CSV without network access:

```bash
./scripts/manage.sh backfill
```

Refresh from CoinMarketCap if configured, then import the full CSV:

```bash
./scripts/manage.sh run-now
```

If `COINMARKETCAP_API_KEY` is empty, `run-now` imports the existing canonical CSV and recomputes risk without remote
network refresh.

## Automatic Public CoinMarketCap CSV Refresh

Refresh BTC history without a paid CoinMarketCap API account:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
```

The command fetches the missing days after the canonical CSV tail from CoinMarketCap's public historical-data endpoint,
stages the result under `collector/btc-csv/incoming/`, validates the staged CSV, atomically updates
`collector/btc-csv/btc_usd_daily.csv`, and runs the normal database import, risk recomputation, validation write, brief
write, and stale-row cleanup.

If the public endpoint returns an incomplete range, an error response, HTML, or blocked content, the command fails before
rewriting the canonical CSV. Use the manual workflow below or the optional official API-key refresh path.

## Scheduled Public CoinMarketCap Refresh

The desired production-pilot scheduler is public-download-first: once per day after the UTC day closes, the
`data-collector` should try the same public CoinMarketCap download path automatically, then import the validated
canonical CSV, recompute risk, write validation and brief data, and leave `/api/readiness` fresh.

Current implementation note: the long-running scheduled collector still uses the `run-now` refresh behavior. With an
empty `COINMARKETCAP_API_KEY`, it imports the existing CSV and recomputes risk, but it does not yet automatically invoke
the public download path.

Until the scheduled public-download-first behavior is implemented and verified, operators should run
`./scripts/manage.sh download-cmc-csv` after the last completed UTC day when the canonical CSV is stale. Manual
`import-cmc-csv` remains the fallback if the public endpoint automation is unavailable.

When implemented, scheduled no-key refresh failures should be visible in collector logs and readiness alerts. A failed
public download must not rewrite `collector/btc-csv/btc_usd_daily.csv`.

## Manual Downloaded CoinMarketCap CSV Refresh

Refresh BTC history without a paid CoinMarketCap API account by downloading a CSV from:

```text
https://coinmarketcap.com/currencies/bitcoin/historical-data/
```

Use a date range that starts at the day after the canonical CSV tail, or download the full available Bitcoin history.
The target tail is normally the last completed UTC day.

Stage the downloaded file where the `data-collector` container can read it:

```bash
mkdir -p collector/btc-csv/incoming
cp ~/Downloads/bitcoin-historical-data.csv collector/btc-csv/incoming/
```

Optionally inspect the downloaded range before importing:

```bash
PYTHONPATH=backend:collector python3 - <<'PY'
from pathlib import Path
from collector.downloaded_csv import load_coinmarketcap_downloaded_csv

rows = load_coinmarketcap_downloaded_csv(Path("collector/btc-csv/incoming/bitcoin-historical-data.csv"))
print(rows[0]["date"], rows[-1]["date"], len(rows))
PY
```

Import and require coverage through the expected UTC tail:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
```

The command validates the downloaded schema, rejects partial files, duplicate dates and daily gaps, atomically replaces
`collector/btc-csv/btc_usd_daily.csv` only after validation passes, and then runs the normal database import, risk
recomputation, validation write, brief write, and stale-row cleanup.

If validation fails, the existing canonical CSV is preserved. Fix the downloaded file or date range and rerun the command.

Open the app:

```text
http://localhost:3001
```

## Service Logs

Follow all logs:

```bash
./scripts/manage.sh logs
```

Follow a single service:

```bash
./scripts/manage.sh logs backend
./scripts/manage.sh logs data-collector
./scripts/manage.sh logs frontend
./scripts/manage.sh logs timescaledb
```

Backend API access logs include method, path, status, client key, Cloudflare ray ID when present, cache status, and
duration. Use them to distinguish normal page loads from bursts against `/api/waitlist` or `/api/*` without logging
waitlist contact values.

## Health and Readiness

Basic health:

```bash
curl -fsS http://localhost:3001/api/health
```

Production readiness:

```bash
curl -fsS http://localhost:3001/api/readiness
```

Readiness should be used for deployment probes and monitoring alerts. After an automatic or manual CSV import, readiness
should be HTTP 200 before the refreshed data is trusted.

## Cache Verification

Public read endpoints are cacheable at the backend and edge:

- `/api/readiness`
- `/api/risk/latest`
- `/api/risk/history`
- `/api/risk/levels`
- `/api/brief/latest`

Check cache headers on a public read endpoint:

```bash
curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest
```

Expected headers include `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`. Repeat the same request and confirm
`X-Cache: HIT` once the backend has built the payload:

```bash
curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest
```

Current implementation note: the backend public endpoint cache is lazy. The first request for a key after backend
startup, TTL expiry, or a new `btc_risk_validation` marker returns `X-Cache: MISS` and rebuilds the payload from
TimescaleDB. If first-load latency is user-visible, warm the standard public payloads before active traffic:

- `/api/readiness`
- `/api/risk/latest`
- `/api/risk/history?limit=2000`
- `/api/risk/levels`
- `/api/brief/latest`

The expensive first-miss candidate is `/api/risk/levels`, because it reads full OHLCV history and builds risk-level rows
on demand. See
[Public Payload Cache Warmup And Precompute Design](superpowers/specs/2026-07-01-public-payload-cache-warmup-precompute-design.md).

Verify conditional revalidation:

```bash
ETAG="$(curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest | awk 'BEGIN{IGNORECASE=1} /^etag:/ {print $2}' | tr -d '\r')"
curl -s -o /dev/null -w "%{http_code}\n" -H "If-None-Match: ${ETAG}" http://localhost:3001/api/risk/latest
```

The second command should print `304`.

After `backfill`, `run-now`, `download-cmc-csv`, or `import-cmc-csv`, the collector writes a new
`btc_risk_validation` marker. The backend derives `X-Cache-Version` from that marker, so the next public read misses the
old in-process cache and rebuilds from the database. If Cloudflare cache is enabled, purge the hostname or wait for
`PUBLIC_CACHE_MAX_AGE_SECONDS` before using cached public data for a launch snapshot.

`POST /api/waitlist` must remain uncached. Confirm it returns `Cache-Control: no-store` during launch checks.

## Cloudflare Edge Rules

Render the repo-managed Cloudflare WAF, rate-limit, cache, and waitlist bot-challenge rules:

```bash
python3 scripts/cloudflare_edge_rules.py render --hostname risk.example.com > /tmp/bitcoin-risk-cloudflare-edge.json
```

Apply the rules with an operator API token:

```bash
export CLOUDFLARE_ZONE_ID=replace-with-zone-id
export CLOUDFLARE_API_TOKEN=replace-with-api-token
python3 scripts/cloudflare_edge_rules.py apply \
  --zone-id "${CLOUDFLARE_ZONE_ID}" \
  --hostname risk.example.com
```

For a Cloudflare Free plan that is not entitled to execute the managed WAF ruleset, create more than one rate-limit rule,
or use 60-second rate-limit windows, apply the current public-pilot subset instead:

```bash
python3 scripts/cloudflare_edge_rules.py apply \
  --zone-id "${CLOUDFLARE_ZONE_ID}" \
  --hostname bitcoinriskbrief.minihub.app \
  --skip-managed-waf \
  --waitlist-rate-limit-only \
  --rate-limit-period 10 \
  --rate-limit-mitigation-timeout 10
```

The script preserves unrelated Cloudflare rules and only replaces rules with refs starting `bitcoin-risk-brief:`. After
applying it, enable Cloudflare Bot Fight Mode, Super Bot Fight Mode, or equivalent dashboard bot protection if the active
plan supports it. Record any accepted plan limitations before first traffic.

Verify the public hostname after applying edge rules:

```bash
curl -fsS https://risk.example.com/api/health
curl -sD - -o /tmp/bitcoin-risk-readiness.json https://risk.example.com/api/readiness
curl -sD - -o /tmp/bitcoin-risk-latest.json https://risk.example.com/api/risk/latest
```

Public read responses should include `Cache-Control`, `ETag`, and `X-Cache-Version`. Waitlist submissions should still
work for normal users and return `Cache-Control: no-store`.

## Backups

Create a timestamped backup of PostgreSQL and the canonical BTC CSV:

```bash
./scripts/backup.sh
```

Preview the target paths without touching the database:

```bash
./scripts/backup.sh --dry-run
```

Production defaults can be controlled from the environment:

```bash
BACKUP_DIR=./backups BACKUP_RETENTION_DAYS=30 ./scripts/backup.sh
```

Each backup directory contains:

- compressed PostgreSQL custom-format `pg_dump` output;
- a copy of `collector/btc-csv/btc_usd_daily.csv`;
- `manifest.txt` with source metadata;
- `SHA256SUMS` for integrity checks.

Backups should be copied off the server. Keeping the only backup under `./backups` protects against accidental database edits, but not against disk failure.

For USB-based production updates, run a fresh backup before deploying the new project snapshot and copy the new backup
off the server before promotion. The planned USB Update And Install Kit V2 keeps backup artifacts out of the workstation
project snapshot while making the backup gate explicit in the server update flow.

## Restore Notes

Restore only into a staging copy or an intentionally empty production database:

```bash
podman-compose -f podman-compose.yml exec -T timescaledb pg_restore --clean --if-exists --no-owner --no-privileges -U postgres -d bitcoin_risk_brief < backups/<timestamp>/postgres_<timestamp>.dump
cp backups/<timestamp>/btc_usd_daily_<timestamp>.csv collector/btc-csv/btc_usd_daily.csv
./scripts/manage.sh run-now
curl -fsS http://localhost:3001/api/readiness
```

Take the public app offline before restoring production data. TimescaleDB may print circular foreign-key warnings during backup; treat them as informational only when `scripts/backup.sh` exits with code 0.

## Resource And Ownership Checks

Before active traffic, record the operator and recovery path for:

- GitHub repository access;
- Cloudflare account, tunnel, zone, and API token;
- domain registration if a custom domain is used;
- production `.env` storage;
- backup storage;
- server login or physical access;
- optional CoinMarketCap API credentials.

Operational review should also check disk usage, database volume growth, backup directory growth, container restart
loops, Cloudflare Tunnel connector health, public hostname availability, and any infrastructure cost or resource limits.

## First-Response Runbook

Create or maintain a short incident note for these cases:

- `/api/readiness` is degraded or non-200;
- scheduled data refresh fails;
- CoinMarketCap public download fails;
- source CSV, imported OHLCV rows, risk rows, or latest brief snapshot may be wrong after publication;
- waitlist submission fails;
- Cloudflare Tunnel is down;
- public cache appears stale after an import;
- backup fails;
- database volume or disk space is close to full.

Each note should name where to look first, which command or dashboard to check, and which action is safe for the operator
to take without risking data loss.

For a suspected published bad-data incident, prefer a conservative correction flow: record the observed public value and
data date, inspect readiness and validation metadata, stop further automated imports if they could overwrite evidence,
restore or re-import from the last known-good CSV or backup, recompute risk and brief snapshots, verify cache headers,
and capture a correction note. During the free pilot, temporary downtime is preferable to knowingly serving a wrong risk
value.

For production imports, keep sanitized import provenance outside the repository. At minimum, record the source snapshot
or staged source path, retrieval method, UTC import time, source `sha256`, source row count, covered date range, expected
tail date, canonical CSV `sha256` after import, validation/readiness output, and cache evidence. Do not include secrets,
waitlist contacts, raw analytics, or local `.env` values in provenance artifacts.

## Database Checks

Check latest source/risk coverage:

```bash
podman-compose -f podman-compose.yml exec timescaledb   psql -U postgres -d bitcoin_risk_brief -t -A -c   "SELECT max(timestamp)::date, count(*) FROM btc_ohlcv_daily; SELECT max(timestamp)::date, count(*) FROM btc_risk_daily;"
```

Check validation source:

```bash
podman-compose -f podman-compose.yml exec timescaledb   psql -U postgres -d bitcoin_risk_brief -t -A -c   "SELECT validation_json->>'source', validation_json->'validation'->>'source_strategy', row_count FROM btc_risk_validation WHERE validation_key='latest';"
```

## Common Troubleshooting

### Readiness is degraded

Inspect `/api/readiness` and check which flag failed. Common causes:

- collector has not run;
- data is older than `DATA_FRESHNESS_MAX_AGE_DAYS`;
- validation source is not `coinmarketcap_csv`;
- latest risk timestamp does not match validation coverage end.

### Collector skips remote refresh

If `COINMARKETCAP_API_KEY` is empty, this is expected. The collector still imports the existing CSV and recomputes risk.

### Downloaded CSV import fails

The canonical CSV is preserved when a downloaded import fails. Common causes:

- the file was not staged under `collector/btc-csv/incoming/`;
- required columns such as `Date`, `Open`, `High`, `Low`, `Close`, `Volume`, or `Market Cap` are missing;
- the downloaded range skips one or more daily dates;
- the file ends before the existing canonical tail;
- `--expected-end-date` is later than the merged CSV tail.

### Collector fails on remote delta

A non-contiguous CoinMarketCap delta is rejected without rewriting the CSV. Inspect `data-collector` logs and rerun after the upstream data issue is resolved.

### TimescaleDB connection race

The collector wraps pool creation in retry logic, but if the database is unhealthy for longer than the retry window, fix the database container first:

```bash
podman-compose -f podman-compose.yml ps
podman-compose -f podman-compose.yml logs timescaledb
```

## Stopping Services

```bash
./scripts/manage.sh stop
```

This stops containers but keeps `./data/timescaledb` on disk.

## Related Docs

- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Production Readiness](production-readiness.md)
