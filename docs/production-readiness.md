# Production Readiness

This document defines the current production-pilot gate for Bitcoin Risk Brief.

## Current Public Pilot Snapshot

Recorded on 2026-07-01 for `https://bitcoinriskbrief.minihub.app`:

- Cloudflare Rulesets API apply succeeded for the custom waitlist bot challenge, one waitlist rate-limit rule, waitlist
  cache bypass, and public-read origin-cache rules.
- The active Cloudflare plan required the Free-plan-compatible rate-limit settings:
  `--skip-managed-waf --waitlist-rate-limit-only --rate-limit-period 10 --rate-limit-mitigation-timeout 10`.
- `GET /api/health` returned 200 with `{"status":"ok"}`.
- `GET /api/readiness` returned 200 with `status: ready`, `source: coinmarketcap_csv`, `latest_date: 2026-06-30`,
  `covered_end: 2026-06-30`, and `row_count: 5832`.
- `GET /api/risk/latest` returned 200 with `X-Cache: HIT`.
- Conditional `GET /api/risk/latest` with `If-None-Match` returned 304 with `X-Cache: HIT`.

This snapshot confirms the public hostname, readiness path, and public-read cache behavior. It does not replace the
remaining launch checks: waitlist production smoke, browser/device QA on the public hostname, backup/restore setup,
alerts, and the first traffic test.

## Release Gates

Run these before every deploy:

```bash
./scripts/manage.sh test-python
python3 -m compileall backend collector
npm test --prefix frontend
npm run build --prefix frontend
npm run smoke --prefix frontend
./scripts/manage.sh validate
podman-compose -f podman-compose.yml build backend data-collector frontend
./scripts/manage.sh run-now
python3 scripts/cloudflare_edge_rules.py render --hostname risk.example.com > /tmp/bitcoin-risk-cloudflare-edge.json
```

If the production refresh path is no-key CoinMarketCap public data instead of the optional API key path, run this before
the final readiness check:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
```

If the public endpoint automation is unavailable, stage a manually downloaded CSV and run:

```bash
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
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

Verify public read cache headers and conditional revalidation:

```bash
curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest
ETAG="$(curl -sD - -o /tmp/bitcoin-risk-latest.json http://localhost:3001/api/risk/latest | awk 'BEGIN{IGNORECASE=1} /^etag:/ {print $2}' | tr -d '\r')"
curl -s -o /dev/null -w "%{http_code}\n" -H "If-None-Match: ${ETAG}" http://localhost:3001/api/risk/latest
```

The first response should include `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`. The conditional request
should print `304`.

Before public launch, also complete and record:

- browser/device QA for the launch matrix;
- selected BTC data refresh path: automatic public CSV download, manual downloaded CSV intake, or optional CoinMarketCap API refresh;
- selected deployment path: direct Git workflow or USB-based local-server deployment. If USB deployment is used, verify
  the kit contains a filtered project snapshot, server-kit scripts, docs, manifest, and checksums, and does not contain
  local `.env`, `.git`, backups, dependency caches, build output, or container images;
- cache policy for public read endpoints;
- Cloudflare WAF, bot protection, cache rules, and edge rate limits rendered and applied with
  `scripts/cloudflare_edge_rules.py`, plus dashboard bot protection enabled where required by the Cloudflare plan;
- launch operations and governance posture: privacy/terms/disclaimer copy, post-waitlist handling, dependency/security
  maintenance cadence, credential/account ownership, resource monitoring, data-source terms, accessibility, metadata,
  and incident response notes;
- release feedback and operational evidence posture: release notes or decision log, first-user feedback review path,
  support/contact identity, dependency-license review, and launch/backup/restore evidence;
- data correction and service-target posture: bad CSV/import/risk correction flow, correction-note rules, cache
  correction safety, freshness target, RPO/RTO boundaries, and pilot downtime tolerance;
- import provenance and source archive posture: source snapshot, import manifest, `sha256`, retrieval metadata, row
  count, covered range, expected tail, validation/readiness output, cache evidence, and storage outside the repository;
- documentation hygiene pass across roadmap, data pipeline, security, testing, operations, and deployment docs;
- after implementation freeze, a private/portfolio presentation pass covering the root README, docs index, sibling
  product-ideas brief, GitHub description/topics, optional screenshot or GIF, and repository hygiene.

## Production Environment

Start from `.env.production.example`, not `.env.example`.

Required production changes:

- Set `APP_ENV=production`.
- Replace `DB_PASSWORD` with a long random value.
- Set `CORS_ORIGINS` to the public HTTPS domain only.
- Keep `FRONTEND_BIND_IP=127.0.0.1` when Cloudflare Tunnel is the only ingress.
- Set `COINMARKETCAP_API_KEY` only if the optional API refresh path is used.
- If no paid CoinMarketCap API account is available, use the documented automatic or manual public CSV workflow and leave
  `COINMARKETCAP_API_KEY` empty intentionally.
- Keep `DATA_FRESHNESS_MAX_AGE_DAYS=2` unless the product explicitly accepts slower updates.
- Tune `WAITLIST_RATE_LIMIT_PER_HOUR` for expected traffic.
- Keep the public cache defaults unless launch testing shows a reason to tune them:
  `PUBLIC_CACHE_TTL_SECONDS=300`, `PUBLIC_CACHE_MAX_AGE_SECONDS=60`, and
  `PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS=300`.

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
- Before active traffic, the production scheduler should be hardened and verified to use public CoinMarketCap download
  first when `COINMARKETCAP_API_KEY` is empty. Until that is implemented, operators must run
  `./scripts/manage.sh download-cmc-csv` manually when the canonical CSV is stale.
- The production-pilot path supports automatic public CoinMarketCap downloads and validated imports from
  operator-downloaded CoinMarketCap historical CSVs.
- Remote deltas, public downloads, and downloaded CSV imports must exactly match the expected contiguous daily range.
- Non-contiguous or invalid inputs fail without rewriting the canonical CSV.
- CSV writes use atomic replace.
- Every import recalculates all risk rows and removes DB rows after the CSV tail.

## Performance And Caching Gate

Before public traffic, verify the implemented cache policy for public read endpoints:

- latest risk;
- risk history;
- risk levels;
- daily brief;
- readiness.

These endpoints should return `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`. Backend cache invalidation is
versioned from `btc_risk_validation`; after a successful import, the collector rewrites validation and the next backend
read rebuilds against the new version. `POST /api/waitlist` must return `Cache-Control: no-store` and must not be cached
by Cloudflare.

Before active traffic, measure first-load latency for both backend `X-Cache: MISS` and `X-Cache: HIT` responses on the
public hostname. If the first miss after backend startup or nightly import is user-visible, implement public payload
cache warmup for the standard endpoint set and consider precomputing expensive payloads such as `/api/risk/levels`.
Warmup must preserve `X-Cache-Version` invalidation and must not hide stale readiness.

At the Cloudflare edge, respect origin cache headers for the public GET API paths and bypass `/api/waitlist`. If a launch
snapshot must reflect a just-completed import immediately, purge the public hostname or wait for
`PUBLIC_CACHE_MAX_AGE_SECONDS`.

## Security Controls

- Public responses include baseline security headers at the nginx entrypoint.
- Backend responses also set API-safe security headers.
- `POST /api/waitlist` uses input validation, parameterized SQL, and an in-memory per-client rate limit.
- Waitlist contacts are stored server-side only.
- The frontend does not persist submitted contacts in browser storage.
- Cloudflare WAF managed rules, edge rate limits, cache rules, and repo-managed waitlist bot challenge should be active
  before public traffic when the active Cloudflare plan is entitled to run them. Render/apply them with
  `scripts/cloudflare_edge_rules.py`. If the zone is on a Free plan, use the documented Free-plan-compatible subset and
  record the accepted limitation before first traffic.
- Cloudflare Bot Fight Mode, Super Bot Fight Mode, or equivalent dashboard bot protection should be enabled after the
  script is applied and smoke-tested.
- Initial Cloudflare limits should protect `POST /api/waitlist` at 5 requests per minute per IP and `/api/*` at 120
  requests per minute per IP, adjusted only after reviewing real traffic.
- Abuse smoke checks should confirm bursty waitlist/API traffic is challenged, blocked, or rate-limited without breaking
  normal page use.

## Browser And Device Gate

Before public traffic, verify the page on current desktop Chrome, Safari, Firefox, mobile Safari, and mobile Chrome. The
check should cover loading, degraded readiness, API errors, chart rendering, waitlist states, enabled-locale behavior,
localized copy fit, first-viewport price model input labels, and common mobile/desktop viewport widths.

The automated frontend smoke matrix and current results are recorded in [Frontend QA](frontend-qa.md). Treat that as the
minimum automated check; repeat a short manual pass on the production hostname before public launch.

If the Phase 8 localization add-on is implemented before active traffic, include English, Russian, Spanish, and German in
the browser/device pass. Arabic and Chinese should remain disabled until their separate right-to-left, Simplified versus
Traditional, platform, and channel requirements are documented and tested.

## Remaining External Operations

These are operational tasks outside this repository.

Completed or partially completed as of 2026-07-01:

- Cloudflare Tunnel/public hostname is serving `https://bitcoinriskbrief.minihub.app`.
- Public `/api/health`, `/api/readiness`, `/api/risk/latest`, and conditional `/api/risk/latest` checks pass through
  Cloudflare.
- Cloudflare edge cache settings and the waitlist-specific rate-limit/custom challenge subset were applied with
  `scripts/cloudflare_edge_rules.py`.

Still required before treating the pilot as publicly launched:

- Confirm the production host runbook, `.env`, service path, and selected data-refresh workflow.
- If the production host is updated through USB, replace manual copying with the planned USB Update And Install Kit V2 or
  record the manual verification evidence until that script exists.
- Decide whether to accept the current Cloudflare Free-plan subset for first traffic or upgrade/configure additional WAF,
  bot protection, and broader API burst-rate-limit controls.
- Configure scheduled `./scripts/backup.sh` runs and copy backups off the server.
- Implement and verify scheduled public-download-first refresh if the production pilot will run without a
  `COINMARKETCAP_API_KEY`.
- Put request logging, backup health, and operational review in place.
- Configure alerts on `/api/readiness` returning non-200, readiness becoming stale after the nightly update window, or
  collector logs containing scheduled/public/API refresh failures.
- Complete a short browser/device QA pass on the public hostname.
- Submit a deliberate test waitlist lead and verify it is stored server-side without caching the response.
- Complete or explicitly defer the launch operations and governance checklist: privacy/terms, post-waitlist handling,
  credential ownership, resource monitoring, dependency/security maintenance, data-source terms, accessibility,
  SEO/social metadata, and incident response.
- Complete or explicitly defer the release feedback and operational evidence checklist: release notes or decision log,
  first-user feedback path, support/contact identity, dependency-license review, and launch/backup/restore evidence.
- Complete or explicitly defer the data correction and service-target checklist: bad-data correction flow, correction
  note rules, cache correction safety, freshness target, RPO/RTO boundaries, and pilot downtime tolerance.
- Complete or explicitly defer the import provenance and source archive checklist: source snapshot, import manifest,
  `sha256`, retrieval metadata, row count, covered range, expected tail, validation/readiness output, cache evidence, and
  storage outside the repository.
- Complete the documentation and portfolio presentation pass, including the sibling product-ideas brief, if the
  repository will be shown as a private/portfolio project.
- Capture the launch snapshot and run the first small traffic test.

## Related Docs

- [Architecture](architecture.md)
- [Data Pipeline](data-pipeline.md)
- [Security and Privacy](security-and-privacy.md)
- [Operations](operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Testing and Quality](testing-and-quality.md)
