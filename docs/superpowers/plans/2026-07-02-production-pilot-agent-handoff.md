# Production Pilot Agent Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Bitcoin Risk Brief production-pilot readiness by executing one small, verifiable task at a time.

**Architecture:** The product is already implemented as a Podman Compose stack with TimescaleDB, collector, FastAPI backend, and React/Vite frontend. This plan keeps `crypto-scout-canonical-v1`, the current public API, and the one-page BTC risk product stable while closing deployment, backup, monitoring, launch-evidence, and first-traffic gates.

**Tech Stack:** FastAPI, Python collector, TimescaleDB/PostgreSQL, React/Vite, Podman Compose, Cloudflare Tunnel/Rulesets, Bash scripts, Markdown documentation.

---

## Execution Rules For Every Agent Task

- Start by reading `AGENTS.md`, `README.md`, `docs/README.md`, and the task-specific docs listed below.
- Preserve user or previous-agent changes. Do not run destructive git commands.
- For behavior changes, use TDD and update focused tests before implementation.
- For docs-only changes, verify with `git diff -- docs/...` and a targeted read of edited sections.
- Before finalizing, run the verification command named in the task or explain exactly why it could not run.
- Keep Phase 9+ expansion deferred until first-traffic evidence exists.

## Current Priority Order

1. P0: repo baseline and production path evidence.
2. P0: autonomous data freshness if production has no `COINMARKETCAP_API_KEY`.
3. P0: backups, off-server copy, restore drill, monitoring, provenance, and correction policy.
4. P0: launch smoke checks, browser QA, governance, and launch snapshot.
5. P1: cache-miss latency measurement and warmup only if needed.
6. P2: one optional product-polish item at most.
7. P0 after gates: first controlled traffic test.
8. P3: Phase 9 decision from evidence.

## Task 1: Baseline Sync And Public Smoke Evidence

**Priority:** P0

**Files:**
- Read: `docs/production-readiness.md`
- Read: `docs/production-roadmap.md`
- Modify: `docs/production-readiness.md`

- [ ] **Step 1: Check local branch state**

Run:

```bash
git status --short --branch
```

Expected: branch state is understood. If local commits are ahead of `origin/main`, report them before pushing.

- [ ] **Step 2: Push current documentation baseline if approved by the operator**

Run only after confirming the intended branch is `main`:

```bash
git push origin main
```

Expected: push succeeds. If network access or credentials block the push, record the blocker in the final task report.

- [ ] **Step 3: Smoke public endpoints**

Run:

```bash
curl -fsS https://bitcoinriskbrief.minihub.app/api/health
curl -fsS https://bitcoinriskbrief.minihub.app/api/readiness
curl -fsS -D - https://bitcoinriskbrief.minihub.app/api/risk/latest -o /tmp/bitcoin-risk-latest.json
```

Expected:

- health returns `{"status":"ok"}`;
- readiness returns HTTP 200 with `status: ready`;
- latest risk response includes `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`.

- [ ] **Step 4: Record evidence**

Update `docs/production-readiness.md` with a dated subsection under the current public pilot snapshot containing:

- command date;
- public hostname;
- readiness status;
- latest data date and covered end;
- latest risk cache headers;
- any accepted Cloudflare Free-plan limitation still present.

- [ ] **Step 5: Verify docs-only change**

Run:

```bash
git diff -- docs/production-readiness.md
```

Expected: diff contains only the new evidence note.

## Task 2: Select And Record Deployment Path

**Priority:** P0

**Files:**
- Read: `docs/deploy-ubuntu-cloudflare.md`
- Read: `docs/server-msi-cubi5-ubuntu-26.04.md`
- Read: `server-kit/README-RUN-ON-SERVER.md`
- Modify: `docs/production-readiness.md`
- Modify if needed: `docs/operations.md`

- [ ] **Step 1: Identify current production service path**

On the production host or from operator evidence, determine whether the deployed project lives under `/opt/bitcoin-risk-brief` or `/srv/projects/bitcoin-risk-brief`.

Expected: one active path is named.

- [ ] **Step 2: Choose update path**

Record one decision:

- direct Git deploy under `/opt/bitcoin-risk-brief`; or
- USB deploy under `/srv/projects/bitcoin-risk-brief`.

Expected: the selected path matches how the operator can realistically update the server.

- [ ] **Step 3: Update docs**

In `docs/production-readiness.md`, add a dated note with:

- selected deployment path;
- production project directory;
- whether USB kit v2 is required before the next update;
- whether the current `.env` location and owner are known.

- [ ] **Step 4: Verify**

Run:

```bash
git diff -- docs/production-readiness.md docs/operations.md
```

Expected: docs now state the selected deployment path and remaining deployment blockers.

## Task 3: Implement Scheduled Public CMC Refresh If No API Key Is Used

**Priority:** P0 when production `COINMARKETCAP_API_KEY` is empty

**Files:**
- Read: `docs/superpowers/specs/2026-07-01-scheduled-public-cmc-refresh-design.md`
- Modify: `collector/collector/main.py`
- Modify if needed: `collector/collector/config.py`
- Modify if needed: `collector/collector/public_cmc_download.py`
- Test: `collector/tests/test_public_cmc_download.py`
- Add or modify focused scheduler tests under `collector/tests/`
- Modify docs: `docs/data-pipeline.md`, `docs/operations.md`, `docs/production-readiness.md`

- [ ] **Step 1: Write failing collector tests**

Add tests proving scheduled runs with empty `COINMARKETCAP_API_KEY`:

- calculate the last completed UTC day;
- call the public CoinMarketCap download path when the CSV tail is stale;
- import/recompute without download when the CSV already covers the target date;
- leave the canonical CSV unchanged when public download fails;
- use optional API fallback only when an API key is configured.

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -v
```

Expected: new tests fail before implementation for the missing scheduled public-download behavior.

- [ ] **Step 2: Implement minimal scheduled strategy**

Implement the strategy from the spec:

1. target end date is the last completed UTC day;
2. public CMC download is first choice when the CSV is stale;
3. optional official API fallback is used only when configured;
4. failed refresh does not rewrite the canonical CSV;
5. successful path imports full CSV, recomputes risk, writes validation and brief, and cleans stale DB rows.

- [ ] **Step 3: Verify tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -v
./scripts/manage.sh test-python
python3 -m compileall backend collector
```

Expected: collector and Python checks pass.

- [ ] **Step 4: Update docs**

Remove or revise notes saying scheduled no-key refresh is not implemented. Keep manual `import-cmc-csv` as fallback.

- [ ] **Step 5: Verify docs and compose**

Run:

```bash
./scripts/manage.sh validate
git diff -- collector docs
```

Expected: compose validates; diff is limited to scheduled refresh code, tests, and docs.

## Task 4: Backup, Off-Server Copy, And Restore Drill Evidence

**Priority:** P0

**Files:**
- Read: `docs/operations.md`
- Read: `docs/production-readiness.md`
- Modify: `docs/production-readiness.md`
- Modify if commands change: `docs/operations.md`

- [ ] **Step 1: Run production backup**

On the production host, run from the deployed project directory:

```bash
./scripts/backup.sh
```

Expected: backup directory contains PostgreSQL dump, canonical BTC CSV copy, `manifest.txt`, and `SHA256SUMS`.

- [ ] **Step 2: Copy backup off-server**

Copy the backup to the chosen off-server storage.

Expected: off-server destination can list the backup and checksum file.

- [ ] **Step 3: Restore into staging or empty database**

Use the restore flow in `docs/operations.md`.

Expected after restore:

```bash
curl -fsS http://127.0.0.1:3001/api/readiness
```

returns ready in the staging or restored environment.

- [ ] **Step 4: Record redacted evidence**

Update `docs/production-readiness.md` with:

- backup command date;
- backup artifact categories, not secret paths if sensitive;
- off-server copy confirmation;
- restore drill result;
- any warning or accepted limitation.

- [ ] **Step 5: Verify**

Run:

```bash
git diff -- docs/production-readiness.md docs/operations.md
```

Expected: docs contain evidence without `.env` values, waitlist contacts, secrets, or raw backup contents.

## Task 5: Monitoring And First-Response Runbook

**Priority:** P0

**Files:**
- Read: `docs/operations.md`
- Read: `docs/security-and-privacy.md`
- Modify: `docs/operations.md`
- Modify: `docs/production-readiness.md`

- [ ] **Step 1: Define active monitoring**

Record the actual monitor choices for:

- public `/api/health`;
- public `/api/readiness`;
- stale readiness after nightly update window;
- collector refresh failure;
- backup freshness;
- Cloudflare Tunnel health.

- [ ] **Step 2: Add first-response entries**

In `docs/operations.md`, ensure each incident entry names:

- where to look first;
- exact command or dashboard to check;
- first safe action;
- when to stop promotion or take the product offline.

Cover readiness degradation, public CMC download failure, waitlist failure, stale cache, backup failure, disk pressure, and Cloudflare Tunnel outage.

- [ ] **Step 3: Record production status**

In `docs/production-readiness.md`, add whether monitoring is configured, partially configured, or accepted as a limitation for first traffic.

- [ ] **Step 4: Verify**

Run:

```bash
git diff -- docs/operations.md docs/production-readiness.md
```

Expected: runbook is operator-actionable and does not contain secrets.

## Task 6: Import Provenance And Bad-Data Correction Policy

**Priority:** P0

**Files:**
- Read: `docs/superpowers/specs/2026-07-02-import-provenance-source-archive-design.md`
- Read: `docs/superpowers/specs/2026-07-02-data-correction-service-targets-design.md`
- Modify: `docs/data-pipeline.md`
- Modify: `docs/operations.md`
- Modify: `docs/production-readiness.md`

- [ ] **Step 1: Create one sample import evidence packet outside the repository**

Capture:

- source type and retrieval method;
- UTC import timestamp;
- git commit;
- command used;
- source or canonical CSV `sha256`;
- row count;
- covered start and end date;
- expected tail date;
- readiness payload;
- cache headers for `/api/risk/latest`.

Expected: evidence is stored outside the repo and contains no secrets or PII.

- [ ] **Step 2: Add provenance procedure to operations docs**

In `docs/operations.md`, add the exact fields operators must capture for future production imports and where artifacts must not be stored.

- [ ] **Step 3: Add correction policy**

In `docs/operations.md`, add low/medium/high classification and the correction flow:

1. record observed wrong value/date;
2. inspect readiness, validation, logs, and CSV tail;
3. stop further automated imports if needed;
4. restore or re-import known-good CSV;
5. recompute risk and brief;
6. verify origin and edge cache;
7. capture correction note.

- [ ] **Step 4: Update production readiness**

Record whether provenance and correction posture are complete or accepted with limitations.

- [ ] **Step 5: Verify**

Run:

```bash
git diff -- docs/data-pipeline.md docs/operations.md docs/production-readiness.md
```

Expected: docs align with specs and keep pilot targets internal, not public SLA promises.

## Task 7: Production Waitlist Smoke

**Priority:** P0

**Files:**
- Read: `docs/waitlist.md`
- Read: `docs/security-and-privacy.md`
- Modify: `docs/production-readiness.md`

- [ ] **Step 1: Submit a deliberate test lead**

Use the public UI or API. If using API, run with an operator-controlled contact:

```bash
curl -sD - -o /tmp/bitcoin-risk-waitlist.json \
  -H 'Content-Type: application/json' \
  -X POST https://bitcoinriskbrief.minihub.app/api/waitlist \
  --data '{"contact":"operator-test@example.com","locale":"en","source":"launch_smoke"}'
```

Expected: response status is `201` or a valid duplicate/upsert success; headers include `Cache-Control: no-store`.

- [ ] **Step 2: Verify server-side storage**

On production host, inspect `waitlist_leads` without copying the contact value into docs.

Expected: one row exists for the normalized test contact and source/locale are correct.

- [ ] **Step 3: Record redacted evidence**

Update `docs/production-readiness.md` with:

- smoke date;
- response status;
- no-store header result;
- storage verification result;
- statement that the contact value is omitted from docs.

- [ ] **Step 4: Verify**

Run:

```bash
git diff -- docs/production-readiness.md
```

Expected: no PII appears in the diff.

## Task 8: Browser And Device QA On Public Hostname

**Priority:** P0

**Files:**
- Read: `docs/frontend-qa.md`
- Modify: `docs/frontend-qa.md`
- Modify: `docs/production-readiness.md`

- [ ] **Step 1: Run automated frontend checks locally if dependencies are available**

Run:

```bash
npm test --prefix frontend
npm run build --prefix frontend
npm run smoke --prefix frontend
```

Expected: commands pass. If browser install or sandbox blocks smoke checks, record the blocker.

- [ ] **Step 2: Run manual public-hostname QA**

Check public page on available desktop and mobile browsers. Cover:

- latest risk visible;
- readiness/freshness visible;
- risk history chart non-empty;
- risk levels chart non-empty;
- waitlist form states;
- EN/RU locale switch;
- no horizontal overflow or text overlap on mobile.

- [ ] **Step 3: Record results**

Update `docs/frontend-qa.md` with date, hostname, browsers/devices, result, and accepted limitations.

Update `docs/production-readiness.md` with a short launch-gate result.

- [ ] **Step 4: Verify**

Run:

```bash
git diff -- docs/frontend-qa.md docs/production-readiness.md
```

Expected: QA result is clear enough to support launch decision.

## Task 9: Launch Governance And Release Evidence

**Priority:** P0

**Files:**
- Read: `docs/superpowers/specs/2026-07-01-launch-operations-governance-checklist-design.md`
- Read: `docs/superpowers/specs/2026-07-01-release-feedback-operational-evidence-design.md`
- Modify: `docs/security-and-privacy.md`
- Modify: `docs/operations.md`
- Modify: `docs/production-readiness.md`
- Modify if needed: `docs/testing-and-quality.md`

- [ ] **Step 1: Record governance decisions**

Document:

- privacy/terms/disclaimer posture;
- waitlist lead owner and review cadence;
- deletion or unsubscribe contact path;
- credential/account ownership categories;
- data-source terms review status;
- dependency/security maintenance cadence;
- accessibility and metadata pass status.

- [ ] **Step 2: Record release evidence process**

Document:

- launch commit;
- methodology version;
- data refresh path;
- known accepted limitations;
- first-user feedback review path;
- support/contact identity;
- dependency-license review status.

- [ ] **Step 3: Verify docs**

Run:

```bash
git diff -- docs/security-and-privacy.md docs/operations.md docs/production-readiness.md docs/testing-and-quality.md
```

Expected: docs describe launch posture without implying paid SLA, legal certification, or investment advice.

## Task 10: Launch Snapshot

**Priority:** P0

**Files:**
- Modify: `docs/production-readiness.md`
- Modify: `docs/production-roadmap.md`

- [ ] **Step 1: Collect launch facts**

Run:

```bash
git rev-parse HEAD
curl -fsS https://bitcoinriskbrief.minihub.app/api/readiness
curl -sD - -o /tmp/bitcoin-risk-latest.json https://bitcoinriskbrief.minihub.app/api/risk/latest
```

Expected: commit hash, readiness payload, and cache headers are available.

- [ ] **Step 2: Add launch snapshot**

In `docs/production-readiness.md`, record:

- commit hash;
- public hostname;
- latest BTC data date;
- readiness payload summary;
- cache header summary;
- waitlist smoke result;
- browser QA result;
- selected deployment path;
- selected data refresh path;
- latest backup and restore evidence;
- accepted limitations.

- [ ] **Step 3: Update roadmap status**

Move Phase 6-8 statuses to the exact current state: complete, complete with accepted limitations, or still blocked.

- [ ] **Step 4: Verify**

Run:

```bash
git diff -- docs/production-readiness.md docs/production-roadmap.md
```

Expected: launch readiness is readable without consulting private command history.

## Task 11: Cache MISS Latency Measurement

**Priority:** P1

**Files:**
- Read: `docs/superpowers/specs/2026-07-01-public-payload-cache-warmup-precompute-design.md`
- Modify if recording only: `docs/production-readiness.md`
- Create a separate implementation plan before code if warmup is needed.

- [ ] **Step 1: Measure public read endpoints**

Measure `MISS` and `HIT` timing for:

- `/api/readiness`;
- `/api/risk/latest`;
- `/api/risk/history?limit=2000`;
- `/api/risk/levels`;
- `/api/brief/latest`.

Use curl timing and response headers:

```bash
curl -sD - -o /tmp/bitcoin-risk-levels.json -w 'time_total=%{time_total}\n' https://bitcoinriskbrief.minihub.app/api/risk/levels
```

Expected: timing and `X-Cache` are recorded.

- [ ] **Step 2: Decide**

If first MISS latency is not user-visible, record accepted decision and do not implement warmup.

If MISS latency is user-visible, create a dedicated plan under `docs/superpowers/plans/` for backend public cache warmup with tests.

- [ ] **Step 3: Verify docs-only decision**

Run:

```bash
git diff -- docs/production-readiness.md
```

Expected: latency decision is explicit.

## Task 12: Optional Product Polish Gate

**Priority:** P2

**Files:**
- No direct code edits in this task.
- Create a separate plan before any chosen polish implementation.

- [ ] **Step 1: Choose at most one polish item before first traffic**

Pick one only:

1. EN/RU copy polish.
2. `Model price`, `Low`, and `High` first-viewport display.
3. ES/DE localization.
4. Backend cache warmup if Task 11 proves it is needed.

- [ ] **Step 2: Write dedicated implementation plan**

Create a separate plan with exact files, tests, and verification commands.

Expected: no product-polish code is changed without its own plan.

- [ ] **Step 3: Stop if risky**

Defer the polish item if it requires broad API/DB changes, threatens launch timing, or cannot be verified with focused tests.

## Task 13: First Controlled Traffic Test

**Priority:** P0 after Tasks 1-10

**Files:**
- Modify: `docs/production-roadmap.md`
- Modify: `docs/production-readiness.md`
- Modify after review: `docs/01-bitcoin-risk-brief.md`

- [ ] **Step 1: Start small traffic**

Use one known source of users. Make sure the source can be identified through Cloudflare analytics, access logs, URL/source values, or waitlist source.

- [ ] **Step 2: Review after traffic window**

Measure:

- visits;
- repeat-use estimate;
- waitlist conversion;
- endpoint demand;
- direct questions;
- requests for alerts, API, agents, widgets, or licensing.

- [ ] **Step 3: Record evidence and decision**

Update docs with a concise first-traffic review and choose exactly one next move:

- no expansion yet;
- improve copy/funnel;
- test alerts or daily brief;
- publish Agent Access Pack using existing endpoints;
- test `EUR 9-19/month` risk-signal license;
- design privacy-preserving analytics or API client usage tracking.

## Task 14: Phase 9 Gate Before Any Expansion

**Priority:** P3

**Files:**
- Read relevant spec before planning:
  - `docs/superpowers/specs/2026-06-30-agent-access-demand-test-design.md`
  - `docs/superpowers/specs/2026-07-01-product-analytics-usage-attribution-design.md`
  - `docs/superpowers/specs/2026-07-01-email-paid-beta-trust-gates-design.md`
  - `docs/superpowers/specs/2026-07-02-api-db-change-management-design.md`
  - `docs/superpowers/specs/2026-07-01-risk-methodology-research-design.md`
  - `docs/superpowers/specs/2026-07-01-distribution-channel-research-design.md`

- [ ] **Step 1: Confirm evidence trigger**

Do not implement API keys, billing, widgets, Telegram Mini App, browser extension, methodology v2, Fear & Greed core integration, on-chain pipeline, admin dashboard, or public status page unless first-traffic evidence justifies it.

- [ ] **Step 2: Create a focused plan**

For the chosen Phase 9 experiment, create a new implementation plan under `docs/superpowers/plans/` with:

- goal;
- exact scope;
- non-goals;
- files;
- tests;
- verification commands;
- rollback and docs requirements.

- [ ] **Step 3: Apply API/DB gate if needed**

If the experiment changes endpoint contracts, cache semantics, schema, retention, PII, analytics, API clients, or paid access, classify the change as additive, risky, or breaking before code.

## Final Verification Before Declaring Ready For Traffic

Run or record why each command could not run:

```bash
git status --short --branch
./scripts/manage.sh validate
./scripts/manage.sh test-python
python3 -m compileall backend collector
npm test --prefix frontend
npm run build --prefix frontend
curl -fsS https://bitcoinriskbrief.minihub.app/api/health
curl -fsS https://bitcoinriskbrief.minihub.app/api/readiness
curl -fsS -D - https://bitcoinriskbrief.minihub.app/api/risk/latest -o /tmp/bitcoin-risk-latest.json
```

Expected:

- branch state is understood;
- local checks relevant to touched files pass;
- public health, readiness, and latest risk are reachable;
- launch evidence records backup, restore, waitlist, browser QA, provenance, cache, and monitoring status;
- Phase 9 work remains deferred until first-traffic evidence exists.
