# Production Readiness

This document defines the current production-pilot gate for Bitcoin Risk Brief.

## Current Pre-Deployment Reconciliation

Recorded on 2026-07-11 from repository-local evidence. The local evidence tag
`launch-snapshot-helper-local-evidence-2026-07-11` points at commit
`e1a4dc521343b8c48060358204ff5c9cfd7e1ecf`. This records local tooling and documentation state only. It does not prove
a production deployment, production import, public readiness recheck after the latest local commits, external monitor
setup, backup freshness scheduling, restore drill, launch snapshot completion, or first traffic.

Local pre-deployment tooling and evidence that is complete in the repository:

- Scheduled public-download-first CoinMarketCap CSV refresh, validated manual CSV intake, and bundled canonical BTC CSV
  evidence through 2026-07-09.
- Public payload cache warmup, USB Update And Install Kit V2, model-price/OHLC display polish, local SEO/social
  metadata, and local privacy/terms/disclaimer copy near the waitlist.
- `scripts/check_public_endpoints.py` for local health/readiness/latest-risk assertions, including explicit freshness
  policy inputs for future monitor runs.
- `scripts/check_backup_freshness.py` for local backup and off-server copy freshness/checksum checks.
- `scripts/import_provenance_packet.py` for creating or validating sanitized production import provenance manifests
  after an operator has collected the real production source, canonical output, validation/readiness, cache, and
  deployment evidence.
- `scripts/launch_snapshot_packet.py` for creating or validating a sanitized final pre-traffic launch snapshot packet
  from already collected evidence while keeping missing categories pending and `first_traffic_status` at `not_run` by
  default.
- Dependabot configuration, local dependency/license inventory evidence, local accessibility improvements/evidence,
  local waitlist live-region/keyboard evidence, and local public privacy/terms/disclaimer evidence.

Sanitized support/contact and account recovery readiness evidence recorded on 2026-07-12:

- Gate status: partial, not passed. The support/contact blocker and account recovery blocker are completed for
  first-traffic readiness, but first traffic remains blocked by the remaining evidence gates below.
- Scope/safety: documentation-only evidence update. No deploy, push, tag, refresh/import, waitlist POST,
  Cloudflare/routing change, alert configuration, backup/off-server copy, first traffic, or production mutation was
  performed. Exact support addresses, provider details, account IDs, usernames, recovery text, private URLs, tokens,
  passwords, raw headers, and secrets remain outside Git.
- Support/contact readiness: support email status is created and ready. The contact category is a dedicated support
  mailbox with a project-domain alias; exact addresses are kept outside Git. The support path was checked by the
  founder/operator. Deletion and unsubscribe handling is a manual request through the dedicated support contact path,
  with the exact address kept outside Git. No paid support SLA is claimed.
- Account recovery readiness: the account recovery record is created outside Git and current. GitHub owner role,
  Cloudflare/domain owner role, server owner role, secrets/.env owner role, and backups owner role are all
  founder/operator. Do not record account holders, account IDs, private recovery paths, secret locations, or recovery
  text in Git.

Small-pilot external monitoring acceptance recorded on 2026-07-14:

- Gate status: partial, with the small operator-watched pilot monitoring blocker accepted/closed by explicit operator
  decision. First traffic remains blocked by the remaining first-traffic blockers below.
- Scope/safety: documentation-only evidence update. No deploy, push, tag, refresh/import, waitlist POST,
  Cloudflare/routing change, production endpoint probe, monitor configuration, alert delivery test, backup/off-server
  copy, restore drill, first traffic, or production mutation was performed from this workspace. No account IDs, monitor
  IDs, email addresses, alert recipients, private dashboard URLs, webhook URLs, tokens, raw headers, screenshots, provider
  secrets, or private filesystem paths are recorded.
- Sanitized coverage accepted for the small operator-watched pilot: Cloudflare Tunnel Health Alert is configured; the
  external uptime monitor provider category is HetrixTools/external uptime monitor provider; and a homepage availability
  monitor is configured for the public homepage.
- Accepted limitation: this proves only Tunnel health notification plus public homepage availability coverage for a small
  operator-watched pilot. No dedicated external `/api/health` monitor evidence, dedicated external `/api/readiness`
  freshness monitor evidence, JSON assertion evidence, stale-data after-window alert evidence, or explicit alert delivery
  test evidence is recorded yet.
- Broader launch monitoring remains pending before broader traffic or broader readiness claims: dedicated external
  `/api/health` monitor evidence, dedicated external `/api/readiness` freshness monitor evidence, and explicit sanitized
  alert delivery evidence without private details.

Fresh manual backup/off-server copy and public readiness evidence recorded on 2026-07-15:

- Gate status: partial, not launched. The fresh manual backup plus off-server copy blocker is completed for the current
  first-traffic evidence set, but first traffic remains blocked by the remaining gates below.
- Scope/safety: documentation/evidence update only. No deploy, push, tag, refresh/import, waitlist POST,
  Cloudflare/routing change, restore drill, first traffic, or production mutation was performed from this workspace. No
  raw backup contents, raw CSV contents, raw manifests, raw checksum files, `.env` values, tokens, account IDs, private
  server details, raw logs, or private operator details are recorded.
- Repository/package identity: current repository `HEAD` and `origin/main` were `18e07e6` while this evidence was
  recorded. The mounted USB server kit manifest records `created_at_utc=2026-07-15T06:46:06Z`,
  `source_commit=8020384ddaa53f3805f0f29c54928ea53c91cce1`, and
  `project_snapshot=project/bitcoin-risk-brief`. Treat `8020384` as the deployed USB package source for this evidence;
  do not claim that later repository commit `18e07e6` was deployed unless separate evidence proves it.
- Fresh backup/off-server copy evidence: copied backup timestamp basename `20260715T082457Z` was present on mounted
  removable media. Sanitized artifact filenames were present for the PostgreSQL dump, canonical BTC CSV copy, manifest,
  and checksum categories: `postgres_20260715T082457Z.dump`, `btc_usd_daily_20260715T082457Z.csv`, `manifest.txt`, and
  `SHA256SUMS`.
- Checksum evidence: `shasum -a 256 -c SHA256SUMS` passed for the copied backup artifacts covered by the checksum file:
  PostgreSQL dump, BTC CSV copy, and manifest.
- Public GET-only readiness evidence after deploy: `GET /api/health` returned `status=ok`; `GET /api/readiness` returned
  `status=ready`, `latest_date=2026-07-14`, `covered_end=2026-07-14`, `data_age_days=1`, `max_age_days=2`,
  `source=coinmarketcap_csv`, `row_count=5846`, and `methodology_version=crypto-scout-canonical-v1`.
- Public latest-risk evidence after deploy: `GET /api/risk/latest` returned timestamp
  `2026-07-14T00:00:00+00:00`, risk `0.2694028326125623`, `risk_state=low`,
  `model_price_usd=64069.92364076667`, `low_usd=62207.522497`, and `high_usd=65046.1341991`.
- Public cache/header evidence: GET header capture for `/api/risk/latest` showed
  `Cache-Control: public, max-age=60, stale-while-revalidate=300`, an `ETag`, an `X-Cache-Version` containing the
  validation timestamp and latest date, and `cf-cache-status: HIT`. GET header capture for `/api/readiness` showed
  `Cache-Control: no-store` and `cf-cache-status: DYNAMIC`.
- Method boundary: `HEAD` requests returned 405 with `Allow: GET`; readiness evidence for this pass is GET-only and does
  not claim HEAD support.
- Remaining first-traffic blockers after this pass: manual keyboard, screen-reader/assistive-tech, and physical/native
  browser checks; sanitized import/data-refresh proof if still required beyond public checks and operator confirmation;
  final launch snapshot packet; and separate operator approval/run for first traffic. Restore drill remains an accepted
  deferred limitation until a safe staging or intentionally empty restore target exists. Dedicated API monitoring and
  alert delivery remain broader-launch limitations.

Manual/native browser QA evidence recorded on 2026-07-15:

- Gate status: partial, not launched. Manual keyboard/native browser QA is completed for the small operator-watched
  pilot, but first traffic remains blocked by the remaining evidence gates below.
- Scope/safety: documentation/evidence update only. No deploy, push, tag, refresh/import, waitlist POST,
  Cloudflare/routing change, public endpoint probe, monitor configuration, backup/off-server copy, restore drill, first
  traffic, or production mutation was performed from this workspace. No exact device model, user account, screenshot,
  contact detail, private browser/profile detail, private filesystem path, token, secret, or raw production artifact is
  recorded.
- Public site checked: `https://bitcoinriskbrief.minihub.app/`.
- Sanitized environment categories checked: notebook/native desktop browser and mobile/native browser.
- Reported result: page loaded correctly; current risk/date were visible; the main visual/chart was visible; no obvious
  layout issue was reported; and the language toggle plus visible controls worked correctly.
- Waitlist boundary: no production waitlist POST was claimed by this evidence.
- Accessibility boundary: this closes the small-pilot manual keyboard/native browser evidence blocker only. No separate
  screen-reader or assistive-tech tool pass was reported in this manual/native pass.
- Remaining first-traffic blockers immediately after this manual/native pass, before the assistive-tech proxy QA below:
  the dedicated assistive-tech status still needed a separate decision; sanitized import/data-refresh proof if still
  required beyond public checks and operator confirmation; fresh public readiness/latest-risk checks in the launch window;
  final launch snapshot packet; and separate operator approval/run for first traffic. Restore drill remains an accepted
  deferred limitation until a safe staging or intentionally empty restore target exists. Dedicated API monitoring and
  alert delivery remain broader-launch limitations.

Assistive-tech proxy QA and pilot limitation recorded on 2026-07-15:

- Gate status: partial, not launched. The strongest AI-doable local/browser accessibility proxy checks passed, and the
  absence of a dedicated screen-reader/manual assistive-tech pass is accepted only as a limitation for the small
  operator-watched pilot. First traffic remains blocked by the remaining evidence gates below.
- Scope/safety: local frontend tests, local browser automation, mocked API routes, documentation update, and git-state
  inspection only. No deploy, push, tag, refresh/import, cache warmup, production endpoint probe, waitlist POST,
  Cloudflare/routing change, monitor configuration, backup/off-server copy, restore drill, first traffic, or production
  mutation was performed from this workspace.
- Existing accessibility tooling/source inspection: `frontend/src/App.test.tsx` covers waitlist live status/error
  semantics, invalid-input linkage, no browser-storage persistence for contacts, screen-reader chart data alternatives,
  accessible chart labels, visible focus styles, Arabic RTL/LTR numeric isolation, and localized waitlist behavior.
  `frontend/e2e/frontend-quality.spec.ts` covers mocked-route layout/chart rendering, focused axe scans, keyboard/focus
  navigation through the public controls, degraded readiness, API failure behavior, and Arabic RTL browser-profile
  checks.
- Local verification passed: `npm test --prefix frontend` passed 4 files / 54 tests; `npm run build --prefix frontend`
  passed; `npm run smoke --prefix frontend` was confirmed safe/non-mutating because it uses local preview plus mocked API
  routes and does not reach the production waitlist. The first sandboxed smoke attempt was blocked by `listen EPERM` on
  `127.0.0.1:4173`; the approved local/browser rerun exposed a stale keyboard-smoke adjacency assumption after 25 checks
  passed and 5 keyboard checks failed. After updating the smoke to verify bounded keyboard reachability through the
  current tab order, the focused Chromium keyboard check passed and the full approved local mocked smoke passed 30
  Playwright checks across Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles, including focused axe and
  keyboard/focus checks.
- Local ARIA snapshot proxy: an approved local Playwright `locator('main').ariaSnapshot()` check against the built app
  with mocked API routes exposed the main navigation, H1, current risk/readiness region, methodology region, waitlist
  textbox/button, and screen-reader chart data alternatives including recent history and threshold-price tables. The
  probe aborted any waitlist request and made no production request.
- Boundary: this is assistive-tech proxy evidence, not a VoiceOver, NVDA, TalkBack, switch-control, screen-magnifier, or
  manual assistive-tech pass. It is not full WCAG conformance, legal accessibility approval, or a claim that canvas-drawn
  chart internals are directly accessible without the implemented non-canvas alternatives.
- Remaining first-traffic blockers after this pass: sanitized import/data-refresh proof if still required beyond public
  checks and operator confirmation; fresh public readiness/latest-risk checks in the launch window; final launch snapshot
  packet; and separate operator approval/run for first traffic. The dedicated screen-reader/manual assistive-tech pass is
  deferred as an accepted limitation only for the small operator-watched pilot. Restore drill remains an accepted deferred
  limitation until a safe staging or intentionally empty restore target exists. Dedicated API monitoring and alert
  delivery remain broader-launch limitations.

AI-resolvable pre-traffic readiness sweep recorded on 2026-07-12:

- Gate status: AI-resolvable sweep completed; overall launch gate remains blocked, not passed. First traffic is not
  allowed now because the remaining blockers require operator/manual or external-provider evidence.
- Scope/safety: local verification, docs reconciliation, git-state inspection, and public GET-only endpoint validation
  only. No deploy, refresh/import, cache warmup, waitlist POST to production, Cloudflare/routing change, external provider
  configuration, alert delivery test, backup/off-server copy, restore drill, first traffic, raw SQL output capture,
  private contact capture, or production mutation was performed.
- Starting git state for the sweep: local `HEAD` was `bbb5147`, `origin/main` was `08ff527`, and
  `git rev-list --left-right --count origin/main...HEAD` returned `0 2`. The local tag
  `support-recovery-ready-evidence-2026-07-12` pointed at `HEAD`; the two unpushed evidence commits were
  `68b8e02 docs: record operator decision resolution status` and
  `bbb5147 docs: record support recovery readiness status`.
- Public GET-only endpoint probe: the sandboxed first attempt failed before receiving `/api/health` because network
  access was unavailable. The same approved GET-only command then passed:
  `python3 scripts/check_public_endpoints.py --base-url https://bitcoinriskbrief.minihub.app --max-data-age-days 2
  --require-cache-header Cache-Control --require-cache-header ETag --require-cache-header X-Cache-Version
  --require-cache-header X-Cache`. Sanitized result:
  `OK public endpoints healthy latest_date=2026-07-11 risk=0.2190 freshness=max_data_age_days:2
  cache_headers=Cache-Control,ETag,X-Cache-Version,X-Cache`.
- Local frontend verification: `npm test --prefix frontend` passed 2 test files and 27 tests;
  `npm run build --prefix frontend` passed with `dist/index.html` at 1.36 kB gzip 0.46 kB, `index` JS at
  218.57 kB gzip 69.43 kB, and lazy `Chart` JS at 557.61 kB gzip 188.87 kB; `npm run smoke --prefix frontend` was
  confirmed safe/non-mutating because it uses a local preview server and mocked API routes, including the waitlist route.
  The sandboxed smoke attempt was blocked by `listen EPERM` on `127.0.0.1:4173`; the approved local rerun passed 25
  Playwright checks.
- Remaining true manual/external blockers after the later 2026-07-15 backup/readiness, manual/native QA, and
  assistive-tech proxy QA evidence: sanitized production import/data-refresh proof if still required beyond public checks
  and operator confirmation; fresh public readiness/latest-risk checks in the launch window; final launch snapshot packet
  after remaining blockers are complete; and the operator-watched first traffic run. Dedicated external `/api/health` and
  `/api/readiness` monitoring plus alert delivery remain pending for broader launch, not as a small-pilot first-traffic
  blocker. A true screen-reader/manual assistive-tech pass remains deferred only as an accepted small-pilot limitation.
- First traffic decision: not allowed now. Keep `first_traffic_status` at `not_run` until the manual/external blockers
  above are completed, the final launch snapshot exists, and the operator separately approves the first traffic run.

Production/operator evidence still pending before public launch:

- Final pre-traffic public readiness/freshness recheck. The 2026-07-11 backup-gated update evidence below records
  update-time public readiness/latest/cache evidence, and the 2026-07-12 monitoring/alert gap pass plus the later
  2026-07-12 AI-resolvable sweep record current local public GET-only endpoint probes, but freshness remains
  time-sensitive.
- Production import provenance packet for a real production refresh/import, including sanitized source category,
  retrieval/import timestamp, row count/range, readiness/latest-risk output, and checksum if available. The operator has
  confirmed that the refresh/import workflow is complete and operational for the small operator-watched pilot, but the
  sanitized packet still needs to be recorded before or during the final launch snapshot. Use
  [docs/import-provenance-evidence-packet-template.md](import-provenance-evidence-packet-template.md) to collect a
  sanitized packet outside Git before copying final outcomes into launch docs. The template is not completed evidence
  and does not close this blocker by itself.
- Fresh manual backup plus off-server copy is completed for the current first-traffic evidence set by the 2026-07-15
  mounted-removable-media backup copy and checksum verification above. Recurring backup automation and backup freshness
  alerting remain deferred until after the initial operator-watched pilot. Use
  [docs/backup-restore-evidence-packet-template.md](backup-restore-evidence-packet-template.md) for future backup/restore
  evidence and any later restore-drill packet. The template is not completed evidence by itself.
- Broader-launch monitoring proof: the 2026-07-14 operator decision accepts Cloudflare Tunnel Health Alert plus an
  external homepage availability monitor as sufficient for a small operator-watched pilot. Dedicated external
  `/api/health` and `/api/readiness` freshness monitor evidence, stale-data after-window alert evidence, and explicit
  sanitized alert delivery evidence remain pending before broader traffic or broader readiness/freshness claims.
- Restore drill evidence on a staging project or intentionally empty restore target; no live-production restore drill is
  recorded or recommended.
- Manual keyboard/native browser evidence is completed for the small pilot by the 2026-07-15 manual/native QA note above,
  and the 2026-07-15 local assistive-tech proxy QA pass records the missing dedicated screen-reader/manual assistive-tech
  pass as an accepted limitation only for the small operator-watched pilot. Full accessibility/WCAG, legal approval,
  broader assistive-tech coverage, and full dependency/license compliance evidence remain pending before broader claims.
- Commercial/broader-launch source-terms review or paid-plan decision before commercial claims, paid beta, broader
  distribution, or any claim of legal approval or commercial readiness. The current source-terms posture is accepted only
  for a small unpaid/non-commercial operator-watched pilot.
- Final launch snapshot packet and an operator-watched first traffic test.
  Use [docs/launch-snapshot-evidence-packet-template.md](launch-snapshot-evidence-packet-template.md) to prepare the
  final snapshot outside Git first; the template is not completed evidence and does not close this blocker by itself.

External gates that cannot be closed from this local workspace include broader-launch Cloudflare or external monitor
provider configuration, alert delivery tests, recurring production backup/off-server automation, restore target
provisioning, legal/license approval, and first traffic.

Recommended next production sequence before first traffic:

1. Complete the remaining operator-owned setup after the 2026-07-15 backup/readiness, manual/native QA, and
   assistive-tech proxy QA evidence: sanitized import proof if still required beyond public checks and operator
   confirmation, fresh launch-window public readiness/latest-risk checks, and the final launch snapshot.
2. Deploy or update the selected production path and record project revision, health/readiness, public-host
   privacy/metadata/accessibility smoke, and selected Cloudflare edge posture.
3. Run the production refresh/import path and create the production import provenance packet from the real source,
   canonical output, validation/readiness, cache evidence, and deployment context.
4. Carry the completed 2026-07-15 fresh backup/off-server copy evidence into the final launch snapshot, keep recurring
   backup automation as post-pilot work, and keep the restore drill pending until a safe restore target exists.
5. Keep the accepted small-pilot monitoring coverage active, run the public endpoint probe with the selected freshness
   policy for final evidence, and defer dedicated external `/api/health`, `/api/readiness`, stale-data, collector-failure,
   backup-freshness, and alert-delivery monitoring evidence to broader launch.
6. Keep public-host metadata, privacy/terms/disclaimer copy, browser/device smoke, manual/native browser evidence, and
   assistive-tech proxy evidence current without claiming a true screen-reader/manual assistive-tech pass, full WCAG
   conformance, or legal accessibility approval.
7. Create and validate the final launch snapshot packet from already collected sanitized evidence, using
   [docs/launch-snapshot-evidence-packet-template.md](launch-snapshot-evidence-packet-template.md) as the outside-Git
   collection template before copying final sanitized outcomes into launch docs.
8. Run the operator-watched first traffic test only after freshness and all launch gates are completed or explicitly
   accepted.

Consolidated first-traffic blocker and acceptance register recorded on 2026-07-12:

- Gate status: partial/blocked, not passed. First traffic is not allowed by the current evidence. This register
  consolidates the current launch-gate blockers, newly recorded sanitized operator decisions, the 2026-07-12
  support/contact and account recovery readiness evidence, and accepted limitations from repository-visible docs,
  existing dated evidence notes, and the 2026-07-12 operator decision resolution pass. It does not create a launch
  snapshot packet, run first traffic, deploy, push, tag, refresh/import data, configure alerts, or close any gate by
  inference.
- Scope/safety: documentation-only register update. No deploy, refresh/import, production endpoint probe, waitlist POST,
  Cloudflare/routing change, monitor configuration, alert delivery test, backup/off-server copy, restore drill, first
  traffic, push, or tag was performed. At the start of this operator-decision pass, local `HEAD` and `origin/main` were
  `08ff527`, the local tag at `HEAD` was `first-traffic-blocked-evidence-2026-07-12`, and the local branch was
  `main...origin/main`.
- Accepted limitations: restore-drill deferral until a safe staging or intentionally empty restore target exists; the
  current Cloudflare Free-plan-compatible subset for a small operator-watched pilot only; recurring backup automation and
  backup freshness alerting deferred until after the initial pilot now that the 2026-07-15 fresh manual backup plus
  off-server copy has passed; small-pilot monitoring coverage limited to Cloudflare Tunnel Health Alert plus public
  homepage availability monitoring; dedicated screen-reader/manual assistive-tech pass deferred only for the small
  operator-watched pilot after the 2026-07-15 proxy QA pass; and CoinMarketCap/source-terms commercial or paid-plan
  decision deferred only for commercial claims, paid beta, or broader distribution. Missing sanitized import proof if still
  required beyond public checks and operator confirmation, launch snapshot, and first-traffic operator approval are not
  accepted limitations. Manual keyboard/native browser QA is completed for the small pilot by the 2026-07-15 evidence
  note. Dedicated external
  `/api/health` and `/api/readiness` freshness monitors plus explicit alert delivery evidence remain pending
  broader-launch limitations.

| Gate area | Consolidated status | Blocker or required acceptance before first traffic |
| --- | --- | --- |
| Waitlist governance | Resolved for sanitized first-traffic decision; support path is ready for manual requests. | Owner role is founder/operator; review cadence is several times per week during pilot; review method is a manual operator-run database query or script; pilot contacts are retained until beta ends and deleted earlier on operator-approved request; deletion/unsubscribe requests use the dedicated support contact path kept outside Git; follow-up is manual founder/operator follow-up only, with no automated newsletter. |
| Support/contact path | Completed for first-traffic readiness. | Support email status is created and ready. The contact category is a dedicated support mailbox with a project-domain alias; exact addresses and provider details are kept outside Git. The support path was checked by the founder/operator. Deletion/unsubscribe requests use a manual request through the dedicated support contact path. No paid support SLA is claimed. |
| Account recovery ownership | Completed for first-traffic readiness. | The account recovery record is created outside Git and current. GitHub, Cloudflare/domain, server, secrets/.env, and backups owner role is founder/operator. Do not record account IDs, holders, recovery paths, recovery text, private URLs, or secret locations in Git. |
| Source terms and import governance owner | Partial with accepted pilot limitation. | Current product status is unpaid/non-commercial pilot. Source terms owner role is founder/operator. If interest or paid/commercial use appears, the operator intends to buy the appropriate plan or make the required terms/plan decision. Terms review or paid plan remains required before commercial claims, paid beta, or broader distribution. This is acceptable only for a small operator-watched pilot and is not legal approval or commercial readiness. |
| Dependency/security ownership and status | Partial. | Dependency/security owner role is founder/operator with monthly review cadence during pilot. GitHub-hosted Dependabot execution/first PR evidence remains pending; dependency/license external confirmation remains pending before broader commercial launch. No vulnerability clearance, legal approval, or full license compliance is claimed. |
| First-user feedback path | Partial/resolved for planned path; post-traffic evidence pending. | Feedback channels are waitlist notes and direct support-email replies with no raw contacts in Git. Reviewer role is founder/operator. Review cadence is after the first traffic window and several times per week during pilot. Evidence summaries must be aggregate/sanitized only, with no raw contacts or message text. |
| External provider/dashboard monitoring proof | Accepted/closed for the small operator-watched pilot with limitation. | Cloudflare Tunnel Health Alert is configured, and a HetrixTools/external uptime monitor provider category is recorded for public homepage availability. No account IDs, monitor IDs, private dashboard URLs, alert recipients, webhook URLs, tokens, screenshots, or secrets are recorded. Dedicated external `/api/health`, `/api/readiness`, and latest-risk monitor evidence remains pending for broader launch. |
| Health/readiness/stale-data alert rules | Deferred broader-launch limitation, not a small-pilot first-traffic blocker. | No dedicated external `/api/health` or `/api/readiness` freshness monitor evidence, stale-data after-window alert evidence, JSON assertion evidence, or explicit alert delivery test evidence is recorded yet. Record those before broader traffic or broader readiness/freshness claims. |
| Collector failure alert | Deferred broader-launch limitation. | Record sanitized alert coverage for scheduled refresh failures, public-download failures, optional API fallback failures, missed scheduled runs, and repeated collector restarts before broader traffic. |
| Backup freshness alert | Deferred only after first traffic prerequisites. | Recurring backup automation and freshness alerting are deferred until after the initial operator-watched pilot. This limitation is accepted for the small pilot because the 2026-07-15 fresh manual backup plus off-server copy passed before first traffic. |
| Cloudflare Tunnel health notification | Accepted/closed for the small operator-watched pilot. | Cloudflare Tunnel Health Alert is configured. Keep account IDs, tunnel IDs, private dashboard URLs, alert recipients, routing details, tokens, and screenshots out of Git. |
| Alert delivery test | Deferred broader-launch limitation. | No explicit alert delivery test evidence is recorded. Send and record sanitized delivery evidence before broader traffic or broader monitoring claims, including covered rules and delivered/not-delivered result without private recipients. |
| Fresh manual backup and off-server copy | Completed for current first-traffic evidence. | The 2026-07-15 mounted-removable-media backup copy for timestamp basename `20260715T082457Z` included PostgreSQL dump, BTC CSV, manifest, and checksum categories, and copied-backup SHA-256 verification passed. Keep raw backup contents and private paths outside Git. |
| Recurring production backup schedule | Accepted limitation/deferred only after initial pilot. | Recurring automation is deferred until after the initial operator-watched pilot. |
| Recurring off-server copy | Accepted limitation/deferred only after initial pilot. | Recurring copy automation is deferred until after the initial operator-watched pilot. |
| Backup freshness monitor | Accepted limitation/deferred only after initial pilot. | Backup freshness monitoring is deferred until after the initial operator-watched pilot. |
| Backup alert delivery | Accepted limitation/deferred only after initial pilot. | Backup alert delivery is deferred until after the initial operator-watched pilot. |
| Restore drill | Accepted limitation/deferred. | Keep deferred until a safe staging or intentionally empty restore target exists. No live-production restore drill should be run. When a safe target exists, record checksum verification, restore result, readiness, and cleanup status. |
| Production import source/archive proof | Partial/blocking for final snapshot. | The operator confirms the production data refresh path is complete and working correctly for the small pilot. Record sanitized proof before or during the final launch snapshot, including latest source category, retrieval/import timestamp, row count/range, readiness/latest-risk output, and checksum if available. |
| Production import metadata and validation | Partial/blocking for final snapshot. | Record sanitized validation/import metadata and readiness/latest-risk output in the final snapshot if not already in Git. No accepted limitation is intended for the refresh workflow. |
| Database row count and recomputation proof | Partial/blocking for final snapshot. | Record row count/range and readiness/latest-risk output from the current production data state in sanitized final evidence. |
| Source owner decision | Partial/resolved for owner role. | Source terms owner role is founder/operator. Commercial/broader-launch source terms review or paid-plan decision remains required before commercial claims, paid beta, or broader distribution. |
| Manual keyboard accessibility evidence | Completed for small-pilot manual/native QA. | The 2026-07-15 manual/native browser QA evidence records manual keyboard/native check status as passed for the public site. This does not claim a dedicated screen-reader/assistive-tech pass or full WCAG/legal accessibility compliance. |
| Screen-reader or assistive-tech evidence | Accepted limitation/deferred for the small operator-watched pilot. | The 2026-07-15 local assistive-tech proxy QA passed, but no VoiceOver, NVDA, TalkBack, switch-control, screen-magnifier, or manual assistive-tech pass was performed. Do not claim a true screen-reader/manual assistive-tech pass; record one before broader accessibility claims or broader launch. |
| Physical/native browser evidence | Completed for small-pilot manual/native QA. | The 2026-07-15 manual/native browser QA evidence covers notebook/native desktop browser and mobile/native browser categories on the public site, with page load, current risk/date, main visual/chart, layout, language toggle, and visible controls reported working. Exact device models, screenshots, and private browser/profile details are not recorded. |
| Full WCAG/legal accessibility status | Not claimed; broader-launch/legal evidence pending. | Do not claim full WCAG/legal accessibility compliance. Manual/native browser QA and local assistive-tech proxy QA support the small pilot only; broader compliance evidence and legal accessibility approval are not recorded. |
| Remaining cache-miss/edge-hit latency matrix | Partial historical evidence; blocked if still required by the launch matrix. | Record current endpoint-specific cache-miss and edge-hit timing for any public read endpoints not covered by current accepted evidence, or explicitly accept remaining latency limitations. |
| Cloudflare Free-plan first-traffic decision | Accepted limitation for small operator-watched pilot only. | The current Free-plan-compatible subset is accepted for a small operator-watched pilot. Managed WAF/additional rate-limit controls are deferred until broader traffic or observed abuse risk. Do not claim broader Cloudflare security readiness. |
| Fresh pre-traffic readiness evidence | Supporting 2026-07-15 public GET-only evidence recorded; final snapshot still pending. | Public health, readiness, latest-risk, freshness, date alignment, readiness `no-store`, and latest-risk cache headers are recorded for `latest_date=2026-07-14`. If first traffic is delayed, recheck freshness in the final launch snapshot window. |
| Sanitized final launch snapshot packet | Blocked pending packet. | Create and validate a real sanitized launch snapshot packet from collected evidence outside Git, then copy only sanitized final status into launch docs. Do not treat templates or helper availability as a packet. |
| Final operator acceptance | Blocked pending operator acceptance. | Record sanitized final operator acceptance only after all required gates are completed, the launch snapshot exists, and the only remaining limitations are the accepted limitations listed in this register. No final acceptance is recorded now. |
| Remote publication if required | Not blocking in current local state. | Local `HEAD` and `origin/main` both resolved to `08ff527` at the start of the decision pass. This pass does not push or tag. |

- First traffic decision: not allowed now. The project remains not publicly launched, and first traffic must stay
  `not_run` until the remaining small-pilot blockers above are completed, the final launch snapshot packet is created
  from current evidence, and the only remaining limitations are the accepted limitations listed in this register.

Final launch snapshot readiness/gap pass recorded on 2026-07-12:

- Gate status: blocked, not passed. No real sanitized final launch snapshot packet was provided or created from current
  evidence, and no final first-traffic operator acceptance is recorded. The project remains not publicly launched.
- Scope/safety: documentation/evidence pass only. This pass inspected current repository docs, the launch snapshot packet
  template, `scripts/launch_snapshot_packet.py`, helper tests, local branch state, and the read-only remote `main` ref.
  No deploy, refresh/import, cache warmup, waitlist POST, Cloudflare/routing change, production host command, external
  monitor configuration, alert delivery test, backup/off-server copy, restore drill, first traffic, push, or tag was
  performed. No new public GET endpoint checks were run during this pass.
- Launch revision state before this documentation edit was committed: local HEAD was
  `32d55da2f334d7e0766bc699cb2399494432c716` (`32d55da`). The only local tag pointing at that launch-candidate HEAD was
  `launch-matrix-qa-partial-evidence-2026-07-12`. The local branch was `main...origin/main [ahead 5]`; `origin/main` and
  read-only `git ls-remote origin refs/heads/main` both resolved to `fe20c6ed2bcbb71772c066f27f50fe2b7b3d5b9a`.
  Therefore the five evidence commits listed by
  `git log --oneline --decorate origin/main..HEAD` were not published to remote `main` at the time of this pass.
  After this documentation edit was committed, current local `HEAD` is
  `70020e30eb18edf26f8c2cd41b30384fa8bd606f` (`70020e3`), the local branch is
  `main...origin/main [ahead 6]` while remote `main` remains `fe20c6e`, and no local tag points at `HEAD`.
- Supporting public-host evidence: no fresh public GET checks were run for this snapshot pass. Existing 2026-07-12
  public GET-only evidence in this document supports current public behavior only: health/readiness/latest-risk checks
  passed with `latest_date=2026-07-11`, rounded latest risk `0.2190`, `risk_state=low` where captured by the
  launch-matrix pass, and product cache headers were present where checked. This is supporting current public evidence,
  not final pre-traffic evidence, because upstream launch gates remain incomplete.
- Required evidence reference status: support/contact and account recovery readiness are completed by the later
  2026-07-12 sanitized evidence note; small-pilot monitoring coverage is accepted/closed by the 2026-07-14 sanitized
  note with dedicated API readiness/freshness monitoring and alert delivery deferred for broader launch; the fresh manual
  backup/off-server copy blocker is completed by the 2026-07-15 evidence, while recurring backup/off-server
  copy/freshness automation is deferred until after the initial pilot; production import provenance remains partial
  pending sanitized final proof;
  launch matrix/accessibility/public-host QA remains partial; restore-drill deferral and the Cloudflare Free-plan subset
  are accepted only for the small operator-watched pilot under the limitations recorded in the current blocker register.
- Launch snapshot helper status: `scripts/launch_snapshot_packet.py` and
  [Launch Snapshot Evidence Packet Template](launch-snapshot-evidence-packet-template.md) were inspected. The helper
  exposes local-only `create` and `validate` modes, stores evidence basenames instead of full paths, rejects unsafe
  values, keeps missing categories pending, and defaults `first_traffic_status` to `not_run`. Local helper validation
  `python3 scripts/launch_snapshot_packet.py --help` completed successfully, and
  `python3 -m unittest backend.tests.test_launch_snapshot_packet` passed 12 tests. This validates helper availability
  only; it does not create a final packet or close launch evidence gaps.
- Blockers preventing a true final launch snapshot: sanitized production import
  source/import proof if still required beyond public checks and operator confirmation; remaining cache-miss/edge-hit
  latency matrix if still required; final pre-traffic public readiness evidence; final first-traffic operator acceptance;
  first traffic itself; and remote publication of the current local evidence commit if remote publication is required.
  Production-host accessibility beyond the recorded manual/native, automated axe, and local proxy evidence, full
  WCAG/legal accessibility evidence, and a true screen-reader/manual assistive-tech pass remain unclaimed limitations, not
  completed evidence.
- First traffic remains blocked. Do not treat the final launch snapshot gate as closed until a real sanitized packet is
  created from current evidence, all required blockers are completed, the only remaining limitations are the accepted
  limitations listed in the 2026-07-12 decision pass, and first traffic is separately approved and recorded.

Backup-gated USB production update evidence recorded on 2026-07-11:

- Scope/safety: documentation-only evidence note for existing operator/public evidence. During this docs update, no code,
  tests, scripts, CSV data, config, lockfiles, deploy, refresh/import, cache warmup, waitlist POST,
  Cloudflare/routing change, production endpoint call, monitor configuration, first traffic, commit, push, or tag was
  performed. This note intentionally avoids private paths, raw logs, raw backup contents, raw CSV contents, `.env` values,
  secrets, account details, private dashboard URLs, raw waitlist contacts, private contacts, and PII.
- Production update identity: target commit `86cb2dad889baf24a7464a105bbe2224f75b14ef`; evidence tag
  `predeployment-readiness-reconciled-2026-07-11`.
- Backup-gated USB update status: completed with server-reported exit code 0. Backup timestamp basename:
  `20260711T190355Z`.
- Backup evidence: copied/off-server backup freshness/checksum checker passed as valid and fresh,
  age `0.28h <= max 30h`. Expected copied artifact filenames were present: `postgres_20260711T190355Z.dump`,
  `btc_usd_daily_20260711T190355Z.csv`,
  `manifest.txt`, and `SHA256SUMS`. These correspond to the PostgreSQL dump, canonical BTC CSV copy, backup manifest,
  and checksum file categories. Local backup checksum verification is evidenced by the deploy exit 0 and the USB update
  script flow, which verifies local backup checksums before copying and exits on failure.
- Public API probe evidence: readiness/latest checks passed with `latest_date=2026-07-10`, `row_count=5842`,
  `data_fresh=True`, `risk=0.26161621315507155`, and `risk_state=low`. Required public cache headers were present:
  `Cache-Control`, `ETag`, `X-Cache-Version`, and `X-Cache`.
- Public metadata/privacy evidence: the public homepage included `title`, meta description, canonical URL, Open Graph
  `type`, `title`, `description`, `url`, and `site_name`, plus Twitter `card`, `title`, and `description`. `og:image`
  and `twitter:image` were absent as expected because no real repo-served production image asset exists. The public
  privacy/disclaimer note was present in the browser smoke.
- Browser smoke evidence: desktop and mobile smoke passed with the H1, readiness, and latest date visible; charts were
  nonblank; the EN/RU toggle worked; no horizontal overflow was observed; the privacy/disclaimer note was present; and
  no waitlist POSTs were observed.
- Explicit non-events: no data refresh/import, waitlist POST, Cloudflare/routing change, external monitor configuration,
  manual cache warmup, first traffic, or import provenance packet for a new production import occurred in this update.
- Remaining gates after this evidence: external monitors and alert delivery, import provenance if a later refresh/import
  runs, recurring backup freshness monitoring and alert delivery, restore drill target and drill, manual/native
  accessibility checks, final launch snapshot, and first traffic.

External monitoring and alert delivery gate remains partial/blocked as of 2026-07-11:

Use [docs/monitoring-alert-evidence-packet-template.md](monitoring-alert-evidence-packet-template.md) to collect
sanitized monitoring and alert evidence outside Git before copying final outcomes into this gate. The template is not
completed evidence and does not close monitor/provider or alert-delivery blockers by itself.

- Scope/safety: public GET-only endpoint validation plus documentation-only gate status. No code, test, script, CSV data,
  config, or lockfile changes were made; no deploy, refresh/import, cache warmup command, waitlist POST,
  Cloudflare/routing change, external monitor configuration, alert delivery test, first traffic, commit, push, or tag was
  performed. The sandboxed public probe first failed on network access, then the same GET-only probe was rerun with
  network access. This note intentionally avoids secrets, tokens, private dashboard URLs, account IDs, recipient
  addresses, phone numbers, private contacts, raw logs, `.env` values, raw waitlist contacts, raw backup contents, and
  private filesystem paths.
- Provider name/type: not recorded because no external monitoring provider dashboard/API evidence was available in this
  workspace. No chosen provider, monitor IDs, dashboard URLs, account IDs, or delivery recipients were inspected.
- Latest public endpoint check time: 2026-07-11T20:46:22Z. Local probe command:
  `python3 scripts/check_public_endpoints.py --base-url https://bitcoinriskbrief.minihub.app --max-data-age-days 2
  --require-cache-header Cache-Control --require-cache-header ETag --require-cache-header X-Cache-Version
  --require-cache-header X-Cache`.
- Public endpoint probe result: passed. Assertions covered `GET /api/health` HTTP 200 with `status: ok`,
  `GET /api/readiness` HTTP 200 with `status: ready`, all required readiness checks true including `data_fresh`, matching
  readiness/latest-risk dates, latest data age no more than 2 UTC days, and required cache headers on cacheable product
  responses. Sanitized summary: `latest_date=2026-07-10`, `risk=0.2616`, cache headers present.
- Backup freshness checker result from this workstation: failed/stale for local backup timestamp basename
  `20260626T165423Z` with a 30-hour freshness window. This is not production-host or off-server scheduler evidence. The
  latest recorded production update backup evidence remains the historical 2026-07-11 copied/off-server checker pass for
  timestamp basename `20260711T190355Z`, but recurring backup scheduling, selected-scheduler execution, off-server-root
  monitoring, and alert delivery are still unverified.

| Required coverage | 2026-07-11 sanitized status | Assertion type / limitation |
| --- | --- | --- |
| Uptime monitor for `GET /api/health` | Broader-launch pending after the 2026-07-14 small-pilot acceptance. Local public probe passed, but no dedicated external provider monitor was configured or verified. | HTTP 200 and JSON `status: ok` assertion proven by local probe only; record dedicated external API monitor evidence before broader traffic. |
| Readiness/freshness monitor for `GET /api/readiness` | Broader-launch pending after the 2026-07-14 small-pilot acceptance. Local public probe passed, but no dedicated external provider JSON assertion evidence was available. | HTTP 200, JSON `status: ready`, required readiness checks, `data_fresh`, date match, max age, and readiness `no-store` proven by local probe only. If the selected provider cannot assert JSON before broader traffic, use this probe from cron or a synthetic runner and record that limitation. |
| Latest-risk monitor for `GET /api/risk/latest` | Broader-launch pending. Local public probe passed, but no external provider monitor evidence was available. | HTTP 200, parseable timestamp date matching readiness, numeric risk in range, freshness, and cache headers proven by local probe only. |
| Backup freshness monitor | Deferred recurring-operations limitation. Workstation-local checker failed stale; production/off-server scheduler evidence was unavailable. | The later 2026-07-15 fresh manual backup/off-server pass closes the small-pilot first-traffic backup prerequisite; recurring monitoring can be recorded from the production host or selected scheduler with off-server root later. |
| Cloudflare Tunnel connector health notification | Accepted/closed for the small operator-watched pilot by the 2026-07-14 monitoring acceptance. | Cloudflare Tunnel Health Alert is configured. Keep account IDs, tunnel IDs, routing details, dashboard URLs, alert recipients, screenshots, and tokens out of Git. |
| Alert delivery | Deferred broader-launch limitation. No provider channel was available and no test alert was sent. | Record channel type, test time, and delivered/not-delivered only after an operator sends a test through the chosen channel before broader traffic. |

- Monitoring/alert delivery gate status: accepted/closed for the small operator-watched pilot with limitation after the
  2026-07-14 monitoring acceptance. Public health/readiness/latest-risk behavior was healthy by local probe, and
  Cloudflare Tunnel Health Alert plus public homepage availability monitoring are accepted for the watched pilot.
  Dedicated external API monitor proof, JSON assertion configuration or documented provider limitation, backup freshness
  scheduler proof, stale-data/collector-failure alert proof, and alert delivery test evidence remain broader-launch work.
- Remaining first-traffic blockers from this area: keep final pre-traffic public readiness fresh. Dedicated API monitors
  and alert delivery are broader-launch limitations, not small-pilot first-traffic blockers.

Fresh public endpoint readiness probe recorded on 2026-07-11:

- UTC check time: 2026-07-11T22:53:24Z.
- Base URL: `https://bitcoinriskbrief.minihub.app`.
- Probe command:
  `python3 scripts/check_public_endpoints.py --base-url https://bitcoinriskbrief.minihub.app --max-data-age-days 2
  --require-cache-header Cache-Control --require-cache-header ETag --require-cache-header X-Cache-Version
  --require-cache-header X-Cache`.
- Endpoints covered: `GET /api/health`, `GET /api/readiness`, and `GET /api/risk/latest`.
- Freshness policy: latest public data age no more than 2 UTC days.
- Sanitized result summary: probe passed; all covered public GET endpoints satisfied HTTP 200 assertions; readiness state
  was `ready`; latest date was `2026-07-10`; rounded latest risk was `0.2616`; readiness freshness was validated and
  required cache headers `Cache-Control`, `ETag`, `X-Cache-Version`, and `X-Cache` were present on cacheable product
  assertions. The probe output did not emit a risk state value.
- Limitation: this is a local/public GET-only probe. It does not prove external monitor provider configuration,
  scheduled monitor execution, or alert delivery, and the external monitoring/alert-delivery gate remains
  partial/blocked, not passed.

External monitoring and alert delivery evidence gap pass recorded on 2026-07-12:

Use [docs/monitoring-alert-evidence-packet-template.md](monitoring-alert-evidence-packet-template.md) to collect
sanitized monitoring and alert evidence outside Git before copying final outcomes into this gate. The template is not
completed evidence and does not close monitor/provider or alert-delivery blockers by itself.

- Scope/safety: documentation evidence plus a public GET-only endpoint probe. No code, test, script, CSV data, config, or
  lockfile changes were made; no deploy, refresh/import, cache warmup command, waitlist POST, Cloudflare/routing change,
  external monitor configuration, alert delivery test, first traffic, push, or tag was performed. The sandboxed public
  probe failed on network access, then the same GET-only probe was rerun with approved network access. This note
  intentionally avoids secrets, tokens, private dashboard URLs, account IDs, recipient addresses, phone numbers, private
  contacts, raw logs, `.env` values, raw waitlist contacts, raw backup contents, and private filesystem paths.
- Operator-provided monitoring evidence status: absent from the current repository and not provided during this pass. No
  sanitized external monitoring provider dashboard/API proof, alert rule proof, Cloudflare notification proof, backup
  monitor/scheduler proof, or alert-delivery test evidence was available. Repository evidence remains limited to local
  probe/checker tooling, templates, runbook expectations, and historical public/backup evidence notes.
- Public endpoint probe date: 2026-07-12. The probe output does not emit an exact response timestamp. Local probe
  command:
  `python3 scripts/check_public_endpoints.py --base-url https://bitcoinriskbrief.minihub.app --max-data-age-days 2
  --require-cache-header Cache-Control --require-cache-header ETag --require-cache-header X-Cache-Version
  --require-cache-header X-Cache`.
- Public endpoint probe result: passed. Sanitized output:
  `OK public endpoints healthy latest_date=2026-07-11 risk=0.2190 freshness=max_data_age_days:2
  cache_headers=Cache-Control,ETag,X-Cache-Version,X-Cache`. The probe covered `GET /api/health`, `GET /api/readiness`,
  and `GET /api/risk/latest`; readiness freshness and latest-risk cache headers were validated. The probe output did not
  emit `risk_state`, and this pass does not require `risk_state` from the probe.
- Backup freshness/off-server copy evidence status: no new production-host, off-server scheduler, monitor, or alert
  evidence was available. The latest recorded production update backup evidence remains the historical 2026-07-11
  copied/off-server checker pass for timestamp basename `20260711T190355Z`; recurring backup scheduling, selected
  freshness-window monitoring, off-server-root alerting, alert delivery, and restore-drill proof remain unverified. Do not
  claim a restore drill passed unless a staging or intentionally empty restore target exists.

| Required coverage | 2026-07-12 sanitized status | Evidence / remaining proof |
| --- | --- | --- |
| Uptime monitor for `GET /api/health` | Broader-launch pending; not a small-pilot blocker after the 2026-07-14 monitoring acceptance. | Local GET-only evidence supports HTTP 200/JSON health behavior. Dedicated external API monitor/dashboard or chosen scheduled runner proof, plus alerts on non-200, timeout, or TLS failure, remain required before broader traffic. |
| Readiness/freshness monitor for `GET /api/readiness` | Broader-launch pending; not a small-pilot blocker after the 2026-07-14 monitoring acceptance. | The approved local public probe passed with max data age 2 and readiness freshness checks. Dedicated external readiness/freshness JSON assertion, scheduled after-window run, and alert route evidence remain required before broader traffic. |
| Latest-risk public endpoint probe for `GET /api/risk/latest` | Broader-launch pending. | The approved local public probe passed with `latest_date=2026-07-11`, rounded risk `0.2190`, readiness/latest-risk date alignment, and required cache headers. Provider/scheduler proof and alert behavior for timeout, non-200, malformed JSON, stale/mismatched date, nonnumeric risk, or missing required cache headers remain broader-launch work. |
| Collector failure alert | Deferred broader-launch limitation. | Configure and record sanitized alerts for `scheduled_refresh_failed`, `public_cmc_download_failed`, API fallback failure when configured, missed scheduled refresh evidence, and repeated `data-collector` restarts before broader traffic. |
| Backup freshness/off-server copy alert | Deferred recurring-operations limitation. | Historical copied/off-server checker evidence exists for `20260711T190355Z`, and the later 2026-07-15 fresh manual backup/off-server pass closes the small-pilot first-traffic backup prerequisite. No recurring scheduler/monitor or delivery proof is recorded, so recurring backup alerting remains deferred after the small pilot prerequisites. |
| Cloudflare Tunnel health notification | Accepted/closed for the small operator-watched pilot by the 2026-07-14 monitoring acceptance. | Cloudflare Tunnel Health Alert is configured. Keep account IDs, tunnel IDs, dashboard URLs, tokens, routing details, screenshots, and recipient details out of Git. |
| Alert delivery channel | Deferred broader-launch limitation. | No explicit alert delivery test evidence is recorded. Send a real test notification through the chosen monitoring or alert system before broader traffic and record only the channel type, test time, delivered/not-delivered result, and covered rules. |

- Monitoring/alert delivery gate status: accepted/closed for the small operator-watched pilot with limitation after the
  2026-07-14 acceptance. Current public health/readiness/latest-risk behavior is supported by a local public GET-only
  probe, and Cloudflare Tunnel Health Alert plus public homepage availability monitoring are accepted for the watched
  pilot. Dedicated external API monitor/provider proof, alert rules, stale-data/readiness after-window alert proof,
  collector-failure alert proof, recurring backup freshness/off-server alert proof, and alert-delivery test evidence
  remain missing for broader launch.
- This 2026-07-12 gap status is superseded for the small operator-watched pilot by the 2026-07-14 sanitized monitoring
  acceptance note: Cloudflare Tunnel Health Alert plus public homepage availability monitoring are accepted as sufficient
  small-pilot coverage. The missing dedicated external `/api/health` monitor, dedicated external `/api/readiness`
  freshness monitor, stale-data after-window alert, collector-failure alert, backup freshness/off-server alert, and
  explicit alert delivery evidence remain broader-launch limitations, not small-pilot first-traffic blockers.

Recurring backup, off-server copy, and backup freshness evidence gap pass recorded on 2026-07-12:

Use [docs/backup-restore-evidence-packet-template.md](backup-restore-evidence-packet-template.md) to collect sanitized
recurring backup, off-server copy, backup freshness, alert, and restore-drill evidence outside Git before copying final
outcomes into this gate. The template is not completed evidence and does not close scheduler, copy, freshness-monitor,
alert-delivery, or restore-drill blockers by itself.

- Scope/safety: documentation evidence plus local non-production helper validation. No code, script, CSV data, config, or
  lockfile changes were made; no deploy, refresh/import, cache warmup command, waitlist POST, Cloudflare/routing change,
  production backup command, production scheduler change, off-server copy, external monitor configuration, alert
  delivery test, restore drill, first traffic, push, or tag was performed. This note intentionally avoids secrets, raw
  backup manifests, raw checksum files, raw logs, account details, private backup roots, private off-server destinations,
  private scheduler identifiers, contact details, `.env` values, raw waitlist contacts, and private filesystem paths.
- Operator-provided recurring backup evidence status: absent from the current repository and not provided during this
  pass. No sanitized cron, systemd timer, external scheduler, synthetic runner, production-host schedule, operator/owner
  role, recurring copy job, chosen off-server destination category, current freshness-window execution, backup freshness
  alert rule, or alert-delivery test evidence was available.
- Historical/supporting one-time evidence remains recorded but does not close recurring operations:
  - 2026-07-07: one checksum-verified off-server USB backup copy was verified for timestamp basename
    `20260707T111928Z`, with PostgreSQL dump, canonical BTC CSV, manifest, and checksum categories present.
  - 2026-07-11: the backup-gated USB update recorded copied/off-server freshness/checksum checker status valid and fresh
    for timestamp basename `20260711T190355Z`, age `0.28h <= max 30h`, with expected PostgreSQL dump, BTC CSV, manifest,
    and checksum categories present.
  - 2026-07-15: the fresh manual backup/off-server copy blocker is completed for the current first-traffic evidence set
    by mounted-removable-media copy timestamp basename `20260715T082457Z`; PostgreSQL dump, BTC CSV, manifest, and
    checksum categories were present, and copied-backup SHA-256 verification passed.
- Local helper validation: `python3 scripts/check_backup_freshness.py --help` completed successfully and showed the
  expected non-mutating checker interface: `--backup-root`, required `--max-age-hours` or
  `BACKUP_FRESHNESS_MAX_AGE_HOURS`, and optional `--off-server-root` or `OFFSERVER_BACKUP_ROOT`. This validates helper
  availability only; it is not a production backup, scheduler, off-server copy, freshness-window pass, or alert-delivery
  proof.
- Restore drill status: accepted limitation/deferred only. No staging project or intentionally empty restore target
  evidence was available, and no live-production restore drill was attempted or should be counted as launch evidence.

| Required backup coverage | 2026-07-12 sanitized status | Evidence / remaining proof |
| --- | --- | --- |
| Recurring production backup schedule for `./scripts/backup.sh` or equivalent | Blocked pending operator evidence. The backup script exists and historical manual/update-time backup evidence exists, but no recurring production cron, systemd timer, external scheduler, synthetic runner, cadence, latest scheduled run, or owner/operator role is recorded. | Choose and record the sanitized scheduler category, cadence, owner role, latest scheduled run UTC time, result, and failure behavior. Do not record private cron files, service account names, private paths, job IDs, account IDs, or raw logs. |
| Recurring off-server copy | Partial historical evidence only. One 2026-07-07 USB off-server copy and one 2026-07-11 copied/off-server checker pass exist, but no recurring copy job, cadence, destination category for recurring operation, latest recurring copy timestamp, or recurring checksum-verification evidence is recorded. | Configure and record recurring copy to a sanitized destination category such as mounted removable media, mounted remote storage, or an operator-controlled archive. Record matching timestamp basename, category presence, checksum result, latest copied-check UTC time, and cadence only. |
| Backup freshness monitoring | Partial tooling evidence; blocked for production monitoring. `scripts/check_backup_freshness.py` exists, is covered by local tests, and its help output was validated locally. No chosen production freshness window, scheduled checker runner, current production-host checker result, or off-server-root monitoring proof was available. | Choose the freshness window, run the checker against the local backup root and required off-server root from the production host or selected scheduler, and record timestamp basename, pass/fail, checksum result, latest check UTC time, runner category, and cadence. |
| Backup freshness alert delivery | Blocked. No backup freshness alert rule, route type, latest alert-rule evaluation, or delivery-test evidence was available. | Alert when no checksum-verified local backup plus off-server copy exists inside the chosen window, and cover missing backup, stale backup, malformed timestamp, missing artifact categories, checksum failure, missing off-server copy, and runner failure. Record only sanitized channel type, evaluation time, and delivered/not-delivered result. |
| Restore drill | Accepted limitation/deferred. The accepted limitation is the absence of a staging or intentionally empty restore target. | Keep the drill deferred until a safe target exists. When available, record target type, timestamp basename, checksum verification, restore command result, post-restore readiness, and cleanup/teardown status without private paths or raw restore logs. |

- Backup/off-server/freshness gate status: partial overall. Fresh manual backup/off-server copy is completed for the
  current first-traffic evidence set by the 2026-07-15 evidence, but recurring production backup scheduling, recurring
  off-server copy, scheduled freshness monitoring, freshness alert delivery, and restore-drill proof are still missing
  for broader launch or later operations.
- First traffic is no longer blocked by the fresh manual backup plus off-server copy prerequisite. The current operator
  register accepts recurring backup automation, recurring off-server copy, backup freshness monitoring, backup alert
  delivery, and restore-drill deferral as limitations only for the small operator-watched pilot.

Production import provenance evidence gap pass recorded on 2026-07-12:

Use [docs/import-provenance-evidence-packet-template.md](import-provenance-evidence-packet-template.md) to collect
sanitized production import provenance outside Git before copying final outcomes into this gate. The template is not
completed evidence and does not close source/archive, production import metadata, validation, or cache-linkage blockers
by itself.

- Scope/safety: documentation evidence plus local non-production helper validation. No deploy, refresh/import, cache
  warmup command, waitlist POST, Cloudflare/routing change, production endpoint probe, production host command,
  database query, source/archive collection, external monitor configuration, alert delivery test, first traffic, push, or
  tag was performed. This note intentionally avoids private source/archive paths, private hostnames, usernames, account
  IDs, tokens, raw headers, private URLs, raw logs, `.env` values, raw CSV contents, raw waitlist contacts, operator
  contact details, and PII.
- Operator-provided provenance evidence status: absent from the current repository and not provided during this pass. No
  sanitized production import packet, source snapshot basename, source/archive reference, retrieval timestamp, source
  checksum, source row count/range, expected tail date, production import command, direct validation/import table
  metadata, database row count, risk recomputation proof, or operator/source-owner decision was available.
- Existing supporting public consistency evidence: the 2026-07-12 monitoring/alert evidence gap pass recorded an
  approved local public GET-only probe for `GET /api/health`, `GET /api/readiness`, and `GET /api/risk/latest`; sanitized
  output was `latest_date=2026-07-11`, rounded risk `0.2190`, max data age 2 days, and required cache headers
  `Cache-Control`, `ETag`, `X-Cache-Version`, and `X-Cache` present. This public consistency evidence supports current
  public read behavior only. It is not direct source/archive proof and is not paired with a real production import
  packet.
- Existing supporting local repository data evidence: the bundled canonical CSV evidence through 2026-07-09 and local
  incoming CoinMarketCap CSV hash recorded in repository docs support local repository history only. They do not prove
  production host import execution, production database state, production source/archive provenance, or post-import
  validation metadata.
- Local helper validation: `python3 scripts/import_provenance_packet.py --help` completed successfully and showed the
  local-only `create` and `validate` commands; `python3 -m unittest backend.tests.test_import_provenance_packet` passed
  11 tests. This validates helper availability and safety behavior only. It did not create or validate a real production
  packet and does not prove a source archive exists.

| Import provenance area | 2026-07-12 sanitized status | Evidence / remaining proof |
| --- | --- | --- |
| Source/archive provenance | Blocked pending operator evidence. Source category remains unknown for the current production data from direct evidence; no public CoinMarketCap download, manual CSV, API fallback, restore, or correction packet was provided. | Capture the sanitized source type, source snapshot/archive basename or reference, retrieval method and timestamps, source `sha256`, byte size when available, row count, covered start/end, expected tail date, and operator/source-owner role from the real production import archive outside Git. |
| Production import metadata | Blocked pending production-host or operator evidence. No import command/path, scheduler run, production validation/import table row, validation source, validation covered end/latest timestamp, database row count, risk recomputation result, or collector command evidence was available. | Record the import mode and command category, production revision, validation source/source strategy, validation row count and covered end, latest risk date, risk recomputation status, and database/cache evidence from the same production import. |
| Public consistency evidence | Partial supporting evidence only. Historical and current public GET-only checks show healthy readiness/latest-risk behavior and product cache headers, including the 2026-07-12 probe above, but public responses do not identify the exact production source archive or prove the production import command. | Pair public readiness/latest/product-cache headers with the real source/archive packet and direct production validation/import metadata before marking provenance passed. |
| Local helper/tooling evidence | Passed for local helper availability only. `scripts/import_provenance_packet.py`, the packet template, and focused unittest coverage exist and the helper help/tests passed locally. | Run `create` and `validate` against the real production source snapshot, canonical output, and evidence-file basenames after an operator collects the outside-Git packet. Treat any local sample or repository CSV-only packet as non-production evidence. |
| Gate status | Partial, not passed. Meaningful supporting public/local evidence exists, and the operator now confirms the refresh/import workflow is operational for the small pilot, but sanitized final source/import proof is still missing. | First traffic remains blocked by this gate until the final snapshot records source category, retrieval/import timestamp, row count/range, readiness/latest-risk output, and checksum if available. No accepted limitation is intended for the refresh workflow. |

Launch Matrix, accessibility, and public-host QA evidence pass recorded on 2026-07-12:

- Scope/safety: evidence and documentation pass only. No deploy, refresh/import, cache warmup, waitlist POST, database
  write, Cloudflare/routing change, external monitor configuration, alert delivery test, first traffic, push, or tag was
  performed. Public checks were GET-only, browser checks did not submit forms, and the public browser/axe scripts
  intercepted `/api/waitlist` so an unexpected waitlist request would fail the check instead of reaching production.
  This note intentionally avoids private contacts, emails, account IDs, tokens, private URLs, raw headers, raw logs,
  `.env` values, raw waitlist contacts, raw analytics, and PII.
- Network and browser approvals: the sandboxed local Playwright smoke first failed on `listen EPERM: operation not
  permitted 127.0.0.1:4173`; the same mocked/local smoke was rerun with approved local browser/server permissions and
  passed. The sandboxed public endpoint probe first failed on `GET /api/health request failed`; the same GET-only probe
  was rerun with approved network access and passed. Public API field reads, public homepage smoke, public-host axe, and
  public metadata checks were also run with approved network/browser access.
- Local frontend verification: `npm test --prefix frontend` passed 2 files / 27 tests; `npm run build --prefix frontend`
  passed with `index` at 218.57 kB minified / 69.43 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip;
  `npm run smoke --prefix frontend` passed 25 Playwright checks after the approved rerun. The smoke suite uses mocked
  API routes, covers Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles, includes nonblank chart canvas checks,
  a focused axe scan, degraded/API-error states, and mocked waitlist keyboard/focus behavior.
- Public GET endpoint evidence: `scripts/check_public_endpoints.py` passed for `GET /api/health`, `GET /api/readiness`,
  and `GET /api/risk/latest` with max data age 2 days and required `Cache-Control`, `ETag`, `X-Cache-Version`, and
  `X-Cache` headers present on cacheable assertions. Sanitized API state from the approved GET-only checks:
  `/api/readiness` returned `status=ready`, `latest_date=2026-07-11`, `covered_end=2026-07-11`, `data_age_days=1`,
  `max_age_days=2`, `source=coinmarketcap_csv`, `row_count=5843`, `methodology_version=crypto-scout-canonical-v1`, and
  `data_fresh=true`; `/api/risk/latest` returned timestamp `2026-07-11T00:00:00+00:00`, risk
  `0.2190062736405601`, and `risk_state=low`. This is current public GET evidence only; it does not prove external
  monitor/provider configuration, scheduled monitor execution, stale-data alerting, collector-failure alerting, backup
  freshness alerting, Cloudflare Tunnel notification, or alert delivery.
- Public homepage smoke: approved Playwright Chromium checks passed for desktop `1440x1000` and mobile `390x844`.
  The homepage returned HTTP 200; the H1/product signal, current risk, latest date `2026-07-11`, and
  privacy/terms/disclaimer note were visible; EN/RU toggle behavior worked; no obvious horizontal overflow was observed
  (`overflow=0` for both profiles); both chart canvases were nonblank. Desktop chart canvases were `537x360`; mobile
  chart canvases were `324x360`. No console errors, page errors, failed same-origin app/API requests, or waitlist
  requests were observed in the passing smoke.
- Public-host accessibility automation: approved public-host axe scans passed with zero violations in desktop Chromium
  and mobile Chromium after the charts rendered. No waitlist requests were observed during these scans. This is automated
  public-host DOM evidence only; it is not a manual keyboard pass, screen-reader/assistive-tech pass,
  physical-device/native browser pass, full WCAG conformance audit, legal accessibility approval, or proof that
  canvas-drawn chart internals are directly accessible without the implemented non-canvas alternatives.
- Physical/native device evidence: no new physical device, native branded desktop browser, iOS Safari, Android Chrome, or
  manual device lab evidence was performed or provided in this 2026-07-12 pass. The later 2026-07-15 manual/native
  browser QA evidence completes the small-pilot manual keyboard/native desktop and mobile browser blocker without
  recording exact device models, screenshots, or private browser/profile details.
- Public metadata/privacy evidence: the live public homepage returned HTTP 200 with `title`, meta description, canonical
  URL, Open Graph `type`, `title`, `description`, `url`, and `site_name`, plus Twitter `card`, `title`, and
  `description`. `og:image` and `twitter:image` remain absent as expected because no real repo-served production image
  asset exists. The privacy/terms/disclaimer note was verified as visible by the public homepage smoke; this does not
  resolve waitlist owner, retention, deletion/unsubscribe, support/contact, legal approval, or full privacy/terms
  decisions.
- Cache/latency evidence: this pass verified public readiness/latest-risk behavior and latest-risk cache-header presence.
  It did not run a new cache-miss/edge-hit latency matrix for all public product read endpoints. Existing 2026-07-05 and
  2026-07-07 latency/cache evidence remains historical; unmeasured or stale endpoint-specific cache-miss/edge-hit latency
  evidence stays pending.
- Launch Matrix / Accessibility / Public-Host QA gate status: partial, not passed. Current public endpoint freshness,
  public homepage desktop/mobile Chromium smoke, public metadata/privacy smoke, local browser-profile smoke, local axe,
  local mocked keyboard/focus, public-host axe evidence, the later 2026-07-15 manual/native browser QA evidence, and the
  later 2026-07-15 assistive-tech proxy QA evidence are recorded. After the later 2026-07-14 monitoring acceptance,
  2026-07-15 backup/readiness evidence, 2026-07-15 manual/native QA evidence, and 2026-07-15 assistive-tech proxy QA
  evidence, first traffic remains blocked by direct production import proof if still required beyond public checks and
  operator confirmation, fresh launch-window readiness/latest-risk checks, final launch snapshot, and separate operator
  approval/run for first traffic. Dedicated external API monitoring, alert delivery, and a true screen-reader/manual
  assistive-tech pass remain pending before broader launch or broader accessibility claims.

## Operator Launch Decision Register

### 2026-07-12 Operator Decision Resolution Pass

Recorded on 2026-07-12 from explicit sanitized operator decisions provided for first-traffic readiness. No private
contact value, raw waitlist export, raw database output, query detail, support address, account holder, account ID,
dashboard URL, token, `.env` value, private server path, private source record, raw message text, or secret was written.
This pass did not deploy, push, tag, refresh/import data, call `POST /api/waitlist`, change Cloudflare/routing, configure
monitoring, send alerts, run backups, run first traffic, or mutate production state. At the start of this pass, local
`HEAD` and `origin/main` were `08ff527`, the local tag at `HEAD` was
`first-traffic-blocked-evidence-2026-07-12`, and the local branch was `main...origin/main`.

Gate status: partial, not passed. Operator decisions are substantially recorded, the support/contact and account recovery
blockers are completed by the later 2026-07-12 sanitized readiness evidence, small-pilot monitoring is accepted by the
later 2026-07-14 monitoring acceptance, and the fresh backup/off-server copy blocker is completed by the later
2026-07-15 evidence. Dedicated external health/readiness monitors and alert delivery proof remain broader-launch
limitations, not small-pilot first-traffic blockers. The later 2026-07-15 manual/native browser QA evidence completes
the small-pilot manual keyboard/native desktop and mobile browser blocker, and the later 2026-07-15 assistive-tech proxy
QA pass records the missing dedicated screen-reader/manual assistive-tech pass as an accepted small-pilot limitation.
Sanitized import proof if still required beyond public checks and operator confirmation, fresh launch-window
readiness/latest-risk checks, final launch snapshot, and first traffic remain pending. First traffic remains blocked and
`not_run`.

| Decision area | Sanitized status | Recorded decision and remaining action |
| --- | --- | --- |
| Waitlist handling | Resolved for sanitized governance; support path ready. | Owner role is founder/operator. Review cadence is several times per week during pilot. Review method is a manual operator-run database query or script. Pilot contacts are retained until beta ends and deleted earlier on operator-approved request. Deletion/unsubscribe requests use the dedicated support contact path kept outside Git. Follow-up is manual founder/operator follow-up only; no automated newsletter is planned. Do not commit raw contacts, raw output, private paths, or query details. |
| Support/contact | Completed for first-traffic readiness. | Support email status is created and ready. The support/contact path category is a dedicated support mailbox with a project-domain alias; exact addresses and provider details are kept outside Git. The support path was checked by the founder/operator. Deletion/unsubscribe requests use manual requests through the dedicated support contact path. No paid support SLA or public address value is recorded here. |
| Account and credential ownership/recovery | Completed for first-traffic readiness. | GitHub owner role, Cloudflare/domain owner role, server owner role, secrets/.env owner role, and backups owner role are founder/operator. The account recovery record is created outside Git and current. |
| CoinMarketCap/source terms | Accepted pilot limitation; commercial/broader launch blocked pending terms/plan decision. | Current product status is unpaid/non-commercial pilot. If demonstrated interest or paid/commercial use appears, the operator will buy the appropriate plan or make the required terms/plan decision. Source terms owner role is founder/operator. Terms review or paid plan is required before commercial claims, paid beta, or broader distribution. This is acceptable only for a small operator-watched pilot; do not claim legal approval or commercial readiness. |
| Dependency/security | Partial. | Dependency/security owner role is founder/operator. Security review cadence is monthly during pilot. Dependency/license external confirmation remains pending before broader commercial launch. GitHub-hosted Dependabot execution and first PR evidence remain pending until observed. |
| Cloudflare Free-plan posture | Accepted limitation for small operator-watched pilot only. | The current Free-plan-compatible subset is accepted for a small operator-watched pilot. Managed WAF and additional rate-limit controls are deferred until broader traffic or observed abuse risk. Do not claim broader Cloudflare security readiness. |
| Accessibility/manual-device | Completed for small-pilot manual/native plus proxy scope; broader accessibility claims pending. | Manual keyboard/native desktop and mobile browser checks are completed for the small pilot by the 2026-07-15 manual/native browser QA evidence. The 2026-07-15 local assistive-tech proxy QA passed, but no dedicated VoiceOver, NVDA, TalkBack, or manual assistive-tech pass was performed. The missing dedicated pass is accepted only as a small-pilot limitation. Do not claim a dedicated screen-reader pass or full WCAG/legal accessibility compliance. |
| Monitoring and incident response | Accepted/closed for the small operator-watched pilot with limitation after the later 2026-07-14 monitoring acceptance; broader launch pending. | Pilot resource watcher role and incident/rollback decision owner role are founder/operator. Response path is to pause traffic, check readiness/logs, follow the operations runbook, and rollback/update only if needed. Cloudflare Tunnel Health Alert plus public homepage availability monitoring are accepted as sufficient for the small pilot. Dedicated external `/api/health` monitoring, dedicated external `/api/readiness` freshness monitoring, and explicit alert delivery proof remain pending before broader launch. |
| Backups | Fresh manual backup/off-server copy completed; automation and restore drill remain limited. | The 2026-07-15 evidence records a copied backup timestamp basename `20260715T082457Z` with PostgreSQL dump, BTC CSV, manifest, and checksum categories present and copied-backup SHA-256 verification passed. Recurring backup automation and backup freshness alerting are deferred until after the initial operator-watched pilot. Restore-drill deferral remains accepted until a safe staging or intentionally empty restore target exists. |
| Production import/data freshness | Partial/blocker for final evidence. | The founder/operator considers the production data refresh path complete and operational for the small operator-watched pilot. No accepted limitation is intended for the refresh workflow. Sanitized proof still needs recording before or during the final launch snapshot, including latest source category, retrieval/import timestamp, row count/range, readiness/latest-risk output, and checksum if available. |
| Final readiness and launch snapshot | Blocked. | Run fresh public GET-only `/api/readiness` and `/api/risk/latest` checks immediately before first traffic. Create a sanitized launch snapshot packet after all remaining blockers are resolved and before traffic starts. |
| First-user feedback | Partial/resolved for planned path; evidence pending traffic. | Feedback channel category is waitlist notes and direct support-email replies, with no raw contacts in Git. Reviewer role is founder/operator. Review cadence is after the first traffic window and several times per week during pilot. Evidence summary format is aggregate/sanitized only, with no raw contacts or message text in Git. |

Accepted limitations after this pass, as updated by the later 2026-07-14 monitoring acceptance:

- Restore-drill deferral until a safe staging or intentionally empty restore target exists.
- Cloudflare Free-plan-compatible subset for a small operator-watched pilot only.
- Recurring backup automation and backup freshness alerting deferred until after the initial pilot; the fresh manual
  backup plus off-server copy prerequisite passed in the 2026-07-15 evidence.
- CoinMarketCap/source-terms commercial or paid-plan decision deferred only for commercial claims, paid beta, or broader
  distribution; this is not legal approval or commercial readiness.
- Small-pilot monitoring coverage limited to Cloudflare Tunnel Health Alert plus public homepage availability monitoring;
  dedicated external API monitors and explicit alert delivery proof remain pending before broader launch.
- Dedicated screen-reader/manual assistive-tech pass deferred only for the small operator-watched pilot after the
  2026-07-15 assistive-tech proxy QA pass; do not claim a true screen-reader pass, full WCAG conformance, or legal
  accessibility approval.

Actions still pending before first traffic:

- Record sanitized import/data-refresh proof in the final snapshot unless it is already derivable from public checks or
  recorded in Git.
- Use the 2026-07-15 public readiness/latest-risk evidence in the final snapshot, or rerun fresh public checks if the
  traffic window is delayed.
- Create the final sanitized launch snapshot packet.
- Obtain separate operator approval for the first traffic run after the final snapshot is ready.

Dedicated external `/api/health` and `/api/readiness` monitors plus explicit alert delivery proof remain pending before
broader launch, not before the small operator-watched pilot first-traffic decision.

First traffic remains blocked. This pass supersedes pending-status language in the 2026-07-11 operator governance pass
only where a 2026-07-12 sanitized decision is explicitly recorded above.

### 2026-07-11 Operator Governance Pass

Recorded on 2026-07-11 from repository-visible evidence and the current operator prompt. No private operator contact
list, account export, recovery path, source-terms text, dashboard URL, token, `.env` value, raw log, or raw waitlist
contact was available or written. This register does not prove deployment, data refresh/import, cache warmup, waitlist
submission, Cloudflare/routing change, monitor configuration, first traffic, commit, push, or tag.

Use [docs/operator-launch-decision-packet-template.md](operator-launch-decision-packet-template.md) to collect sanitized
operator answers before updating this register. The template is not completed evidence and does not close any pending
decision by itself.

| Decision area | Sanitized status | Exact remaining operator decision |
| --- | --- | --- |
| Waitlist handling: owner, review cadence, retention, deletion/unsubscribe, and post-waitlist follow-up | Superseded/resolved by later 2026-07-12 evidence. The public note describes current server-side storage and operational log behavior. Later sanitized evidence records the founder/operator owner role, review cadence, retention policy, manual deletion/unsubscribe path through the dedicated support contact path, and manual founder/operator follow-up only. | Keep private contact details and raw waitlist contacts out of Git. |
| Support/contact identity | Superseded/completed by later 2026-07-12 evidence. The public note states no paid support SLA, and the later sanitized readiness evidence records a dedicated support mailbox with project-domain alias as created and ready. | Keep actual private addresses, handles, names, recipient lists, routing details, inbox URLs, account IDs, credential values, and support messages out of Git unless the operator intentionally publishes a public contact value. |
| Credential/account ownership and recovery | Superseded/completed by later 2026-07-12 evidence. Required ownership categories are documented, owner roles are founder/operator, and the later sanitized readiness evidence records the outside-Git account recovery record as created and current. | Keep holders, personal contacts, account IDs, dashboard URLs, recovery paths, credential locations, credential values, and account details out of Git. |
| Data-source terms and import governance | Pending operator decision/evidence. No completed CoinMarketCap public-download/manual CSV terms review, optional CoinMarketCap API usage review, attribution outcome, or accepted limitation is recorded. Production import provenance remains separate and still requires a real source/archive packet after production imports. No owner role for future source review is recorded. | Record a sanitized status for CoinMarketCap public CSV and optional API usage as passed, accepted limitation, or pending; record any attribution or usage limitation; choose the owner role for future source review; and keep private source terms, account details, raw CSV rows, and private archive paths out of Git. |
| Dependency, security, and license posture | Partial local evidence. `.github/dependabot.yml` is configured locally for conservative monthly version-update checks across frontend npm, backend and collector pip requirements, GitHub Actions, Dockerfiles, and a root `docker-compose` ecosystem entry. The dependency/license review records local npm lockfile license metadata and known gaps. GitHub-hosted Dependabot execution, first PR evidence, vulnerability/advisory clearance, external/manual license confirmation, container/OS package license review, project license choice, and legal approval remain pending. A monthly manual review cadence is documented, but the owner role for security updates is not recorded. | Choose the owner role for dependency/security updates, keep or revise the monthly cadence, record GitHub-hosted Dependabot execution and first PR evidence when available, complete or explicitly defer vulnerability/advisory, credential-scan, license, container image, OS package, CI action, and legal compatibility review, and record only date/scope/outcome/follow-up. |
| Cloudflare Free-plan first-traffic decision | Pending first-traffic decision. Historical public snapshots used the documented Free-plan-compatible subset, but no operator decision accepts that subset for first traffic or requires an upgrade. Managed WAF execution, broader `/api/*` burst limiting, multiple rate-limit rules, and longer rate-limit windows are not proven active in the current subset. | Accept the current Free-plan subset for one operator-watched first traffic window, or require an upgrade/equivalent controls before first traffic. Record the accepted limitation or blocker without Cloudflare account IDs, zone IDs, tunnel IDs, rule IDs, dashboard URLs, credential values, private event logs, or routing details. |
| Accessibility and device evidence | Superseded by later evidence; small-pilot manual/native plus proxy scope completed with limitation. Local automated axe, browser-profile, chart-alternative, live-region, and keyboard/focus evidence exists. Public-host desktop/mobile Chromium smoke and public-host automated axe evidence are recorded through 2026-07-12. The later 2026-07-15 manual/native browser QA evidence completes the small-pilot manual keyboard/native desktop and mobile browser blocker, and the later 2026-07-15 assistive-tech proxy QA pass accepts the missing dedicated screen-reader/manual assistive-tech pass only as a small-pilot limitation. | Record true assistive-tech and broader accessibility evidence before broader launch or broader accessibility claims. Record only sanitized status and follow-up owner role; do not claim full WCAG/legal accessibility compliance. |
| Resource monitoring and incident response | Superseded by the later 2026-07-12 operator decision pass and 2026-07-14 monitoring acceptance. The operations runbook documents local/public readiness checks, logs to inspect, backup checks, Cloudflare Tunnel checks, disk/database pressure checks, cache-stale handling, bad-data correction steps, pause/take-down conditions, and rollback-style recovery through known-good CSV/import/backup paths. | Current small-pilot coverage accepts Cloudflare Tunnel Health Alert plus public homepage availability monitoring. Dedicated external API monitor proof and alert delivery proof remain pending before broader launch; record only sanitized evidence when those broader-launch items are completed. |
| Release feedback and first-user feedback | Partial/pending. The runbook says that after the first controlled traffic window, operators should summarize waitlist conversion, repeat-use signals, direct questions, and requests for alerts, API access, agents, widgets, embeddings, or licensing into readiness or roadmap notes without raw contacts. First traffic has not run, no reviewer role is recorded, and no post-traffic evidence exists. | Choose the first-user feedback collection paths, reviewer role, review cadence, and sanitized evidence format. After first traffic, record aggregate waitlist/source/locale/repeat-use/request evidence and direct-question themes without raw contacts, private messages, raw analytics, or personal details. |
| Accepted launch limitations and hard blockers | Superseded by the 2026-07-12 operator decision pass, later 2026-07-14 monitoring acceptance, later 2026-07-15 backup/readiness evidence, and later 2026-07-15 assistive-tech proxy QA evidence. At the time of this 2026-07-11 pass, only restore drill was explicitly accepted/deferred until a staging project or intentionally empty restore target existed. | Use the current accepted-limitations list: restore-drill deferral, Cloudflare Free-plan subset for a small operator-watched pilot, recurring backup automation/freshness alert deferral after the 2026-07-15 fresh manual backup/off-server copy pass, CoinMarketCap commercial/source-terms decision deferred only for commercial/broader launch, small-pilot monitoring coverage limited to Tunnel Health plus homepage availability while dedicated API monitor and alert delivery proof remain pending before broader launch, and dedicated screen-reader/manual assistive-tech pass deferred only for the small watched pilot after the 2026-07-15 proxy QA pass. Do not mark the project publicly launched until all required blockers are closed, the final launch snapshot exists, and first traffic evidence exists. |

Launch governance in this 2026-07-11 pass was recorded only as a partial governance pass. It is superseded by the
2026-07-12 operator decision resolution pass where that later pass records sanitized decisions or accepted limitations.
First traffic must still not run until the remaining blockers are completed, the final launch snapshot exists, and the
project is separately approved for first traffic.

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

This 2026-07-01 snapshot confirmed the public hostname, readiness path, and public-read cache behavior. At the time it
was recorded, it did not replace the then-remaining launch checks: waitlist production smoke, browser/device QA on the
public hostname, backup/restore setup, alerts, and the first traffic test.

Additional public smoke evidence recorded on 2026-07-02 for `https://bitcoinriskbrief.minihub.app`:

- `GET /api/health` returned 200 with `{"status":"ok"}`.
- `GET /api/readiness` returned 200 with `status: ready`, `source: coinmarketcap_csv`, `latest_date: 2026-06-30`,
  `covered_end: 2026-06-30`, `data_age_days: 2`, `max_age_days: 2`, and `row_count: 5832`.
- `GET /api/risk/latest` returned 200 for timestamp `2026-06-30T00:00:00+00:00` with `Cache-Control: public,
  max-age=60, stale-while-revalidate=300`, `ETag: "a860789d405dbf015592328b"`, `X-Cache: MISS`, and
  `X-Cache-Version: validation:2026-07-02T01:00:05.718106+00:00:2026-06-30T00:00:00+00:00:5832:true`.
- The Cloudflare Free-plan first-traffic decision was pending at the time of this historical snapshot. The 2026-07-12
  operator decision resolution pass later accepted the Free-plan-compatible subset for a small operator-watched pilot
  only, while managed WAF/additional rate limits remain deferred until broader traffic or observed abuse risk.

Deployment path decision status recorded on 2026-07-02:

- Selected deployment path: USB-based local-server deployment under `/srv/projects/bitcoin-risk-brief`, confirmed by
  the operator on 2026-07-02. The direct Git workflow under `/opt/bitcoin-risk-brief` is not the active production
  update path for the next update.
- Production project directory: `/srv/projects/bitcoin-risk-brief`.
- At the time of this 2026-07-02 decision, USB Update And Install Kit V2 was implemented locally but production benefit
  still required a real USB package and a production-host run. The 2026-07-07 post-deploy evidence below supersedes this
  pending status for the operator-run USB deploy path.
- Production `.env` location: `/srv/projects/bitcoin-risk-brief/.env`; filesystem owner still needs production-host
  confirmation.
- Production `COINMARKETCAP_API_KEY`: empty. Data refresh should use the scheduled public-download-first collector path;
  `download-cmc-csv` and manual downloaded CSV intake remain operator fallbacks. The 2026-07-07 post-deploy snapshot
  proves current public freshness, not future scheduled runs.

Local implementation reconciliation recorded on 2026-07-06:

- Local repository tags exist for `cache-warmup-local-complete-2026-07-05`,
  `usb-kit-v2-local-complete-2026-07-05`, and `price-model-ohlc-local-complete-2026-07-06`. These tags are local
  implementation evidence only; the production-host result is recorded separately in the 2026-07-07 post-deploy evidence
  below.
- Public cache warmup is implemented locally through backend startup warmup and
  `PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache`. Production benefit for the public
  smoke path is now supported by the 2026-07-07 post-deploy cache evidence after USB deploy and healthy readiness.
- First-viewport model-price/OHLC polish is implemented locally: the latest risk payload/display can expose explicit
  `model_price_usd`, nullable `low_usd`, and nullable `high_usd` for the latest completed daily candle. Production
  visibility is now verified in the 2026-07-07 public smoke evidence.
- USB Update And Install Kit V2 is implemented locally, and the production-host USB deploy verification passed according
  to the 2026-07-07 operator evidence.
- The prior public data freshness blocker is closed by the 2026-07-07 public `/api/readiness` HTTP 200 evidence. Broader
  public launch remains limited by the operator-owned launch gates that are still listed below unless they are explicitly
  completed or accepted.

Post-deploy production verification evidence recorded on 2026-07-07 for `https://bitcoinriskbrief.minihub.app`:

- Repository state before recording this note: `git status --short --branch` returned `## main...origin/main`.
- USB deploy verification passed after the operator-run production deployment under
  `/srv/projects/bitcoin-risk-brief`.
- Freshness blocker status: closed. `GET /api/readiness` returned HTTP 200 with `data_fresh: true`,
  `latest_date: 2026-07-06`, `covered_end: 2026-07-06`, and `data_age_days: 1`. The latest public data date is
  `2026-07-06`.
- Latest risk payload: `GET /api/risk/latest` returned HTTP 200 for timestamp `2026-07-06T00:00:00+00:00` with
  `risk_state: low`, `price_usd: 63289.47099956666`, `model_price_usd: 63289.47099956666`,
  `low_usd: 61275.826328`, and `high_usd: 64597.5707661`.
- Public frontend smoke passed with Playwright against `https://bitcoinriskbrief.minihub.app/`. Desktop and mobile
  verified the first viewport showing Current risk `28%`, `Low`, latest date `2026-07-06`, Model price `$63,289`,
  Low `$61,276`, and High `$64,598`.
- Mobile overflow check passed: viewport width `390`, scroll width `390`.
- Repeated public cache requests after warmup were fast, about `0.14s` to `0.22s`, with Cloudflare `cf-cache-status:
  HIT` and `age` around `33` to `35`.
- Cache-header nuance: the app-level `X-Cache` header may still show `MISS` on a cached origin response served through
  Cloudflare. Treat Cloudflare `HIT` plus fast repeat timings as the public latency evidence here; do not treat the
  cached origin `X-Cache: MISS` value as a latency blocker by itself.
- This note intentionally records only redacted operational evidence. It does not include secrets, raw waitlist contacts,
  private account details, or private paths beyond the already documented production project path.

Backup, off-server copy, and restore drill status recorded on 2026-07-07:

- USB backup found: yes, on mounted USB backup storage for timestamp basename `20260707T111928Z`. The backup copy was
  mounted outside the current USB kit directory, whose own `manifest.txt` and `SHA256SUMS` were present.
- Production commit HEAD: direct live checkout proof was not available from this workstation session because
  `/srv/projects/bitcoin-risk-brief` is absent here. The deploy-source evidence available for this pass is local
  `git rev-parse HEAD` and USB kit `manifest.txt`, both recording commit
  `285cbf5547a5a3b106a09085e0d2506175db00f6`.
- USB kit checksum verification passed with `sha256sum --quiet -c SHA256SUMS` from the mounted USB kit directory.
- Latest backup timestamp basename: `20260707T111928Z`.
- Artifact categories verified non-empty: PostgreSQL custom-format dump, canonical BTC CSV copy, backup manifest, and
  backup `SHA256SUMS`.
- Backup checksum verification passed with `sha256sum -c SHA256SUMS` from the mounted USB backup copy directory for the
  PostgreSQL dump, BTC CSV, and backup manifest.
- Off-server copy status: verified on USB for timestamp basename `20260707T111928Z`; backup and off-server copy evidence
  are no longer missing for this gate.
- Local production backup counterpart: not checked here. `/srv/projects/bitcoin-risk-brief/backups/20260707T111928Z`
  could not be inspected because `/srv` is absent in this session; this does not block the off-server copy status because
  the mounted USB copy passed checksum verification.
- Restore drill status: blocked pending an explicit staging project or intentionally empty restore target. No such target
  was found in the checked local, temp, `/opt`, or USB paths, and no restore was attempted against live production.
- This note intentionally records only redacted operational evidence. It does not include secrets, raw dump contents, raw
  CSV contents, waitlist contacts, credentials, `.env` values, or private account details.
- For future backup and restore evidence, use the production-host procedure below.

```bash
set -euo pipefail
cd /srv/projects/bitcoin-risk-brief
git status --short --branch
BACKUP_LOG="/tmp/bitcoin-risk-backup-$(date -u +%Y%m%dT%H%M%SZ).log"
./scripts/backup.sh | tee "${BACKUP_LOG}"
BACKUP_PATH="$(awk '/^Backup complete:/ {print $3}' "${BACKUP_LOG}" | tail -n 1)"
test -n "${BACKUP_PATH}"
test -s "${BACKUP_PATH}"/postgres_*.dump
test -s "${BACKUP_PATH}"/btc_usd_daily_*.csv
test -s "${BACKUP_PATH}/manifest.txt"
test -s "${BACKUP_PATH}/SHA256SUMS"
(cd "${BACKUP_PATH}" && sha256sum -c SHA256SUMS)
```

- Copy the verified backup to the confirmed off-server storage. Set `OFFSERVER_BACKUP_ROOT` to the mounted off-server
  backup directory before running:

```bash
set -euo pipefail
BACKUP_PATH="<backup-directory-from-production-backup-step>"
OFFSERVER_BACKUP_ROOT="<mounted-off-server-backup-directory>"
case "${OFFSERVER_BACKUP_ROOT}" in
  ""|/srv/projects/bitcoin-risk-brief|/srv/projects/bitcoin-risk-brief/*)
    echo "OFFSERVER_BACKUP_ROOT must be outside the production project directory" >&2
    exit 2
    ;;
esac
install -d -m 700 "${OFFSERVER_BACKUP_ROOT}"
cp -a "${BACKUP_PATH}" "${OFFSERVER_BACKUP_ROOT}/"
OFFSERVER_BACKUP_PATH="${OFFSERVER_BACKUP_ROOT%/}/$(basename "${BACKUP_PATH}")"
test -s "${OFFSERVER_BACKUP_PATH}/SHA256SUMS"
(cd "${OFFSERVER_BACKUP_PATH}" && sha256sum -c SHA256SUMS)
```

- On a staging project checkout or intentionally empty restore target, run the restore drill with the copied backup:

```bash
set -euo pipefail
STAGING_PROJECT_DIR="<staging-or-empty-project-directory>"
RESTORE_BACKUP_PATH="<copied-backup-directory-on-staging>"
cd "${STAGING_PROJECT_DIR}"
test -s "${RESTORE_BACKUP_PATH}/SHA256SUMS"
(cd "${RESTORE_BACKUP_PATH}" && sha256sum -c SHA256SUMS)
./scripts/manage.sh start
podman-compose -f podman-compose.yml exec -T timescaledb pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  -U postgres \
  -d bitcoin_risk_brief < "${RESTORE_BACKUP_PATH}"/postgres_*.dump
cp "${RESTORE_BACKUP_PATH}"/btc_usd_daily_*.csv collector/btc-csv/btc_usd_daily.csv
./scripts/manage.sh run-now
curl -fsS http://127.0.0.1:3001/api/readiness
```

- Record only redacted evidence: command date, production commit, backup artifact categories, checksum verification
  result, off-server copy confirmation, restore target type, and readiness result. Do not record `.env` values,
  secrets, waitlist contacts, raw dump or CSV contents, or private off-server paths.

Monitoring and alerts evidence pass recorded on 2026-07-10 at 06:13 UTC for
`https://bitcoinriskbrief.minihub.app`:

- Scope/safety: docs and evidence pass only. No deploy, refresh/import, cache warmup, commit, push, or tag was performed.
  This note intentionally records only redacted operational metadata and does not include tokens, account IDs, private
  dashboard URLs, recipient contacts, phone numbers, IPs, raw logs with PII, `.env` values, credentials, or waitlist
  contacts.
- Local repository state before the docs edit: `git status --short --branch` returned `## main...origin/main`.
- Public endpoint checks: the first sandboxed DNS attempt failed, then the required public curl checks were rerun with
  network access. `GET /api/health` returned HTTP 200 with `status: ok` and `cf-cache-status: DYNAMIC`.
- Public readiness: `GET /api/readiness` returned HTTP 200 with `status: ready`, `data_fresh: true`,
  `latest_date: 2026-07-09`, `covered_end: 2026-07-09`, `data_age_days: 1`, `max_age_days: 2`,
  `source: coinmarketcap_csv`, `row_count: 5841`, and methodology `crypto-scout-canonical-v1`. Relevant public cache
  headers were `Cache-Control: public, max-age=60, stale-while-revalidate=300`, `ETag: "2982cd45d5bc626fecfb86c4"`,
  `X-Cache: MISS`, `X-Cache-Version` marker
  `validation:2026-07-10T01:00:06.300719+00:00:2026-07-09T00:00:00+00:00:5841:true`, and
  `cf-cache-status: EXPIRED`. This readiness cache-header observation is historical and predates the live-readiness
  no-store policy; current `/api/readiness` must return `Cache-Control: no-store`, and cache-header assertions apply to
  cacheable product endpoints only.
- Latest risk: `GET /api/risk/latest` returned HTTP 200 for timestamp `2026-07-09T00:00:00+00:00` with
  `risk_state: low`, risk approximately `0.2494`, `model_price_usd: 62753.94724853333`,
  `low_usd: 61645.7524817`, and `high_usd: 63422.9415885`. The latest risk date matches readiness `covered_end`.
  Relevant public cache headers were `Cache-Control: public, max-age=60, stale-while-revalidate=300`,
  `ETag: "970d143369867a8e06f4af55"`, `X-Cache: MISS`, the same `X-Cache-Version` as readiness, and
  `cf-cache-status: EXPIRED`.
- Monitor/provider evidence status from this historical 2026-07-10 pass: blocked at that time. This workstation session
  had no external monitoring provider dashboard/API, Cloudflare dashboard/API, alert-delivery dashboard, production host
  at `/srv/projects/bitcoin-risk-brief`, service logs, or current backup/off-server filesystem evidence available. The
  later 2026-07-14 acceptance supersedes this only for small-pilot monitoring coverage: Cloudflare Tunnel Health Alert
  plus public homepage availability monitoring are accepted, while dedicated external API readiness/freshness monitoring
  and alert delivery remain pending before broader launch.

| Evidence area | 2026-07-10 status | Exact remaining operator action |
| --- | --- | --- |
| Local public endpoint probe tooling | Implemented locally after the 2026-07-10 evidence pass. `scripts/check_public_endpoints.py` can validate public `GET /api/health`, `GET /api/readiness`, and `GET /api/risk/latest` with an explicit `--max-data-age-days` or `--expected-latest-date` freshness policy, readiness `no-store`, and optional cache-header assertions for cacheable product responses. Focused unit tests cover success, endpoint failures, stale readiness, missing readiness fields, malformed JSON/latest risk, date mismatch, readiness no-store, cache-header requirements, handled network failure, and GET-only behavior. | Put the probe under cron, a synthetic monitor runner, or an external monitoring provider using a chosen freshness policy; record only sanitized latest status, assertion summary, interval/window, and delivery route. This does not replace provider/dashboard proof or alert-delivery evidence. |
| External uptime monitor for `/api/health` | Broader-launch pending after the 2026-07-14 small-pilot acceptance. Public `/api/health` was HTTP 200 in this historical pass, but no dedicated external uptime monitor dashboard/API proof was available. | Configure or show an external HTTP monitor for `https://bitcoinriskbrief.minihub.app/api/health`; alert on non-200, timeout, or TLS failure; record provider/dashboard name, sanitized check name, interval, latest check status, and delivery route without account details before broader traffic. |
| External readiness/freshness monitor for `/api/readiness` | Broader-launch pending after the 2026-07-14 small-pilot acceptance. Public `/api/readiness` was HTTP 200 and fresh in this historical pass, but no monitor assertion or alert evidence was available. | Configure or show an external HTTP monitor for `https://bitcoinriskbrief.minihub.app/api/readiness`; alert when HTTP is non-200, `status` is not `ready`, or `checks.data_fresh` is not `true`; record sanitized assertion and latest check evidence before broader traffic. |
| Stale-data alert | Broader-launch pending. Current public readiness was fresh in this historical pass, but no stale-data alert rule or delivery proof was available. | After the nightly collector window plus the operator-defined grace period, alert when readiness is HTTP 503, `data_age_days` exceeds `max_age_days`, or `latest_date`/`covered_end` is older than the last completed UTC day. |
| Collector failure alert | Deferred broader-launch limitation. No collector container status, scheduled run proof, restart alert, or log-alert dashboard was available from this workstation. | Configure production alerts for `scheduled_refresh_failed`, `public_cmc_download_failed`, API fallback failure, missed scheduled refresh evidence, and repeated `data-collector` restarts; record the alert source and latest passing scheduled run without raw log dumps. |
| Backup freshness/off-server copy monitor | Deferred recurring-operations limitation; local checker tooling is implemented and tested, but only historical backup-copy evidence remains. The 2026-07-07 checksum-verified USB off-server backup copy is still the last recorded backup-copy evidence for this historical pass, but no current production freshness-window check, recurring backup schedule, or backup alert evidence was available here. | Choose the freshness window, schedule backups and off-server copies, run `scripts/check_backup_freshness.py` against the local backup root and required off-server root, alert when no checksum-verified backup plus off-server copy exists inside the chosen window, and record only sanitized timestamp basenames/status from the production host. |
| Cloudflare Tunnel connector health notification | Accepted/closed for the small operator-watched pilot by the 2026-07-14 monitoring acceptance. | Cloudflare Tunnel Health Alert is configured. Keep private dashboard URLs, account IDs, tunnel IDs, routing details, alert recipients, screenshots, and tokens out of Git. |
| Alert delivery channel | Deferred broader-launch limitation. No email, chat, pager, or other delivery-channel configuration/test proof was available. | Choose the alert channel before broader traffic, send a test notification from the monitoring provider, and record channel type, test time, and delivered/not-delivered result without recipient addresses, handles, phone numbers, tokens, or private contacts. |

- Monitoring/alerts gate status: accepted/closed for the small operator-watched pilot with limitation after the
  2026-07-14 monitoring acceptance. Local public endpoint probe tooling is implemented and tested, and previous public
  health, readiness, and latest-risk endpoint evidence was healthy/current. Dedicated API monitor provider/dashboard
  evidence and alert delivery evidence remain pending before broader traffic.
- Local public endpoint probe status: implemented and covered by focused unit tests in this repository. This is local
  tooling only; no external monitor provider, dashboard/API proof, alert rule, delivery channel, or current production
  probe run evidence is recorded here.
- Local backup freshness checker status: implemented and covered by focused unit tests in this repository. This is local
  tooling only. The 2026-07-15 evidence records the current fresh manual backup/off-server copy pass, but production
  backup scheduling, recurring off-server copies, external monitor execution, and alert delivery remain pending. No
  restore drill has been completed.
- Local launch snapshot packet status: implemented and covered by focused unit tests in this repository. The helper
  `scripts/launch_snapshot_packet.py` creates or validates a sanitized JSON packet template for the final pre-traffic
  evidence window, stores evidence basenames instead of full paths, keeps missing categories as pending gates, and keeps
  `first_traffic_status` at `not_run` unless explicit first-traffic evidence fields are deliberately supplied. This is
  local tooling only; the actual final launch snapshot packet, sanitized import proof if still required beyond public
  checks and operator confirmation, fresh launch-window readiness/latest-risk checks, operator approval, and first traffic
  remain pending. Dedicated API monitor/alert delivery proof and a true screen-reader/manual assistive-tech pass remain
  broader-launch limitations.

Bundled canonical CSV repository evidence recorded on 2026-07-11:

- Scope/safety: documentation-only evidence note. This pass records existing local repository and tag state. It did not
  edit code or CSV data, deploy, refresh/import data, warm cache, run a real waitlist POST, change Cloudflare/routing, or
  create a new commit, push, or tag.
- Local repository state before the docs edit: `git status --short --branch` returned `## main...origin/main`;
  `git rev-parse HEAD` returned `8cbc6998c757f1ca1716277104e099b4705dfba9`; local tag
  `btc-csv-through-2026-07-09-evidence-2026-07-11` was present.
- Bundled data evidence: commit `8cbc6998c757f1ca1716277104e099b4705dfba9`
  (`data: update bundled BTC CSV through 2026-07-09`) added 11 rows to the repository's bundled canonical CSV,
  `collector/btc-csv/btc_usd_daily.csv`, covering 2026-06-29 through 2026-07-09. The bundled canonical CSV therefore
  includes rows through 2026-07-09 in this repository state.
- Local source review: the incoming source reviewed for that commit was
  `collector/btc-csv/incoming/coinmarketcap-public-btc-20260629-20260709.csv`, with SHA-256
  `38e9b0e8717013f217b93e7501aa3e216b1f989b52899cacff9e14c13f309d07`. Raw source rows and raw logs are intentionally
  not copied into this document. The reviewed `timeHigh`/`timeLow` mismatch is not treated as a blocker for the
  canonical CSV path because those fields are not consumed as authoritative canonical fields.
- Evidence boundary: this is local repository data evidence only. It does not prove production deployment, production
  database import, public-host freshness after this commit, direct production source/archive provenance,
  validation/import table metadata from the production database, launch readiness, or first traffic.
- Pending production evidence: direct production import source/archive provenance remains pending until an
  operator-controlled evidence packet exists outside the repository. Production refresh/import verification also remains
  pending until deployment or operator evidence proves the production host imported this repository state or an
  equivalent production source.

Launch governance gap pass recorded on 2026-07-10:

- Scope/safety: docs and evidence pass only. No deploy, refresh/import, cache warmup, waitlist POST, Cloudflare/routing
  change, runtime test, commit, push, or tag was performed. This note records only repository-visible and previously
  redacted operational evidence; it does not include private contact details, account details, dashboard URLs, tokens,
  `.env` values, raw logs, raw waitlist contacts, or PII.
- Local repository state before this docs edit: `git status --short --branch` returned `## main...origin/main`, and
  `git log --oneline --decorate -5` showed `HEAD` at `d5a798f`.
- Launch governance gate status: partial/blocked, not public-launch-ready. Existing repository evidence closes public
  freshness and the browser-like waitlist smoke, and it documents several operator procedures. First traffic is still
  limited to an explicitly operator-watched window because unresolved items remain in the accepted limitation, pending
  operator decision, pending external evidence, and blocked categories below.

| Checklist item | Status classification | Current evidence | Exact remaining action |
| --- | --- | --- | --- |
| Public freshness and latest-risk launch evidence | passed with current update evidence | The 2026-07-15 public GET-only evidence records public readiness/latest checks passed with `latest_date=2026-07-14`, `covered_end=2026-07-14`, `data_age_days=1`, `row_count=5846`, `risk=0.2694028326125623`, `risk_state=low`, readiness `no-store`, latest-risk cache headers present, and Cloudflare HIT on the cacheable latest-risk response. | Use this evidence in the final launch snapshot, or recheck public `/api/readiness` if the first traffic window is delayed because freshness is time-sensitive. |
| Browser-like waitlist smoke | passed with existing repo evidence | The 2026-07-08 browser-like smoke records HTTP 201, `Cache-Control: no-store`, `Pragma: no-cache`, expected JSON shape, and aggregate-only storage verification. | Keep raw contacts out of repo notes; rerun only with an operator-approved test contact when a new launch snapshot needs fresh evidence. |
| Privacy, terms, and disclaimer posture | public-host smoke verified; sanitized operator decisions partial | The 2026-07-11 desktop/mobile browser smoke observed the privacy/disclaimer note on the public page and no waitlist POSTs. The source still contains the compact public privacy/terms/disclaimer note near the waitlist with no-advice, no sensitive-info, waitlist storage, operational-log, no recommendation, no paid-SLA, and current no product analytics/tracking-cookie source-code statements. The 2026-07-12 operator decision pass records waitlist handling and support-path category, and the later 2026-07-12 support readiness evidence records mailbox readiness. Legal approval, full privacy policy, and terms-of-service decisions remain incomplete. | Keep the public note current after future deployments. Keep private contacts, raw waitlist data, and support address values out of Git. |
| Waitlist contact handling owner, review cadence, retention, deletion, and unsubscribe path | resolved for sanitized governance; support path ready | Owner role is founder/operator. Review cadence is several times per week during pilot. Retention lasts until beta ends, with earlier operator-approved deletion on request. Follow-up is manual founder/operator only; no automated newsletter is planned. Deletion/unsubscribe requests use manual requests through the dedicated support contact path kept outside Git. | Do not commit private contact details, raw contacts, raw output, or query details. |
| Support/contact identity for questions, deletion, unsubscribe, API, and license interest | completed for first-traffic readiness | Support email status is created and ready. Support/contact path category is a dedicated support mailbox with a project-domain alias, exact addresses and provider details kept outside Git. No paid support SLA is implied. | Keep the actual address, routing, inbox URLs, account IDs, and support messages out of Git unless intentionally published. |
| Credential/account ownership and recovery record | completed for first-traffic readiness | Required ownership categories are documented, the 2026-07-12 pass records founder/operator as the owner role for GitHub, Cloudflare/domain, server, secrets/.env, and backups, and the account recovery record is created outside Git and current. Actual owners/recovery paths are intentionally absent from the repository. | Keep private recovery details outside Git; record only sanitized completion status in Git if needed. |
| Data-source terms and attribution review | accepted limitation for unpaid pilot; commercial/broader launch pending | The 2026-07-12 pass records unpaid/non-commercial pilot status and founder/operator as source terms owner. | Terms review or paid plan remains required before commercial claims, paid beta, or broader distribution. Do not claim legal approval or commercial readiness. |
| Dependency/security maintenance cadence | partial; owner/cadence recorded and GitHub execution pending | [Security and Privacy](security-and-privacy.md), [Operations](operations.md), and `.github/dependabot.yml` record a conservative monthly Dependabot version-update configuration for frontend npm, backend and collector pip requirements, GitHub Actions, Dockerfiles, and a root `docker-compose` ecosystem entry for Compose-style image references. The 2026-07-12 pass records founder/operator ownership and monthly security review cadence during pilot. | Observe the first GitHub-hosted Dependabot run or PRs and continue manual checks for advisories, vulnerability scans, secret-scan output, Python transitive inventory, container image/OS package licenses, CI action/license posture, project license choice, and legal compatibility. |
| Accessibility pass evidence | proxy passed with accepted small-pilot limitation | Browser-capable public-hostname QA, source inspection, the 2026-07-10 focused local axe pass, local chart data alternative implementation, local waitlist live-region/keyboard smoke, the 2026-07-15 manual/native browser QA evidence, and the 2026-07-15 local assistive-tech proxy QA pass are recorded. `@axe-core/playwright` is in the Playwright smoke suite, the chart panels expose a screen-reader-only current summary plus recent history/threshold tables, waitlist submit feedback exposes status/alert semantics, and the updated `npm run smoke --prefix frontend` passed 30 checks outside the sandbox across Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles with focused axe and keyboard/focus checks. The manual/native browser evidence completes the small-pilot manual keyboard/native desktop and mobile browser blocker; the missing dedicated screen-reader/manual assistive-tech pass is accepted only as a small-pilot limitation. | Do not claim VoiceOver, NVDA, TalkBack, manual assistive-tech, full WCAG/legal accessibility compliance, or broader accessibility approval. Record true assistive-tech and broader compliance evidence before broader launch or broader accessibility claims. |
| SEO/social metadata pass evidence | public-host verified for 2026-07-11 update | The 2026-07-11 public metadata check found `title`, description, canonical URL, Open Graph type/title/description/url/site name, and Twitter card/title/description. `og:image` and `twitter:image` were absent as expected because no real repo-served production image asset exists. | Keep public metadata current after future deployments. Keep image metadata omitted unless a real publicly served production image asset is added. |
| Incident response readiness | passed with existing repo evidence | [Operations](operations.md) includes the first-response runbook, monitoring alert expectations, bad-data correction policy, restore guidance, and cache-safety procedures. | Keep the runbook aligned as new monitor, restore, and provenance evidence arrives. |
| Release notes or decision log | passed with existing repo evidence | This document and [Production Roadmap](production-roadmap.md) contain dated evidence notes and decision/status history through 2026-07-10. | Add the final launch snapshot note only when the actual first-traffic window is ready; do not reuse the stale 2026-07-05 snapshot as a launch-ready note. |
| First-user feedback review path | passed with existing repo evidence | This document and [Operations](operations.md) define a post-window review path for waitlist conversion, repeat-use signals, direct questions, methodology confusion, and requests for alerts/API/agents/widgets/licensing. | Run the review only after first traffic creates evidence; do not copy raw waitlist contacts into summaries. |
| Dependency-license review | partial; local evidence recorded, external/manual confirmation pending | [Dependency and License Review](dependency-license-review.md) records the 2026-07-10 local inventory from npm lockfile, Python requirements, container references, CI workflow references, and local Dependabot configuration. Local npm lockfile entries all include license metadata, including `@axe-core/playwright` and `axe-core` as `MPL-2.0`; Python and container license metadata remain unknown from repository files. | Confirm GitHub-hosted Dependabot execution and first PR evidence, Python package metadata, transitive dependencies, container image and OS package licenses, CI action/license posture, vulnerability/advisory status, project license choice, and legal compatibility before broader portfolio sharing or commercial claims. |
| Launch snapshot evidence | pending external evidence | The 2026-07-05 launch snapshot is historical and was blocked by stale readiness. Later public freshness evidence exists, including the 2026-07-15 GET-only readiness/latest-risk evidence, and local launch snapshot packet tooling is implemented/tested, but no final launch snapshot/first-traffic evidence packet is recorded. | Use `scripts/launch_snapshot_packet.py` during the final pre-traffic window to create or validate a sanitized packet from already collected local evidence, then capture the launch commit, public hostname, readiness payload, cache headers, waitlist smoke, launch limitations, and related backup/restore/provenance references immediately before first traffic. |
| External monitoring and alert delivery | accepted/closed for small operator-watched pilot; broader launch pending | The 2026-07-14 monitoring acceptance records Cloudflare Tunnel Health Alert as configured, a HetrixTools/external uptime monitor provider category, and public homepage availability monitoring for the pilot. The 2026-07-12 local public GET-only probe still supports health, readiness, and latest-risk behavior, but no dedicated external `/api/health` monitor, dedicated external `/api/readiness` freshness monitor, stale-data after-window alert, collector-failure alert, recurring backup freshness alert, or explicit alert delivery test evidence is recorded. | Keep small-pilot monitoring limited to the accepted Tunnel health plus homepage availability coverage. Before broader traffic or broader readiness/freshness claims, record sanitized dedicated API monitor evidence and alert delivery proof without private provider details. |
| Import provenance source archive and direct production metadata | partial supporting evidence; direct production evidence pending | The 2026-07-09 pass publicly verified data/cache consistency, and the 2026-07-12 import provenance gap pass verified local helper availability plus existing public/local supporting evidence. Neither pass proved the exact source path/category, source archive, direct production validation/import table metadata, or collector command evidence. | Capture sanitized production import proof outside the repository before or during the final launch snapshot with source category, retrieval/import timestamp, row counts/range, validation/readiness output, latest-risk output, and checksum if available. No accepted limitation is intended for the refresh workflow. |
| Restore drill | accepted limitation for operator-watched first traffic | Checksum-verified off-server USB backup copy evidence is recorded for 2026-07-07, copied/off-server freshness/checksum checker evidence is recorded for timestamp `20260711T190355Z`, and fresh manual backup/off-server evidence is recorded for timestamp `20260715T082457Z`, but the current setup has only the live production server and no staging or empty restore target. | Defer the drill until a separate target exists; do not run restore testing against live production. Record target type and readiness result after the drill. |
| First traffic test | blocked | No first traffic window has run. Freshness, public metadata/privacy smoke, waitlist smoke evidence, support/contact readiness, account recovery readiness, small-pilot monitoring acceptance, fresh backup/off-server evidence, small-pilot manual/native browser QA evidence, and local assistive-tech proxy QA evidence exist. Sanitized import proof if still required beyond public checks/operator confirmation, fresh launch-window readiness/latest-risk checks, and final snapshot evidence remain incomplete. | Run only after remaining required small-pilot blockers are completed, the final launch snapshot exists, and the only remaining limitations are the accepted limitations listed in the current operator decision register. |

Browser/device/accessibility/metadata gap pass recorded on 2026-07-10:

- Scope/safety: evidence pass only. No code change, deploy, refresh/import, cache warmup, waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, dashboard URLs, tokens, `.env` values, browser profiles, or PII were recorded.
- Local repository state before the pass: `git status --short --branch` returned `## main...origin/main`, and
  `git log --oneline --decorate -5` showed `HEAD` at `59b4f5e` tagged
  `launch-governance-gap-evidence-2026-07-10`.
- Automated checks: `npm test --prefix frontend` passed 2 files / 21 tests; `npm run build --prefix frontend` passed;
  `npm run smoke --prefix frontend` was first blocked in the sandbox by
  `listen EPERM: operation not permitted 127.0.0.1:4173`, then passed 15 Playwright checks outside the sandbox.
- Browser/device evidence: automated Playwright browser-profile smoke passed for the local production build with mocked
  API responses in Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles. This is automated browser-profile
  evidence, not native/manual desktop Chrome, Safari, Firefox, iOS Safari, Android Chrome, or physical-device evidence.
- Accessibility evidence: source inspection found `html lang="en"`, semantic `main`, `nav`, section/article structure,
  headings, several `aria-label` attributes, status fallbacks, an `aria-live` error state, and an aria-labeled waitlist
  input. No dedicated axe, pa11y, Lighthouse, keyboard, screen-reader, color-contrast, mobile text-fit, or chart
  accessibility pass was run, so the focused accessibility gate remains pending.
- Public metadata evidence: `GET https://bitcoinriskbrief.minihub.app/` returned HTTP 200 with `title` set to
  `Bitcoin Risk Brief` and the expected charset/viewport tags. The returned HTML did not include a meta description,
  canonical link, Open Graph title/description/image/url, or Twitter card/title/description/image metadata.
- Gap-pass status at that snapshot: partial/blocked, not launch-passed. Automated Playwright smoke passed, but
  native/manual browser-device coverage remained pending, focused accessibility evidence remained pending, and
  SEO/social metadata was inspected but incomplete. The later local implementation status is recorded below.

SEO/social metadata local implementation recorded on 2026-07-10:

- Scope/safety: frontend HTML and docs only. No deploy, refresh/import, cache warmup, waitlist POST, Cloudflare/routing
  change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account details, dashboard URLs,
  tokens, `.env` values, private contacts, or PII were recorded.
- Local implementation: `frontend/index.html` keeps `title` as `Bitcoin Risk Brief` and adds a concise meta description,
  canonical URL for `https://bitcoinriskbrief.minihub.app/`, Open Graph `type`, `title`, `description`, `url`, and
  `site_name`, plus Twitter `card`, `title`, and `description`.
- Image metadata is intentionally omitted: no `og:image` or `twitter:image` tag was added because no real production
  image asset exists in the repo and is served publicly.
- Local verification: `npm test --prefix frontend` passed 2 files / 21 tests; `npm run build --prefix frontend` passed;
  source/build inspection confirmed the title, description, canonical, Open Graph, and Twitter tags in
  `frontend/index.html` and `frontend/dist/index.html`.
- Production status: not deployed or public-host verified in this local implementation pass. The 2026-07-11 backup-gated
  update evidence records the public host serving the expected metadata, with image metadata absent as expected.

Focused accessibility local pass recorded on 2026-07-10:

- Scope/safety: focused frontend test/tooling and docs only. No deploy, refresh/import, cache warmup, waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, dashboard URLs, tokens, `.env` values, private contacts, or PII were recorded.
- Tooling: no axe, pa11y, or Lighthouse tool was present at the start of this pass. The sandboxed install attempt for
  `@axe-core/playwright` failed with DNS `ENOTFOUND`; the approved network rerun installed `@axe-core/playwright` 4.12.1
  and `axe-core` 4.12.1. The install audit reported 0 vulnerabilities.
- Local implementation: `frontend/e2e/frontend-quality.spec.ts` now runs a focused axe scan after the mocked production
  page and chart canvases render.
- Local verification: `npm test --prefix frontend` passed 2 files / 21 tests; `npm run build --prefix frontend` passed;
  `npm run smoke --prefix frontend` was first blocked in the sandbox by `listen EPERM: operation not permitted
  127.0.0.1:4173`, then passed 20 Playwright checks outside the sandbox. The focused axe scan passed in Chromium,
  Firefox, WebKit, Pixel 5, and iPhone 13 profiles with no reported violations.
- Manual/source checklist: `frontend/index.html` declares `html lang="en"`; the app renders `main`, language `nav`,
  section/article structure, a single page `h1`, `h2` section headings, `h3` brief-card headings, an aria-labeled
  waitlist input, visible waitlist success/error text, focus-visible styles for primary controls, chart loading/empty
  `role="status"` fallbacks, an `aria-live` API error state, and aria labels around language/current-state/methodology
  and threshold areas. The later waitlist live-region implementation below supersedes the earlier visible-text-only
  status-message limitation.
- Limitations: this is local automated/source evidence, not a manual keyboard pass, screen-reader/assistive-tech pass,
  physical-device/native browser pass, production-host pass, or full accessibility conformance audit. Axe can evaluate
  rendered DOM color contrast, but not canvas-drawn chart internals. The chart alternative implementation below
  supersedes the earlier missing chart-equivalent-table limitation for local source evidence only, and the later
  waitlist live-region implementation below supersedes the earlier waitlist announcement limitation for local automated
  evidence only.
- Accessibility gate status: partial. The prior "focused accessibility evidence pending" state is replaced by local
  automated axe evidence, but manual/native/assistive-tech evidence remains a launch limitation.

Chart accessibility alternative local implementation recorded on 2026-07-10:

- Scope/safety: frontend code/tests/docs only. No deploy, refresh/import, cache warmup, waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, dashboard URLs, tokens, `.env` values, private contacts, or PII were recorded.
- Local implementation: `frontend/src/App.tsx` now renders a semantic, screen-reader-only chart alternative: a concise
  current chart summary with latest date, current risk/state, model price, and daily low/high when present; a recent
  risk-history table capped at the latest six observations; and a risk-threshold price table for the key 35% and 65%
  bands. `frontend/src/App.css` adds a standard `.sr-only` utility.
- The risk-history and risk-level chart containers now have accessible names/descriptions tied to that non-canvas
  summary/table content, while the visible layout and ECharts canvases remain unchanged for sighted users.
- Local verification: `npm test --prefix frontend` passed 2 files / 23 tests; `npm run build --prefix frontend` passed
  with `index` at 215.92 kB minified / 68.57 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip;
  `npm run smoke --prefix frontend` was first blocked in the sandbox by `listen EPERM: operation not permitted
  127.0.0.1:4173`, then passed 20 Playwright checks outside the sandbox across Chromium, Firefox, WebKit, Pixel 5, and
  iPhone 13 profiles, including the focused axe scan.
- Accessibility status after this pass: chart screen-reader alternative evidence is locally implemented and verified.
  Manual keyboard, manual screen-reader/assistive-tech, physical-device/native browser, production-host accessibility,
  and full WCAG/accessibility compliance evidence remain pending and must not be claimed complete.

Waitlist live-region and keyboard/focus local implementation recorded on 2026-07-10:

- Scope/safety: frontend code/tests/docs only. No deploy, refresh/import, cache warmup, real waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, dashboard URLs, tokens, `.env` values, private contacts, or PII were recorded.
- Local implementation: waitlist submitting and success feedback uses polite `role="status"` live-region semantics;
  waitlist error feedback uses `role="alert"`; the input uses `aria-invalid` and `aria-describedby` when an error is
  present; and the disabled submit button exposes `aria-busy` while submission is pending.
- Local automated coverage: unit tests verify submitting/success status regions, the assertive error alert, input error
  description, busy/disabled submit state, and no browser-storage persistence. Playwright tabs through the public
  controls, verifies reverse focus movement between waitlist submit and input, submits only to a mocked local waitlist
  route with a reserved `.invalid` test address, and verifies the success status region.
- Local verification: `npm test --prefix frontend` passed 2 files / 25 tests; `npm run build --prefix frontend` passed
  with `index` at 216.21 kB minified / 68.64 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip;
  `npm run smoke --prefix frontend` was first blocked in the sandbox by `listen EPERM: operation not permitted
  127.0.0.1:4173`, then passed 25 Playwright checks outside the sandbox across Chromium, Firefox, WebKit, Pixel 5, and
  iPhone 13 profiles.
- Accessibility status after this pass: local automated live-region and keyboard/focus evidence exists. Manual keyboard,
  manual screen-reader/assistive-tech, physical-device/native browser, production-host accessibility, first-traffic, and
  full WCAG/accessibility compliance evidence remain pending and must not be claimed complete.

Privacy/terms/disclaimer local implementation recorded on 2026-07-10:

- Scope/safety: frontend code/tests/docs only. No deploy, refresh/import, cache warmup, real waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, private URLs, tokens, `.env` values, raw logs, account details, or PII were recorded.
- Source-inspected behavior behind the copy: the waitlist form accepts an email address or Telegram handle and sends the
  trimmed contact value with locale and source `landing`; the backend validates and stores `contact`,
  `normalized_contact`, `contact_type`, `locale`, `source`, `status`, `created_at`, and `updated_at`; access logs may
  include method, path, status, client key, Cloudflare ray ID, cache status, and duration; frontend/backend application
  code did not contain product analytics or tracking-cookie code.
- Local implementation: the waitlist section now includes a compact native expandable note with English and Russian
  copy. It states that Bitcoin Risk Brief is informational research only and not financial advice, investment advice, or
  a trading recommendation; warns users not to enter sensitive information; describes the implemented waitlist storage
  and operational log fields; says no buy, sell, portfolio, or trading action is recommended; says no paid support SLA is
  provided; and narrowly states that the current app source does not include product analytics or tracking-cookie code.
- Local verification: `npm test --prefix frontend` passed 2 files / 27 tests; `npm run build --prefix frontend` passed
  with `index` at 218.57 kB minified / 69.43 kB gzip and lazy `Chart` at 557.61 kB minified / 188.87 kB gzip;
  `npm run smoke --prefix frontend` was first blocked in the sandbox by `listen EPERM: operation not permitted
  127.0.0.1:4173`, then passed 25 Playwright checks outside the sandbox across Chromium, Firefox, WebKit, Pixel 5, and
  iPhone 13 profiles, including the focused axe scan and keyboard/focus smoke.
- Remaining status: production/public-host smoke verification for the note is recorded in the 2026-07-11 update evidence.
  Waitlist owner, review cadence, retention period, deletion path, unsubscribe path, support/contact identity, legal
  approval, full privacy policy, and terms-of-service decisions remain pending. Launch governance remains partial/blocked,
  not launch-passed.

Dependency and license local evidence pass recorded on 2026-07-10:

- Scope/safety: docs-only local evidence pass. No deploy, refresh/import, cache warmup, real waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, tokens, `.env` values, private URLs, account details, raw logs, or PII were recorded.
- Local repository state before the pass: `git status --short --branch` returned `## main...origin/main`;
  `git rev-parse HEAD` returned `b26daf6407d88a2a65bc278f1ef0cc3343bd3040`; and the local evidence tag
  `waitlist-accessibility-local-evidence-2026-07-10` was present.
- Reviewed local files: `frontend/package.json`, `frontend/package-lock.json`, `backend/requirements.txt`,
  `collector/requirements.txt`, `pyproject.toml`, `backend/Dockerfile`, `collector/Dockerfile`,
  `frontend/Dockerfile`, `podman-compose.yml`, `podman-compose.cloudflare.yml`, and `.github/workflows/ci.yml`.
- Frontend npm evidence: the npm lockfile has 160 non-root package entries and no missing local `license` fields. Direct
  dependency license metadata is recorded in [Dependency and License Review](dependency-license-review.md). The recently
  added accessibility packages are explicitly recorded: `@axe-core/playwright` 4.12.1 has local lockfile license
  metadata `MPL-2.0`, depends on `axe-core` `~4.12.1`, and `axe-core` is locked at 4.12.1 with local lockfile license
  metadata `MPL-2.0`.
- Python evidence: backend and collector direct package pins are visible in requirements files, but the repository has no
  Python lockfile and the requirements files do not include license metadata. Python direct and transitive license
  confirmation remains external/manual.
- Container and CI evidence: Dockerfiles and compose files reference `node:22-alpine`, `nginx:1.27-alpine`,
  `python:3.13-slim-bookworm`, `timescale/timescaledb:2.17.2-pg16`, and optional `cloudflare/cloudflared:2026.6.1`.
  CI references `actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4`, Python 3.13, Node 22, and
  Playwright browser installation. Local files identify these versions but do not prove base image, OS package, browser,
  or action license posture.
- Dependency/license gate status after this pass: partial local evidence recorded, not legal approval, not full license
  compliance, not vulnerability/advisory clearance, and not production launch readiness. Remaining checks include Python
  package metadata, npm external registry/tarball verification if required, container image and OS package SBOM/license
  review, GitHub Actions/license posture, data-source terms, project license choice, and legal compatibility review.

Local dependency update automation config pass recorded on 2026-07-10:

- Scope/safety: local config and docs evidence pass only. No deploy, refresh/import, cache warmup, real waitlist POST,
  Cloudflare/routing change, commit, push, or tag was performed. No secrets, raw waitlist contacts, private account
  details, tokens, `.env` values, private URLs, account details, raw logs, or PII were recorded.
- Local repository state before the pass: `git status --short --branch` returned `## main...origin/main`;
  `git rev-parse HEAD` returned `68439864a46c5ffe49c6ae76cd925e67aaeb7fca`; and the local evidence tag
  `privacy-terms-local-evidence-2026-07-10` was present.
- Config added: `.github/dependabot.yml` uses monthly version-update checks with modest pull request limits and simple
  groups for `npm` in `/frontend`, `pip` in `/backend` and `/collector`, `github-actions` in `/`, `docker` in
  `/backend`, `/collector`, and `/frontend`, and `docker-compose` in `/` for root Compose-style image references.
- Evidence limits: GitHub-hosted Dependabot execution, first PR evidence, and root Podman Compose filename handling
  remain pending until the local config is merged/pushed and observed. This is not vulnerability/advisory clearance,
  legal approval, full license compliance, container image license review, OS package license review, or production
  launch readiness.

Monitoring, alerts, and single-server restore evidence pass recorded on 2026-07-08:

- Production topology constraint: there is currently one server, and that server is production. No staging project,
  intentionally empty restore target, or separate restore host is available or planned for this pass.
- Restore drill status: accepted limitation/deferred until a separate restore target exists. A live production database
  restore drill is prohibited and was not attempted.
- This pass was read-only against public endpoints and repository documentation. No deploy, refresh/import, warmup,
  commit, push, or tag was performed.
- Public endpoint checks from this session at 2026-07-08 08:08 UTC:
  - `GET https://bitcoinriskbrief.minihub.app/api/health` returned HTTP 200 with `{"status":"ok"}`.
  - `GET https://bitcoinriskbrief.minihub.app/api/readiness` returned HTTP 200 with `status: ready`,
    `data_fresh: true`, `latest_date: 2026-07-07`, `covered_end: 2026-07-07`, `data_age_days: 1`,
    `max_age_days: 2`, `row_count: 5839`, and methodology `crypto-scout-canonical-v1`.
  - `GET https://bitcoinriskbrief.minihub.app/api/risk/latest` returned HTTP 200 for timestamp
    `2026-07-07T00:00:00+00:00` with `risk_state: low`, risk approximately `0.2648`, and
    `model_price_usd: 63392.986942233336`.
- Monitoring evidence status from this historical 2026-07-08 pass: partially verified at that time. Public
  health/readiness/risk endpoints were reachable and current, public readiness was healthy, and one checksum-verified
  off-server USB backup copy was recorded for 2026-07-07. The later 2026-07-14 acceptance supersedes this only for
  small-pilot monitoring coverage: Cloudflare Tunnel Health Alert plus public homepage availability monitoring are
  accepted, while dedicated external API readiness/freshness monitoring and alert delivery remain pending before broader
  launch.

| Evidence area | 2026-07-08 status | Exact remaining operator action |
| --- | --- | --- |
| External uptime/readiness monitor dashboard/evidence | Broader-launch pending after the 2026-07-14 small-pilot acceptance. Public endpoints were reachable, but no dedicated API monitor provider/dashboard proof was available in this session. | Configure or show HTTP monitors for `/api/health` and `/api/readiness`; record provider/dashboard name, sanitized check names, latest check time, and expected status rules without account details before broader traffic. |
| Stale-data alert or readiness HTTP 503 alert | Broader-launch pending. No alert rule or delivery proof was available. | Alert when `/api/readiness` returns non-200, when `status` is not `ready`, or after the nightly collector window plus grace period when `latest_date`/`covered_end` is older than the last completed UTC day or `data_age_days` exceeds `DATA_FRESHNESS_MAX_AGE_DAYS`. |
| Collector failure/container log alert | Deferred broader-launch limitation. Code and runbooks name the relevant log events, but no production log alert evidence was available. | Configure alerts for `scheduled_refresh_failed`, `public_cmc_download_failed`, API fallback failure, and repeated `data-collector` restarts; record the alert source and latest passing scheduled run before broader traffic. |
| Backup freshness/off-server copy monitor | Partially verified. One checksum-verified USB off-server backup copy is recorded for timestamp `20260707T111928Z`, but no recurring backup freshness monitor or alert evidence was available. | Schedule backups and off-server copies, alert when no checksum-verified backup plus off-server copy exists inside the chosen freshness window, and record sanitized evidence from the production host. |
| Cloudflare Tunnel connector health notification | Accepted/closed for the small operator-watched pilot by the 2026-07-14 monitoring acceptance. | Cloudflare Tunnel Health Alert is configured. Keep account IDs, tunnel IDs, routing details, dashboard URLs, alert recipients, screenshots, and tokens out of Git. |
| Alert delivery channel | Deferred broader-launch limitation. No email, chat, pager, or other delivery-channel proof was available. | Choose the alert channel before broader traffic, send a test alert from the monitoring provider, and record the channel type, test time, and success result without addresses, handles, tokens, or private contacts. |

- The 2026-07-14 monitoring acceptance supersedes the blocked small-pilot status above: monitoring is accepted/closed for
  the small operator-watched pilot with limitation, while dedicated API monitoring and alert delivery remain pending
  before broader traffic.

Monitoring and first-response status recorded on 2026-07-05:

- Overall monitoring status for this historical 2026-07-05 note: blocked pending operator evidence at that time. The
  first-response runbook is documented in [Operations](operations.md), and previous public smoke checks prove the public
  health/readiness paths exist. The later 2026-07-14 operator decision now records that Cloudflare Tunnel Health Alert
  plus public homepage availability monitoring are accepted for the small operator-watched pilot, while dedicated API
  monitoring and alert delivery remain pending before broader launch.

| Monitor area | Current status | Required operator action |
| --- | --- | --- |
| Public `/api/health` | Broader-launch pending after the 2026-07-14 small-pilot acceptance. Endpoint exists and has previous smoke evidence, but no dedicated external uptime monitor evidence is recorded. | Configure an HTTP monitor for `https://bitcoinriskbrief.minihub.app/api/health`, alert on non-200, timeout, or TLS failure, and record the provider/dashboard name plus alert channel without account details before broader traffic. |
| Public `/api/readiness` | Broader-launch pending after the 2026-07-14 small-pilot acceptance. Endpoint exists and has previous smoke evidence, but no dedicated external readiness alert evidence is recorded. | Configure an HTTP monitor for `https://bitcoinriskbrief.minihub.app/api/readiness`, alert on non-200, and route the alert to the `/api/readiness` first-response entry in `docs/operations.md` before broader traffic. |
| Stale readiness after nightly update window | Broader-launch pending. No scheduled stale-data monitor evidence is recorded. | After the default 01:00 UTC collector window plus operator-defined grace period, check `/api/readiness`; alert if `status` is not `ready`, `latest_date`/`covered_end` is older than the last completed UTC day, or `data_age_days` exceeds `DATA_FRESHNESS_MAX_AGE_DAYS`. |
| Collector refresh failure | Deferred broader-launch limitation. The scheduled public-download-first path is documented, but no production log alert evidence is recorded. | Configure production log/container alerts for `scheduled_refresh_failed`, `public_cmc_download_failed`, API fallback failure, and repeated `data-collector` restarts; record the alert source and latest passing scheduled run before broader traffic. |
| Backup freshness | Partially blocked. One checksum-verified off-server USB backup copy is recorded for 2026-07-07, but no restore drill or recurring backup freshness monitor evidence is recorded here. | Schedule `./scripts/backup.sh`, copy verified backups off-server, alert when no checksum-verified backup and off-server copy exists inside the chosen freshness window, run a restore drill only on staging or an intentionally empty restore target, and record redacted evidence from the production host. |
| Cloudflare Tunnel health | Accepted/closed for the small operator-watched pilot by the 2026-07-14 monitoring acceptance. | Cloudflare Tunnel Health Alert is configured. Keep account IDs, tunnel IDs, routing details, dashboard URLs, alert recipients, screenshots, and tokens out of Git. |

- Public traffic remains limited to a controlled operator-watched pilot. Pause broader promotion while dedicated API
  monitors or alert delivery evidence are missing.

Production import provenance evidence pass recorded on 2026-07-09 from 16:19 to 16:20 UTC for
`https://bitcoinriskbrief.minihub.app`:

- Scope/safety: docs and evidence pass only. No deploy, refresh/import, cache warmup, commit, push, or tag was performed.
  This note intentionally records only redacted operational metadata and does not include raw CSV contents, `.env`
  values, API keys, Cloudflare tokens, waitlist contacts, browser profiles, private account exports, credentials, or
  other PII.
- Local repository state before the docs edit: `git status --short --branch` returned `## main...origin/main`, and
  `git log --oneline --decorate -5` showed local `HEAD` at `d997f8b`.
- Production project/source evidence: `/srv/projects/bitcoin-risk-brief` is absent in this workstation session, no
  production SSH target is documented here, and no mounted USB kit manifest was found under `/Volumes`. A live
  production `.git` check and a current USB/deploy manifest check were therefore not available in this pass. Temporary
  local USB-kit smoke manifests under the workstation temp directory were not treated as production deploy evidence. The
  earlier 2026-07-07 USB deploy note remains the last recorded deploy-source evidence, but it was not revalidated here.
- Public readiness: `GET /api/readiness` returned HTTP 200 with `status: ready`, `data_fresh: true`,
  `latest_date: 2026-07-08`, `covered_end: 2026-07-08`, `data_age_days: 1`, `max_age_days: 2`,
  `source: coinmarketcap_csv`, `row_count: 5840`, and methodology `crypto-scout-canonical-v1`.
- Latest risk: `GET /api/risk/latest` returned HTTP 200 for timestamp `2026-07-08T00:00:00+00:00` with
  `risk_state: low`, risk approximately `0.2536`, `model_price_usd: 62485.70392776667`, `low_usd: 61492.6501591`, and
  `high_usd: 63706.8859194`. The latest risk date matches readiness `covered_end`.
- Validation/import metadata summary: direct production `psql` metadata queries were not available because this session
  has no production host/project access. Public readiness payload data and product cache-version metadata consistently
  exposed validation marker `validation:2026-07-09T01:00:06.303623+00:00:2026-07-08T00:00:00+00:00:5840:true`, which
  corresponds to computed validation time `2026-07-09T01:00:06.303623+00:00`, validation `covered_end`
  `2026-07-08T00:00:00+00:00`, row count `5840`, and `risk_range_ok: true`. This public metadata aligns with readiness
  and latest risk, but it is not a substitute for a direct production validation-table query.
- Source path/category: partially verified only. The public payloads prove the current validation source is
  `coinmarketcap_csv`, but logs, direct validation/import metadata, source snapshot, manifest, and production collector
  command evidence were unavailable. Therefore this pass does not prove whether the latest data was produced by the
  scheduled public CoinMarketCap refresh, manual `download-cmc-csv`, manual `import-cmc-csv`, `run-now` existing CSV
  import, optional API fallback, restore, or correction.
- Historical public cache evidence from this pass predates the live-readiness no-store policy. Current readiness should
  return `Cache-Control: no-store`; cache headers below are retained only as historical evidence.
- Public cache evidence: all checked public read endpoints returned HTTP 200 with `Cache-Control: public, max-age=60,
  stale-while-revalidate=300`, an `ETag`, `X-Cache: MISS`, and the same validation-versioned `X-Cache-Version`.
  Cloudflare cache status on repeat requests was `HIT` for `/api/readiness`, `/api/risk/latest`,
  `/api/risk/history?limit=2000`, `/api/risk/levels`, and `/api/brief/latest`. The app-level `X-Cache: MISS` value on a
  Cloudflare HIT remains the known cached-origin-header nuance already recorded above.

| Endpoint | HTTP | ETag | X-Cache-Version | cf-cache-status evidence |
| --- | --- | --- | --- | --- |
| `/api/readiness` | 200 | `"9ac0754f06ecc44d3d921901"` | `validation:2026-07-09T01:00:06.303623+00:00:2026-07-08T00:00:00+00:00:5840:true` | initial `MISS`, repeat `HIT` with age about 38s |
| `/api/risk/latest` | 200 | `"5886d24bdc7925a1a3585a87"` | same as readiness | `HIT` with age about 2s, repeat `HIT` with age about 37s |
| `/api/risk/history?limit=2000` | 200 | `"f861ecd2321988c97f2cfec5"` | same as readiness | initial `MISS`, repeat `HIT` with age about 35s |
| `/api/risk/levels` | 200 | `"47c635efa5b13af4a6689070"` | same as readiness | initial `MISS`, repeat `HIT` with age about 28s |
| `/api/brief/latest` | 200 | `"0ad423e6c0e4cbc1da79a8f4"` | same as readiness | initial `MISS`, repeat `HIT` with age about 19s |

- Import provenance gate status: partial, not passed. Production data consistency is publicly verified because readiness,
  latest risk, validation-version metadata, and cache headers all align on `2026-07-08` / row count `5840`; however, the
  exact source path/category and direct production validation/import metadata remain pending production-host or operator
  evidence. No mismatch was observed in the public evidence.
- Local helper status: `scripts/import_provenance_packet.py` is implemented and tested locally to create or validate a
  sanitized JSON manifest for a future production import evidence packet. This is local tooling only; it did not create a
  real production source/archive packet and does not close the pending exact source path/category or direct
  validation/import metadata gaps.

Import provenance and bad-data correction status recorded on 2026-07-05:

- Task 6 status: blocked pending operator evidence for the real production import evidence packet. The operator
  procedure and bad-data correction policy are documented in [Operations](operations.md), and the data-pipeline
  provenance contract is documented in [Data Pipeline](data-pipeline.md).
- Real sample import evidence packet: not present in this repository and not created from this agent environment. This
  session has no access to the production host at `/srv/projects/bitcoin-risk-brief`, no mounted outside-repository
  provenance archive, and no Cloudflare/production host evidence source. A workstation-local or repository-local sample
  would not prove production import provenance, so it should not be recorded as completion evidence.
- Current import-proof boundary: the 2026-07-12 operator decision pass does not accept a limitation for the refresh
  workflow. Do not mark provenance complete until sanitized proof for the real production data state exists outside the
  repository and references source category, retrieval/import timestamp, row counts/range, readiness/latest-risk output,
  and checksum if available.
- Exact operator actions needed on the production host:

```bash
cd /srv/projects/bitcoin-risk-brief
git status --short --branch
git rev-parse HEAD
export PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app
export IMPORT_ARCHIVE_ROOT="<outside-repository-import-evidence-root>"
test -n "${IMPORT_ARCHIVE_ROOT}"
case "${IMPORT_ARCHIVE_ROOT}" in
  /srv/projects/bitcoin-risk-brief|/srv/projects/bitcoin-risk-brief/*) exit 2 ;;
esac
EXPECTED_END_DATE="$(date -u -d 'yesterday' +%F)"
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
curl -fsS http://127.0.0.1:3001/api/readiness
curl -sD - -o /tmp/bitcoin-risk-latest-public.json "${PUBLIC_BASE_URL}/api/risk/latest"
```

- After the import command above, follow the `Production Import Provenance` procedure in [Operations](operations.md):
  copy the source snapshot and canonical CSV under the per-import archive directory, calculate `sha256` and
  row/date-range evidence, save origin readiness and public cache headers, create `manifest.json`, link any
  launch/restore/correction note, and inspect the packet for forbidden data.
- Sensitive data rule for the evidence packet: do not include `.env` values, API keys, Cloudflare tokens, waitlist
  contacts, raw analytics, browser profiles, private account exports, or other PII.
- Bad-data correction posture: documented for the pilot with low/medium/high classification, observe/inspect/freeze,
  known-good restore or re-import, risk/brief recomputation, origin and edge cache verification, correction notes, and
  internal freshness/RPO/RTO/downtime boundaries. These are internal pilot targets, not public SLA commitments.

Production waitlist smoke status recorded on 2026-07-08:

- Browser-like retry source label used: `ops-smoke-20260708115806`.
- Public endpoint tested: `POST https://bitcoinriskbrief.minihub.app/api/waitlist`.
- Browser-like path: a `Mozilla/` User-Agent was used through Cloudflare, matching the user-path smoke guidance and
  avoiding the known default-curl bot challenge.
- HTTP/API smoke status: passed. The single authorized valid-contact POST returned HTTP 201 with
  `Content-Type: application/json`.
- Cache header result: passed. The response included `Cache-Control: no-store` and `Pragma: no-cache`.
- Response shape result: passed. The saved JSON envelope contained `data.contact_type: email`, `data.locale: en`, and
  boolean `data.created`.
- Production source state: `git status` and `git rev-parse HEAD` were unavailable because the production directory is not
  a Git checkout and `.git` is absent.
- Server-side storage verification: passed. The operator ran an aggregate-only production-host query against
  `waitlist_leads` for source `ops-smoke-20260708115806`, `contact_type='email'`, and `locale='en'`, without selecting
  `contact` or `normalized_contact`. Result: count `1`, max `created_at`
  `2026-07-02 12:12:54.605104+00`, max `updated_at` `2026-07-08 11:58:07.184215+00`.
  The older `created_at` with the 2026-07-08 `updated_at` indicates an upsert/update of an existing lead, not proof that
  a new lead was created.
- Waitlist smoke gate: closed for this browser-like smoke because HTTP 201, no-store/no-cache headers, response shape,
  and aggregate storage verification all passed.
- Contact value is intentionally omitted from this document, and no raw contact or other PII is recorded in the evidence
  note.

Production waitlist default-curl smoke failure recorded on 2026-07-08:

- Public endpoint tested: `POST https://bitcoinriskbrief.minihub.app/api/waitlist`.
- Source label used: `ops-smoke-20260708085956`.
- HTTP saved/upsert status: failed. The single authorized production smoke request reached Cloudflare and returned
  HTTP 403, so the API did not return the expected 201 saved/upsert response.
- Cache header result: failed for this Cloudflare 403 artifact. The response did not include `Cache-Control: no-store`
  or `Pragma: no-cache`; this artifact did not verify the origin waitlist no-store contract. The browser-like retry
  above now verifies the origin no-store/no-cache result.
- Response shape result: failed. The saved response artifact was HTML from Cloudflare rather than the expected JSON
  envelope with `data.contact_type`, `data.locale`, and `data.created`.
- Server-side storage verification: blocked from this workstation. `/srv/projects/bitcoin-risk-brief` is not present and
  no safe production database access was available, so the aggregate `waitlist_leads` query by source/contact type/locale
  was not run.
- Contact value is intentionally omitted from this document, and no raw contact or other PII is recorded in the evidence
  note.

Production waitlist Cloudflare 403 diagnostic recorded on 2026-07-08:

- Scope/safety: root-cause diagnostic only. No real contact was used, and both diagnostic requests used only the invalid
  non-PII payload `contact: "not-a-contact"`, locale `en`, and source label `ops-diag-20260708091951`.
- Default curl User-Agent result: `POST https://bitcoinriskbrief.minihub.app/api/waitlist` returned HTTP 403 with
  `Content-Type: text/html; charset=UTF-8` and `cf-mitigated: challenge`. The response was a Cloudflare challenge
  artifact and did not include origin `Cache-Control: no-store` or `Pragma: no-cache` headers.
- Browser-like User-Agent result: the same invalid payload with a `Mozilla/` User-Agent returned HTTP 422 JSON from the
  origin with `Cache-Control: no-store`, `Pragma: no-cache`, and `cf-cache-status: DYNAMIC`.
- Cloudflare dashboard/API evidence: unavailable from this workstation because Cloudflare API credentials were not
  present; no Security Events details were recorded.
- Root-cause conclusion: the previous waitlist smoke method was blocked by the repo-managed waitlist bot challenge
  because the default curl User-Agent is non-browser-like and lacks `Mozilla/`.
- The browser-like retry smoke above reached origin with an operator-approved valid contact, passed the HTTP/API checks,
  and has aggregate-only storage verification recorded above.

Production waitlist smoke status recorded on 2026-07-05:

- Public endpoint for the smoke: `POST https://bitcoinriskbrief.minihub.app/api/waitlist`.
- Waitlist submission was not performed from this agent environment because no operator-controlled test contact value or
  other private contact handoff was available. Using a placeholder would not satisfy the Task 7 contact constraint.
- HTTP saved/upsert status: blocked/not collected because no waitlist submission was sent.
- Cache header result: blocked/not collected. `Cache-Control: no-store` and optional `Pragma: no-cache` still need
  verification on a successful or duplicate/upsert waitlist response.
- Server-side storage verification: blocked from this workstation. `/srv/projects/bitcoin-risk-brief` is not present and
  no safe production database access was available, so `waitlist_leads` was not queried.
- Contact value is intentionally omitted from this document and must also be omitted from logs summaries, final reports,
  screenshots, and commit messages.

Browser and device QA status recorded on 2026-07-05:

- Automated frontend checks completed: `npm test --prefix frontend` passed 2 files / 17 tests;
  `npm run build --prefix frontend` passed; `npm run smoke --prefix frontend` was first blocked in the sandbox by
  `listen EPERM: operation not permitted 127.0.0.1:4173`, then passed 15 Playwright checks when rerun outside the
  sandbox.
- Public-hostname browser-capable QA was performed against `https://bitcoinriskbrief.minihub.app/` with Playwright
  desktop Chromium, mobile Chromium Pixel 5, and mobile WebKit iPhone 13 profiles. The page loaded, latest risk was
  visible, readiness/freshness was visible, both chart canvases were non-empty, the waitlist form was visible, EN/RU
  switching worked, and mobile checks found no horizontal overflow or obvious text overlap in saved screenshots.
- Launch-gate result for this 2026-07-05 pass: browser-capable public-hostname rendering passed with limitations, but
  broader launch was blocked/limited by degraded data freshness shown on the public page (`2026-06-30`, `4 days old`) and
  by the missing physical device/native branded browser pass. No production waitlist submission was sent as part of this
  Task 8 pass.

Launch governance and release evidence status recorded on 2026-07-05:

- Launch snapshot commit: `f42f266542981483a87964fa8726a5513eb339d6`. This was a snapshot target only, not a
  production-ready or launch-ready declaration, because readiness was degraded during this snapshot.
- Methodology version: `crypto-scout-canonical-v1`.
- Selected data refresh path: scheduled public-download-first CoinMarketCap CSV refresh with manual
  `download-cmc-csv` or `import-cmc-csv` fallback. The optional official CoinMarketCap API path is used only when
  `COINMARKETCAP_API_KEY` is configured.
- Known accepted limitations for that snapshot candidate: no standalone privacy/terms page was recorded at that time;
  waitlist lead owner, review cadence, deletion/unsubscribe contact path, and support/contact identity were pending
  operator decisions at that time;
  production backup/off-server copy/restore evidence was missing at that time; monitoring evidence is missing; production
  import provenance evidence is missing; waitlist smoke was not run; public page data was observed stale during Task 8;
  full native-device/browser QA, focused accessibility, and SEO/social metadata evidence were not complete then;
  Cloudflare remained on the documented Free-plan-compatible subset. Later evidence above supersedes the missing
  backup/off-server copy portion, records local privacy/terms/disclaimer and SEO/social metadata implementation, records
  2026-07-11 public-host privacy/disclaimer smoke plus metadata verification, and records the 2026-07-12 sanitized
  operator decision pass, while restore drill evidence remains deferred until a safe target exists.
- Governance evidence process: keep privacy/terms/disclaimer posture, waitlist handling, credential/account ownership,
  data-source terms review, dependency/security maintenance, accessibility, and metadata status in
  [Security and Privacy](security-and-privacy.md) and [Operations](operations.md). Unknown operator-owned facts must be
  recorded as pending decisions, not guessed.
- First-user feedback review path: after the first controlled traffic window, summarize waitlist conversion,
  repeat-use signals, direct questions, methodology confusion, and requests for alerts, daily briefs, API access,
  agents, embeddings, widgets, or commercial reuse into this document or [Production Roadmap](production-roadmap.md).
  Do not copy raw waitlist contacts into feedback notes.
- Support/contact identity status: superseded by the 2026-07-12 support/contact readiness evidence. A dedicated support
  mailbox with a project-domain alias is created and ready, exact addresses are kept outside Git, and no public support
  portal, paid SLA, or guaranteed response time is implied for the first pilot.
- Dependency-license review status: superseded by the 2026-07-10 local evidence pass above. Local npm lockfile license
  metadata, Python manifest gaps, container references, and CI references are now recorded in
  [Dependency and License Review](dependency-license-review.md). External/manual confirmation and project license choice
  remain pending, and the project must not claim legal approval, full license compliance, or open-source status unless a
  license is intentionally chosen.
- Release evidence packet process: the final launch snapshot should reference the launch commit, public hostname,
  readiness payload, cache headers, selected refresh path, deployment path, backup/off-server and restore-drill evidence,
  waitlist smoke, browser QA, known limitations, and any related import provenance manifest. Store private artifacts, raw
  contacts, secrets, account details, and private storage paths outside this repository.

Task 10 launch snapshot recorded on 2026-07-05 at 11:37 UTC for `https://bitcoinriskbrief.minihub.app`:

- Repository state: `git status --short --branch` returned `## main...origin/main`, and `git rev-parse HEAD` returned
  `f42f266542981483a87964fa8726a5513eb339d6`. No commit or push was performed for this snapshot.
- Public health: `GET /api/health` returned HTTP 200 with `status: ok`.
- Public readiness: `GET /api/readiness` returned HTTP 503 with `status: degraded`. All readiness checks were true
  except `data_fresh: false`; the payload reported `latest_date: 2026-06-30`, `covered_end: 2026-06-30`,
  `data_age_days: 4`, `max_age_days: 2`, `source: coinmarketcap_csv`, `row_count: 5832`, and
  `methodology_version: crypto-scout-canonical-v1`.
- Latest BTC data and risk: `GET /api/risk/latest` returned HTTP 200 for timestamp `2026-06-30T00:00:00+00:00` with
  `risk_state: low` and risk approximately `0.2860`. At the time, the latest BTC data date remained `2026-06-30`, so
  production data freshness blocked launch for this snapshot.
- Cache headers: this historical snapshot predates the live-readiness no-store policy. Current `/api/readiness` must
  return `Cache-Control: no-store`; cacheable product responses such as latest risk should carry `Cache-Control`, `ETag`,
  `X-Cache`, and `X-Cache-Version`. At the time, the readiness response used
  `ETag: "e794a17b08b6404888453563"`, `X-Cache: MISS`,
  `X-Cache-Version: validation:2026-07-04T01:00:05.639122+00:00:2026-06-30T00:00:00+00:00:5832:true`, and
  `cf-cache-status: STALE`. The latest-risk response used `Cache-Control: public, max-age=60, stale-while-revalidate=300`,
  `ETag: "0b452ec072778d840d5ed64d"`, `X-Cache: MISS`,
  `X-Cache-Version: validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true`, and
  `cf-cache-status: UPDATING`.
- Waitlist smoke status: blocked/not collected. No operator-controlled test contact was available, no public waitlist
  submission was sent, and server-side storage was not verified.
- Browser QA status: browser-capable public-hostname QA passed with accepted limitations. The public page rendered in
  Playwright desktop Chromium, mobile Chromium, and mobile WebKit profiles, but it visibly showed stale data and no
  physical-device/native branded browser pass is recorded.
- Selected deployment path: USB-based local-server deployment under `/srv/projects/bitcoin-risk-brief`; USB Update And
  Install Kit V2 existed locally with a default one-command deploy entrypoint and explicit backup-gated mode, but a real
  USB package and production-host deploy were still pending for this snapshot, and the production `.env` owner still
  needed host confirmation.
- Selected data refresh path: scheduled public-download-first CoinMarketCap CSV refresh, with manual
  `download-cmc-csv` and `import-cmc-csv` fallbacks. The public readiness result in this snapshot proved this path had not
  kept production fresh through the accepted freshness window and needed operator action before launch.
- Backup/restore evidence status for this historical snapshot: blocked pending operator evidence. At that time, no real
  production backup, off-server copy, restore drill, or backup freshness monitor was recorded. The 2026-07-07 evidence
  above supersedes the backup/off-server copy portion, while restore drill and backup freshness monitor evidence remain
  open.
- Monitoring status for this historical snapshot: blocked pending operator evidence at that time. Public endpoints exist,
  but no external monitor dashboard, alert delivery, collector failure alert, backup freshness alert, or Cloudflare Tunnel
  health alert evidence was recorded in that snapshot. The 2026-07-14 operator decision now accepts Cloudflare Tunnel
  Health Alert plus public homepage availability monitoring for the small operator-watched pilot, while dedicated API
  monitoring and alert delivery remain pending before broader launch.
- Import provenance status: blocked pending operator evidence. No sanitized production import evidence packet is recorded
  outside the repository.
- Limitations/blockers for this historical snapshot: Cloudflare remained on the documented Free-plan-compatible
  subset; waitlist smoke, backup/off-server/restore, monitoring, production import provenance, physical/native browser
  QA, support/contact identity, dependency-license review, and focused accessibility/SEO metadata evidence were
  incomplete. The launch blocker for this snapshot was data freshness: readiness was HTTP 503 with `data_fresh: false`.
  The 2026-07-07 post-deploy evidence above closes that readiness condition and the backup/off-server copy portion, but
  the first traffic test should still not be marked complete until the other required launch limitations, including the
  restore drill, are explicitly resolved or accepted and the traffic window runs.

USB Update And Install Kit V2 local implementation status recorded on 2026-07-05:

- Local repository support is implemented for workstation packaging with
  `bash server-kit/prepare-usb-kit.sh /Volumes/USB`. The package creates
  `/Volumes/USB/bitcoin-risk-brief-server-kit` with deployment docs, ordered server scripts including
  `scripts/07-update-bitcoin-risk-brief-from-usb.sh`, a filtered project snapshot, `manifest.txt`, and `SHA256SUMS`.
- The local package contract excludes production secrets and local state: `.env`, `.git`, backups, database volumes,
  dependency caches, build output, browser artifacts, container images, and offline package mirrors are not part of the
  USB kit.
- The server update wrapper requires the existing `/srv/projects/bitcoin-risk-brief/.env`, runs
  `./scripts/backup.sh` before copying new code, verifies the backup, copies the verified backup to the USB default
  `backups-from-server/` or an operator-provided `BACKUP_COPY_DEST`, verifies the copy, deploys the USB project
  snapshot, restarts the service, and runs local health/readiness plus optional public readiness checks.
- Production `.env` is preserved by the deploy/update flow and is not sourced from the USB kit.
- Production benefit is now verified for the operator-run USB deploy path by the 2026-07-07 post-deploy evidence above:
  USB deploy verification passed, public readiness returned HTTP 200, public frontend smoke passed, and one off-server
  USB backup copy passed checksum verification. Restore-drill evidence remains tracked separately under the
  backup/restore gate.

Task 11 cache latency measurement recorded on 2026-07-05 from 12:15 to 12:17 UTC for
`https://bitcoinriskbrief.minihub.app`:

- Measurement context: production readiness was degraded during this historical pass. `GET /api/readiness` returned HTTP
  503 with
  `status: degraded`, `data_fresh: false`, `latest_date: 2026-06-30`, `covered_end: 2026-06-30`, `data_age_days: 4`,
  `max_age_days: 2`, `source: coinmarketcap_csv`, and `row_count: 5832`. This measurement is useful for cache-latency
  evidence, but it did not close the launch blocker at the time. The readiness cache headers in this table predate the
  live-readiness no-store policy. The 2026-07-07 post-deploy evidence above closes the freshness blocker and records fast
  repeated Cloudflare HIT behavior after warmup.
- Commands used `curl -sS -D - -o /tmp/... -w 'time_total=%{time_total}\n'` against the public hostname. Initial sandbox
  DNS resolution failed, so the public curl checks were rerun with network access for the measurement.

| Endpoint | HTTP | X-Cache | X-Cache-Version | Cache-Control | First observed `time_total` | Repeat behavior |
| --- | --- | --- | --- | --- | --- | --- |
| `/api/readiness` | 503 | `MISS` | `validation:2026-07-04T01:00:05.639122+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `0.579072s` | Repeats stayed `X-Cache: MISS` with Cloudflare `STALE`; observed `0.223646s` to `0.293653s`. |
| `/api/risk/latest` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `15.720018s` | Repeats were fast through Cloudflare (`HIT` or `UPDATING`) at `0.156413s` to `0.182181s`, but the public response still exposed cached origin `X-Cache: MISS`. |
| `/api/risk/history?limit=2000` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `0.502109s` | Repeats stayed under `0.37s` through Cloudflare (`HIT` or `UPDATING`), with cached origin `X-Cache: MISS`. |
| `/api/risk/levels` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `16.289584s` | Repeats were fast through Cloudflare (`HIT` or `UPDATING`) at `0.155345s` to `0.184155s`, but the public response still exposed cached origin `X-Cache: MISS`. |
| `/api/brief/latest` | 200 | `MISS` | `validation:2026-07-05T01:00:05.626717+00:00:2026-06-30T00:00:00+00:00:5832:true` | `public, max-age=60, stale-while-revalidate=300` | `0.291438s` | Repeats were fast through Cloudflare (`HIT` or `UPDATING`) at `0.159051s` to `0.170369s`, with cached origin `X-Cache: MISS`. |

- Backend `X-Cache: HIT` behavior was not directly observable from the public Cloudflare path in this pass. Repeated
  requests showed fast Cloudflare edge behavior, but the response header continued to expose the cached origin
  `X-Cache: MISS` value.
- Slow MISS/revalidation was observed for `/api/risk/levels` and `/api/risk/latest` during this historical pass. Local
  public cache warmup was later deployed through USB, healthy readiness was restored, and the 2026-07-07 public evidence
  recorded fast repeated Cloudflare HIT behavior after warmup. Continue to measure any endpoint not covered by the
  post-deploy smoke before broader traffic.
- Cache warmup remains a pre-traffic production operation: check `/api/readiness` first, then warm `/api/risk/latest`,
  `/api/risk/history?limit=2000`, `/api/risk/levels`, and `/api/brief/latest` after backend startup and after successful
  import/validation-version changes. Warmup must not hide stale readiness, and it must preserve `X-Cache-Version`
  invalidation for cacheable product payloads.

Task 4 local public-cache warmup command implementation recorded on 2026-07-05:

- Startup warmup is implemented in the backend after the database pool is ready. It checks readiness first and warms the
  standard product public read keys only when validation exists and readiness is HTTP 200; missing validation, readiness
  probe failures, and degraded readiness are logged and skipped so stale production data is not hidden.
- The operator command is `PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache`. It calls normal
  public GET routes against a local/private origin: `/api/readiness` is a `curl -fsS` gate, then `/api/risk/latest`,
  `/api/risk/history?limit=2000`, `/api/risk/levels`, and `/api/brief/latest` are warmed. Readiness 503 or any later
  non-success response fails the command. No public admin endpoint is added.
- `POST /api/waitlist` remains outside the public read cache contract and must continue to return `Cache-Control:
  no-store`.
- Local implementation and documentation are complete, and production benefit for the public smoke path is supported by
  the 2026-07-07 post-deploy evidence after USB deploy and public readiness HTTP 200. Continue to run the warmup command
  after backend startup and successful import/validation-version changes.
- Task 5 local verification was run on 2026-07-05 from commit `5517f49fd0540ce96b304cf80fcd0c707076f48b`: focused
  public-cache tests passed, all backend and collector Python tests passed, Python sources compiled, and compose
  configuration validation returned `compose config ok`. This is local implementation evidence only; the later 2026-07-07
  post-deploy evidence above verifies deploy, fresh data, and public smoke-path cache timing, while any endpoints not
  covered by that smoke still need measurement.

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

If a one-off production refresh is needed before the scheduled collector has run, use the no-key public CoinMarketCap
path before the final readiness check:

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
  local `.env`, `.git`, backups, dependency caches, build output, browser artifacts, container images, or offline
  package mirrors;
- cache policy for public read endpoints;
- Cloudflare WAF, bot protection, cache rules, and edge rate limits rendered and applied with
  `scripts/cloudflare_edge_rules.py`, plus dashboard bot protection enabled where required by the Cloudflare plan;
- launch operations and governance posture: public-host verification of the privacy/terms/disclaimer copy,
  post-waitlist handling, dependency/security maintenance cadence, credential/account ownership, resource monitoring,
  data-source terms, accessibility, public-host metadata verification, and incident response notes;
- release feedback and operational evidence posture: release notes or decision log, first-user feedback review path,
  support/contact identity, dependency-license review external/manual confirmation, launch evidence, and restore-drill
  evidence;
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
- Scheduled collector runs target the last completed UTC day. If the CSV is stale, they use public CoinMarketCap
  download first and fall back to the optional official API delta refresh only when `COINMARKETCAP_API_KEY` is
  configured.
- If the CSV already covers the scheduled target date, the collector imports and recomputes from the existing CSV
  without downloading.
- The production-pilot path supports automatic public CoinMarketCap downloads and validated imports from
  operator-downloaded CoinMarketCap historical CSVs.
- Remote deltas, public downloads, and downloaded CSV imports must exactly match the expected contiguous daily range.
- Non-contiguous or invalid inputs fail without rewriting the canonical CSV.
- CSV writes use atomic replace.
- Every import recalculates all risk rows and removes DB rows after the CSV tail.

## Performance And Caching Gate

Before public traffic, verify the implemented cache policy for public read endpoints:

- readiness;
- latest risk;
- risk history;
- risk levels;
- daily brief.

Readiness should return `Cache-Control: no-store`. Cacheable product endpoints should return `Cache-Control`, `ETag`,
`X-Cache`, and `X-Cache-Version`. Backend cache invalidation is versioned from `btc_risk_validation`; after a successful
import, the collector rewrites validation and the next backend product read rebuilds against the new version unless
startup or operator warmup has already rebuilt the standard key. `POST /api/waitlist` must return
`Cache-Control: no-store` and must not be cached by Cloudflare.

Before active traffic, measure first-load latency for both backend `X-Cache: MISS` and `X-Cache: HIT` responses on the
public hostname. Use startup warmup and the local-origin `warm-public-cache` operator command for the standard endpoint
set before active traffic, and consider precomputing expensive payloads such as `/api/risk/levels` if warmup is still
not enough. Warmup must preserve `X-Cache-Version` invalidation and must not hide stale readiness.

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

If issue #28 localization expansion is implemented before active traffic, include English, Russian, Simplified Chinese,
German, French, Spanish, and Arabic in the browser/device pass. Arabic must include right-to-left layout verification,
waitlist locale attribution, and checks that chart data, USD prices, and ISO dates remain readable.

## Remaining External Operations

These are operational tasks outside this repository.

Completed or partially completed as of 2026-07-01:

- Cloudflare Tunnel/public hostname is serving `https://bitcoinriskbrief.minihub.app`.
- Public `/api/health`, `/api/readiness`, `/api/risk/latest`, and conditional `/api/risk/latest` checks pass through
  Cloudflare.
- Cloudflare edge cache settings and the waitlist-specific rate-limit/custom challenge subset were applied with
  `scripts/cloudflare_edge_rules.py`.
- The tracked repository documentation and portfolio presentation pass is locally complete as of 2026-07-06. At that
  time, this docs-only repository status did not prove backup/restore, monitoring, waitlist, import provenance,
  browser/device/accessibility, or first-traffic readiness.
- Post-deploy evidence recorded on 2026-07-07 verifies the operator-run USB deploy, closes the public data freshness
  blocker, confirms public `/api/readiness` HTTP 200 with latest public data date `2026-07-06`, verifies latest
  risk/model-price/OHLC display on desktop and mobile Playwright smoke, records fast repeated Cloudflare HIT behavior
  after warmup, and records one checksum-verified off-server USB backup copy.
- Backup-gated USB production update evidence recorded on 2026-07-11 verifies target commit
  `86cb2dad889baf24a7464a105bbe2224f75b14ef`, server-reported exit code 0, copied/off-server backup freshness/checksum
  checker status valid and fresh for timestamp basename `20260711T190355Z`, public readiness/latest/cache evidence through
  latest date `2026-07-10`, public metadata/privacy smoke, and desktop/mobile browser smoke without waitlist POSTs.
- Fresh manual backup/off-server copy evidence recorded on 2026-07-15 completes that first-traffic blocker for the
  current evidence set: USB package source commit `8020384ddaa53f3805f0f29c54928ea53c91cce1`, copied backup timestamp
  basename `20260715T082457Z`, PostgreSQL dump/BTC CSV/manifest/checksum categories present, and copied-backup SHA-256
  verification passed. Supporting public GET-only evidence recorded public readiness `latest_date=2026-07-14`,
  `row_count=5846`, `risk_state=low`, readiness `no-store`, latest-risk cache headers, and Cloudflare HIT on the
  cacheable latest-risk response.
- Browser-like waitlist smoke evidence recorded on 2026-07-08 verifies HTTP 201, no-store/no-cache headers, expected JSON
  response shape, and aggregate-only storage verification for source `ops-smoke-20260708115806`; the waitlist smoke gate
  is closed for that smoke.

Still required before treating the pilot as publicly launched:

- Confirm the production host runbook, `.env`, service path, and selected data-refresh workflow.
- Keep the USB deploy evidence current on future production updates, including the project revision, health/readiness
  checks, and backup-gated mode when a fresh pre-update database dump is required.
- Keep the current Cloudflare Free-plan-compatible subset limited to a small operator-watched pilot; defer managed WAF,
  bot protection upgrades, and broader API burst-rate-limit controls until broader traffic or observed abuse risk.
- Keep the 2026-07-15 fresh backup/off-server copy evidence available for the final launch snapshot. Recurring scheduled
  backups, recurring off-server backup copies, and backup freshness monitoring are deferred until after the initial
  operator-watched pilot.
- Continue verifying the scheduled public-download-first refresh on the production host because the production pilot runs
  without a `COINMARKETCAP_API_KEY`; the 2026-07-11 update evidence proves update-time freshness, not future scheduled
  runs.
- Put request logging, backup health, and operational review in place.
- Keep the accepted small-pilot monitoring coverage active: Cloudflare Tunnel Health Alert plus external homepage
  availability monitoring. Dedicated external `/api/health` and `/api/readiness` freshness monitors, stale-data
  after-window alerting, and explicit alert delivery evidence remain pending before broader launch.
- Keep the 2026-07-15 manual/native browser QA and assistive-tech proxy QA evidence available for the final launch
  snapshot. Do not claim a true screen-reader/manual assistive-tech pass, full WCAG conformance, or legal accessibility
  approval.
- Complete the remaining launch operations and governance checklist: keep public-host privacy/terms/disclaimer and
  SEO/social metadata verification current after future deployments; keep the sanitized support/contact and account
  recovery evidence current without recording private details; record resource monitoring, dependency/security,
  data-source terms, accessibility, and incident response status according to the 2026-07-12 decision pass.
- Complete the remaining release feedback and operational evidence checklist: release notes or decision log, first-user
  feedback path after traffic, dependency-license review external/manual confirmation before broader commercial launch,
  final launch evidence, and restore-drill evidence after a safe target exists.
- Keep the documented bad-data correction and service-target policy current as real restore/import evidence arrives;
  pilot freshness, RPO/RTO, correction, and downtime targets remain internal targets, not public SLA promises.
- Capture a real production import evidence packet outside the repository: source snapshot, import manifest, `sha256`,
  retrieval metadata, row count, covered range, expected tail, validation/readiness output, cache evidence, and any
  related launch, restore, or correction note.
- Update external portfolio surfaces such as GitHub description/topics or the sibling product-ideas brief only by
  separate request; they were not changed by the tracked repository docs pass.
- Capture the launch snapshot and run the first small traffic test only after the remaining blockers are completed and
  the operator separately approves the run.

## Related Docs

- [Architecture](architecture.md)
- [Data Pipeline](data-pipeline.md)
- [Security and Privacy](security-and-privacy.md)
- [Operations](operations.md)
- [Ubuntu and Cloudflare Tunnel Deployment](deploy-ubuntu-cloudflare.md)
- [Testing and Quality](testing-and-quality.md)
