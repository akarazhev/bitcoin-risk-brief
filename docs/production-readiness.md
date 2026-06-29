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

Before public launch, also complete and record:

- browser/device QA for the launch matrix;
- selected BTC data refresh path: downloaded CSV intake or optional CoinMarketCap API refresh;
- cache policy for public read endpoints;
- Cloudflare WAF, bot protection, and edge rate limits;
- documentation hygiene pass across roadmap, data pipeline, security, testing, operations, and deployment docs.

## Production Environment

Start from `.env.production.example`, not `.env.example`.

Required production changes:

- Set `APP_ENV=production`.
- Replace `DB_PASSWORD` with a long random value.
- Set `CORS_ORIGINS` to the public HTTPS domain only.
- Keep `FRONTEND_BIND_IP=127.0.0.1` when Cloudflare Tunnel is the only ingress.
- Set `COINMARKETCAP_API_KEY` only if the optional API refresh path is used.
- If no paid CoinMarketCap API account is available, implement and use the documented downloaded CSV intake workflow, and
  leave `COINMARKETCAP_API_KEY` empty intentionally.
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
- When the optional API path is configured, scheduled collector runs fetch only missing completed UTC days from
  CoinMarketCap.
- The production-pilot path should also support validated imports from operator-downloaded CoinMarketCap historical CSVs.
- Remote deltas and downloaded CSV inputs must exactly match the expected contiguous daily range.
- Non-contiguous or invalid inputs fail without rewriting the canonical CSV.
- CSV writes use atomic replace.
- Every import recalculates all risk rows and removes DB rows after the CSV tail.

## Performance And Caching Gate

Before public traffic, define and verify the cache policy for public read endpoints:

- latest risk;
- risk history;
- risk levels;
- daily brief;
- readiness.

The cache policy must document maximum age, invalidation or refresh behavior after a successful data import, and which
headers are expected at the public hostname. `POST /api/waitlist` must not be cached.

## Security Controls

- Public responses include baseline security headers at the nginx entrypoint.
- Backend responses also set API-safe security headers.
- `POST /api/waitlist` uses input validation, parameterized SQL, and an in-memory per-client rate limit.
- Waitlist contacts are stored server-side only.
- The frontend does not persist submitted contacts in browser storage.
- Cloudflare WAF managed rules, edge rate limits, and bot/spam controls should be active before public traffic.
- Abuse smoke checks should confirm bursty waitlist/API traffic is blocked or rate-limited without breaking normal use.

## Browser And Device Gate

Before public traffic, verify the page on current desktop Chrome, Safari, Firefox, mobile Safari, and mobile Chrome. The
check should cover loading, degraded readiness, API errors, chart rendering, waitlist states, locale behavior, and common
mobile/desktop viewport widths.

## Remaining External Operations

These are operational tasks outside this repository:

- Run one live data refresh/import on the production host before public launch, using either the optional
  `COINMARKETCAP_API_KEY` path or the validated downloaded CSV workflow.
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
