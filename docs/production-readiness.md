# Production Readiness

## Release Gates

Run these before every deploy:

```bash
./scripts/manage.sh test-python
python3 -m compileall backend collector
npm test --prefix frontend
npm run build --prefix frontend
./scripts/manage.sh validate
podman-compose -f podman-compose.yml build backend data-collector frontend
./scripts/manage.sh run-now
```

After services are running, verify:

```bash
curl -fsS http://localhost:3001/api/health
curl -fsS http://localhost:3001/api/readiness
```

`/api/readiness` returns HTTP 200 only when risk data exists, validation exists, data is fresh, risk range validation passed, the validation source is `coinmarketcap_csv`, and the latest risk timestamp matches the validation coverage end.

## Production Environment

Start from `.env.production.example`, not `.env.example`. Required production changes:

- Set `APP_ENV=production`.
- Replace `DB_PASSWORD` with a long random value.
- Set `CORS_ORIGINS` to the public HTTPS domain only.
- Set `COINMARKETCAP_API_KEY` to the production key.
- Keep `DATA_FRESHNESS_MAX_AGE_DAYS=2` unless the product explicitly accepts slower updates.
- Tune `WAITLIST_RATE_LIMIT_PER_HOUR` for expected traffic.

## Data Pipeline Guarantees

- `collector/btc-csv/btc_usd_daily.csv` is the canonical source.
- Scheduled collector runs fetch only missing completed UTC days from CoinMarketCap.
- Remote deltas must exactly match the requested contiguous daily range. Non-contiguous deltas fail without rewriting the CSV.
- CSV writes use atomic replace, so a failed write should not leave a partial canonical CSV.
- Every import recalculates all risk rows and removes DB rows after the CSV tail.

## Security Controls

- Public responses include baseline security headers at the nginx entrypoint.
- Backend responses also set API-safe security headers.
- `POST /api/waitlist` uses input validation, parameterized SQL, and an in-memory per-client rate limit.
- Waitlist contacts are stored server-side only; the frontend does not persist submitted contacts in browser storage.

## Remaining External Operations

These are operational tasks outside this repository:

- Run one live `./scripts/manage.sh run-now` with the real `COINMARKETCAP_API_KEY` before public launch.
- Configure host-level backups for `./data/timescaledb` or move TimescaleDB to a managed PostgreSQL/Timescale service.
- Put TLS, request logging, and edge rate limiting in front of the frontend service.
- Configure alerts on `/api/readiness` returning non-200 or collector logs containing remote refresh failures.
