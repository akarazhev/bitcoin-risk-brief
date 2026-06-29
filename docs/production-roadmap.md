# Production Roadmap

This roadmap tracks the work needed to move Bitcoin Risk Brief from a local validation product to a production-pilot
service. The target is not a broad analytics platform. The target is one reliable public Bitcoin risk page, safe waitlist
capture, daily data freshness, and an operator workflow that can be monitored and rolled back.

## Target State

Production-pilot readiness means:

- the public page explains current BTC risk without implying certainty or financial advice;
- users can see whether the latest data is fresh and validation passed;
- the waitlist flow works without storing leads in browser storage;
- automated checks run before deploys and before changes enter `main`;
- the deployed stack can be updated, monitored, backed up, restored, and rolled back;
- the first traffic test can measure whether a single BTC risk signal creates waitlist and repeat-visit demand.

## Current Baseline

Already implemented:

- React frontend with EN/RU brief copy, risk history chart, risk levels chart, and waitlist form.
- FastAPI backend with latest risk, history, levels, brief, waitlist, health, and readiness endpoints.
- TimescaleDB storage and migration script.
- Canonical BTC CSV import and CoinMarketCap delta refresh.
- Server-side waitlist storage with validation and rate limiting.
- Containerized local stack and Ubuntu plus Cloudflare Tunnel deployment docs.
- Production readiness, operations, security, testing, architecture, and data-pipeline documentation.

Known product gaps from the alignment review:

- public freshness and validation state are not visible on the page;
- methodology version and no-advice disclaimer are not visible on the page;
- methodology docs are not exposed through public product navigation;
- the risk ladder does not explicitly call out the nearest state-change prices.

## Roadmap Phases

### Phase 1: Public Trust Layer

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

### Phase 2: CI And Quality Gates

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

### Phase 3: Frontend Production Quality

Goal: reduce avoidable frontend risk before launch.

Deliverables:

- Split or lazy-load the ECharts bundle so the main chunk warning is removed or explicitly accepted.
- Add a smoke or e2e check for desktop and mobile layout.
- Verify that chart canvases render non-empty and occupy the expected container width.
- Exercise loading, empty, degraded readiness, and API error states.
- Keep the page focused on the BTC risk product, not a broad dashboard.

Acceptance criteria:

- `npm run build --prefix frontend` completes without unexpected warnings, or the remaining warning is documented and accepted.
- Automated smoke checks detect blank charts or obvious mobile layout breakage.
- Error and degraded-data states are usable and do not look like successful fresh data.

### Phase 4: Production Environment And Deployment

Goal: run the full stack on the intended production-pilot host.

Deliverables:

- Create production `.env` from `.env.production.example`.
- Set production values for `APP_ENV`, `DB_PASSWORD`, `CORS_ORIGINS`, `COINMARKETCAP_API_KEY`, freshness limit, and waitlist rate limit.
- Deploy the repository under `/opt/bitcoin-risk-brief`.
- Run `validate`, `start`, `migrate`, and one live `run-now`.
- Configure Cloudflare Tunnel for the public hostname.
- Keep the frontend bound to localhost when Cloudflare Tunnel is the only ingress.
- Enable baseline Cloudflare HTTPS, WAF, and edge rate limiting for `/api/waitlist` and `/api/*`.

Acceptance criteria:

- `curl -fsS http://127.0.0.1:3001/api/health` succeeds.
- `curl -fsS http://127.0.0.1:3001/api/readiness` succeeds.
- `curl -fsS https://risk.example.com/api/health` succeeds for the configured public hostname.
- `curl -fsS https://risk.example.com/api/readiness` succeeds for the configured public hostname.
- The public frontend loads and API calls use the intended HTTPS origin.

### Phase 5: Backups, Restore, And Monitoring

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

### Phase 6: Launch Checklist And First Traffic Test

Goal: launch deliberately and measure product demand.

Deliverables:

- Run the full release gate from `docs/production-readiness.md`.
- Confirm latest risk, risk levels, brief, readiness, and waitlist endpoints on the public hostname.
- Submit a test waitlist lead and verify it is stored server-side.
- Check desktop and mobile rendering on the public hostname.
- Capture the first production snapshot: commit, data date, readiness payload, and public hostname.
- Start a small traffic test.

Acceptance criteria:

- The public page is usable on desktop and mobile.
- Waitlist submission works and respects rate limiting.
- The readiness endpoint is 200 at launch.
- The product can measure waitlist conversion and repeat visits.

### Phase 7: Post-Launch Learning Loop

Goal: decide whether the single BTC risk signal is worth extending.

Deliverables:

- Review waitlist conversion, repeat visits, and direct user questions.
- Track requests for alerts, daily notifications, and personal plan comparisons.
- Avoid broad feature expansion until demand signals justify it.
- If demand is positive, design the next validation increment: alerts, daily email/Telegram, or paid beta.

Acceptance criteria:

- Product decisions are based on usage and waitlist evidence, not feature appetite.
- The next scope is a small validation step, not a general crypto dashboard.

## Working Order

Recommended implementation order:

1. Public Trust Layer.
2. CI And Quality Gates.
3. Frontend Production Quality.
4. Production Environment And Deployment.
5. Backups, Restore, And Monitoring.
6. Launch Checklist And First Traffic Test.
7. Post-Launch Learning Loop.

## Production-Pilot Gate

The project is ready for a first public production pilot when:

- Phase 1 is complete;
- CI passes on `main`;
- the production host returns 200 from public `/api/health` and `/api/readiness`;
- the first live `run-now` with the production CoinMarketCap key has completed;
- daily backup and off-server copy are configured;
- alerting exists for readiness failures;
- a rollback path has been verified or rehearsed.

## Related Docs

- [Product Spec and Alignment Review](01-bitcoin-risk-brief.md)
- [Production Readiness](production-readiness.md)
- [Operations](operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Testing and Quality](testing-and-quality.md)
- [Security and Privacy](security-and-privacy.md)
