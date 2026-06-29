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

`POST /api/waitlist` has an in-memory fixed-window per-client rate limit. This protects a single-instance pilot deployment from simple abuse, but production should still add edge-level rate limiting.

## Bot And Abuse Protection

The public pilot should assume automated traffic will hit both static pages and API endpoints. The in-memory backend
waitlist limiter is only a fallback control; it is not enough by itself for public exposure.

Before launch, configure and verify:

- Cloudflare WAF managed rules for common web attacks;
- edge rate limits for `POST /api/waitlist` and bursty `/api/*` traffic;
- bot or challenge controls that can be tightened if waitlist spam appears;
- request logging that preserves enough metadata to investigate abusive traffic without logging waitlist contacts in
  clear operational channels;
- backend body-size and validation behavior for malformed waitlist and API requests.

If normal edge rate limiting is not enough, add a human-verification step such as Cloudflare Turnstile to the waitlist
flow before expanding traffic.

## Caching Safety

Public read endpoints may be cached after an explicit cache policy is implemented. `POST /api/waitlist` must never be
cached. Any caching layer must have a clear invalidation or refresh path after a successful data import so stale risk data
does not remain visible as fresh data.

## Known External Requirements

Before public launch, configure:

- HTTPS/TLS termination;
- production request logs;
- host or managed database backups;
- alerts on `/api/readiness` failures;
- edge/WAF rate limiting if exposed publicly;
- bot/spam controls for the waitlist flow;
- the accepted cache policy for public read endpoints.
