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

## Health and Readiness

Basic health:

```bash
curl -fsS http://localhost:3001/api/health
```

Production readiness:

```bash
curl -fsS http://localhost:3001/api/readiness
```

Readiness should be used for deployment probes and monitoring alerts.

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
