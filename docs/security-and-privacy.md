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

The public note does not publish a support address or promise a response time. The 2026-07-12 operator decision pass and
later 2026-07-12 support readiness evidence record sanitized waitlist owner, cadence, retention,
deletion/unsubscribe category, manual follow-up decisions, and support mailbox readiness. Exact support addresses and
provider details stay outside Git. The 2026-07-11 desktop/mobile public smoke observed the note on the public host
without any waitlist POSTs.

The product currently has no authentication and no user accounts. Waitlist contacts are operational lead data and should be handled as PII.

The dedicated support contact path for deletion and unsubscribe requests is created and ready, with exact addresses kept
outside Git. If the project adds email or Telegram delivery later, update this section before sending recurring messages.

Before recurring email or Telegram delivery, also complete the deferred email/outreach readiness gate: opt-in source,
sender or bot ownership, unsubscribe or stop handling, provider recovery, no-advice framing, and delivery privacy copy.

## Launch Governance Status

The current launch governance checklist and 2026-07-12 sanitized operator decision register are recorded in
[Production Readiness](production-readiness.md). Security and privacy status as of the 2026-07-10 gap pass, local
metadata implementation, focused local accessibility pass, local dependency/license evidence pass, and current decision
register:

Use [docs/operator-launch-decision-packet-template.md](operator-launch-decision-packet-template.md) to collect sanitized
operator decisions outside Git before copying final outcomes into the launch register. The template is not completed
evidence.

| Area | Status classification | Notes |
| --- | --- | --- |
| Privacy, terms, and disclaimer posture | public-host smoke verified; sanitized operator decisions partial | The frontend includes a compact public privacy/terms/disclaimer note near the waitlist with no-advice, no sensitive-info, waitlist storage, operational-log, no recommendation, no paid-SLA, and current no product analytics/tracking-cookie source-code statements. The 2026-07-11 desktop/mobile public smoke observed the privacy/disclaimer note and no waitlist POSTs. The 2026-07-12 operator decision pass records waitlist handling and support-path category, and the later 2026-07-12 support readiness evidence records support mailbox readiness; legal approval, full privacy policy, and terms-of-service decisions remain incomplete. |
| Waitlist owner, cadence, retention, deletion, and unsubscribe path | resolved for sanitized pilot governance | Waitlist contacts remain server-side operational lead data in PostgreSQL. Owner role is founder/operator, review cadence is several times per week during pilot, retention lasts until beta ends with earlier operator-approved deletion on request, and follow-up is manual founder/operator only. Deletion/unsubscribe requests use manual requests through the dedicated support contact path kept outside Git. Do not commit personal contact details, raw contacts, raw output, or query details. |
| Support/contact identity | completed for first-traffic readiness | The support/contact path category is a dedicated support mailbox with a project-domain alias; exact addresses and provider details are kept outside Git. The support path was checked by the founder/operator. No public support SLA, help center, or paid-user support process is implied. |
| Credential and account ownership | completed for first-traffic readiness | GitHub, Cloudflare/domain, server, secrets/.env, and backups owner role is founder/operator. The account recovery record is created outside Git and current. Actual account holders, recovery channels, secret locations, account IDs, and private recovery paths must stay in an operator-controlled record outside this repository. |
| Data-source terms and attribution review | accepted limitation for unpaid pilot; commercial/broader launch pending | Current product status is unpaid/non-commercial pilot. Source terms owner role is founder/operator. If demonstrated interest or paid/commercial use appears, the operator will buy the appropriate plan or make the required terms/plan decision. Terms review or paid plan remains required before commercial claims, paid beta, or broader distribution; this is not legal approval or commercial readiness. |
| Dependency and security maintenance cadence | partial; owner/cadence recorded, external evidence pending | `.github/dependabot.yml` is now present with conservative monthly version-update checks for frontend npm, backend and collector pip requirements, GitHub Actions, Dockerfiles, and a root `docker-compose` ecosystem entry for Compose-style image references. Dependency/security owner role is founder/operator, with monthly review cadence during pilot. GitHub-hosted Dependabot execution, first PR evidence, external dependency/license confirmation, vulnerability/advisory clearance, and legal compatibility remain pending. [Dependency and License Review](dependency-license-review.md) records the 2026-07-10 local inventory and the local automation configuration limits. |
| Accessibility and metadata evidence | partial/blocker; accessibility gap not accepted | Browser-capable public-hostname QA and the 2026-07-10 local Playwright profile smoke are recorded with limitations. `@axe-core/playwright` is integrated into the smoke suite, and the focused local axe scan passed across Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles with no reported violations. Manual keyboard, screen-reader/assistive-tech, native/physical-device, production-host accessibility, and full compliance evidence remain pending and are required before first traffic. Public metadata verification on 2026-07-11 found title, description, canonical URL, Open Graph type/title/description/url/site name, and Twitter card/title/description, with image metadata intentionally omitted because no real repo-served production image asset exists. |

Pre-traffic gate boundary after the 2026-07-12 operator decision pass and later support/recovery readiness evidence:
public-host privacy/disclaimer smoke and metadata verification are recorded, and sanitized waitlist/support/account
decisions are completed for first-traffic readiness. They do not prove legal approval, commercial readiness, full license
compliance, full accessibility/WCAG conformance, production-host accessibility, or external/manual dependency-license
confirmation. Record only sanitized operator decisions and keep private contacts, account details, tokens, `.env` values,
raw logs, dashboard URLs, and raw waitlist contacts out of repository notes.

## Product Analytics Privacy

As of the 2026-07-10 local source inspection, frontend and backend application code did not contain product analytics or
tracking-cookie code. Future source changes must recheck this before making any public no-analytics or no-cookie claim.
Cloudflare Web Analytics automatic setup and Beacon injection are intentionally disabled for the production pilot. The
frontend CSP must not allow `static.cloudflareinsights.com` unless a later analytics/privacy design updates the public UI
copy, retention rules, and operator runbooks. Static frontend responses include `Cache-Control` directives with
`no-transform` so the Cloudflare proxy should not rewrite the HTML to inject third-party scripts.

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

`GET /api/readiness` is the live freshness/status endpoint and is intentionally uncached with `Cache-Control: no-store`
and `Pragma: no-cache`.

The backend caches these public product read endpoints:

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

Before broader public launch, configure:

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

For the small operator-watched pilot, use the current accepted limitations and remaining blocker register in
[Production Readiness](production-readiness.md).
