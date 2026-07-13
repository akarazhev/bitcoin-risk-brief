# Live Readiness No-Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/api/readiness` a live, non-cacheable status endpoint while keeping the heavier public product payloads cacheable.

**Architecture:** Readiness is the trust/control-plane endpoint, so the backend should build it on each request and return `Cache-Control: no-store` for both ready and degraded responses. Cloudflare rules and browser fetches should explicitly bypass cache for readiness, while `/api/risk/latest`, `/api/risk/history`, `/api/risk/levels`, and `/api/brief/latest` keep the existing public cache behavior. Operational probes should validate readiness freshness semantics separately from cacheable product payloads.

**Tech Stack:** FastAPI, Python `unittest`, Bash, Cloudflare ruleset JSON generation, React/Vite, Vitest.

---

## File Structure

- Modify `backend/app/main.py`
  - Responsibility: serve `/api/readiness` directly with `no_store_headers()` instead of the shared public cache helper; remove readiness from backend public cache warmup targets.
- Modify `backend/tests/test_public_cache_warmup.py`
  - Responsibility: lock the backend readiness route and warmup target behavior.
- Modify `scripts/cloudflare_edge_rules.py`
  - Responsibility: generate Cloudflare cache settings that bypass readiness and cache only product read endpoints.
- Modify `backend/tests/test_cloudflare_edge_rules.py`
  - Responsibility: lock Cloudflare cache rule generation.
- Modify `frontend/src/api.ts`
  - Responsibility: request readiness with browser cache disabled.
- Modify `frontend/src/api.test.ts`
  - Responsibility: lock readiness fetch options and degraded `503` parsing.
- Modify `scripts/check_public_endpoints.py`
  - Responsibility: require `no-store` on readiness and cache headers only on cacheable product endpoints.
- Modify `backend/tests/test_public_endpoint_probe.py`
  - Responsibility: lock public probe expectations.
- Modify `scripts/warm-public-cache.sh`
  - Responsibility: use readiness as a pre-warm gate but do not warm readiness as a cached payload.
- Modify `docs/operations.md`, `docs/security-and-privacy.md`, and `docs/testing-and-quality.md`
  - Responsibility: document the new cache semantics and production purge boundary.

## Task 1: Backend Readiness Is No-Store And Not Warmed

**Files:**
- Modify: `backend/tests/test_public_cache_warmup.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing backend route and warmup tests**

In `backend/tests/test_public_cache_warmup.py`, add `import json` below the future import:

```python
from __future__ import annotations

import json
from types import SimpleNamespace
import unittest
```

In `StandardPublicWarmupTargetTest.test_standard_warmup_targets_use_frontend_public_cache_keys`, change the expected keys to remove readiness:

```python
        self.assertEqual(
            [target.key for target in targets],
            [
                "GET /api/risk/latest",
                "GET /api/risk/history?limit=2000",
                "GET /api/risk/levels",
                "GET /api/brief/latest",
            ],
        )
```

Add this test method to `WarmedEndpointResponseTest` after `test_warmed_endpoint_returns_hit_without_rebuilding`:

```python
    async def test_readiness_handler_returns_no_store_without_public_cache_headers(self) -> None:
        payload = {
            "status": "degraded",
            "checks": {"data_fresh": False},
            "data": {"latest_date": "2026-06-30", "data_age_days": 6},
        }

        async def fake_readiness():
            return payload, 503

        self.patch_main("_produce_readiness_payload", fake_readiness)

        response = await main.readiness()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["pragma"], "no-cache")
        self.assertNotIn("etag", response.headers)
        self.assertNotIn("x-cache", response.headers)
        self.assertNotIn("x-cache-version", response.headers)
        self.assertEqual(json.loads(response.body), payload)
```

- [ ] **Step 2: Run the failing backend tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache_warmup.StandardPublicWarmupTargetTest backend.tests.test_public_cache_warmup.WarmedEndpointResponseTest -v
```

Expected result before implementation:

```text
FAIL: test_standard_warmup_targets_use_frontend_public_cache_keys
FAIL: test_readiness_handler_returns_no_store_without_public_cache_headers
```

- [ ] **Step 3: Implement backend no-store readiness**

In `backend/app/main.py`, replace `_standard_public_cache_warmup_targets()` with:

```python
def _standard_public_cache_warmup_targets() -> tuple[PublicCacheWarmupTarget, ...]:
    return (
        PublicCacheWarmupTarget("GET /api/risk/latest", _produce_risk_latest_payload),
        PublicCacheWarmupTarget("GET /api/risk/history?limit=2000", _risk_history_producer(limit=2000)),
        PublicCacheWarmupTarget("GET /api/risk/levels", _produce_risk_levels_payload),
        PublicCacheWarmupTarget("GET /api/brief/latest", _produce_brief_latest_payload),
    )
```

In the same file, replace the readiness route with:

```python
@app.get("/api/readiness")
async def readiness() -> Response:
    payload, status_code = await _produce_readiness_payload()
    return JSONResponse(status_code=status_code, content=payload, headers=no_store_headers())
```

- [ ] **Step 4: Run the backend tests again**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache_warmup.StandardPublicWarmupTargetTest backend.tests.test_public_cache_warmup.WarmedEndpointResponseTest -v
```

Expected result after implementation:

```text
OK
```

- [ ] **Step 5: Commit backend readiness behavior**

Run:

```bash
git status --short
git add backend/app/main.py backend/tests/test_public_cache_warmup.py
git commit -m "fix: serve readiness without cache"
```

Do not add unrelated dirty files such as `.gitignore`.

## Task 2: Cloudflare Bypasses Readiness Cache

**Files:**
- Modify: `backend/tests/test_cloudflare_edge_rules.py`
- Modify: `scripts/cloudflare_edge_rules.py`

- [ ] **Step 1: Write failing Cloudflare rule tests**

In `backend/tests/test_cloudflare_edge_rules.py`, update the cache rule assertions inside `test_plan_contains_waf_bot_rate_limit_and_cache_rules_for_hostname` to:

```python
        cache_rules = plan["http_request_cache_settings"]["rules"]
        self.assertFalse(cache_rules[0]["action_parameters"]["cache"])
        self.assertIn('http.request.uri.path eq "/api/waitlist"', cache_rules[0]["expression"])
        self.assertFalse(cache_rules[1]["action_parameters"]["cache"])
        self.assertIn('http.request.uri.path eq "/api/readiness"', cache_rules[1]["expression"])
        self.assertTrue(cache_rules[2]["action_parameters"]["cache"])
        self.assertEqual(cache_rules[2]["action_parameters"]["edge_ttl"]["mode"], "respect_origin")
        self.assertIn('http.request.uri.path eq "/api/risk/latest"', cache_rules[2]["expression"])
        self.assertNotIn('http.request.uri.path eq "/api/readiness"', cache_rules[2]["expression"])
```

Add this test method after `test_plan_contains_waf_bot_rate_limit_and_cache_rules_for_hostname`:

```python
    def test_public_read_cache_paths_exclude_readiness(self) -> None:
        self.assertNotIn("/api/readiness", cloudflare_edge_rules.PUBLIC_READ_PATHS)
        self.assertIn("/api/risk/latest", cloudflare_edge_rules.PUBLIC_READ_PATHS)
        self.assertIn("/api/risk/history", cloudflare_edge_rules.PUBLIC_READ_PATHS)
        self.assertIn("/api/risk/levels", cloudflare_edge_rules.PUBLIC_READ_PATHS)
        self.assertIn("/api/brief/latest", cloudflare_edge_rules.PUBLIC_READ_PATHS)
```

- [ ] **Step 2: Run the failing Cloudflare tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_cloudflare_edge_rules.CloudflareEdgeRulesPlanTest -v
```

Expected result before implementation:

```text
FAIL: test_plan_contains_waf_bot_rate_limit_and_cache_rules_for_hostname
FAIL: test_public_read_cache_paths_exclude_readiness
```

- [ ] **Step 3: Implement Cloudflare readiness cache bypass**

In `scripts/cloudflare_edge_rules.py`, replace the path constants near the top with:

```python
READINESS_PATH = "/api/readiness"

PUBLIC_READ_PATHS = (
    "/api/risk/latest",
    "/api/risk/history",
    "/api/risk/levels",
    "/api/brief/latest",
)
```

Add this helper below `_waitlist_expression()`:

```python
def _readiness_expression(hostname: str) -> str:
    return (
        f"({_host_expression(hostname)} and http.request.method eq \"GET\" "
        f'and http.request.uri.path eq "{READINESS_PATH}")'
    )
```

In `build_edge_ruleset_plan()`, replace the `http_request_cache_settings` rules list with:

```python
            "rules": [
                {
                    "ref": f"{OWNED_RULE_PREFIX}waitlist-cache-bypass",
                    "description": "Bypass cache for waitlist submissions",
                    "enabled": True,
                    "expression": _waitlist_expression(hostname),
                    "action": "set_cache_settings",
                    "action_parameters": {"cache": False},
                },
                {
                    "ref": f"{OWNED_RULE_PREFIX}readiness-cache-bypass",
                    "description": "Bypass cache for readiness status",
                    "enabled": True,
                    "expression": _readiness_expression(hostname),
                    "action": "set_cache_settings",
                    "action_parameters": {"cache": False},
                },
                {
                    "ref": f"{OWNED_RULE_PREFIX}public-api-origin-cache",
                    "description": "Respect origin cache headers for cacheable public read endpoints",
                    "enabled": True,
                    "expression": _public_read_expression(hostname),
                    "action": "set_cache_settings",
                    "action_parameters": {
                        "cache": True,
                        "edge_ttl": {"mode": "respect_origin"},
                        "browser_ttl": {"mode": "respect_origin"},
                    },
                },
            ],
```

- [ ] **Step 4: Run the Cloudflare tests again**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_cloudflare_edge_rules.CloudflareEdgeRulesPlanTest -v
```

Expected result after implementation:

```text
OK
```

- [ ] **Step 5: Commit Cloudflare cache rules**

Run:

```bash
git status --short
git add scripts/cloudflare_edge_rules.py backend/tests/test_cloudflare_edge_rules.py
git commit -m "fix: bypass edge cache for readiness"
```

Do not add unrelated dirty files.

## Task 3: Frontend Requests Readiness Without Browser Cache

**Files:**
- Modify: `frontend/src/api.test.ts`
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Write the failing frontend API test**

In `frontend/src/api.test.ts`, add this test after `parses degraded readiness payloads returned with a 503 status`:

```typescript
test('requests readiness with browser cache disabled', async () => {
  const payload = {
    status: 'ready',
    checks: {
      risk_data_available: true,
      validation_available: true,
      risk_range_ok: true,
      validation_has_rows: true,
      latest_matches_validation_end: true,
      source_is_canonical: true,
      data_fresh: true,
    },
    data: {
      latest_date: '2026-07-10',
      covered_end: '2026-07-10',
      data_age_days: 1,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5841,
      methodology_version: 'crypto-scout-canonical-v1',
    },
  }
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => payload,
  }))
  vi.stubGlobal('fetch', fetchMock)

  await expect(fetchReadiness()).resolves.toEqual(payload)

  expect(fetchMock).toHaveBeenCalledWith('/api/readiness', { cache: 'no-store' })
})
```

- [ ] **Step 2: Run the failing frontend test**

```bash
npm test --prefix frontend -- api.test.ts
```

Expected result before implementation:

```text
FAIL  src/api.test.ts > requests readiness with browser cache disabled
```

- [ ] **Step 3: Implement frontend no-store fetch**

In `frontend/src/api.ts`, replace `fetchReadiness()` with:

```typescript
export async function fetchReadiness() {
  const response = await fetch('/api/readiness', { cache: 'no-store' })
  const payload = (await response.json()) as ReadinessPayload
  if (!response.ok && response.status !== 503) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return payload
}
```

- [ ] **Step 4: Run the frontend API tests again**

Run:

```bash
npm test --prefix frontend -- api.test.ts
```

Expected result after implementation:

```text
PASS  src/api.test.ts
```

- [ ] **Step 5: Commit frontend no-store fetch**

Run:

```bash
git status --short
git add frontend/src/api.ts frontend/src/api.test.ts
git commit -m "fix: disable browser cache for readiness"
```

Do not add unrelated dirty files.

## Task 4: Public Probe Separates Readiness No-Store From Product Cache Headers

**Files:**
- Modify: `scripts/check_public_endpoints.py`
- Modify: `backend/tests/test_public_endpoint_probe.py`

- [ ] **Step 1: Write failing public probe tests**

In `backend/tests/test_public_endpoint_probe.py`, update `_healthy_responses()` so readiness uses no-store headers while latest risk keeps cache headers:

```python
        cache_headers = {
            "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
            "ETag": '"abc123"',
            "X-Cache-Version": "validation:2026-07-10",
            "X-Cache": "HIT",
        }
        readiness_headers = {
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        }
```

Then change the readiness `FakeResponse` call that currently passes `headers=cache_headers` to:

```python
                headers=readiness_headers,
```

Leave the `/api/risk/latest` response on `headers=cache_headers`.

Update `test_cache_header_requirement_passes_and_fails_as_expected` to assert cache headers are required only on latest risk:

```python
    def test_cache_header_requirement_passes_and_fails_as_expected(self) -> None:
        status, stdout, stderr, _opener = self._run_probe(
            self._healthy_responses(),
            "--expected-latest-date",
            "2026-07-10",
            "--require-cache-header",
            "ETag",
            "--require-cache-header",
            "X-Cache",
        )
        self.assertEqual(0, status, stderr)
        self.assertIn("cache_headers=ETag,X-Cache", stdout)

        responses = self._healthy_responses()
        responses["/api/risk/latest"] = FakeResponse(
            200,
            responses["/api/risk/latest"]._body,
            headers={"ETag": '"abc123"'},
        )
        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
            "--require-cache-header",
            "X-Cache",
        )
        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("GET /api/risk/latest missing X-Cache", stderr)

        responses = self._healthy_responses()
        responses["/api/readiness"] = FakeResponse(
            200,
            responses["/api/readiness"]._body,
            headers={"Cache-Control": "no-store"},
        )
        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
            "--require-cache-header",
            "X-Cache",
        )
        self.assertEqual(0, status, stderr)
        self.assertIn("cache_headers=X-Cache", stdout)
```

Add this test after `test_cache_header_requirement_passes_and_fails_as_expected`:

```python
    def test_readiness_must_be_no_store(self) -> None:
        responses = self._healthy_responses()
        responses["/api/readiness"] = FakeResponse(
            200,
            responses["/api/readiness"]._body,
            headers={"Cache-Control": "public, max-age=60"},
        )

        status, stdout, stderr, _opener = self._run_probe(
            responses,
            "--expected-latest-date",
            "2026-07-10",
        )

        self.assertNotEqual(0, status)
        self.assertEqual("", stdout)
        self.assertIn("GET /api/readiness Cache-Control must include no-store", stderr)
```

- [ ] **Step 2: Run the failing public probe tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_endpoint_probe.PublicEndpointProbeTests -v
```

Expected result before implementation:

```text
FAIL: test_readiness_must_be_no_store
```

- [ ] **Step 3: Implement public probe semantics**

In `scripts/check_public_endpoints.py`, change `CACHEABLE_ENDPOINTS` near the top to:

```python
CACHEABLE_ENDPOINTS = (
    "/api/risk/latest",
)
```

Add this function below `validate_readiness()`:

```python
def validate_readiness_cache_headers(result: EndpointResult) -> None:
    cache_control = result.headers.get("cache-control", "")
    directives = {
        directive.strip().lower()
        for directive in cache_control.split(",")
        if directive.strip()
    }
    if "no-store" not in directives:
        raise ProbeError("GET /api/readiness Cache-Control must include no-store")
```

In `build_parser()`, replace the `--require-cache-header` help text with:

```python
        help=(
            "Require a cache header on cacheable public API responses. "
            "Readiness is expected to return Cache-Control: no-store. "
            "Repeat for multiple headers. Choices: %(choices)s."
        ),
```

In `run_check()`, add the readiness header validation immediately after the `validate_readiness` call:

```python
    validate_health(results["/api/health"].payload)
    readiness = validate_readiness(results["/api/readiness"].payload)
    validate_readiness_cache_headers(results["/api/readiness"])
    latest = validate_latest_risk(results["/api/risk/latest"].payload)
```

Keep the later `validate_cache_headers(results, required_cache_headers)` call unchanged.

- [ ] **Step 4: Run the public probe tests again**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_endpoint_probe.PublicEndpointProbeTests -v
```

Expected result after implementation:

```text
OK
```

- [ ] **Step 5: Commit public probe changes**

Run:

```bash
git status --short
git add scripts/check_public_endpoints.py backend/tests/test_public_endpoint_probe.py
git commit -m "fix: probe readiness no-store policy"
```

Do not add unrelated dirty files.

## Task 5: Warmup Script Uses Readiness Only As A Gate

**Files:**
- Modify: `scripts/warm-public-cache.sh`

- [ ] **Step 1: Update warmup script**

Replace the contents of `scripts/warm-public-cache.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail

base_url="${PUBLIC_BASE_URL:-http://localhost:3001}"
base_url="${base_url%/}"

readiness_path="/api/readiness"
curl -fsS -o /dev/null "${base_url}${readiness_path}"
echo "readiness ok ${base_url}${readiness_path}"

paths=(
  "/api/risk/latest"
  "/api/risk/history?limit=2000"
  "/api/risk/levels"
  "/api/brief/latest"
)

for path in "${paths[@]}"; do
  curl -fsS -o /dev/null "${base_url}${path}"
  echo "warmed ${base_url}${path}"
done
```

- [ ] **Step 2: Verify warmup script content**

Run:

```bash
sed -n '1,80p' scripts/warm-public-cache.sh
```

Expected output includes:

```text
readiness ok ${base_url}${readiness_path}
```

Expected output does not include readiness inside the `paths` array.

- [ ] **Step 3: Commit warmup script change**

Run:

```bash
git status --short
git add scripts/warm-public-cache.sh
git commit -m "fix: stop warming readiness cache"
```

Do not add unrelated dirty files.

## Task 6: Documentation Matches The New Cache Policy

**Files:**
- Modify: `docs/operations.md`
- Modify: `docs/security-and-privacy.md`
- Modify: `docs/testing-and-quality.md`

- [ ] **Step 1: Update operations cache verification docs**

In `docs/operations.md`, update the `## Cache Verification` section so it says:

```markdown
Readiness is intentionally not cacheable. `GET /api/readiness` should return `Cache-Control: no-store` and should be
used as the live freshness/status check before trusting public risk payloads.

Public product read endpoints are cacheable at the backend and edge:

- `/api/risk/latest`
- `/api/risk/history`
- `/api/risk/levels`
- `/api/brief/latest`
```

In the same section, change the warmup list to:

```markdown
Warm the standard public product payloads after manual or scheduled imports before active traffic:

- `/api/risk/latest`
- `/api/risk/history?limit=2000`
- `/api/risk/levels`
- `/api/brief/latest`
```

Keep the existing explanation that readiness runs first as a `curl -f` gate, but adjust it to say readiness is checked and not warmed.

- [ ] **Step 2: Update operations stale cache runbook**

In `docs/operations.md`, in `### Public cache stale after import or correction`, replace the expected-header paragraph with:

```markdown
Expected readiness headers include `Cache-Control: no-store`. Expected cacheable public read headers include
`Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`; the latest timestamp should match readiness `covered_end`.
```

Replace the first safe action paragraph with:

```markdown
- First safe action: purge the single public hostname/API cache in Cloudflare when the previous readiness or product API
  response may already be cached at the edge. After purge, verify `/api/readiness` is `no-store` and compare it with
  `/api/risk/latest`. Do not rerun imports solely to clear a stale edge cache.
```

- [ ] **Step 3: Update security and privacy cache policy docs**

In `docs/security-and-privacy.md`, update `## Caching Safety` so it states:

```markdown
`GET /api/readiness` is the live freshness/status endpoint and is intentionally uncached with `Cache-Control: no-store`
and `Pragma: no-cache`.

The backend caches these public product read endpoints:

- `/api/risk/latest`
- `/api/risk/history`
- `/api/risk/levels`
- `/api/brief/latest`
```

Keep the existing default cache setting bullets for the cacheable product endpoints.

- [ ] **Step 4: Update testing and quality docs**

Run:

```bash
rg -n "readiness.*cache|cache.*readiness|/api/readiness" docs/testing-and-quality.md
```

Edit only the matching lines that describe cache headers so they say readiness is expected to be `no-store`, while product public reads are expected to have cache headers.

- [ ] **Step 5: Verify there are no stale readiness-cache claims**

Run:

```bash
rg -n "Public read endpoints are cacheable|The backend caches these public read endpoints|/api/readiness" docs/operations.md docs/security-and-privacy.md docs/testing-and-quality.md
```

Expected result: references to `/api/readiness` describe live/no-store status or readiness checks, not a cacheable public read endpoint.

- [ ] **Step 6: Commit documentation changes**

Run:

```bash
git status --short
git add docs/operations.md docs/security-and-privacy.md docs/testing-and-quality.md
git commit -m "docs: clarify readiness cache policy"
```

Do not add unrelated dirty files.

## Task 7: Full Verification And Production Boundary

**Files:**
- Read: repository root

- [ ] **Step 1: Run focused Python tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest \
  backend.tests.test_public_cache_warmup \
  backend.tests.test_cloudflare_edge_rules \
  backend.tests.test_public_endpoint_probe \
  backend.tests.test_public_cache \
  -v
```

Expected result:

```text
OK
```

- [ ] **Step 2: Run all Python tests**

Run:

```bash
./scripts/manage.sh test-python
```

Expected result:

```text
OK
```

- [ ] **Step 3: Run frontend tests**

Run:

```bash
npm test --prefix frontend
```

Expected result: Vitest exits with status 0 and reports all frontend test files passed.

- [ ] **Step 4: Run frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected result:

```text
built in
```

- [ ] **Step 5: Validate compose configuration**

Run:

```bash
./scripts/manage.sh validate
```

Expected result:

```text
compose config ok
```

- [ ] **Step 6: Review the final diff**

Run:

```bash
git status --short
git diff --stat
git diff -- backend/app/main.py scripts/cloudflare_edge_rules.py frontend/src/api.ts scripts/check_public_endpoints.py scripts/warm-public-cache.sh
```

Expected result:

```text
backend readiness returns no-store, Cloudflare bypasses readiness, frontend fetch uses cache no-store, public probe requires readiness no-store, and warmup no longer warms readiness.
```

- [ ] **Step 7: Record the production purge boundary in the handoff**

Do not run Cloudflare purge commands unless the operator explicitly authorizes production access and provides the required credentials. The implementation handoff should say:

```text
After deployment, purge the Cloudflare cache for the public hostname or the API paths that may contain stale readiness responses. Then verify:

curl -sD - -o /tmp/bitcoin-risk-readiness.json https://bitcoinriskbrief.minihub.app/api/readiness
curl -sD - -o /tmp/bitcoin-risk-readiness-cb.json "https://bitcoinriskbrief.minihub.app/api/readiness?cb=$(date -u +%Y%m%d%H%M%S)"
curl -sD - -o /tmp/bitcoin-risk-latest.json https://bitcoinriskbrief.minihub.app/api/risk/latest

Both readiness requests should agree on latest_date, covered_end, data_age_days, and status. Readiness should include Cache-Control: no-store. Cloudflare should not serve a multi-day STALE readiness object. Latest risk should still have the expected cache headers.
```

- [ ] **Step 8: Final commit if verification changes were needed**

If Task 7 required small fixes, commit only those exact files:

```bash
git status --short
git add backend/app/main.py backend/tests/test_public_cache_warmup.py scripts/cloudflare_edge_rules.py backend/tests/test_cloudflare_edge_rules.py frontend/src/api.ts frontend/src/api.test.ts scripts/check_public_endpoints.py backend/tests/test_public_endpoint_probe.py scripts/warm-public-cache.sh docs/operations.md docs/security-and-privacy.md docs/testing-and-quality.md
git commit -m "fix: make readiness live and uncached"
```

If all earlier commits already contain the final changes, skip this commit.

## Acceptance Criteria

- `GET /api/readiness` returns `Cache-Control: no-store` and `Pragma: no-cache` on both `200` ready and `503` degraded responses.
- `GET /api/readiness` does not return `ETag`, `X-Cache`, or `X-Cache-Version`.
- Backend public cache warmup no longer includes `GET /api/readiness`, but startup still calls readiness as the gate before warming product payloads.
- Cloudflare generated cache settings include a readiness cache-bypass rule and exclude `/api/readiness` from the cacheable public-read expression.
- Frontend `fetchReadiness()` calls `fetch('/api/readiness', { cache: 'no-store' })` and still accepts degraded `503` readiness payloads.
- Public probe tooling validates readiness `no-store` and requires cache headers only on cacheable product reads.
- Docs state that readiness is live/no-store and product payloads are cacheable.
- Focused Python tests, all Python tests, frontend tests, frontend build, and compose validation pass.
