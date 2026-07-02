# Production Pilot Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish production-pilot readiness by closing the Phase 6-8 critical path and deferring Phase 9+ work until first-traffic evidence exists.

**Architecture:** Treat the product as already built and deployed enough for public smoke checks. Complete operational resilience first, then launch hygiene, then optional user-facing polish only if it does not delay the first traffic test. Keep the current `crypto-scout-canonical-v1` risk metric, public API shape, and production-pilot scope stable.

**Tech Stack:** FastAPI backend, React/Vite frontend, Python collector, TimescaleDB/PostgreSQL, Podman Compose, Cloudflare Tunnel/Rulesets, shell scripts in `scripts/` and `server-kit/`, Markdown docs.

---

## Priority Model

Use four buckets:

1. **P0 Launch Blocker:** must be completed before broader external exposure.
2. **P1 Strongly Recommended Before Traffic:** complete before active traffic unless explicitly deferred with a reason.
3. **P2 Product Polish:** valuable before traffic only if time allows.
4. **P3 Post-Launch Learning:** starts after first traffic produces evidence.

Do not start Phase 9+ product expansion until P0 is done and P1 is either done or deliberately deferred.

## File Structure

This master plan coordinates existing specs and docs. It should not add application code by itself.

- Modify during execution as evidence accumulates: `docs/production-roadmap.md`
- Modify during execution as launch gates close: `docs/production-readiness.md`
- Modify during execution for operator commands/evidence: `docs/operations.md`
- Modify after implementation freeze: `README.md`, `docs/README.md`, `docs/01-bitcoin-risk-brief.md`
- Reference specs:
  - `docs/superpowers/specs/2026-07-01-scheduled-public-cmc-refresh-design.md`
  - `docs/superpowers/specs/2026-07-01-usb-update-install-kit-v2-design.md`
  - `docs/superpowers/specs/2026-07-01-launch-operations-governance-checklist-design.md`
  - `docs/superpowers/specs/2026-07-01-release-feedback-operational-evidence-design.md`
  - `docs/superpowers/specs/2026-07-02-data-correction-service-targets-design.md`
  - `docs/superpowers/specs/2026-07-02-import-provenance-source-archive-design.md`
  - `docs/superpowers/specs/2026-07-01-localization-quality-language-expansion-design.md`
  - `docs/superpowers/specs/2026-07-01-price-model-input-ohlc-display-design.md`
  - `docs/superpowers/specs/2026-07-01-public-payload-cache-warmup-precompute-design.md`
  - `docs/superpowers/specs/2026-07-01-documentation-portfolio-presentation-design.md`

## Task 1: Push Current Documentation Baseline

**Priority:** P0

**Files:**
- No file edits expected.

- [ ] **Step 1: Verify clean local working tree**

Run:

```bash
git status --short --branch
```

Expected: no unstaged or staged files. The branch may be ahead of `origin/main`.

- [ ] **Step 2: Push documentation commits**

Run:

```bash
git push origin main
```

Expected: push succeeds and `origin/main` contains the latest documentation gates.

- [ ] **Step 3: Confirm branch sync**

Run:

```bash
git status --short --branch
```

Expected:

```text
## main...origin/main
```

## Task 2: Close Phase 6 Production Deployment Mechanics

**Priority:** P0

**Files:**
- Modify if implementation work is needed: `server-kit/`
- Modify if deploy docs change: `docs/deploy-ubuntu-cloudflare.md`
- Modify if operations commands change: `docs/operations.md`
- Update evidence: `docs/production-readiness.md`

- [ ] **Step 1: Validate compose configuration locally**

Run:

```bash
./scripts/manage.sh validate
```

Expected: compose configuration validates without errors.

- [ ] **Step 2: Verify current production public endpoints**

Run from a network that can reach the public hostname:

```bash
curl -fsS https://bitcoinriskbrief.minihub.app/api/health
curl -fsS https://bitcoinriskbrief.minihub.app/api/readiness
curl -fsS -D - https://bitcoinriskbrief.minihub.app/api/risk/latest -o /tmp/bitcoin-risk-latest.json
```

Expected:

- health returns `{"status":"ok"}`;
- readiness returns `status: ready`;
- latest risk response includes cache headers.

- [ ] **Step 3: Decide direct Git deploy vs USB deploy for next update**

Record the selected path in `docs/production-readiness.md`.

Expected decision:

- direct Git deploy if the server can safely pull from the repo;
- USB deploy if the local-server workflow is preferred.

- [ ] **Step 4: If USB deploy is selected, implement or verify USB kit v2 before using it**

Use `docs/superpowers/specs/2026-07-01-usb-update-install-kit-v2-design.md`.

Minimum evidence before using USB for production:

- filtered project snapshot excludes `.env`, `.git`, backups, dependency caches, build output, and container images;
- manifest and checksums are present;
- server update flow requires a backup before promotion.

- [ ] **Step 5: Update production readiness evidence**

Modify `docs/production-readiness.md` with:

- selected deployment path;
- public endpoint smoke result date;
- accepted Cloudflare Free-plan limitations;
- any remaining Phase 6 blockers.

## Task 3: Implement Phase 7 Backup, Restore, Monitoring, And Recovery Evidence

**Priority:** P0

**Files:**
- Modify if scripts need adjustment: `scripts/backup.sh`
- Modify if operational docs change: `docs/operations.md`
- Update evidence: `docs/production-readiness.md`, `docs/production-roadmap.md`

- [ ] **Step 1: Run a production backup**

On the production host, from the deployed project directory:

```bash
./scripts/backup.sh
```

Expected: a timestamped backup directory contains PostgreSQL dump, canonical BTC CSV copy, and manifest.

- [ ] **Step 2: Copy backup off the server**

Use the selected off-server storage path.

Expected: backup exists outside the production server and can be listed from the destination.

- [ ] **Step 3: Run a restore drill into staging or an empty database**

Use the restore commands documented in `docs/operations.md`.

Expected: restored database contains BTC OHLCV rows, risk rows, validation row, and brief snapshot.

- [ ] **Step 4: Configure readiness and health monitoring**

Minimum checks:

- `/api/health` uptime monitor;
- `/api/readiness` production gate monitor;
- stale readiness alert after the nightly update window;
- collector refresh failure alert from logs or scheduled job status.

- [ ] **Step 5: Create import provenance evidence for the current production CSV**

Use `docs/superpowers/specs/2026-07-02-import-provenance-source-archive-design.md`.

Minimum evidence:

- source type and retrieval method;
- UTC import timestamp;
- source or canonical CSV `sha256`;
- row count;
- covered start/end;
- expected tail date;
- readiness payload;
- cache headers.

- [ ] **Step 6: Record data correction and service target posture**

Use `docs/superpowers/specs/2026-07-02-data-correction-service-targets-design.md`.

Expected evidence:

- low/medium/high issue classification exists;
- correction flow references known-good CSV/backup;
- temporary downtime is accepted over knowingly serving a wrong risk value;
- pilot RPO/RTO boundaries are internal, not public SLA promises.

- [ ] **Step 7: Update Phase 7 status**

Modify `docs/production-roadmap.md` and `docs/production-readiness.md`.

Expected: Phase 7 moves from `Pending` to either `Complete` or `Complete with accepted limitations`.

## Task 4: Complete Phase 8 Launch Gates

**Priority:** P0

**Files:**
- Modify as evidence accumulates: `docs/production-readiness.md`
- Modify if privacy/security posture changes: `docs/security-and-privacy.md`
- Modify if testing notes change: `docs/testing-and-quality.md`, `docs/frontend-qa.md`

- [ ] **Step 1: Run waitlist production smoke**

Submit one deliberate test contact through the public UI or API.

Expected:

- response is not cached;
- row is stored server-side;
- no contact value is written into public logs or docs.

- [ ] **Step 2: Run desktop/mobile browser QA on public hostname**

Use `docs/frontend-qa.md`.

Expected:

- public page loads;
- chart renders;
- latest risk/freshness state is visible;
- waitlist form works;
- no mobile layout clipping or overlapping content.

- [ ] **Step 3: Complete launch governance checklist**

Use `docs/superpowers/specs/2026-07-01-launch-operations-governance-checklist-design.md`.

Minimum decisions:

- privacy/terms/disclaimer posture;
- waitlist handling owner;
- contact deletion/unsubscribe path;
- credential/account ownership;
- data-source terms and attribution;
- accessibility and metadata pass;
- incident response first steps.

- [ ] **Step 4: Complete release feedback and evidence checklist**

Use `docs/superpowers/specs/2026-07-01-release-feedback-operational-evidence-design.md`.

Expected:

- decision log or release note exists;
- first-user feedback review path is defined;
- support/contact path is defined;
- dependency-license review is recorded;
- launch/backup/restore evidence is linked.

- [ ] **Step 5: Capture launch snapshot**

Record in `docs/production-readiness.md`:

- commit hash;
- public hostname;
- latest BTC data date;
- readiness payload;
- cache headers;
- waitlist smoke result without contact value;
- browser/device QA result;
- selected data refresh path;
- selected deployment path;
- backup and restore evidence.

- [ ] **Step 6: Decide whether to defer optional Phase 8 polish**

Use this rule:

- defer if it delays traffic or touches risky shared behavior;
- implement only if small, tested, and trust-improving.

Candidate optional polish:

- localization EN/RU copy polish and ES/DE support;
- first-viewport `Model price`, `Low`, and `High`;
- cache warmup if MISS latency is user-visible;
- final portfolio README pass after implementation freeze.

## Task 5: Optional Phase 8 Product Polish

**Priority:** P1/P2 depending on effort

**Files:**
- Potential frontend changes: `frontend/src/`
- Potential backend/API changes: `backend/app/`, `collector/collector/`
- Potential docs: `docs/api-reference.md`, `docs/frontend-qa.md`, `docs/production-roadmap.md`

- [ ] **Step 1: Choose at most one polish item before traffic**

Recommended order:

1. EN/RU copy polish if visible trust issues exist.
2. `Model price`/`Low`/`High` if current HLC3 labeling feels misleading.
3. ES/DE localization if copy and QA time are available.
4. Cache warmup only if measured MISS latency is user-visible.

- [ ] **Step 2: Write a dedicated implementation plan before code**

Create a separate plan under `docs/superpowers/plans/`.

Expected: the plan names exact files, tests, commands, and commits for that one polish item.

- [ ] **Step 3: Implement with tests and build checks**

Use the relevant commands:

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
```

Expected: commands relevant to touched code pass.

## Task 6: First Traffic Test

**Priority:** P0 after Tasks 1-4

**Files:**
- Update evidence: `docs/production-roadmap.md`, `docs/production-readiness.md`
- Update learnings later: `docs/01-bitcoin-risk-brief.md`

- [ ] **Step 1: Start controlled traffic**

Use a small, known source of users.

Expected: traffic source can be identified in logs, Cloudflare analytics, or waitlist `source`.

- [ ] **Step 2: Review after the first traffic window**

Measure:

- visits;
- repeat-use estimate;
- waitlist conversion;
- endpoint demand;
- direct questions;
- requests for alerts/API/agents/widgets/licensing.

- [ ] **Step 3: Convert evidence into Phase 9 decision**

Choose one:

- no expansion yet;
- improve launch funnel/copy;
- test alerts or daily brief;
- publish Agent Access Pack using existing endpoints;
- test `EUR 9-19/month` risk-signal license;
- design API client usage tracking.

## Task 7: Defer Phase 9+ Work Until Evidence Exists

**Priority:** P3

**Files:**
- No immediate code edits.
- Future docs/plans only after evidence exists.

- [ ] **Step 1: Keep these deferred until first traffic evidence**

Do not implement before Task 6:

- new paid API;
- API keys;
- billing;
- widgets;
- Telegram Mini App;
- browser extensions;
- methodology v2;
- on-chain data pipeline;
- Fear & Greed integration into core metric;
- public status page;
- admin dashboard.

- [ ] **Step 2: Apply gates before any deferred work**

Use the relevant specs:

- `2026-06-30-agent-access-demand-test-design.md`
- `2026-07-01-product-analytics-usage-attribution-design.md`
- `2026-07-01-risk-methodology-research-design.md`
- `2026-07-01-distribution-channel-research-design.md`
- `2026-07-01-email-paid-beta-trust-gates-design.md`
- `2026-07-02-api-db-change-management-design.md`

Expected: each future implementation has its own dedicated implementation plan before code.

## Recommended Execution Order

1. Push current docs.
2. Close Phase 6 deployment path and evidence.
3. Complete Phase 7 backups, restore drill, monitoring, provenance, and correction posture.
4. Complete Phase 8 launch gates and launch snapshot.
5. Implement at most one optional Phase 8 polish item if it is cheap and trust-improving.
6. Run first traffic test.
7. Review evidence and choose one Phase 9 experiment.

## Stop Conditions

Stop and ask for a decision if:

- production restore drill fails;
- public readiness becomes degraded;
- waitlist smoke fails;
- production data freshness exceeds the accepted window;
- source provenance cannot be captured for launch data;
- a planned polish item requires risky API/DB changes before traffic.

## Verification

Before marking the production pilot ready for traffic, run or record:

```bash
git status --short --branch
./scripts/manage.sh validate
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
curl -fsS https://bitcoinriskbrief.minihub.app/api/health
curl -fsS https://bitcoinriskbrief.minihub.app/api/readiness
curl -fsS -D - https://bitcoinriskbrief.minihub.app/api/risk/latest -o /tmp/bitcoin-risk-latest.json
```

Expected:

- local branch state is understood;
- compose config validates;
- touched backend/collector/frontend checks pass;
- public health/readiness/latest risk are reachable;
- launch evidence records any command that could not be run and why.
