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

Local public-page implementation recorded on 2026-07-10: the frontend includes a compact expandable
privacy/terms/disclaimer note near the waitlist. The note states that Bitcoin Risk Brief is informational research only,
not financial advice, investment advice, or a trading recommendation; that users should not enter sensitive
information; that no buy, sell, portfolio, or trading action is recommended; and that no paid support SLA is provided.
It summarizes the implemented waitlist behavior: the app stores the submitted contact value, a normalized copy, contact
type, locale, source, status, and timestamps. It also states that operational logs may include request method, path,
status, client key, Cloudflare ray ID, cache status, and timing.

The public note does not promise deletion, unsubscribe, support, response time, owner, cadence, or retention handling
because those operator decisions are not recorded in this repository. The 2026-07-11 desktop/mobile public smoke observed
the note on the public host without any waitlist POSTs.

The product currently has no authentication and no user accounts. Waitlist contacts are operational lead data and should be handled as PII.

Before active traffic, finish the remaining waitlist-contact handling decisions: how long contacts are kept, who can
access them, how manual outreach works, and how a user can unsubscribe or request deletion. If the project adds email or
Telegram delivery later, update this section before sending recurring messages.

Before recurring email or Telegram delivery, also complete the deferred email/outreach readiness gate: opt-in source,
sender or bot ownership, unsubscribe or stop handling, provider recovery, no-advice framing, and delivery privacy copy.

## Launch Governance Status

The current launch governance checklist and 2026-07-11 sanitized operator decision register are recorded in
[Production Readiness](production-readiness.md). Security and privacy status as of the 2026-07-10 gap pass, local
metadata implementation, focused local accessibility pass, local dependency/license evidence pass, and current decision
register:

| Area | Status classification | Notes |
| --- | --- | --- |
| Privacy, terms, and disclaimer posture | public-host smoke verified for 2026-07-11 update; operator decisions pending | The frontend includes a compact public privacy/terms/disclaimer note near the waitlist with no-advice, no sensitive-info, waitlist storage, operational-log, no recommendation, no paid-SLA, and current no product analytics/tracking-cookie source-code statements. The 2026-07-11 desktop/mobile public smoke observed the privacy/disclaimer note and no waitlist POSTs. This does not resolve waitlist owner, review cadence, retention, deletion, unsubscribe, support/contact identity, legal approval, full privacy policy, or terms-of-service decisions. |
| Waitlist owner, cadence, retention, deletion, and unsubscribe path | pending operator decision | Waitlist contacts remain server-side operational lead data in PostgreSQL. The repository does not name an owner role, review cadence, retention period or deferral, deletion path, or unsubscribe path. Do not invent or commit personal contact details here. |
| Support/contact identity | partial; no paid SLA recorded, contact path pending | One operator-owned public contact path is required for deletion, unsubscribe, product questions, bug reports, and professional/API/license interest, unless intentionally deferred. No public support SLA, help center, or paid-user support process is implied. |
| Credential and account ownership | pending outside-Git record evidence | The account categories below are the required ownership categories. Actual account holders, recovery channels, secret locations, account IDs, and private recovery paths must stay in an operator-controlled record outside this repository. |
| Data-source terms and attribution review | pending review outcome | No completed CoinMarketCap public CSV, optional CoinMarketCap API, or future methodology-source terms review evidence is recorded here. Record a sanitized outcome before broader launch or commercial/portfolio source-rights claims: passed, accepted limitation, or pending. |
| Dependency and security maintenance cadence | partial; local automation config and dependency/license evidence recorded | `.github/dependabot.yml` is now present with conservative monthly version-update checks for frontend npm, backend and collector pip requirements, GitHub Actions, Dockerfiles, and a root `docker-compose` ecosystem entry for Compose-style image references. GitHub-hosted Dependabot execution, first PR evidence, and Podman-specific filename handling remain pending until the config is merged/pushed and observed. Manual monthly review still needs to cover advisories, vulnerability scans, secret-scan output, Python transitive inventory, container image/OS package licenses, GitHub Actions/license posture, project license choice, and legal compatibility. [Dependency and License Review](dependency-license-review.md) records the 2026-07-10 local inventory and the local automation configuration limits. |
| Accessibility and metadata evidence | partial; accepted-limitation decision pending | Browser-capable public-hostname QA and the 2026-07-10 local Playwright profile smoke are recorded with limitations. `@axe-core/playwright` is integrated into the smoke suite, and the focused local axe scan passed across Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles with no reported violations. The chart panels now include a screen-reader-only current summary plus recent risk-history and threshold tables, verified locally. Waitlist submit feedback now exposes polite status semantics for submitting/success states and alert semantics for errors; automated keyboard/focus smoke verifies tab and reverse-tab movement through the public controls using mocked local API routes. Manual keyboard, screen-reader/assistive-tech, native/physical-device, production-host accessibility, and full compliance evidence remain pending unless explicitly accepted as a limitation for an operator-watched pilot. Public metadata verification on 2026-07-11 found title, description, canonical URL, Open Graph type/title/description/url/site name, and Twitter card/title/description, with image metadata intentionally omitted because no real repo-served production image asset exists. |

Pre-traffic gate boundary after the 2026-07-11 backup-gated update evidence: public-host privacy/disclaimer smoke and
metadata verification are recorded for that update, and local accessibility improvements, dependency/license inventory,
and Dependabot configuration remain repository-local evidence. They do not prove legal approval, data-source terms
approval, full license compliance, full accessibility/WCAG conformance, production-host accessibility, external/manual
dependency-license confirmation, waitlist retention/deletion/unsubscribe decisions, or support/contact ownership. Record
only sanitized operator decisions and keep private contacts, account details, tokens, `.env` values, raw logs, dashboard
URLs, and raw waitlist contacts out of repository notes.

## Product Analytics Privacy

As of the 2026-07-10 local source inspection, frontend and backend application code did not contain product analytics or
tracking-cookie code. Future source changes must recheck this before making any public no-analytics or no-cookie claim.

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

If a fuller separate privacy policy or terms page is published later, it should summarize these analytics and waitlist
choices without implying financial advice, investment advice, or trading recommendations.

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
