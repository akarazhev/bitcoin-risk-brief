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
- launch governance is explicit: privacy/terms posture, waitlist handling, credential ownership, resource monitoring,
  dependency maintenance, data-source terms, accessibility, and incident response are documented;
- USB-based updates and fresh installs can be prepared reproducibly without copying local secrets, dependency caches, or
  stale build artifacts;
- after implementation stabilizes, the private or portfolio repository has a professional README, current docs, and
  accurate GitHub description/topics;
- the first traffic test can measure whether a single BTC risk signal creates waitlist, repeat-visit, source-attributed,
  and endpoint-usage demand without storing raw IP addresses in product analytics.

## Current Baseline

Already implemented:

- React frontend with EN/RU brief copy, risk history chart, risk levels chart, and waitlist form.
- FastAPI backend with latest risk, history, levels, brief, waitlist, health, and readiness endpoints.
- TimescaleDB storage and migration script.
- Canonical BTC CSV import and CoinMarketCap API delta refresh when an API key is configured.
- Validated operator-downloaded CoinMarketCap historical CSV import without a paid API key.
- Scheduled public-download-first CoinMarketCap CSV refresh in the collector, with optional API fallback only when an API
  key is configured and manual CSV intake as the operator fallback.
- Server-side waitlist storage with validation and rate limiting.
- Public read endpoint caching for readiness, latest risk, history, levels, and brief responses, with validation-versioned
  refresh after successful imports.
- Local startup and operator public-cache warmup for the standard public read payloads, tagged
  `cache-warmup-local-complete-2026-07-05`; post-deploy public smoke on 2026-07-07 recorded fast repeated Cloudflare
  HIT behavior after warmup.
- Latest risk payload and first-viewport display polish for explicit `model_price_usd`, nullable `low_usd`, and nullable
  `high_usd`, tagged `price-model-ohlc-local-complete-2026-07-06`; production visibility is verified in the 2026-07-07
  public smoke evidence.
- No-store waitlist responses, backend request logging, and repo-managed Cloudflare WAF, waitlist bot-challenge,
  cache-rule, and edge rate-limit settings for the production pilot.
- Containerized local stack and Ubuntu plus Cloudflare Tunnel deployment docs.
- Server-run USB kit scripts for host bootstrap, optional `cloudflared` install, project deploy, service enablement,
  health checks, and debug reports.
- USB kit v2 workstation packaging and server-side update wrapper are implemented locally, including filtered snapshot
  packaging, manifest/checksums, backup-before-update, off-server/USB backup copy, `.env` preservation, service restart,
  and health/readiness checks. Local evidence is tagged `usb-kit-v2-local-complete-2026-07-05`; production USB deploy
  verification passed according to the 2026-07-07 post-deploy evidence.
- Production readiness, operations, security, testing, architecture, and data-pipeline documentation.

## Current Roadmap Status

Current status reflects evidence through 2026-07-10 from repository files, local implementation tags, public hostname
checks, and the post-deploy/evidence notes in [Production Readiness](production-readiness.md). Local tags remain
implementation evidence only; production status depends on the recorded operator/public-host evidence.

| Phase | Status | Repository evidence |
| --- | --- | --- |
| Phase 1: Public Trust Layer | Complete | `ca85ad4`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx` |
| Phase 2: Data Source Resilience And Documentation Hygiene | Complete | `9fe25cd`, `7f7b8c4`, `collector/collector/main.py`, `collector/tests/test_downloaded_csv_import.py`, `collector/tests/test_public_cmc_download.py` |
| Phase 3: CI And Quality Gates | Complete | `1b162a5`, `.github/workflows/ci.yml`, `docs/testing-and-quality.md` |
| Phase 4: Frontend Production Quality | Complete | `22793fb`, `frontend/e2e/frontend-quality.spec.ts`, `frontend/src/Chart.tsx`, `docs/frontend-qa.md` |
| Phase 5: Performance, Caching, And Abuse Protection | Complete in repository; post-deploy Cloudflare HIT/fast repeat behavior verified for public smoke | `3c66df9`, `5bb179d`, `cache-warmup-local-complete-2026-07-05`, 2026-07-07 repeated public cache requests about `0.14s` to `0.22s` with Cloudflare `cf-cache-status: HIT`, `backend/app/public_cache.py`, `backend/app/main.py`, `scripts/cloudflare_edge_rules.py`, `backend/tests/test_cloudflare_edge_rules.py` |
| Phase 6: Production Environment And Deployment | Verified for USB deploy and public freshness; closed as stale-data blocker | 2026-07-07 USB deploy verification passed; public `/api/readiness` returned HTTP 200 with `data_fresh: true`, `latest_date: 2026-07-06`, `covered_end: 2026-07-06`, and `data_age_days: 1`; selected path is USB deployment under `/srv/projects/bitcoin-risk-brief` |
| Phase 7: Backups, Restore, And Monitoring | Partially verified; blocked by remaining operator action | One checksum-verified off-server USB backup copy is recorded for 2026-07-07, the 2026-07-10 public health/readiness/latest-risk checks were healthy and fresh, and the 2026-07-09 import provenance pass partially verified public data/readiness/cache alignment. Restore drill remains deferred because the current setup has only the live production server and no separate restore target; external monitor dashboard/alert delivery, backup freshness alert, collector failure alert, Cloudflare Tunnel health alert, direct production validation/import metadata, and exact import source path/category remain pending. |
| Phase 8: Launch Checklist And First Traffic Test | Blocked by remaining operator evidence gates; freshness blocker closed, first traffic test not run | 2026-07-07 post-deploy snapshot recorded readiness 200/fresh, latest-risk 200, public desktop/mobile Playwright smoke passed, model-price/OHLC display verified, fast repeated Cloudflare HIT behavior after warmup, and one off-server backup copy; 2026-07-08 public checks again returned health/readiness/latest-risk 200, browser-like waitlist smoke closed, and 2026-07-10 public checks remained healthy with `data_fresh: true` for `2026-07-09`. The 2026-07-09 import provenance pass verified public data/cache consistency but left exact source-path proof pending. The 2026-07-10 launch governance gap pass classifies privacy/terms as an accepted limitation for operator-watched first traffic, several owner/contact/account/source-review decisions as pending operator decisions, and accessibility/license/snapshot evidence as pending external evidence. SEO/social metadata is implemented locally, but deployment/public-host verification remains pending. Restore drill, monitoring/alert evidence, backup freshness monitoring, direct import source/archive proof, broader launch-matrix/accessibility/governance evidence, and first traffic remain pending. |
| Phase 9: Post-Launch Learning Loop | Pending | Starts after launch traffic creates usage evidence, including optional agent-access demand testing |
| Phase 10: Risk Methodology Research | Pending | Starts only after launch evidence justifies method work; current production metric remains `crypto-scout-canonical-v1` |
| Phase 11: Distribution Channel Research | Pending | Evaluates PWA, Telegram Mini App, browser extension, and other channel packaging after launch evidence |

Current production-pilot progress after Phase 1-5:

- public hostname `bitcoinriskbrief.minihub.app` is connected through Cloudflare and returned 200 for `/api/health` and
  `/api/risk/latest` on 2026-07-05, post-deploy public checks returned fresh readiness on 2026-07-07, a 2026-07-08
  evidence pass returned HTTP 200 for `/api/health`, `/api/readiness`, and `/api/risk/latest`, and a 2026-07-10
  monitoring evidence pass again returned HTTP 200 for those same public paths;
- public `/api/readiness` returned HTTP 200 on 2026-07-10 with `data_fresh: true`, `latest_date: 2026-07-09`,
  `covered_end: 2026-07-09`, `data_age_days: 1`, and `row_count: 5841`; the prior stale-data launch blocker is closed;
- public read caching is observable through `Cache-Control`, validation-versioned `ETag`, `X-Cache`, and
  `X-Cache-Version`; post-deploy repeated public cache requests after warmup were fast with Cloudflare
  `cf-cache-status: HIT`, while the cached origin `X-Cache` header may still show `MISS`;
- browser-capable public-hostname QA passed on 2026-07-07 with Playwright desktop/mobile smoke, fresh data, visible
  Current risk `28%`, `Low`, latest date `2026-07-06`, Model price `$63,289`, Low `$61,276`, High `$64,598`, and no
  mobile horizontal overflow at a 390px viewport; physical-device/native branded browser evidence is still pending if
  required by the launch matrix;
- Cloudflare Rulesets API apply succeeded for the custom waitlist bot challenge, one waitlist rate-limit rule, waitlist
  cache bypass, and public-read origin-cache rules;
- the active Cloudflare plan did not entitle the zone to execute the managed WAF ruleset, more than one rate-limit rule,
  a rate-limit period other than 10 seconds, or a mitigation timeout other than 10 seconds, so the current public edge
  config intentionally uses the Free-plan-compatible subset.

Remaining production-pilot gaps:

- keep the production host runbook, `.env`, service path, and data-refresh workflow aligned with the verified USB deploy
  path;
- keep scheduled public CoinMarketCap refresh verification current on the production host without a
  `COINMARKETCAP_API_KEY`; the 2026-07-07 snapshot proves current freshness, not future scheduled runs;
- continue cache-miss/edge-hit latency measurement for any endpoint not covered by the 2026-07-07 post-deploy smoke; add
  precomputed expensive payloads only if the first real user would still pay visible database/build cost after startup or
  nightly import;
- decide whether to accept the current Cloudflare Free-plan subset for first traffic or upgrade/configure additional WAF,
  bot protection, and broader API burst-rate-limit controls;
- recurring daily backups, recurring off-server copies, backup freshness monitoring, restore drill, and monitoring alerts
  still need to be configured and verified; one off-server USB backup copy was verified on 2026-07-07, but the
  2026-07-10 monitoring pass did not have current backup freshness or monitor-provider evidence;
- privacy/terms posture, post-waitlist handling, dependency/security maintenance, resource monitoring, credential
  ownership, accessibility, public-host metadata verification, data-source terms, and incident response need a launch
  completeness pass;
- full browser/device launch matrix, remaining cache-miss latency measurement, and first traffic test still need to run;
  the stale-data blocker and browser-like waitlist smoke are closed, but broader launch gates remain;
- tracked repository documentation and portfolio presentation work is locally complete as of 2026-07-06, but this does
  not close restore drill, backup freshness monitoring, monitoring alerts, direct import source/archive proof,
  browser/device/accessibility, GitHub settings, or sibling product-ideas evidence;
- post-launch learning cannot start until real usage evidence exists.

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

Status: Complete in repository and partially applied at the public edge; post-deploy public smoke on 2026-07-07 verified
Cloudflare HIT/fast repeat behavior after warmup, while broader endpoint MISS measurement remains an external launch gate.
Verified by commits `3c66df9` and `5bb179d`, local tag `cache-warmup-local-complete-2026-07-05`,
`backend/app/public_cache.py`, `backend/app/main.py`, `scripts/cloudflare_edge_rules.py`, and
`backend/tests/test_cloudflare_edge_rules.py`. On 2026-07-01, `bitcoinriskbrief.minihub.app` returned 200 for public GET
smoke checks and 304 for conditional `/api/risk/latest` revalidation with `X-Cache: HIT`.

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
- As a pre-traffic hardening follow-up, deploy and verify startup/operator warmup for standard public payloads, then
  precompute expensive payloads only if the first request after startup or nightly import is still slow.
- Document which endpoints must not be cached, especially `POST /api/waitlist`.
- Configure Cloudflare WAF managed rules, bot protections appropriate for a public pilot, and edge rate limits for
  `/api/waitlist` and `/api/*`.
- Keep backend waitlist rate limiting as an application-level fallback.
- Add request logging or operational checks that help distinguish real users from abusive traffic.

Acceptance criteria:

- Repeated public page loads do not require unnecessary database work for unchanged daily data.
- Cache behavior is observable and has a clear invalidation path after data refresh.
- If first cache misses are slow, standard public payloads are warmed for the current validation version before active
  traffic reaches the public hostname.
- Waitlist submissions cannot be cached and still store server-side only.
- Standard public payload warmup has local evidence and is verified in production before active traffic.
- Basic bot, spam, and burst-traffic tests are blocked or rate-limited without breaking normal page use.
- Security and caching expectations are documented in `docs/security-and-privacy.md` and `docs/production-readiness.md`.

### Phase 6: Production Environment And Deployment

Status: Verified for the USB deploy path and current public freshness as of the 2026-07-07 post-deploy evidence. USB
deploy verification passed, `GET /api/readiness` returned HTTP 200 with `data_fresh: true`, `latest_date: 2026-07-06`,
`covered_end: 2026-07-06`, and `data_age_days: 1`, and `GET /api/risk/latest` returned HTTP 200 for
`2026-07-06T00:00:00+00:00`. The selected deployment path is USB-based deployment under
`/srv/projects/bitcoin-risk-brief`. Keep future update evidence current, and keep production `.env` ownership and
scheduled-refresh operation aligned with the runbook.

Goal: run the full stack on the intended production-pilot host.

Deliverables:

- Create production `.env` from `.env.production.example`.
- Set production values for `APP_ENV`, `DB_PASSWORD`, `CORS_ORIGINS`, freshness limit, waitlist rate limit, and either
  the optional `COINMARKETCAP_API_KEY` or the documented CSV download/import workflow.
- Configure the scheduled refresh strategy so production defaults to public CoinMarketCap download first, optional
  official API fallback when a key is configured, and manual downloaded CSV import as the last fallback.
- Deploy the repository through the selected production path: direct Git workflow under `/opt/bitcoin-risk-brief` or
  local USB deployment under `/srv/projects/bitcoin-risk-brief`.
- If using the local USB deployment path, prepare the deployment USB from a reproducible kit that contains only the
  filtered project snapshot, scripts, docs, manifest, and checksums. Do not include local `.env`, `.git`, backups,
  dependency caches, build output, browser artifacts, container images, or offline package mirrors.
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
- A production deployment with an empty `COINMARKETCAP_API_KEY` can refresh through the last completed UTC day via the
  scheduled public CoinMarketCap download path without manual operator action.
- If USB deployment is used, the operator can identify the project revision on the USB and verify that no local secrets
  were staged.

### Phase 7: Backups, Restore, And Monitoring

Status: Partially verified; blocked by remaining operator action. The runbooks and policies are documented, and one
checksum-verified off-server USB backup copy was recorded on 2026-07-07. Public health, readiness, and latest-risk checks
were healthy and fresh in the 2026-07-10 monitoring evidence pass, but that pass found no external monitor/provider
dashboard, alert delivery, backup freshness monitor, collector failure alert, or Cloudflare Tunnel health notification
evidence. The current setup has only the live production server, so the restore drill remains an accepted
limitation/deferred until a separate staging or empty restore target exists.

Goal: make production operations recoverable.

Deliverables:

- Schedule `scripts/backup.sh` daily on the production host.
- Copy backups off the server.
- Require a fresh backup before USB-based production updates and copy that backup off the server before promotion.
- Track backup age and backup command failures.
- Run a restore drill into a staging or intentionally empty restore target when one exists; do not run the drill against
  the live production database.
- Configure public uptime monitoring on `/api/health`.
- Configure production gate monitoring on `/api/readiness`.
- Alert on collector refresh failures and readiness degradation after the daily collector window.
- Alert when the scheduled public CoinMarketCap refresh fails, when optional API fallback is used after a public-download
  failure, or when `/api/readiness` is stale after the nightly update window.
- Monitor Cloudflare Tunnel connector health.
- Document credential/account ownership and recovery paths for GitHub, Cloudflare, domain, production `.env`, backups,
  server access, and optional CoinMarketCap API credentials.
- Define a dependency and security maintenance cadence for container images, Python packages, npm packages, GitHub
  Actions, and vulnerability or secret scans.
- Track disk usage, database volume growth, backup directory growth, container restart loops, domain ownership, and
  infrastructure cost/resource limits.
- Create a short incident response runbook for readiness degradation, data refresh failures, waitlist failures,
  Cloudflare Tunnel issues, stale cache, backup failures, and disk pressure.
- Define a data correction and service-target policy for bad CSV/import/risk incidents, correction notes, cache safety,
  freshness, RPO/RTO, and pilot downtime boundaries.
- Define an import provenance and source archive policy for production data imports: source snapshot, `sha256`,
  retrieval method, row count, covered range, expected tail, validation/readiness output, and cache evidence.

Acceptance criteria:

- A recent PostgreSQL dump and BTC CSV backup exist off-server.
- A production update runbook includes the backup-before-update gate for USB-based deployments.
- A restore drill has been completed and documented.
- Readiness failures produce an alert.
- Scheduled no-key refresh failures are visible in collector logs and alerts, and failed downloads do not rewrite the
  canonical CSV.
- Operators know how to inspect collector, backend, frontend, and database logs.
- Operators know who owns production credentials and what to do in the first 15 minutes of common incidents.
- Operators know how to classify and correct a published bad-data or wrong-risk incident without silently serving a
  known-wrong risk value.
- Operators can identify which source file or download produced a production validation version and where its sanitized
  evidence is stored.

### Phase 8: Launch Checklist And First Traffic Test

Status: Blocked by remaining operator evidence gates; freshness blocker closed and first traffic test not run. The
2026-07-07 post-deploy snapshot recorded public readiness 200/fresh, latest-risk 200, desktop/mobile Playwright public
smoke passed, first-viewport model-price/OHLC display verified, mobile overflow passed, and repeated public cache
requests after warmup were fast through Cloudflare HIT. The 2026-07-08 browser-like waitlist smoke is closed. The
2026-07-09 import provenance pass verified public data/cache consistency but did not prove the exact import source
path/category or direct production validation/import table metadata. The 2026-07-10 monitoring evidence pass found
public health/readiness/latest-risk healthy and current for `2026-07-09`, but monitor dashboard, alert delivery, backup
freshness alert, collector failure alert, and Cloudflare Tunnel notification evidence remained blocked. Backup/restore,
monitoring, broader browser/device/accessibility/governance evidence remain incomplete. The 2026-07-10 browser/device/
accessibility/metadata gap pass added current automated smoke and public metadata evidence: Playwright profile smoke
passed, but native/manual browser-device evidence and focused accessibility evidence remain pending. SEO/social metadata
is implemented locally, but public-host verification remains pending until the deployed homepage serves the tags. The
2026-07-10 launch governance gap pass in
[Production Readiness](production-readiness.md) is the current status checklist for accepted limitations, pending
operator decisions, pending external evidence, and blocked launch items; first traffic must remain pending until those
gates are completed or explicitly accepted.

Goal: launch deliberately and measure product demand.

Deliverables:

- Run the full release gate from `docs/production-readiness.md`.
- Confirm latest risk, risk levels, brief, readiness, and waitlist endpoints on the public hostname.
- Submit a test waitlist lead and verify it is stored server-side.
- Check desktop and mobile rendering on the public hostname.
- Check the launch browser/device matrix and record any accepted limitations.
- Deploy and verify the first-viewport price input polish before traffic: show `Model price`, `Low`, and `High` for the
  latest completed daily candle without implying that HLC3 is a live spot or close-only price.
- Complete the Phase 8 localization add-on if it is still in scope before active traffic: polish EN/RU copy, prepare the
  frontend for more than two locales, add ES/DE UI copy, and keep AR/ZH deferred until dedicated RTL, platform, and
  channel research justify them.
- Complete the Launch Operations And Governance checklist: privacy/terms/disclaimer posture, post-waitlist workflow,
  data-source terms and attribution, accessibility pass, public-host SEO/social metadata verification, and launch incident
  response notes.
- Complete the Release Feedback And Operational Evidence checklist: release notes or decision log, first-user feedback
  review path, support/contact identity, dependency-license review, and launch/backup/restore evidence.
- Complete or explicitly defer the Data Correction And Service Targets checklist: bad-data correction flow, correction
  note rules, cache correction safety, freshness target, RPO/RTO boundaries, and pilot downtime tolerance.
- Complete or explicitly defer the Import Provenance And Source Archive checklist: source snapshot, import manifest,
  `sha256`, retrieval metadata, row count, covered range, expected tail, validation/readiness output, cache evidence,
  and storage outside the repository.
- Capture the first production snapshot: commit, data date, readiness payload, and public hostname.
- Confirm caching, bot protection, and edge rate limits are active.
- Measure first public read latency for both `X-Cache: MISS` and `X-Cache: HIT` after deploying local warmup; if MISS
  latency is still user-visible, tune warmup or add precomputed expensive payloads before active traffic.
- Confirm the first-traffic measurement path for visits, repeat-use estimate, source attribution, endpoint usage, and
  waitlist conversion. Existing backend access logs and Cloudflare analytics may be enough for the first snapshot, but
  persisted product analytics should follow the Product Analytics And Usage Attribution design before product decisions
  depend on repeat-use or integration counts.
- After implementation freeze, complete the Documentation And Portfolio Presentation pass: professional README, current
  docs, synchronized `product-ideas/01-bitcoin-risk-brief.md`, private/portfolio GitHub description and topics,
  screenshot or GIF if useful, and repository hygiene check.
- Start a small traffic test.

Progress recorded on 2026-07-01:

- `GET https://bitcoinriskbrief.minihub.app/api/health` returned 200 with `{"status":"ok"}`.
- `GET https://bitcoinriskbrief.minihub.app/api/readiness` returned 200 with `status: ready`, `source:
  coinmarketcap_csv`, `latest_date: 2026-06-30`, `covered_end: 2026-06-30`, and `row_count: 5832`.
- `GET https://bitcoinriskbrief.minihub.app/api/risk/latest` returned 200 with `X-Cache: HIT`.
- Conditional `GET https://bitcoinriskbrief.minihub.app/api/risk/latest` with `If-None-Match` returned 304 with
  `X-Cache: HIT`.

Launch snapshot recorded on 2026-07-05:

- `GET https://bitcoinriskbrief.minihub.app/api/health` returned 200 with `status: ok`.
- `GET https://bitcoinriskbrief.minihub.app/api/readiness` returned HTTP 503 with `status: degraded`, `data_fresh:
  false`, `latest_date: 2026-06-30`, `data_age_days: 4`, and `max_age_days: 2`.
- `GET https://bitcoinriskbrief.minihub.app/api/risk/latest` returned 200 for `2026-06-30T00:00:00+00:00` with a low
  risk state and expected public cache headers.
- Browser-capable public-hostname QA passed with accepted limitations, but the public page visibly showed stale data.

Post-deploy snapshot recorded on 2026-07-07:

- USB deploy verification passed.
- `GET https://bitcoinriskbrief.minihub.app/api/readiness` returned HTTP 200 with `data_fresh: true`,
  `latest_date: 2026-07-06`, `covered_end: 2026-07-06`, and `data_age_days: 1`.
- `GET https://bitcoinriskbrief.minihub.app/api/risk/latest` returned HTTP 200 for
  `2026-07-06T00:00:00+00:00` with `risk_state: low`, `price_usd: 63289.47099956666`,
  `model_price_usd: 63289.47099956666`, `low_usd: 61275.826328`, and `high_usd: 64597.5707661`.
- Public Playwright smoke passed on desktop and mobile: Current risk `28%`, `Low`, latest date `2026-07-06`, Model
  price `$63,289`, Low `$61,276`, and High `$64,598`.
- Mobile overflow passed with viewport width `390` and scroll width `390`.
- Repeated public cache requests after warmup were about `0.14s` to `0.22s` with Cloudflare `cf-cache-status: HIT` and
  `age` around `33` to `35`. App-level `X-Cache` may still show `MISS` from a cached origin response, so that header
  alone is not a public-latency blocker.

Still pending for Phase 8: full browser/device launch matrix, localization add-on if accepted for pre-traffic scope,
public-host SEO/social metadata verification, release/feedback/evidence checklist, data-correction/service-target
evidence, direct import-provenance source archive and production validation/import metadata proof, external GitHub
settings or sibling product-ideas updates if separately requested, any remaining endpoint cache-miss latency measurement
not covered by the post-deploy smoke, and first traffic test. The tracked repository documentation and portfolio
presentation pass is locally complete as of 2026-07-06. Do not mark the first traffic test complete until the required
launch gates are completed or explicitly accepted and the traffic window actually runs.

Acceptance criteria:

- The public page is usable on desktop and mobile.
- Waitlist submission works and respects rate limiting.
- The readiness endpoint is 200 at launch.
- Cached public data remains consistent with the latest successful import.
- First public page load after backend startup or nightly import does not expose users to slow database-backed cache
  misses for the standard public payloads.
- The first-viewport price input labels the HLC3 value as `Model price` if daily `Low` and `High` are shown alongside it.
- The root README, core docs, and sibling product-ideas brief describe current behavior and future ideas without stale
  claims, and the private/portfolio GitHub description plus topics are ready.
- The product can measure waitlist conversion, repeat visits, source attribution, and endpoint demand without storing raw
  IP addresses or waitlist contact values in analytics events.
- Enabled locales pass desktop and mobile QA without clipped text, overlapping UI, inconsistent no-advice framing, or
  broken waitlist locale attribution.
- Privacy, waitlist handling, account ownership, dependency maintenance, accessibility, public-host metadata verification,
  data-source terms, and incident-response expectations are documented before broad external exposure.
- Release notes, key product decisions, support/contact path, dependency-license review, first-user feedback review, and
  launch/backup/restore evidence are documented before broader external exposure.
- Bad-data correction flow, correction-note rules, cache safety, freshness target, RPO/RTO boundaries, and pilot downtime
  tolerance are documented before broader external exposure.
- Production import evidence links source snapshots, hashes, retrieval metadata, validation/readiness output, and cache
  evidence without storing secrets or PII in the repository.

### Phase 9: Post-Launch Learning Loop

Status: Pending.

Goal: decide whether the single BTC risk signal is worth extending.

Deliverables:

- Review waitlist conversion, repeat visits, and direct user questions.
- Track requests for alerts, daily notifications, and personal plan comparisons.
- Run an Agent Access And Risk-Signal Licensing Demand Test if the first traffic test creates enough attention to justify
  a small integration experiment.
- Publish a lightweight Agent Access Pack for HTTP-capable agents that uses the existing public endpoints, requires a
  readiness-first flow, and keeps the risk output framed as analytics rather than financial advice.
- Track `source=agent_access` waitlist leads and direct integration requests for API keys, webhooks, MCP, SDKs, embeds,
  alerts, or commercial reuse.
- If professionals or agent builders ask to reuse only the BTC risk metric, test a low-friction `EUR 9-19/month`
  early license before designing enterprise pricing. This test should cover one product or AI agent, clear attribution,
  current methodology/freshness metadata, and modest usage; it must exclude redistribution, white-label, SLA, high-volume
  limits, and custom methodology work.
- If agent or professional-product demand appears, design client-level API usage tracking with API client identities, key
  identifiers or hashes, daily request counts, endpoint groups, methodology version, status counts, and usage limits. Do
  not use raw IP addresses as the billing or licensing identity.
- Avoid broad feature expansion until demand signals justify it.
- If demand is positive, design the next validation increment: alerts, daily email/Telegram, paid beta, or paid API
  access for integrations.
- Before recurring email or Telegram delivery, complete the email/outreach readiness gate: sender identity, platform
  ownership, opt-in source, unsubscribe or stop handling, provider recovery, no-advice framing, and privacy copy.
- Before accepting the first paid-beta payment or paid risk-signal license, complete the paid-beta/licensing readiness
  gate: payment or invoice path, owner, currency, tax assumptions, refund/cancel policy, entitlement, attribution,
  support/contact path, usage limits, and separation from anonymous analytics.
- Before broader professional exposure, review account recovery paths, synthetic journey monitoring needs, and a small
  trust artifact covering methodology version, data source, freshness expectation, and accepted limitations.
- Before adding analytics tables, API keys, paid API access, widgets, agent-specific contracts, or methodology-v2
  behavior, complete the API/DB change-management gate: classify additive/risky/breaking changes, preserve endpoint
  compatibility where practical, document migrations, run focused contract tests, and define rollback.

Acceptance criteria:

- Product decisions are based on usage and waitlist evidence, not feature appetite.
- Agent access is judged by waitlist leads and integration requests, not raw API traffic alone.
- The first agent-access experiment does not add new API, auth, billing, SDK, MCP, or SLA scope before demand is proven.
- The `EUR 9-19/month` risk-signal license is treated as an early paid-intent test, not as a complete commercial API
  plan or redistribution license.
- Professional product or agent usage is judged by explicit source values or future client/API keys, not by raw IP traffic
  alone.
- The next scope is a small validation step, not a general crypto dashboard.
- Recurring notifications, paid beta access, paid risk-signal licenses, and broader trust claims are gated by explicit
  readiness checks rather than added opportunistically.
- Future API clients, agents, paid integrations, analytics schema, and methodology-version changes are protected by
  explicit API compatibility, migration, backup, verification, and rollback rules.

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
- Start with open or free data sources and document access, licensing, attribution, history depth, and update behavior
  before considering paid data or node-backed infrastructure.
- Treat a self-hosted Bitcoin node as unnecessary for the first research pass because MVRV, realized cap, NUPL, and
  SOPR-style metrics require an indexer, historical prices, and a separate calculation pipeline beyond raw node data.
- Require any candidate data source to have historical coverage, licensing clarity, reproducible backfill, stable daily
  updates, documented revision behavior, and operational failure behavior that does not break readiness.
- If a new methodology wins, design it as a versioned v2 with side-by-side comparison, updated docs, API metadata, and
  interpretation limits.
- If methodology v2 changes endpoint fields, cached payload assumptions, or database schema, apply the API/DB
  change-management gate before production exposure.

Acceptance criteria:

- No production metric change happens before there is launch usage evidence and a written research comparison.
- Methodology decisions are based on defined quality criteria, not a general desire for a more complex formula.
- Fear and Greed does not enter the core score unless later evidence overrides the current context-only recommendation.
- On-chain candidates are evaluated for data quality and operational reliability before any production integration.
- The first research pass does not require paid data or a self-hosted node unless the source review justifies that
  infrastructure.
- If evidence is weak, the product keeps `crypto-scout-canonical-v1` and avoids methodology churn.

### Phase 11: Distribution Channel Research

Status: Pending.

Goal: evaluate whether additional packaging and platform channels can improve discovery, repeat use, and paid-intent
signals without turning the product into a multi-platform maintenance burden.

Deliverables:

- Create a channel scorecard for PWA, Telegram Mini App, browser extensions, VK Mini Apps, WeChat Mini Programs, and
  Discord Activities.
- Evaluate PWA/installable web app first because it reuses the current web product with the lowest packaging overhead.
- Evaluate Telegram Mini App as the first social-platform experiment for crypto-native distribution and future
  notification or subscription tests.
- Treat browser extensions as later candidates that need a real daily utility, such as a BTC risk badge, popup, quick
  link, or validated alert workflow.
- Keep VK Mini Apps, WeChat Mini Programs, and Discord Activities conditional until audience, partner, or community
  evidence justifies platform-specific work.
- Track channel demand through explicit waitlist or analytics source values such as `source=pwa`,
  `source=telegram_mini_app`, and `source=browser_extension`.
- Preserve readiness/freshness display, API error handling, degraded-data states, and no-financial-advice framing in
  every channel experiment.

Acceptance criteria:

- No more than one new distribution channel is implemented at a time.
- The first experiment has defined source tracking and success metrics before implementation.
- Platform wrappers do not introduce new backend scope unless a separate design justifies it.
- Browser extensions are not published as simple website launchers.
- WeChat, VK, and Discord remain out of scope until channel-specific demand exists.
- Distribution work supports retention and demand validation; monetization remains tied to alerts, recurring briefs,
  paid API/agent access, or premium context.

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
11. Distribution Channel Research.

## Production-Pilot Gate

The project is ready for a first public production pilot when:

- Phase 1 is complete;
- BTC data refresh works through the documented CSV download/import path or an explicitly configured CoinMarketCap API key;
- scheduled production refresh can run without a CoinMarketCap API key by using the public CoinMarketCap download path;
- CI passes on `main`;
- the production host returns 200 from public `/api/health` and `/api/readiness`;
- the first live data refresh/import has completed on the production host;
- public read endpoints have an accepted caching strategy;
- bot and abuse protection has been configured and smoke-tested;
- daily backup and off-server copy are configured;
- alerting exists for readiness failures;
- browser/device QA has been completed for the launch matrix;
- project documentation has been cleaned up and matches the launch configuration;
- the private or portfolio repository presentation has been reviewed if the project will be shown to external reviewers;
- launch operations and governance checklist items are either completed or explicitly accepted as limitations;
- a rollback path has been verified or rehearsed.

## Related Docs

- [Product Spec and Alignment Review](01-bitcoin-risk-brief.md)
- [Production Readiness](production-readiness.md)
- [Operations](operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Testing and Quality](testing-and-quality.md)
- [Security and Privacy](security-and-privacy.md)
- [Agent Access And Risk-Signal Licensing Demand Test Design](superpowers/specs/2026-06-30-agent-access-demand-test-design.md)
- [Product Analytics And Usage Attribution Design](superpowers/specs/2026-07-01-product-analytics-usage-attribution-design.md)
- [Public Payload Cache Warmup And Precompute Design](superpowers/specs/2026-07-01-public-payload-cache-warmup-precompute-design.md)
- [Launch Operations And Governance Checklist Design](superpowers/specs/2026-07-01-launch-operations-governance-checklist-design.md)
- [Documentation And Portfolio Presentation Design](superpowers/specs/2026-07-01-documentation-portfolio-presentation-design.md)
- [Localization Quality And Language Expansion Design](superpowers/specs/2026-07-01-localization-quality-language-expansion-design.md)
- [Scheduled Public CoinMarketCap Refresh Design](superpowers/specs/2026-07-01-scheduled-public-cmc-refresh-design.md)
- [Risk Methodology Research Design](superpowers/specs/2026-07-01-risk-methodology-research-design.md)
- [Distribution Channel Research Design](superpowers/specs/2026-07-01-distribution-channel-research-design.md)
