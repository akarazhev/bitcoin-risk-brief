# Production Roadmap

This roadmap tracks the work needed to move Bitcoin Risk Brief from a local validation product to a production-pilot
service. The target is not a broad analytics platform. The target is one reliable public Bitcoin risk page, safe waitlist
capture, daily data freshness, and an operator workflow that can be monitored and rolled back.

## Target State

Production-pilot readiness means:

- the public page explains current BTC risk without implying certainty or financial advice;
- users can see whether the latest data is fresh and validation passed;
- the waitlist flow works without storing leads in browser storage;
- BTC data can be refreshed without requiring a paid CoinMarketCap API account;
- frequently requested public data loads quickly through an explicit caching strategy;
- public endpoints and the waitlist flow have bot, spam, and abuse protection at the edge and application layers;
- automated checks run before deploys and before changes enter `main`;
- the user interface has been checked across the target browsers, screen sizes, and devices;
- product, operations, security, testing, and data-pipeline docs are current and agree with the implemented system;
- the deployed stack can be updated, monitored, backed up, restored, and rolled back;
- the first traffic test can measure whether a single BTC risk signal creates waitlist and repeat-visit demand.

## Current Baseline

Already implemented:

- React frontend with EN/RU brief copy, risk history chart, risk levels chart, and waitlist form.
- FastAPI backend with latest risk, history, levels, brief, waitlist, health, and readiness endpoints.
- TimescaleDB storage and migration script.
- Canonical BTC CSV import and CoinMarketCap API delta refresh when an API key is configured.
- Validated operator-downloaded CoinMarketCap historical CSV import without a paid API key.
- Server-side waitlist storage with validation and rate limiting.
- Public read endpoint caching for readiness, latest risk, history, levels, and brief responses, with validation-versioned
  refresh after successful imports.
- No-store waitlist responses, backend request logging, and repo-managed Cloudflare WAF, waitlist bot-challenge,
  cache-rule, and edge rate-limit settings for the production pilot.
- Containerized local stack and Ubuntu plus Cloudflare Tunnel deployment docs.
- Production readiness, operations, security, testing, architecture, and data-pipeline documentation.

## Current Roadmap Status

Verified on 2026-07-01 from repository files, recent commit history, and public hostname smoke checks.

| Phase | Status | Repository evidence |
| --- | --- | --- |
| Phase 1: Public Trust Layer | Complete | `ca85ad4`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx` |
| Phase 2: Data Source Resilience And Documentation Hygiene | Complete | `9fe25cd`, `7f7b8c4`, `collector/collector/main.py`, `collector/tests/test_downloaded_csv_import.py`, `collector/tests/test_public_cmc_download.py` |
| Phase 3: CI And Quality Gates | Complete | `1b162a5`, `.github/workflows/ci.yml`, `docs/testing-and-quality.md` |
| Phase 4: Frontend Production Quality | Complete | `22793fb`, `frontend/e2e/frontend-quality.spec.ts`, `frontend/src/Chart.tsx`, `docs/frontend-qa.md` |
| Phase 5: Performance, Caching, And Abuse Protection | Complete in repository; Free-plan edge subset applied | `3c66df9`, `5bb179d`, `backend/app/public_cache.py`, `backend/app/main.py`, `scripts/cloudflare_edge_rules.py`, `backend/tests/test_cloudflare_edge_rules.py` |
| Phase 6: Production Environment And Deployment | In progress | `bitcoinriskbrief.minihub.app` public `/api/health`, `/api/readiness`, `/api/risk/latest`, and conditional `ETag` checks passed on 2026-07-01 |
| Phase 7: Backups, Restore, And Monitoring | Pending | Requires production backup schedule, off-server copy, restore drill, and alerts |
| Phase 8: Launch Checklist And First Traffic Test | Pending; public API smoke partially complete | Requires waitlist smoke, browser/device pass on the public hostname, launch snapshot, and first traffic test |
| Phase 9: Post-Launch Learning Loop | Pending | Starts after launch traffic creates usage evidence, including optional agent-access demand testing |
| Phase 10: Risk Methodology Research | Pending | Starts only after launch evidence justifies method work; current production metric remains `crypto-scout-canonical-v1` |

Current production-pilot progress after Phase 1-5:

- public hostname `bitcoinriskbrief.minihub.app` is connected through Cloudflare and returns 200 for `/api/health`,
  `/api/readiness`, and `/api/risk/latest`;
- public read caching is observable through `Cache-Control`, validation-versioned `ETag`, `X-Cache: HIT`, and a 304
  conditional response for `/api/risk/latest`;
- Cloudflare Rulesets API apply succeeded for the custom waitlist bot challenge, one waitlist rate-limit rule, waitlist
  cache bypass, and public-read origin-cache rules;
- the active Cloudflare plan did not entitle the zone to execute the managed WAF ruleset, more than one rate-limit rule,
  a rate-limit period other than 10 seconds, or a mitigation timeout other than 10 seconds, so the current public edge
  config intentionally uses the Free-plan-compatible subset.

Remaining production-pilot gaps:

- confirm the production host runbook, `.env`, service path, and data-refresh workflow are the documented source of truth;
- decide whether to accept the current Cloudflare Free-plan subset for first traffic or upgrade/configure additional WAF,
  bot protection, and broader API burst-rate-limit controls;
- daily backups, off-server copy, restore drill, and monitoring alerts still need to be configured and verified;
- a launch snapshot, waitlist test, browser/device check on the public hostname, and first traffic test still need to run;
- post-launch learning cannot start until real usage and waitlist evidence exist.

## Roadmap Phases

### Phase 1: Public Trust Layer

Status: Complete. Verified by commit `ca85ad4`, `frontend/src/App.tsx`, and `frontend/src/App.test.tsx`.

Goal: make the public page honest enough for first external users.

Deliverables:

- Fetch `/api/readiness` from the frontend.
- Render a compact freshness and validation badge near the latest data date.
- Show methodology version, latest date, covered end, and data age.
- Add a concise disclaimer: risk levels are scenario outputs, not financial advice or trading instructions.
- Add a public methodology link or compact methodology section that references `crypto-scout-canonical-v1`.
- Derive and render next-band price callouts for the nearest `0.35` and `0.65` risk thresholds.

Acceptance criteria:

- A user can tell whether the latest import passed validation before trusting the chart.
- A user can find the methodology reference from the product page.
- The page states that risk levels are not buy/sell instructions.
- Tests cover readiness rendering, degraded state copy, methodology/disclaimer copy, and next-band callouts.

### Phase 2: Data Source Resilience And Documentation Hygiene

Status: Complete. Verified by commits `9fe25cd` and `7f7b8c4`, collector CLI support in `collector/collector/main.py`,
and CSV intake tests in `collector/tests/test_downloaded_csv_import.py` and `collector/tests/test_public_cmc_download.py`.

Goal: keep BTC data fresh without depending on a paid CoinMarketCap API account and keep documentation aligned with the
actual system.

Deliverables:

- Add an operator workflow for downloading BTC historical CSV data from
  `https://coinmarketcap.com/currencies/bitcoin/historical-data/`.
- Add a validated import path that stages the downloaded CSV, normalizes it to the canonical local CSV shape, checks daily
  continuity, and atomically replaces the canonical CSV only after validation passes.
- Keep the official CoinMarketCap API delta refresh as an optional path, not as a production-pilot requirement.
- Document how operators verify the CSV tail date, run import/backfill, and confirm `/api/readiness`.
- Clean up project documentation so current behavior, planned work, and historical implementation notes are clearly
  separated.
- Remove or revise stale documentation that still describes older data-source, deployment, or launch assumptions.

Acceptance criteria:

- A production operator can refresh BTC data from a downloaded CoinMarketCap historical CSV without a paid API key.
- Invalid, partial, non-contiguous, or schema-incompatible CSV downloads do not replace the canonical CSV.
- `docs/data-pipeline.md`, `docs/operations.md`, and `docs/production-readiness.md` agree on the supported refresh paths.
- `docs/README.md` clearly identifies the current operational docs and the historical design/spec archive.

### Phase 3: CI And Quality Gates

Status: Complete. Verified by commit `1b162a5`, `.github/workflows/ci.yml`, and `docs/testing-and-quality.md`.

Goal: protect `main` and make future changes cheap to verify.

Deliverables:

- Add GitHub Actions for backend tests, collector tests, frontend tests, and frontend build.
- Include `python3 -m compileall backend collector`.
- Add a compose/build validation job if runner time is acceptable.
- Document required checks and branch protection expectations.

Acceptance criteria:

- Every push to `main` runs the automated checks.
- A failing backend, collector, frontend test, or frontend build blocks promotion.
- The CI workflow is documented in `docs/testing-and-quality.md`.

### Phase 4: Frontend Production Quality

Status: Complete. Verified by commit `22793fb`, `frontend/e2e/frontend-quality.spec.ts`, `frontend/src/Chart.tsx`, and
`docs/frontend-qa.md`. Repeat a short manual pass on the public hostname during Phase 8.

Goal: reduce avoidable frontend and product-experience risk before launch.

Deliverables:

- Split or lazy-load the ECharts bundle so the main chunk warning is removed or explicitly accepted.
- Add a smoke or e2e check for desktop and mobile layout.
- Verify that chart canvases render non-empty and occupy the expected container width.
- Exercise loading, empty, degraded readiness, and API error states.
- Check the interface in the launch browser/device matrix, including current Chrome, Safari, Firefox, mobile Safari, and
  mobile Chrome.
- Improve visual styling, spacing, responsive behavior, and chart readability while keeping the page focused on one BTC
  risk product.
- Keep the page focused on the BTC risk product, not a broad dashboard.

Acceptance criteria:

- `npm run build --prefix frontend` completes without unexpected warnings, or the remaining warning is documented and accepted.
- Automated smoke checks detect blank charts or obvious mobile layout breakage.
- Error and degraded-data states are usable and do not look like successful fresh data.
- Manual or automated browser/device QA results are documented before public launch.
- The public page looks production-ready on desktop and mobile without adding unrelated dashboard scope.

### Phase 5: Performance, Caching, And Abuse Protection

Status: Complete in repository and partially applied at the public edge. Verified by commits `3c66df9` and `5bb179d`,
`backend/app/public_cache.py`, `backend/app/main.py`, `scripts/cloudflare_edge_rules.py`, and
`backend/tests/test_cloudflare_edge_rules.py`. On 2026-07-01, `bitcoinriskbrief.minihub.app` returned 200 for public
GET smoke checks and 304 for conditional `/api/risk/latest` revalidation with `X-Cache: HIT`.

The active Cloudflare plan is using the Free-plan-compatible subset: custom waitlist bot challenge, one waitlist
rate-limit rule with `period=10` and `mitigation_timeout=10`, waitlist cache bypass, and origin-header-respecting cache
rules for public read endpoints. Managed WAF execution and the broader `/api/*` burst limit remain launch-risk items
unless the Cloudflare plan is upgraded or the limitation is explicitly accepted for first traffic.

Goal: make the public page fast enough for first traffic and resistant to simple bot or abuse traffic.

Deliverables:

- Define cache headers or an application cache for public read endpoints: latest risk, history, levels, brief, and
  readiness.
- Invalidate or refresh cached data after a successful collector/import run so users do not see stale risk data after the
  canonical CSV changes.
- Document which endpoints must not be cached, especially `POST /api/waitlist`.
- Configure Cloudflare WAF managed rules, bot protections appropriate for a public pilot, and edge rate limits for
  `/api/waitlist` and `/api/*`.
- Keep backend waitlist rate limiting as an application-level fallback.
- Add request logging or operational checks that help distinguish real users from abusive traffic.

Acceptance criteria:

- Repeated public page loads do not require unnecessary database work for unchanged daily data.
- Cache behavior is observable and has a clear invalidation path after data refresh.
- Waitlist submissions cannot be cached and still store server-side only.
- Basic bot, spam, and burst-traffic tests are blocked or rate-limited without breaking normal page use.
- Security and caching expectations are documented in `docs/security-and-privacy.md` and `docs/production-readiness.md`.

### Phase 6: Production Environment And Deployment

Status: In progress. Public hostname smoke checks passed on 2026-07-01 for `bitcoinriskbrief.minihub.app`. The remaining
work is to confirm the production host runbook, environment, service path, and refresh workflow as documented operations.

Goal: run the full stack on the intended production-pilot host.

Deliverables:

- Create production `.env` from `.env.production.example`.
- Set production values for `APP_ENV`, `DB_PASSWORD`, `CORS_ORIGINS`, freshness limit, waitlist rate limit, and either
  the optional `COINMARKETCAP_API_KEY` or the documented CSV download/import workflow.
- Deploy the repository under `/opt/bitcoin-risk-brief`.
- Run `validate`, `start`, `migrate`, and one live `run-now`.
- Configure Cloudflare Tunnel for the public hostname.
- Keep the frontend bound to localhost when Cloudflare Tunnel is the only ingress.
- Enable baseline Cloudflare HTTPS, WAF, and edge rate limiting for `/api/waitlist` and `/api/*`.

Acceptance criteria:

- `curl -fsS http://127.0.0.1:3001/api/health` succeeds.
- `curl -fsS http://127.0.0.1:3001/api/readiness` succeeds.
- `curl -fsS https://risk.example.com/api/health` succeeds for the configured public hostname. Current pilot hostname:
  `https://bitcoinriskbrief.minihub.app/api/health`.
- `curl -fsS https://risk.example.com/api/readiness` succeeds for the configured public hostname. Current pilot hostname:
  `https://bitcoinriskbrief.minihub.app/api/readiness`.
- The public frontend loads, API calls use the intended HTTPS origin, and the selected data-refresh path is documented.

### Phase 7: Backups, Restore, And Monitoring

Status: Pending.

Goal: make production operations recoverable.

Deliverables:

- Schedule `scripts/backup.sh` daily on the production host.
- Copy backups off the server.
- Track backup age and backup command failures.
- Run a restore drill into a staging or empty database.
- Configure public uptime monitoring on `/api/health`.
- Configure production gate monitoring on `/api/readiness`.
- Alert on collector refresh failures and readiness degradation after the daily collector window.
- Monitor Cloudflare Tunnel connector health.

Acceptance criteria:

- A recent PostgreSQL dump and BTC CSV backup exist off-server.
- A restore drill has been completed and documented.
- Readiness failures produce an alert.
- Operators know how to inspect collector, backend, frontend, and database logs.

### Phase 8: Launch Checklist And First Traffic Test

Status: Pending; public API smoke checks are partially complete.

Goal: launch deliberately and measure product demand.

Deliverables:

- Run the full release gate from `docs/production-readiness.md`.
- Confirm latest risk, risk levels, brief, readiness, and waitlist endpoints on the public hostname.
- Submit a test waitlist lead and verify it is stored server-side.
- Check desktop and mobile rendering on the public hostname.
- Check the launch browser/device matrix and record any accepted limitations.
- Capture the first production snapshot: commit, data date, readiness payload, and public hostname.
- Confirm caching, bot protection, and edge rate limits are active.
- Start a small traffic test.

Progress recorded on 2026-07-01:

- `GET https://bitcoinriskbrief.minihub.app/api/health` returned 200 with `{"status":"ok"}`.
- `GET https://bitcoinriskbrief.minihub.app/api/readiness` returned 200 with `status: ready`, `source:
  coinmarketcap_csv`, `latest_date: 2026-06-30`, `covered_end: 2026-06-30`, and `row_count: 5832`.
- `GET https://bitcoinriskbrief.minihub.app/api/risk/latest` returned 200 with `X-Cache: HIT`.
- Conditional `GET https://bitcoinriskbrief.minihub.app/api/risk/latest` with `If-None-Match` returned 304 with
  `X-Cache: HIT`.

Still pending for Phase 8: waitlist production smoke, browser/device pass on the public hostname, launch snapshot, and
first traffic test.

Acceptance criteria:

- The public page is usable on desktop and mobile.
- Waitlist submission works and respects rate limiting.
- The readiness endpoint is 200 at launch.
- Cached public data remains consistent with the latest successful import.
- The product can measure waitlist conversion and repeat visits.

### Phase 9: Post-Launch Learning Loop

Status: Pending.

Goal: decide whether the single BTC risk signal is worth extending.

Deliverables:

- Review waitlist conversion, repeat visits, and direct user questions.
- Track requests for alerts, daily notifications, and personal plan comparisons.
- Run an Agent Access Demand Test if the first traffic test creates enough attention to justify a small integration
  experiment.
- Publish a lightweight Agent Access Pack for HTTP-capable agents that uses the existing public endpoints, requires a
  readiness-first flow, and keeps the risk output framed as analytics rather than financial advice.
- Track `source=agent_access` waitlist leads and direct integration requests for API keys, webhooks, MCP, SDKs, embeds,
  alerts, or commercial reuse.
- Avoid broad feature expansion until demand signals justify it.
- If demand is positive, design the next validation increment: alerts, daily email/Telegram, paid beta, or paid API
  access for integrations.

Acceptance criteria:

- Product decisions are based on usage and waitlist evidence, not feature appetite.
- Agent access is judged by waitlist leads and integration requests, not raw API traffic alone.
- The first agent-access experiment does not add new API, auth, billing, SDK, MCP, or SLA scope before demand is proven.
- The next scope is a small validation step, not a general crypto dashboard.

### Phase 10: Risk Methodology Research

Status: Pending.

Goal: evaluate whether the BTC risk metric can become more accurate, robust, or explainable without destabilizing the
public product.

Deliverables:

- Keep `crypto-scout-canonical-v1` stable through the production pilot and initial demand test.
- Define what "more accurate" means before changing any formula.
- Compare the current methodology against candidate inputs only after launch evidence justifies research work.
- Treat the Fear and Greed Index as external context or a confirmation signal, not as a default core-score component.
- Research on-chain data as a possible future `crypto-scout-canonical-v2` input, starting with one durable
  valuation-family candidate instead of a broad indicator basket.
- Require any candidate data source to have historical coverage, licensing clarity, reproducible backfill, stable daily
  updates, documented revision behavior, and operational failure behavior that does not break readiness.
- If a new methodology wins, design it as a versioned v2 with side-by-side comparison, updated docs, API metadata, and
  interpretation limits.

Acceptance criteria:

- No production metric change happens before there is launch usage evidence and a written research comparison.
- Methodology decisions are based on defined quality criteria, not a general desire for a more complex formula.
- Fear and Greed does not enter the core score unless later evidence overrides the current context-only recommendation.
- On-chain candidates are evaluated for data quality and operational reliability before any production integration.
- If evidence is weak, the product keeps `crypto-scout-canonical-v1` and avoids methodology churn.

## Working Order

Recommended implementation order:

1. Public Trust Layer.
2. Data Source Resilience And Documentation Hygiene.
3. CI And Quality Gates.
4. Frontend Production Quality.
5. Performance, Caching, And Abuse Protection.
6. Production Environment And Deployment.
7. Backups, Restore, And Monitoring.
8. Launch Checklist And First Traffic Test.
9. Post-Launch Learning Loop.
10. Risk Methodology Research.

## Production-Pilot Gate

The project is ready for a first public production pilot when:

- Phase 1 is complete;
- BTC data refresh works through the documented CSV download/import path or an explicitly configured CoinMarketCap API key;
- CI passes on `main`;
- the production host returns 200 from public `/api/health` and `/api/readiness`;
- the first live data refresh/import has completed on the production host;
- public read endpoints have an accepted caching strategy;
- bot and abuse protection has been configured and smoke-tested;
- daily backup and off-server copy are configured;
- alerting exists for readiness failures;
- browser/device QA has been completed for the launch matrix;
- project documentation has been cleaned up and matches the launch configuration;
- a rollback path has been verified or rehearsed.

## Related Docs

- [Product Spec and Alignment Review](01-bitcoin-risk-brief.md)
- [Production Readiness](production-readiness.md)
- [Operations](operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Testing and Quality](testing-and-quality.md)
- [Security and Privacy](security-and-privacy.md)
- [Agent Access Demand Test Design](superpowers/specs/2026-06-30-agent-access-demand-test-design.md)
- [Risk Methodology Research Design](superpowers/specs/2026-07-01-risk-methodology-research-design.md)
