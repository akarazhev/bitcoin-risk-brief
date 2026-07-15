# Documentation And Portfolio Presentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the repository README and core documentation so the private or portfolio presentation reflects the current local implementation state without claiming production launch readiness.

**Architecture:** This is a documentation-only consistency pass across the root README, core docs, deployment and operations runbooks, and the `docs/superpowers/` archive index. Core runtime docs remain authoritative over historical specs, and local-complete tags are treated as local implementation evidence only. Production deploy is unavailable, public freshness remains blocked, and the docs must keep those blockers visible.

**Tech Stack:** Markdown documentation, FastAPI API contract docs, React/Vite frontend QA docs, TimescaleDB and Podman Compose operations docs, Cloudflare deployment notes, USB server-kit docs, `rg`, `git diff`, and `git diff --check`.

---

## Current State Anchors

- Initial repository status for this planning goal: `git status --short --branch` returned `## main...origin/main` with no short-status file changes.
- Local completion tags are present:
  - `cache-warmup-local-complete-2026-07-05` at `975c173535822ad4f20630e42fa26e2a316fc40d`.
  - `usb-kit-v2-local-complete-2026-07-05` at `158b6838c225cf9e6b3e265950e222e1b6867c5c`.
  - `price-model-ohlc-local-complete-2026-07-06` at `81dfad07668c7c3c78e0ed4f483a298c989f4933`.
- Treat those tags as local repository evidence, not proof that production has been updated.
- Production deploy is unavailable from the current agent environment.
- Public freshness remains blocked: existing readiness notes show public `/api/readiness` degraded because latest production BTC data was stale.
- Do not commit or push during implementation unless the user gives a separate explicit command.

## Exact Files Likely To Change

- Modify: `README.md` - current-state product and engineering overview, status language, cache warmup, OHLC price fields, USB kit v2 status, blockers, and documentation links.
- Modify: `docs/README.md` - documentation index wording and source-of-truth guidance.
- Modify: `docs/production-roadmap.md` - roadmap phase/status reconciliation after local cache warmup, USB kit v2, and price-model OHLC work.
- Modify: `docs/production-readiness.md` - launch gate status, public freshness blocker, local implementation evidence, and no-launch-ready framing.
- Modify: `docs/operations.md` - operator runbook consistency for `warm-public-cache`, USB kit v2, no-key refresh, production blockers, and hygiene.
- Modify: `docs/deploy-ubuntu-cloudflare.md` - deployment path consistency for `/srv/projects/bitcoin-risk-brief`, USB kit v2, scheduled public refresh status, and Cloudflare/production blockers.
- Modify: `docs/data-pipeline.md` - only if the refresh and readiness wording needs alignment with operations/readiness docs.
- Modify: `docs/api-reference.md` - API response shape consistency for `model_price_usd`, `low_usd`, `high_usd`, history exclusions, and public cache warmup semantics.
- Modify: `docs/frontend-qa.md` - only if the first-viewport OHLC display and public QA limitations need current-state wording; do not invent new QA results.
- Modify: `docs/testing-and-quality.md` - documentation-only verification guidance, cache warmup test coverage wording, USB kit test coverage wording, and no-runtime-tests guidance for docs-only changes.
- Modify: `docs/security-and-privacy.md` - only if the secret/artifact hygiene and launch governance wording needs alignment with the presentation pass.
- Modify: `docs/superpowers/README.md` - archive index status for local-complete cache warmup, USB kit v2, price-model OHLC, and this plan.
- No repository file: GitHub repository description and topics are repository settings, not tracked files. Record recommended values in the final implementation report or a docs note only if the user asks.
- Do not modify: `<external-product-brief-path>` unless the user explicitly requests that external workspace update.

## Non-Goals

- No production deploy.
- No launch-ready, production-ready, or publicly-launched claim while public freshness remains blocked.
- No open-source community scaffolding such as `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, public issue templates, or public support policy.
- No `product-ideas` external file update unless explicitly requested.
- No runtime code, API behavior, database schema, frontend behavior, or Cloudflare configuration changes.
- No commit or push without a separate explicit command.

## Implementation Tasks

### Task 1: Pre-Edit Current-State Scan

**Files:**
- Read: `README.md`
- Read: `docs/README.md`
- Read: `docs/production-roadmap.md`
- Read: `docs/production-readiness.md`
- Read: `docs/operations.md`
- Read: `docs/deploy-ubuntu-cloudflare.md`
- Read: `docs/data-pipeline.md`
- Read: `docs/api-reference.md`
- Read: `docs/frontend-qa.md`
- Read: `docs/testing-and-quality.md`
- Read: `docs/security-and-privacy.md`
- Read: `docs/superpowers/README.md`

- [ ] **Step 1: Confirm the worktree and local tags before editing**

Run:

```bash
git status --short --branch
git tag --list cache-warmup-local-complete-2026-07-05 usb-kit-v2-local-complete-2026-07-05 price-model-ohlc-local-complete-2026-07-06
git show-ref --tags cache-warmup-local-complete-2026-07-05 usb-kit-v2-local-complete-2026-07-05 price-model-ohlc-local-complete-2026-07-06
```

Expected:

```text
## main...origin/main
cache-warmup-local-complete-2026-07-05
price-model-ohlc-local-complete-2026-07-06
usb-kit-v2-local-complete-2026-07-05
```

- [ ] **Step 2: Locate stale status and presentation phrases**

Run:

```bash
rg -n "Future-facing|future-facing|planned|if implemented|until the public-download-first scheduler is implemented|launch-ready|production-ready|publicly launched|product-ideas|CONTRIBUTING|CODE_OF_CONDUCT|issue templates" README.md docs
```

Expected: matches are reviewed one by one. Keep legitimate future-facing items for Phase 9+ and historical specs. Revise matches that describe already implemented local cache warmup, USB kit v2, price-model OHLC display, or scheduled public refresh as merely future work.

- [ ] **Step 3: Locate cache warmup and OHLC references**

Run:

```bash
rg -n "warm-public-cache|warm_public_cache|PUBLIC_BASE_URL|model_price_usd|low_usd|high_usd|price_usd|Model price|Low|High" README.md docs backend frontend scripts server-kit
```

Expected: docs and implementation references agree that latest risk exposes explicit `model_price_usd`, `low_usd`, and `high_usd`; history does not include latest-only OHLC aliases; `warm-public-cache` is a local/private origin operator command for standard public read endpoints.

### Task 2: README Current-State Refresh

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite the status section around current reality**

Edit `README.md` so `## Current Status` says all of the following clearly:

- The repository has local implementations for public cache warmup, USB kit v2, and first-viewport OHLC/model-price polish.
- The public hostname exists in historical smoke evidence, but public freshness is currently blocked and launch readiness must not be claimed.
- Production deploy/update is unavailable from the current workspace and still requires operator action.
- The remaining external blockers include fresh production data/readiness 200, production USB update or selected deploy path verification, backups/off-server copy/restore drill, monitoring alerts, waitlist smoke, production import provenance, browser/device/accessibility checks, and first traffic.

Use wording close to:

```markdown
## Current Status

Bitcoin Risk Brief is locally implementation-complete for the current pre-traffic hardening items: public payload cache warmup, USB Update And Install Kit V2, and first-viewport model-price/OHLC display polish. These are local repository states, not proof that production has been updated.

The public pilot hostname has historical smoke-test evidence, but the current launch posture remains blocked by production data freshness until public `/api/readiness` returns HTTP 200 again. Do not treat the project as publicly launched or launch-ready until the remaining production operations gates are completed or explicitly accepted.
```

Adjust details to fit the existing README style; do not add broad marketing language.

- [ ] **Step 2: Align product surface and API overview**

Make the product surface mention the first-viewport price display accurately:

- `Model price` is the HLC3 value for the latest completed daily candle.
- `Low` and `High` are daily candle values when the matching OHLCV row exists.
- No copy should imply live spot price or close-only price.

Keep the API endpoint list unchanged unless code proves an endpoint changed.

- [ ] **Step 3: Add cache warmup and USB kit v2 to operational summary without overclaiming**

In `README.md`, add or revise concise bullets so a reviewer sees:

- standard public read payloads can be warmed by `PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache` after readiness is healthy;
- USB kit v2 packages a filtered project snapshot and update wrapper, but it does not include production secrets, container images, dependency caches, backups, or a full offline package mirror;
- production benefit for both items still requires deployment/operator execution.

- [ ] **Step 4: Check the README diff**

Run:

```bash
git diff -- README.md
```

Expected: only documentation wording changed; no launch-ready claim was introduced.

### Task 3: Documentation Index Alignment

**Files:**
- Modify: `docs/README.md`

- [ ] **Step 1: Keep the index as a source-of-truth map**

Revise descriptions only where they lag current docs:

- `API Reference` should mention cache semantics and latest model-price/OHLC fields if space allows.
- `Operations` should mention cache warmup and USB kit v2 updates.
- `Production Readiness` should remain the launch gate and blocker source.
- `Superpowers Docs Index` should remain archive/history, not current runtime source.

- [ ] **Step 2: Keep the archive warning explicit**

Ensure the bottom section keeps this invariant:

```markdown
The core documents listed above remain the source of truth for current runtime and operational behavior.
```

If adding text, say historical `docs/superpowers/` files may be locally implemented, superseded, or future-facing, and readers should check `docs/superpowers/README.md` for status.

- [ ] **Step 3: Check the index diff**

Run:

```bash
git diff -- docs/README.md
```

Expected: index descriptions align with current docs; no new document is invented.

### Task 4: Roadmap And Readiness Reconciliation

**Files:**
- Modify: `docs/production-roadmap.md`
- Modify: `docs/production-readiness.md`

- [ ] **Step 1: Update roadmap current baseline**

In `docs/production-roadmap.md`, add local implementation evidence for:

- public payload cache warmup implemented locally and tagged `cache-warmup-local-complete-2026-07-05`;
- USB kit v2 implemented locally and tagged `usb-kit-v2-local-complete-2026-07-05`;
- price-model OHLC display implemented locally and tagged `price-model-ohlc-local-complete-2026-07-06`.

State that production benefit remains pending deploy/operator execution.

- [ ] **Step 2: Reconcile phase statuses without closing blocked phases**

Keep these outcomes:

- Phase 5: repository/local cache hardening is complete, but production freshness and post-deploy measurement remain external gates.
- Phase 6: still blocked by stale production data and operator deployment/update verification.
- Phase 7: still blocked pending real backup/off-server/restore/monitoring evidence.
- Phase 8: still blocked; first traffic not run; documentation presentation pass is being planned but not executed by this plan file.

Remove or revise wording that still asks to "add public payload cache warmup" as if no local implementation exists. Replace with "deploy and verify public payload cache warmup in production" or equivalent.

- [ ] **Step 3: Update readiness notes with the newest local-only state**

In `docs/production-readiness.md`, ensure the status language says:

- cache warmup is implemented locally, with startup warmup and `warm-public-cache`, but production benefit requires deploy plus healthy readiness;
- price-model OHLC display is implemented locally, but production visibility depends on deployment;
- USB kit v2 is implemented locally, but a real USB package and production-host backup-gated update are pending;
- public launch remains blocked by readiness/data freshness until public `/api/readiness` is 200.

Do not delete useful historical snapshots; label them as historical evidence and keep dates.

- [ ] **Step 4: Check roadmap/readiness diffs**

Run:

```bash
git diff -- docs/production-roadmap.md docs/production-readiness.md
```

Expected: local-complete items are reflected, blocked production gates remain blocked, and no launch-ready claim appears.

### Task 5: API And Cache Behavior Consistency

**Files:**
- Modify: `docs/api-reference.md`
- Modify: `docs/data-pipeline.md` only if cross-links or readiness/cache wording need alignment.
- Modify: `docs/testing-and-quality.md` only if coverage wording needs alignment.

- [ ] **Step 1: Confirm latest risk response field names**

Run:

```bash
rg -n "model_price_usd|low_usd|high_usd|price_usd" backend frontend docs/api-reference.md docs/testing-and-quality.md
```

Expected: the docs and frontend/backend names agree. The latest endpoint documents `model_price_usd`, `low_usd`, and `high_usd`; the history endpoint does not promise latest-only fields.

- [ ] **Step 2: Confirm public cache warmup semantics**

Run:

```bash
rg -n "warm-public-cache|startup warmup|PUBLIC_BASE_URL|X-Cache-Version|PUBLIC_CACHE" backend scripts docs/api-reference.md docs/operations.md docs/production-readiness.md docs/testing-and-quality.md
```

Expected: docs say warmup uses normal public GET routes, requires readiness 200, does not add a public admin endpoint, preserves validation-version invalidation, and excludes `POST /api/waitlist`.

- [ ] **Step 3: Revise API docs only where current text is stale**

If needed, update `docs/api-reference.md` so it states:

- public read endpoints include `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`;
- backend startup or operator warmup can build standard public cache keys;
- `warm-public-cache` should target a local/private origin;
- `POST /api/waitlist` remains no-store;
- `price_usd` remains a compatibility alias for the HLC3 model price;
- `model_price_usd` is the explicit HLC3 model price;
- `low_usd` and `high_usd` are nullable latest daily candle values.

- [ ] **Step 4: Check API-related diffs**

Run:

```bash
git diff -- docs/api-reference.md docs/data-pipeline.md docs/testing-and-quality.md
```

Expected: docs match current public contract; no new endpoint or runtime behavior is claimed.

### Task 6: Operations And Deployment Docs Consistency

**Files:**
- Modify: `docs/operations.md`
- Modify: `docs/deploy-ubuntu-cloudflare.md`
- Modify: `docs/security-and-privacy.md` only if hygiene wording needs alignment.

- [ ] **Step 1: Fix stale scheduled-refresh wording**

Search:

```bash
rg -n "until the public-download-first scheduler is implemented|downloaded CSV workflow|scheduled public CoinMarketCap refresh|COINMARKETCAP_API_KEY" docs/operations.md docs/deploy-ubuntu-cloudflare.md docs/production-readiness.md docs/data-pipeline.md
```

Expected: no doc says the public-download-first scheduler is unimplemented. The correct current wording is that scheduled public refresh exists locally/documented, production verification and freshness are pending, and manual `download-cmc-csv` or `import-cmc-csv` remain fallbacks.

- [ ] **Step 2: Align USB kit v2 wording**

Ensure `docs/operations.md` and `docs/deploy-ubuntu-cloudflare.md` agree that:

- workstation packaging command is `bash server-kit/prepare-usb-kit.sh <usb-root-path>`;
- kit output is `<usb-kit-path>`;
- server fresh install uses ordered scripts under the mounted kit;
- existing production update uses `bash scripts/07-update-bitcoin-risk-brief-from-usb.sh`;
- optional public readiness check uses `PUBLIC_URL=https://bitcoinriskbrief.minihub.app`;
- update wrapper preserves existing production `.env`;
- wrapper runs and verifies a backup before code copy;
- copied backup goes to USB default `backups-from-server/` or operator `BACKUP_COPY_DEST`;
- kit excludes `.env`, `.git`, backups, database volumes, dependency caches, build output, browser artifacts, container images, and offline package mirrors;
- production use remains pending until a real USB package is prepared and run on the production host.

- [ ] **Step 3: Keep production blocker language operational**

Ensure operations/deployment docs do not hide:

- public readiness/data freshness blocker;
- missing production backup/off-server/restore evidence;
- missing monitor/alert evidence;
- missing waitlist smoke;
- missing import provenance evidence;
- Cloudflare Free-plan-compatible subset limitations.

- [ ] **Step 4: Check operations/deployment diffs**

Run:

```bash
git diff -- docs/operations.md docs/deploy-ubuntu-cloudflare.md docs/security-and-privacy.md
```

Expected: command examples stay executable, local implementation and production-pending states are separate, and no secrets or private paths are added.

### Task 7: Superpowers Archive Index Status Update

**Files:**
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Update archive review date and summary**

Set `Last reviewed` to `2026-07-06` after edits. In `Current Implementation Summary`, update bullets so they say:

- cache warmup is implemented locally for standard public reads and production benefit requires deploy plus healthy readiness;
- latest risk payload/display has explicit model-price/OHLC polish locally implemented;
- USB kit v2 is locally implemented but not a full offline artifact and production use is pending;
- the documentation/portfolio presentation pass is now planned in `plans/2026-07-06-documentation-portfolio-presentation-implementation.md`.

- [ ] **Step 2: Update spec status rows**

Revise rows as follows unless stronger current evidence says otherwise:

- `specs/2026-07-01-public-payload-cache-warmup-precompute-design.md` -> `Implemented locally, production deploy pending`.
- `specs/2026-07-01-price-model-input-ohlc-display-design.md` -> `Implemented locally, production deploy pending`.
- `specs/2026-07-01-usb-update-install-kit-v2-design.md` -> keep `Implemented locally, production use pending`.
- `specs/2026-07-01-scheduled-public-cmc-refresh-design.md` -> `Implemented locally, production freshness blocked` if current code/docs still support that status.
- `specs/2026-07-01-documentation-portfolio-presentation-design.md` -> `Planned by implementation plan` or equivalent; do not mark complete until the docs pass is executed and verified.

- [ ] **Step 3: Add missing plan rows**

Add status rows for plan files already present but missing from the table:

- `plans/2026-07-05-public-payload-cache-warmup-implementation.md` -> `Implemented locally, production deploy pending`.
- `plans/2026-07-05-usb-update-install-kit-v2-implementation.md` -> `Implemented locally, production use pending`.
- `plans/2026-07-05-price-model-input-ohlc-display-implementation.md` -> `Implemented locally, production deploy pending`.
- `plans/2026-07-06-documentation-portfolio-presentation-implementation.md` -> `Planned` until this docs pass is executed.

- [ ] **Step 4: Check archive diff**

Run:

```bash
git diff -- docs/superpowers/README.md
```

Expected: archive status helps readers separate completed local implementation, pending production use, future-facing work, and historical plans.

### Task 8: Optional GitHub Description And Topics Note

**Files:**
- No tracked file by default.
- Optional modify: `README.md` or `docs/production-readiness.md` only if the user asks to track the recommendation inside the repository.

- [ ] **Step 1: Prepare the private/portfolio repository settings recommendation**

Use this description from the design spec unless the current README wording calls for a small edit:

```text
Production-oriented Bitcoin risk signal with FastAPI, React, TimescaleDB, daily CMC CSV ingestion, readiness checks, and local-server deployment docs.
```

Use these topics:

```text
bitcoin, risk-metric, crypto-analytics, fastapi, react, vite, timescaledb, podman, cloudflare, data-pipeline, portfolio-project
```

- [ ] **Step 2: Do not change GitHub settings from this implementation pass**

Record the recommendation in the final report. Do not use `gh`, browser automation, or GitHub API calls unless the user explicitly asks to update repository settings.

### Task 9: Secret And Artifact Hygiene Check

**Files:**
- Read/check: `.gitignore`
- Read/check: `.env.example`
- Read/check: `.env.production.example`
- Read/check: `docs/`
- Read/check: `scripts/`
- Read/check: `server-kit/`

- [ ] **Step 1: Confirm tracked env files are templates only**

Run:

```bash
git ls-files '.env*'
rg -n "replace-with|example|placeholder|changeme|secret|token|password|CLOUDFLARE|COINMARKETCAP|DB_PASSWORD" .env.example .env.production.example
```

Expected: only non-secret templates such as `.env.example` and `.env.production.example` are tracked; values are placeholders or documented examples, not real credentials.

- [ ] **Step 2: Check for tracked local artifacts**

Run:

```bash
git ls-files | rg '(^|/)(backups|data/timescaledb|node_modules|dist|build|coverage|playwright-report|test-results|browser-profiles|\.pytest_cache|__pycache__|\.DS_Store)(/|$)|\.(dump|sqlite|db|tar|tgz|zip)$'
```

Expected: no production backups, database volumes, dependency caches, browser artifacts, generated frontend output, or ad hoc archives are tracked. If the command returns intentional source files, inspect and document why they are safe.

- [ ] **Step 3: Run a targeted secret-pattern scan**

Run:

```bash
rg -n --hidden --glob '!.git/**' --glob '!frontend/node_modules/**' --glob '!data/**' --glob '!backups/**' "BEGIN (RSA|OPENSSH|PRIVATE) KEY|sk-[A-Za-z0-9]|CLOUDFLARE_API_TOKEN=.+|CLOUDFLARE_TUNNEL_TOKEN=.+|COINMARKETCAP_API_KEY=.+|DB_PASSWORD=.+|DATABASE_URL=postgres" README.md docs scripts server-kit .env.example .env.production.example
```

Expected: no real secrets. Placeholder examples are acceptable only when clearly marked as placeholders.

- [ ] **Step 4: Document hygiene outcome without adding private details**

If the hygiene check finds only expected templates and no tracked artifacts, record that in the final implementation report. If it finds a suspected secret or artifact, stop and ask the user how to handle it; do not print secret values into docs or final messages.

### Task 10: Final Verification For The Docs Pass

**Files:**
- Verify all modified docs.

- [ ] **Step 1: Review the complete docs diff**

Run:

```bash
git diff -- README.md docs/README.md docs/production-roadmap.md docs/production-readiness.md docs/operations.md docs/deploy-ubuntu-cloudflare.md docs/data-pipeline.md docs/api-reference.md docs/frontend-qa.md docs/testing-and-quality.md docs/security-and-privacy.md docs/superpowers/README.md
```

Expected: changes are documentation-only, scoped to current-state presentation, and do not include product/code behavior changes.

- [ ] **Step 2: Run stale phrase checks**

Run:

```bash
rg -n "launch-ready|production-ready|publicly launched|until the public-download-first scheduler is implemented|public payload cache warmup behavior if implemented|planned UI/API polish pass may expose daily `Low` and `High`|CONTRIBUTING.md|CODE_OF_CONDUCT.md|public issue templates" README.md docs
```

Expected:

- No match claims launch-ready or production-ready status.
- No match says implemented local work is merely future/planned.
- Matches for non-goal examples are acceptable only in explicit non-goal wording.

- [ ] **Step 3: Run docs whitespace verification**

Run:

```bash
git diff --check -- README.md docs/README.md docs/production-roadmap.md docs/production-readiness.md docs/operations.md docs/deploy-ubuntu-cloudflare.md docs/data-pipeline.md docs/api-reference.md docs/frontend-qa.md docs/testing-and-quality.md docs/security-and-privacy.md docs/superpowers/README.md
```

Expected: no trailing whitespace or conflict marker errors.

- [ ] **Step 4: State runtime test decision**

Runtime tests are not required if only Markdown docs and repository presentation notes changed. If any non-docs file changed, run the matching verification from `AGENTS.md`:

- Python/backend/collector changes: `./scripts/manage.sh test-python`.
- Frontend behavior/build changes: `npm test --prefix frontend` and `npm run build --prefix frontend`.
- Compose/operational script changes: `./scripts/manage.sh validate`.

- [ ] **Step 5: Final implementation report**

Report:

- files changed;
- current status claims made;
- blocked production gates preserved;
- stale phrase checks run;
- `git diff --check` result;
- runtime tests skipped for docs-only changes, or list runtime tests if non-docs changed;
- no commit or push performed.
