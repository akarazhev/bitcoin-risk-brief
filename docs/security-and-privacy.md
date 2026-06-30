# Security and Privacy

## Security Headers

Public responses from the nginx entrypoint include:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy` for the static frontend and API calls

Backend API responses also include API-safe security headers. In production mode, backend responses include HSTS.

## Secrets

Secrets must be provided through environment variables. Do not commit `.env` files.

Production-sensitive variables:

- `DB_PASSWORD`
- `DATABASE_URL`
- `COINMARKETCAP_API_KEY`, if the optional API refresh path is used
- `CLOUDFLARE_API_TOKEN`, if the edge rules helper is used
- `CLOUDFLARE_TUNNEL_TOKEN`

Use `.env.production.example` as a template and replace all placeholder values before deployment.

## Input Validation

The backend validates:

- waitlist contacts;
- locale values;
- waitlist source strings;
- API query parameters through FastAPI/Pydantic;
- risk source rows before computing risk.

## SQL Safety

Database writes and reads use asyncpg parameterized queries. No user input is concatenated into SQL strings.

## Waitlist Privacy

Waitlist contacts are stored in PostgreSQL. The frontend does not store submitted contacts in `localStorage` or other persistent browser storage.

The product currently has no authentication and no user accounts. Waitlist contacts are operational lead data and should be handled as PII.

## Rate Limiting

`POST /api/waitlist` has an in-memory fixed-window per-client rate limit controlled by
`WAITLIST_RATE_LIMIT_PER_HOUR`. The client key prefers Cloudflare's `CF-Connecting-IP` header, then
`X-Forwarded-For`, then the socket host. This protects a single-instance pilot deployment from simple abuse, but
Cloudflare edge limits are still required for public traffic.

Initial Cloudflare rate-limit rules:

| Scope | Expression | Limit | Action |
| --- | --- | --- | --- |
| Waitlist burst | `http.request.method eq "POST" and http.request.uri.path eq "/api/waitlist"` | 5 requests per minute per IP | Managed challenge, then block if repeated. |
| API burst | `starts_with(http.request.uri.path, "/api/")` | 120 requests per minute per IP | Managed challenge or throttle. |
| Static page | hostname only | Use analytics first | Do not challenge normal page loads unless abuse appears. |

Keep verified search and uptime-monitoring bots allowed where possible. Normal first-page use currently makes a small
number of GET requests to `/api/readiness`, `/api/risk/latest`, `/api/risk/history`, `/api/risk/levels`, and
`/api/brief/latest`, so the API burst rule leaves room for reloads without allowing scraping bursts.

Use the repository helper to render and apply the Cloudflare Rulesets API configuration:

```bash
python3 scripts/cloudflare_edge_rules.py render --hostname risk.example.com
CLOUDFLARE_API_TOKEN=... python3 scripts/cloudflare_edge_rules.py apply --zone-id "${CLOUDFLARE_ZONE_ID}" --hostname risk.example.com
```

The helper preserves unrelated Cloudflare rules and replaces only rules with refs starting `bitcoin-risk-brief:`.

## Bot And Abuse Protection

The public pilot should assume automated traffic will hit both static pages and API endpoints. The in-memory backend
waitlist limiter is only a fallback control; it is not enough by itself for public exposure.

Before launch, configure and verify:

- Cloudflare WAF managed rules for common web attacks;
- the repo-managed custom bot challenge for suspicious waitlist submissions plus Cloudflare Bot Fight Mode,
  Super Bot Fight Mode, or the equivalent bot protection available on the active plan;
- edge rate limits for `POST /api/waitlist` and bursty `/api/*` traffic using the starting thresholds above;
- a cache rule that respects origin `Cache-Control` for public GET endpoints and bypasses `POST /api/waitlist`;
- backend API access logs that include method, path, status, client key, Cloudflare ray ID, cache status, and duration
  without logging waitlist contact values;
- backend body-size and validation behavior for malformed waitlist and API requests.

If normal edge rate limiting is not enough, add a human-verification step such as Cloudflare Turnstile to the waitlist
flow before expanding traffic.

## Caching Safety

The backend caches these public read endpoints:

- `/api/readiness`
- `/api/risk/latest`
- `/api/risk/history`
- `/api/risk/levels`
- `/api/brief/latest`

Cached responses include `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`. Defaults are:

- `PUBLIC_CACHE_TTL_SECONDS=300` for the backend in-process cache;
- `PUBLIC_CACHE_MAX_AGE_SECONDS=60` for browser and edge freshness;
- `PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS=300` for compatible shared caches.

`X-Cache-Version` is derived from the latest `btc_risk_validation` marker. Successful imports rewrite that marker, so the
next backend read uses a new cache version and rebuilds from the database instead of serving the old in-process payload.
Cloudflare should either respect the short origin `max-age` or be purged after production imports when an immediate public
snapshot is required.

`POST /api/waitlist` is explicitly uncached with `Cache-Control: no-store` and `Pragma: no-cache` on success, validation
errors, and backend rate-limit responses.

## Known External Requirements

Before public launch, configure:

- HTTPS/TLS termination;
- production request logs;
- host or managed database backups;
- alerts on `/api/readiness` failures;
- edge/WAF rate limiting if exposed publicly;
- bot/spam controls for the waitlist flow;
- the accepted cache policy for public read endpoints.
