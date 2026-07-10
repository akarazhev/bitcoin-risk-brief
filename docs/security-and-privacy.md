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

Before active traffic, decide and document the public privacy posture for waitlist contacts: how long contacts are kept,
who can access them, how manual outreach works, and how a user can unsubscribe or request deletion. If the project adds
email or Telegram delivery later, update this section before sending recurring messages.

Before recurring email or Telegram delivery, also complete the deferred email/outreach readiness gate: opt-in source,
sender or bot ownership, unsubscribe or stop handling, provider recovery, no-advice framing, and delivery privacy copy.

## Launch Governance Status

The current launch governance checklist is recorded in [Production Readiness](production-readiness.md). Security and
privacy status as of the 2026-07-10 gap pass, local metadata implementation, and focused local accessibility pass:

| Area | Status classification | Notes |
| --- | --- | --- |
| Privacy, terms, and disclaimer posture | accepted limitation for operator-watched first traffic | The README and product copy keep analytics/no-financial-advice framing, but no standalone public privacy policy or terms note is recorded. Before broader sharing, publish a short privacy/terms note for waitlist contacts and operational logs, or explicitly record the operator decision to defer it. |
| Waitlist owner, cadence, retention, deletion, and unsubscribe path | pending operator decision | Waitlist contacts remain server-side operational lead data in PostgreSQL. The repository does not name a lead owner, review cadence, retention period, deletion path, or unsubscribe channel. Do not invent or commit personal contact details here. |
| Support/contact identity | pending operator decision | One operator-owned path is required for deletion, unsubscribe, product questions, bug reports, and professional/API/license interest. No public support SLA, help center, or paid-user support process is implied. |
| Credential and account ownership | pending operator decision | The account categories below are the required ownership categories. Actual account holders, recovery channels, and secret locations must stay in an operator-controlled record outside this repository. |
| Data-source terms and attribution review | pending operator decision | No completed CoinMarketCap public CSV, optional CoinMarketCap API, or future methodology-source terms review evidence is recorded here. Record a sanitized review outcome before broader launch or commercial/portfolio source-rights claims. |
| Dependency and security maintenance cadence | passed with existing repo evidence | The cadence is a manual monthly review of container images, Python dependencies, npm dependencies, GitHub Actions versions, advisories, vulnerability scans, and secret-scan output until automation such as Dependabot or Renovate is chosen. The latest completed review evidence is not recorded yet. |
| Accessibility and metadata evidence | partial; local axe verified, metadata implemented locally, public verification pending | Browser-capable public-hostname QA and the 2026-07-10 local Playwright profile smoke are recorded with limitations. `@axe-core/playwright` is now integrated into the smoke suite, and the focused local axe scan passed across Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles with no reported violations. Manual keyboard, screen-reader/assistive-tech, native/physical-device, and chart alternative evidence remain pending. `frontend/index.html` now includes title, meta description, canonical URL, Open Graph, and Twitter summary-card metadata, with image metadata intentionally omitted because no real repo-served production image asset exists. Public-host metadata verification remains pending until deployment. |

## Product Analytics Privacy

Future persisted product analytics should collect only the fields needed to understand demand and abuse patterns. The
current backend access logs are operational logs; a product analytics table or aggregate should be designed separately
before the product relies on repeat-use, source-attribution, endpoint-usage, or integration counts.

Product analytics may store:

- event time bucket;
- normalized endpoint group and method;
- status code or status family;
- locale when provided;
- explicit source values such as `landing`, `agent_access`, `risk_signal_license`, `pwa`, `telegram_mini_app`, or
  `browser_extension`;
- rotating anonymous client or visitor hashes;
- user-agent family;
- cache status when available.

Product analytics must not store request bodies, waitlist contact values, raw IP addresses, full user-agent strings, or
detailed browser fingerprints. Do not join raw request history to waitlist contact values unless a later design explains
the need, consent basis, retention policy, and operator access controls.

If raw analytics events are introduced, retain them only briefly, for example 30-90 days, then keep aggregate daily stats
that do not contain contact values, raw IPs, or full user-agent strings. Future professional API usage tracking should
identify products or agents through API client records and key identifiers or hashes, not through raw IP addresses.

If a separate privacy policy or terms note is published for the public page, it should summarize these analytics and
waitlist choices without implying financial advice, investment advice, or trading recommendations.

## Account And Credential Ownership

Do not store production secrets in this repository. Before production or portfolio review, document where access is
managed for:

- GitHub repository permissions;
- Cloudflare account, zone, tunnel, and API token;
- domain registration if a custom domain is used;
- production `.env` storage;
- backup storage;
- server login or physical access;
- optional CoinMarketCap API key.

The ownership note should identify recovery paths and responsible operators, not secret values.

## Data Source Terms And Attribution

Before a data source becomes production-critical or enters methodology research, record the source URL, retrieval method,
observed availability limits, licensing or terms notes, attribution requirements, and fallback behavior. This applies to
CoinMarketCap public CSV use, optional CoinMarketCap API use, and future research sources such as Alternative.me or Coin
Metrics.

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

For the current `bitcoinriskbrief.minihub.app` Free-plan pilot, the accepted subset skips the managed WAF ruleset and the
broader `/api/*` burst rule, and uses Cloudflare's allowed 10-second rate-limit window:

```bash
CLOUDFLARE_API_TOKEN=... python3 scripts/cloudflare_edge_rules.py apply \
  --zone-id "${CLOUDFLARE_ZONE_ID}" \
  --hostname bitcoinriskbrief.minihub.app \
  --skip-managed-waf \
  --waitlist-rate-limit-only \
  --rate-limit-period 10 \
  --rate-limit-mitigation-timeout 10
```

The helper preserves unrelated Cloudflare rules and replaces only rules with refs starting `bitcoin-risk-brief:`.

## Bot And Abuse Protection

The public pilot should assume automated traffic will hit both static pages and API endpoints. The in-memory backend
waitlist limiter is only a fallback control; it is not enough by itself for public exposure.

Before launch, configure and verify:

- Cloudflare WAF managed rules for common web attacks when the active plan is entitled to run them, or a documented
  launch limitation/upgrade decision when it is not;
- the repo-managed custom bot challenge for suspicious waitlist submissions plus Cloudflare Bot Fight Mode,
  Super Bot Fight Mode, or the equivalent bot protection available on the active plan;
- edge rate limits for `POST /api/waitlist` and bursty `/api/*` traffic using the starting thresholds above, or the
  documented Free-plan-compatible waitlist-only subset for first traffic;
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
- the accepted cache policy for public read endpoints;
- privacy/terms/disclaimer posture and waitlist contact handling;
- production credential ownership and recovery paths;
- data-source terms and attribution notes.
