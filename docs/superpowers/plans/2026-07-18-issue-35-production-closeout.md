# Issue 35 Production Verification Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the deployed production cache warmup evidence for GitHub issue #35 and close the issue only if the production-host log review and fresh public GET-only smoke checks pass.

**Architecture:** This is an operational closeout, not a code change. Re-check the public HTTPS behavior from this workspace, collect sanitized production-host warmup log evidence from the backend service, then update and close GitHub issue #35 with concrete evidence. Do not mutate production data, do not POST to the waitlist, and do not restart production unless the human operator explicitly approves that action.

**Tech Stack:** FastAPI backend, existing `scripts/check_public_endpoints.py`, existing `scripts/manage.sh warm-public-cache`, GitHub CLI `gh`, shell commands on the production host, public hostname `https://bitcoinriskbrief.minihub.app`.

## Global Constraints

- Follow `AGENTS.md`: add or update focused tests for behavior changes, but this closeout should not change code.
- Use GET-only public endpoint checks; do not perform `POST /api/waitlist`.
- Do not record secrets, `.env` values, account IDs, private dashboard URLs, raw PII, waitlist contacts, IP addresses, full raw logs, or private operator details in GitHub comments.
- Treat `https://bitcoinriskbrief.minihub.app` as the current production pilot hostname.
- Treat `DATA_FRESHNESS_MAX_AGE_DAYS=2` as the production freshness policy unless the operator provides a different deployed value.
- Close issue #35 only when both conditions are true: fresh public smoke checks pass, and production warmup log/output evidence shows successful warmup with no failed targets.
- If production-host log access is unavailable, stop after commenting the blocker on issue #35; do not close the issue.
- If any check fails, stop after commenting the failing evidence on issue #35; do not close the issue.

---

## File Structure

- Modify: no repository source files.
- Use: `scripts/check_public_endpoints.py` for public health/readiness/latest-risk/cache-header verification.
- Use: `scripts/manage.sh warm-public-cache` for local-origin or public GET-only warmup smoke.
- Use: `docs/operations.md` as the source of expected cache warmup behavior.
- Use: GitHub issue `#35` as the evidence and closure target.

## Current Issue State

Issue #35 is open as of 2026-07-18. It already has:

- A 2026-07-16 comment confirming local implementation and tests were merged into `main`.
- A 2026-07-18 comment confirming public GET-only smoke passed from this workspace.
- One remaining closeout gate: production-host startup/import warmup log review.

The current public verification comment is:

```text
https://github.com/akarazhev/bitcoin-risk-brief/issues/35#issuecomment-5010692130
```

### Task 1: Re-Read Issue #35 And Confirm It Is Still Open

**Files:**
- Modify: none
- Test: GitHub issue state

**Interfaces:**
- Consumes: GitHub CLI authentication for `akarazhev/bitcoin-risk-brief`.
- Produces: Current issue state and latest comments for later closeout.

- [ ] **Step 1: Read the issue state**

Run:

```bash
gh issue view 35 --repo akarazhev/bitcoin-risk-brief --json number,title,state,url,updatedAt,comments
```

Expected:

```text
"state": "OPEN"
```

- [ ] **Step 2: Stop if the issue is already closed**

If the command output shows `"state": "CLOSED"`, stop and report that no closeout action is needed. Do not add another issue comment.

- [ ] **Step 3: Confirm the remaining gate**

Verify the latest comments still identify production-host warmup log review as the remaining gate. Continue only if that is still true.

### Task 2: Collect Production Warmup Evidence

**Files:**
- Modify: none
- Test: production backend logs and/or production local-origin warmup output

**Interfaces:**
- Consumes: shell access to the production host, or sanitized log output from the human operator.
- Produces: Sanitized evidence that standard public payload warmup ran successfully with no failed targets.

- [ ] **Step 1: Identify whether production-host shell access is available**

If you have shell access to the production host, continue to Step 2. If you do not, ask the human operator for sanitized output from one of these commands and stop until they provide it:

```bash
cd /srv/projects/bitcoin-risk-brief
podman-compose -f podman-compose.yml logs --tail=300 backend | rg 'public_cache_warmup_(complete|failed|skipped)'
```

```bash
journalctl --user -u bitcoin-risk-brief.service -n 300 --no-pager | rg 'public_cache_warmup_(complete|failed|skipped)'
```

The acceptable sanitized evidence is a backend log line like:

```text
public_cache_warmup_complete warmed=4 failed=0 duration_ms=123.4 slowest=GET /api/risk/levels:80.1ms,GET /api/risk/history?limit=2000:30.2ms,GET /api/brief/latest:10.3ms
```

- [ ] **Step 2: Read backend warmup logs on the production host**

Run this first on the production host:

```bash
cd /srv/projects/bitcoin-risk-brief
podman-compose -f podman-compose.yml logs --tail=300 backend | rg 'public_cache_warmup_(complete|failed|skipped)'
```

Expected passing evidence:

```text
public_cache_warmup_complete warmed=4 failed=0 duration_ms=
```

Expected failing evidence:

```text
public_cache_warmup_failed
```

```text
public_cache_warmup_skipped
```

- [ ] **Step 3: Use systemd logs if compose logs do not include backend startup**

Run this on the production host if Step 2 does not show warmup startup logs:

```bash
journalctl --user -u bitcoin-risk-brief.service -n 300 --no-pager | rg 'public_cache_warmup_(complete|failed|skipped)'
```

Expected passing evidence:

```text
public_cache_warmup_complete warmed=4 failed=0 duration_ms=
```

- [ ] **Step 4: Run production local-origin warmup only if startup logs are missing**

Run this on the production host only if Steps 2 and 3 do not show usable startup warmup evidence and production readiness is healthy:

```bash
cd /srv/projects/bitcoin-risk-brief
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
```

Expected:

```text
readiness ok http://127.0.0.1:3001/api/readiness
warmed http://127.0.0.1:3001/api/risk/latest
warmed http://127.0.0.1:3001/api/risk/history?limit=2000
warmed http://127.0.0.1:3001/api/risk/levels
warmed http://127.0.0.1:3001/api/brief/latest
```

- [ ] **Step 5: Decide whether the warmup evidence passes**

Pass only if at least one of these is true:

- Backend startup logs show `public_cache_warmup_complete warmed=4 failed=0`, include a numeric `duration_ms=` value, and include a non-empty `slowest=` value.
- Production local-origin warmup output shows readiness OK and all four standard payloads warmed.

Fail if any of these is true:

- The newest relevant log shows `public_cache_warmup_failed`.
- The newest relevant log shows `public_cache_warmup_skipped` and no successful production local-origin warmup output is available.
- Production local-origin warmup exits non-zero.
- Production local-origin warmup does not warm all four standard payloads.

### Task 3: Run Fresh Public GET-Only Smoke

**Files:**
- Modify: none
- Test: public HTTPS endpoints

**Interfaces:**
- Consumes: deployed public hostname and current production data.
- Produces: fresh public verification evidence for the final issue comment.

- [ ] **Step 1: Run the existing public endpoint probe**

Run from the workspace:

```bash
python3 scripts/check_public_endpoints.py --base-url https://bitcoinriskbrief.minihub.app --max-data-age-days 2 --require-cache-header Cache-Control --require-cache-header ETag --require-cache-header X-Cache-Version --require-cache-header X-Cache
```

Expected:

```text
OK public endpoints healthy
```

The output must also include:

```text
freshness=max_data_age_days:2
cache_headers=Cache-Control,ETag,X-Cache-Version,X-Cache
```

- [ ] **Step 2: Run public standard-payload warmup smoke**

Run from the workspace:

```bash
PUBLIC_BASE_URL=https://bitcoinriskbrief.minihub.app ./scripts/manage.sh warm-public-cache
```

Expected:

```text
readiness ok https://bitcoinriskbrief.minihub.app/api/readiness
warmed https://bitcoinriskbrief.minihub.app/api/risk/latest
warmed https://bitcoinriskbrief.minihub.app/api/risk/history?limit=2000
warmed https://bitcoinriskbrief.minihub.app/api/risk/levels
warmed https://bitcoinriskbrief.minihub.app/api/brief/latest
```

- [ ] **Step 3: Capture latest-risk headers**

Run:

```bash
curl -sS -D /tmp/brb_issue35_latest_headers.txt -o /tmp/brb_issue35_latest.json https://bitcoinriskbrief.minihub.app/api/risk/latest
rg -i '^HTTP/|^cache-control:|^etag:|^x-cache:|^x-cache-version:|^cf-cache-status:|^age:' /tmp/brb_issue35_latest_headers.txt
python3 -m json.tool /tmp/brb_issue35_latest.json | sed -n '1,80p'
```

Expected headers:

```text
HTTP/2 200
cache-control: public, max-age=60, stale-while-revalidate=300
etag:
x-cache-version: validation:
```

Expected payload:

```text
"timestamp": "20
"risk":
"risk_state":
```

- [ ] **Step 4: Verify conditional revalidation**

Run:

```bash
ETAG="$(awk 'BEGIN{IGNORECASE=1} /^etag:/ {gsub("\r", "", $2); print $2; exit}' /tmp/brb_issue35_latest_headers.txt)"
test -n "${ETAG}"
curl -sS -D /tmp/brb_issue35_conditional_headers.txt -o /tmp/brb_issue35_conditional_body.txt -H "If-None-Match: ${ETAG}" https://bitcoinriskbrief.minihub.app/api/risk/latest
sed -n '1,40p' /tmp/brb_issue35_conditional_headers.txt
```

Expected:

```text
HTTP/2 304
etag:
x-cache-version: validation:
```

### Task 4: Re-Run Focused Local Regression Tests

**Files:**
- Modify: none
- Test: focused backend public-cache tests

**Interfaces:**
- Consumes: local repository checkout and installed Python dependencies.
- Produces: local regression evidence for the final issue comment.

- [ ] **Step 1: Run the focused cache test suite**

Run:

```bash
if [[ -x .venv/bin/python ]]; then PYTHON=.venv/bin/python; else PYTHON=python3; fi
PYTHONPATH=backend:collector "${PYTHON}" -m unittest discover -s backend/tests -p 'test_public_cache*.py' -v
```

Expected:

```text
OK
```

- [ ] **Step 2: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

### Task 5: Comment And Close Issue #35 If All Gates Passed

**Files:**
- Modify: none
- Test: GitHub issue state after closure

**Interfaces:**
- Consumes: passing evidence from Tasks 2, 3, and 4.
- Produces: issue #35 closed with a concrete final evidence comment.

- [ ] **Step 1: Stop if any gate failed**

If Task 2, Task 3, or Task 4 failed, do not close the issue. Add one issue comment that states the failed command and the sanitized failure summary.

Use this command shape:

```bash
gh issue comment 35 --repo akarazhev/bitcoin-risk-brief --body "Closeout remains blocked on 2026-07-18.

Failed gate:
- Production warmup log/output review did not pass, or fresh public smoke did not pass.

Sanitized evidence:
- Include only the failed command name, exit status, and non-sensitive error summary.

No production waitlist POST was performed."
```

- [ ] **Step 2: Add the final passing evidence comment**

Only if every gate passed, run:

```bash
gh issue comment 35 --repo akarazhev/bitcoin-risk-brief --body "Issue #35 production closeout verified on 2026-07-18.

Verified:
- Production warmup evidence reviewed: backend startup warmup or production local-origin warmup completed with all four standard public payloads and no failed targets.
- Fresh public probe passed against https://bitcoinriskbrief.minihub.app with health/readiness/latest-risk healthy, freshness policy max_data_age_days:2, and required cache headers Cache-Control, ETag, X-Cache-Version, and X-Cache.
- Public GET warmup smoke passed for /api/risk/latest, /api/risk/history?limit=2000, /api/risk/levels, and /api/brief/latest.
- GET /api/risk/latest returned public cache headers including ETag and X-Cache-Version.
- Conditional GET /api/risk/latest with the captured ETag returned HTTP 304.
- Focused local public-cache tests passed: PYTHONPATH=backend:collector python -m unittest discover -s backend/tests -p 'test_public_cache*.py' -v.
- git diff --check exited clean.
- No production waitlist POST was performed.

Closing because local implementation was already merged and the remaining post-deploy public smoke plus production warmup review gates have now passed."
```

- [ ] **Step 3: Close the issue**

Run:

```bash
gh issue close 35 --repo akarazhev/bitcoin-risk-brief --reason completed
```

Expected:

```text
✓ Closed issue akarazhev/bitcoin-risk-brief#35
```

- [ ] **Step 4: Verify the closed state**

Run:

```bash
gh issue view 35 --repo akarazhev/bitcoin-risk-brief --json state,url
```

Expected:

```text
"state": "CLOSED"
```

### Task 6: Final Report To The Human Operator

**Files:**
- Modify: none
- Test: final report accuracy

**Interfaces:**
- Consumes: issue URL, command outputs, and closure status.
- Produces: concise final status.

- [ ] **Step 1: Report the result**

If the issue was closed, say:

```text
Issue #35 is closed as completed. Public smoke passed, production warmup evidence passed, focused local tests passed, and no waitlist POST was performed.
```

If the issue remains open, say:

```text
Issue #35 remains open. The blocker is the production warmup log/output gate or a failing public smoke check; I posted the sanitized evidence on the issue and did not close it.
```

## Self-Review Checklist

- Spec coverage: The plan covers issue state, production warmup log/output review, fresh public GET-only smoke, local focused tests, issue comment, issue closure, and final reporting.
- Placeholder scan: The plan contains no unresolved placeholder markers or undefined implementation steps.
- Type consistency: Not applicable; this operational plan does not introduce code interfaces.
- Safety: The plan forbids production data mutation, waitlist POSTs, secret recording, and unapproved production restarts.
