# Production Readiness

This document defines the current production-pilot gate for Bitcoin Risk Brief.

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

Also verify latest risk and risk levels are consistent:

```bash
python3 - <<'PY'
import json
from urllib.request import urlopen
latest = json.load(urlopen('http://localhost:3001/api/risk/latest'))['data']
levels = json.load(urlopen('http://localhost:3001/api/risk/levels'))
print(abs(latest['risk'] - levels['meta']['current_risk']))
PY
```

## Production Environment

Start from `.env.production.example`, not `.env.example`.

Required production changes:

- Set `APP_ENV=production`.
- Replace `DB_PASSWORD` with a long random value.
- Set `CORS_ORIGINS` to the public HTTPS domain only.
- Keep `FRONTEND_BIND_IP=127.0.0.1` when Cloudflare Tunnel is the only ingress.
- Set `COINMARKETCAP_API_KEY` to the production key.
- Keep `DATA_FRESHNESS_MAX_AGE_DAYS=2` unless the product explicitly accepts slower updates.
- Tune `WAITLIST_RATE_LIMIT_PER_HOUR` for expected traffic.

## Readiness Contract

`/api/readiness` returns HTTP 200 only when:

- latest risk data exists;
- validation data exists;
- validation row count is positive;
- risk range validation passed;
- latest risk timestamp matches validation coverage end;
- validation source is `coinmarketcap_csv`;
- data age is within `DATA_FRESHNESS_MAX_AGE_DAYS`.

A non-200 readiness response should block deploy promotion and should alert in production.

## Data Pipeline Guarantees

- `collector/btc-csv/btc_usd_daily.csv` is the canonical source.
- Scheduled collector runs fetch only missing completed UTC days from CoinMarketCap.
- Remote deltas must exactly match the requested contiguous daily range.
- Non-contiguous deltas fail without rewriting the CSV.
- CSV writes use atomic replace.
- Every import recalculates all risk rows and removes DB rows after the CSV tail.

## Security Controls

- Public responses include baseline security headers at the nginx entrypoint.
- Backend responses also set API-safe security headers.
- `POST /api/waitlist` uses input validation, parameterized SQL, and an in-memory per-client rate limit.
- Waitlist contacts are stored server-side only.
- The frontend does not persist submitted contacts in browser storage.

## Remaining External Operations

These are operational tasks outside this repository:

- Run one live `./scripts/manage.sh run-now` with the real `COINMARKETCAP_API_KEY` before public launch.
- Configure Cloudflare Tunnel for the public hostname and keep the frontend bound to localhost.
- Configure scheduled `./scripts/backup.sh` runs and copy backups off the server.
- Put TLS, request logging, WAF rules, and edge rate limiting in front of the frontend service.
- Configure alerts on `/api/readiness` returning non-200 or collector logs containing remote refresh failures.

## Related Docs

- [Architecture](architecture.md)
- [Data Pipeline](data-pipeline.md)
- [Security and Privacy](security-and-privacy.md)
- [Operations](operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Testing and Quality](testing-and-quality.md)
