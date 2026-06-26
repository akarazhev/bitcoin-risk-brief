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
- `COINMARKETCAP_API_KEY`

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

## Known External Requirements

Before public launch, configure:

- HTTPS/TLS termination;
- production request logs;
- host or managed database backups;
- alerts on `/api/readiness` failures;
- edge/WAF rate limiting if exposed publicly.
