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

## Restore Notes

Restore only into a staging copy or an intentionally empty production database:

```bash
podman-compose -f podman-compose.yml exec -T timescaledb pg_restore --clean --if-exists --no-owner --no-privileges -U postgres -d bitcoin_risk_brief < backups/<timestamp>/postgres_<timestamp>.dump
cp backups/<timestamp>/btc_usd_daily_<timestamp>.csv collector/btc-csv/btc_usd_daily.csv
./scripts/manage.sh run-now
curl -fsS http://localhost:3001/api/readiness
```

Take the public app offline before restoring production data. TimescaleDB may print circular foreign-key warnings during backup; treat them as informational only when `scripts/backup.sh` exits with code 0.

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
