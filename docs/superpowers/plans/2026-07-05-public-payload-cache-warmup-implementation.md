# Public Payload Cache Warmup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Warm standard public API payloads before real users hit slow backend cache misses after backend startup or an operator/import refresh.

**Architecture:** Keep TimescaleDB as the durable source and keep the existing in-process `PublicEndpointCache` as the only cache layer. Add a reusable warmup routine that builds the same cache keys and payloads used by normal public GET requests, call it during FastAPI startup after the database pool is ready, and add a private local-origin operator command for post-import warming if the import workflow needs an explicit trigger. Preserve validation-version invalidation through `X-Cache-Version`; do not hide degraded readiness or stale production data.

**Tech Stack:** FastAPI, Python 3.13, `unittest`, asyncpg, existing in-process public cache helpers, Bash `scripts/manage.sh`, Podman Compose, Markdown docs.

---

## Context

Task 11 is committed at `858fb9f75fe41696221921c605f56f969af47b6b`. The 2026-07-05 production-readiness evidence showed slow public MISS latency for `/api/risk/levels` around `16.3s` and `/api/risk/latest` around `15.7s`.

Production data freshness is a separate blocker. Warmup must not make stale or degraded data look ready. Do not execute Task 12 from the handoff plan as part of this work.

## Exact Files Likely To Change

- Modify: `backend/app/public_cache.py`
  - Add warmup target/result dataclasses and a reusable `warm_public_endpoint_cache` helper.
- Modify: `backend/app/main.py`
  - Extract reusable public payload producer helpers.
  - Define the standard warmup cache keys.
  - Run startup warmup after `connect()` succeeds and before the lifespan yields.
- Modify: `backend/tests/test_public_cache.py`
  - Add unit tests for cache-key population, validation-version invalidation, and warmup failure logging.
- Add if main-level startup tests are clearer in a separate file: `backend/tests/test_public_cache_warmup.py`
  - Test startup warmup gating, warmed endpoint `X-Cache: HIT`, waitlist no-store regression, and response schema stability.
- Create if post-import/operator warming is selected: `scripts/warm-public-cache.sh`
  - Warm local-origin public GET endpoints through normal public routes, not through an admin endpoint.
- Modify if post-import/operator warming is selected: `scripts/manage.sh`
  - Add a `warm-public-cache` subcommand that calls `scripts/warm-public-cache.sh`.
- Modify if behavior is documented: `docs/operations.md`
  - Add local-origin warmup command usage after manual imports or production backend restarts.
- Modify if behavior is documented: `docs/production-readiness.md`
  - Record the implemented warmup behavior and remaining production freshness blocker status.
- Modify if behavior is documented: `docs/api-reference.md`
  - Clarify that public read response shapes and cache headers are unchanged; warmup only pre-populates existing keys.
- Read-only reference: `frontend/src/api.ts`
  - Confirms the frontend standard history path is `/api/risk/history?limit=2000`.

## Cache-Key Contract

The warmup routine must populate the same keys returned by `backend/app/main.py::_public_cache_key` for the public page:

```text
GET /api/readiness
GET /api/risk/latest
GET /api/risk/history?limit=2000
GET /api/risk/levels
GET /api/brief/latest
```

Do not warm `GET /api/health`; it is cheap and intentionally not part of the public read cache contract. Do not warm or cache `POST /api/waitlist`.

## Non-Goals

- No Redis, Memcached, CDN-specific worker, or other external cache.
- No public admin endpoint.
- No risk recomputation in backend request handlers beyond the existing `/api/risk/levels` calculation behavior.
- No change to endpoint response shape for `/api/readiness`, `/api/risk/latest`, `/api/risk/history`, `/api/risk/levels`, or `/api/brief/latest`.
- No cache for `POST /api/waitlist`; it must remain `Cache-Control: no-store`.
- No deployment work, Cloudflare changes, or production data freshness repair in this implementation.
- No Task 12 product-polish work.
- No commit or push unless the operator gives a separate explicit command.

## Task 1: Add Reusable Public Cache Warmup Primitive

**Files:**
- Modify: `backend/app/public_cache.py`
- Modify: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Write failing warmup primitive tests**

Add these imports to `backend/tests/test_public_cache.py`:

```python
from app.public_cache import (
    PublicCacheWarmupTarget,
    PublicEndpointCache,
    build_cache_headers,
    etag_matches,
    no_store_headers,
    warm_public_endpoint_cache,
)
```

Add a new `PublicEndpointCacheWarmupTest` class:

```python
class PublicEndpointCacheWarmupTest(unittest.IsolatedAsyncioTestCase):
    async def test_warmup_populates_standard_cache_keys(self) -> None:
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)
        calls: list[str] = []

        def make_producer(name: str):
            async def producer():
                calls.append(name)
                return {"data": {"name": name}}, 200

            return producer

        targets = [
            PublicCacheWarmupTarget("GET /api/readiness", make_producer("readiness")),
            PublicCacheWarmupTarget("GET /api/risk/latest", make_producer("latest")),
            PublicCacheWarmupTarget("GET /api/risk/history?limit=2000", make_producer("history")),
            PublicCacheWarmupTarget("GET /api/risk/levels", make_producer("levels")),
            PublicCacheWarmupTarget("GET /api/brief/latest", make_producer("brief")),
        ]

        result = await warm_public_endpoint_cache(cache, "version-a", targets)

        self.assertEqual(
            result.warmed_keys,
            tuple(target.key for target in targets),
        )
        self.assertEqual(result.failed_keys, ())
        self.assertEqual(calls, ["readiness", "latest", "history", "levels", "brief"])

        async def rebuild_should_not_run():
            raise AssertionError("warm cache entry was rebuilt")

        for target in targets:
            _entry, hit = await cache.get_or_build(target.key, "version-a", rebuild_should_not_run)
            self.assertTrue(hit)

    async def test_warmup_validation_version_change_invalidates_warmed_payload(self) -> None:
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)
        calls = 0

        async def producer():
            nonlocal calls
            calls += 1
            return {"data": {"risk": calls}}, 200

        await warm_public_endpoint_cache(
            cache,
            "validation:old",
            [PublicCacheWarmupTarget("GET /api/risk/latest", producer)],
        )
        entry, hit = await cache.get_or_build("GET /api/risk/latest", "validation:new", producer)

        self.assertFalse(hit)
        self.assertEqual(entry.content["data"]["risk"], 2)

    async def test_warmup_logs_failure_and_keeps_warming_other_keys(self) -> None:
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)

        async def missing_data():
            raise RuntimeError("Risk data has not been collected yet")

        async def good_payload():
            return {"data": {"ok": True}}, 200

        with self.assertLogs("app.public_cache", level="WARNING") as logs:
            result = await warm_public_endpoint_cache(
                cache,
                "version-a",
                [
                    PublicCacheWarmupTarget("GET /api/risk/latest", missing_data),
                    PublicCacheWarmupTarget("GET /api/brief/latest", good_payload),
                ],
            )

        self.assertEqual(result.warmed_keys, ("GET /api/brief/latest",))
        self.assertEqual(result.failed_keys, ("GET /api/risk/latest",))
        self.assertIn("public_cache_warmup_failed key=GET /api/risk/latest", "\n".join(logs.output))
```

- [ ] **Step 2: Run the focused test and confirm it fails**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache.py' -v
```

Expected: FAIL because `PublicCacheWarmupTarget` and `warm_public_endpoint_cache` do not exist.

- [ ] **Step 3: Implement the warmup primitive**

In `backend/app/public_cache.py`, add:

```python
import logging
```

Add these dataclasses below `CachedEndpointPayload`:

```python
@dataclass(frozen=True)
class PublicCacheWarmupTarget:
    key: str
    producer: PayloadProducer


@dataclass(frozen=True)
class PublicCacheWarmupResult:
    warmed_keys: tuple[str, ...]
    failed_keys: tuple[str, ...]
```

Add this helper below `PublicEndpointCache`:

```python
async def warm_public_endpoint_cache(
    cache: PublicEndpointCache,
    data_version: str,
    targets: list[PublicCacheWarmupTarget] | tuple[PublicCacheWarmupTarget, ...],
    *,
    logger: logging.Logger | None = None,
) -> PublicCacheWarmupResult:
    active_logger = logger or logging.getLogger(__name__)
    warmed_keys: list[str] = []
    failed_keys: list[str] = []

    for target in targets:
        try:
            await cache.get_or_build(target.key, data_version, target.producer)
        except Exception as exc:
            failed_keys.append(target.key)
            active_logger.warning(
                "public_cache_warmup_failed key=%s error=%s",
                target.key,
                exc,
                exc_info=True,
            )
            continue
        warmed_keys.append(target.key)

    return PublicCacheWarmupResult(tuple(warmed_keys), tuple(failed_keys))
```

- [ ] **Step 4: Run the focused cache tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache.py' -v
```

Expected: PASS.

## Task 2: Extract Public Payload Producers And Startup Warmup

**Files:**
- Modify: `backend/app/main.py`
- Add if clearer: `backend/tests/test_public_cache_warmup.py`
- Modify if not using a new test file: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Write failing tests for standard keys and startup skip behavior**

Create `backend/tests/test_public_cache_warmup.py` with this starting structure:

```python
from __future__ import annotations

from types import SimpleNamespace
import unittest

from app import main
from app.public_cache import PublicEndpointCache, PublicCacheWarmupResult, warm_public_endpoint_cache
```

Add a cleanup helper so tests do not leak monkeypatches:

```python
class MainPatchMixin:
    def patch_main(self, name: str, value) -> None:
        original = getattr(main, name)
        setattr(main, name, value)
        self.addCleanup(setattr, main, name, original)
```

Add tests:

```python
class StandardPublicWarmupTargetTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_standard_warmup_targets_use_frontend_public_cache_keys(self) -> None:
        targets = main._standard_public_cache_warmup_targets()

        self.assertEqual(
            [target.key for target in targets],
            [
                "GET /api/readiness",
                "GET /api/risk/latest",
                "GET /api/risk/history?limit=2000",
                "GET /api/risk/levels",
                "GET /api/brief/latest",
            ],
        )

    async def test_startup_warmup_skips_without_validation_data(self) -> None:
        self.patch_main("get_pool", lambda: object())

        async def empty_version(_pool):
            return "validation:empty"

        self.patch_main("fetch_public_data_version", empty_version)

        with self.assertLogs("app.access", level="INFO") as logs:
            result = await main.warm_public_read_cache_on_startup()

        self.assertEqual(result, PublicCacheWarmupResult((), ()))
        self.assertIn("public_cache_warmup_skipped reason=no_validation", "\n".join(logs.output))
```

- [ ] **Step 2: Run the focused test and confirm it fails**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache_warmup.py' -v
```

Expected: FAIL because `_standard_public_cache_warmup_targets` and `warm_public_read_cache_on_startup` do not exist.

- [ ] **Step 3: Extract reusable producers in `backend/app/main.py`**

Import the warmup helper types:

```python
from app.public_cache import (
    PublicCacheWarmupResult,
    PublicCacheWarmupTarget,
    PublicEndpointCache,
    build_cache_headers,
    etag_matches,
    no_store_headers,
    warm_public_endpoint_cache,
)
```

Add these producer helpers near `_cached_public_json_response`:

```python
async def _produce_readiness_payload() -> tuple[dict[str, Any], int]:
    pool = get_pool()
    latest = await fetch_latest_risk(pool)
    validation = await fetch_latest_validation(pool)
    return build_readiness_payload(
        latest,
        validation,
        max_age_days=settings.data_freshness_max_age_days,
    )


async def _produce_risk_latest_payload() -> tuple[dict[str, Any], int]:
    latest = await fetch_latest_risk(get_pool())
    if latest is None:
        raise HTTPException(status_code=404, detail="Risk data has not been collected yet")
    return {"data": latest}, 200


def _risk_history_producer(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 2000,
) -> Callable[[], Awaitable[tuple[dict[str, Any], int]]]:
    async def producer() -> tuple[dict[str, Any], int]:
        rows = await fetch_risk_history(get_pool(), start_date=start_date, end_date=end_date, limit=limit)
        return {"data": rows, "meta": {"returned_points": len(rows)}}, 200

    return producer


async def _produce_risk_levels_payload() -> tuple[dict[str, Any], int]:
    pool = get_pool()
    latest = await fetch_latest_risk(pool)
    source_rows = await fetch_ohlcv_history(pool)
    if latest is None or len(source_rows) < 2:
        raise HTTPException(status_code=404, detail="Risk source data has not been collected yet")

    turnover_enabled = bool(latest["turnover_enabled"])
    levels = build_risk_levels(source_rows, {"turnover_enabled": turnover_enabled})
    return {
        "data": [
            {"risk": row["risk"], "price_usd": round(row["price"], 2)}
            for row in levels["risk_level_rows"]
        ],
        "meta": {
            "base": latest,
            "methodology_version": METHODOLOGY_VERSION,
            "evaluation_date": levels["evaluation_date"].isoformat(),
            "current_price": levels["current_price"],
            "current_risk": levels["current_risk"],
            "turnover_enabled": levels["turnover_enabled"],
            "risk_step": 0.025,
            "source_row_count": len(source_rows),
        },
    }, 200


async def _produce_brief_latest_payload() -> tuple[dict[str, Any], int]:
    pool = get_pool()
    persisted = await fetch_latest_brief(pool)
    if persisted is not None:
        return {"data": persisted}, 200
    latest = await fetch_latest_risk(pool)
    if latest is None:
        raise HTTPException(status_code=404, detail="Brief data has not been collected yet")
    previous = await fetch_previous_risk(pool)
    return {"data": build_brief(latest, previous)}, 200
```

Then update the existing route functions to call these helpers instead of keeping duplicated nested producer logic.

- [ ] **Step 4: Add standard target and startup warmup functions**

Add:

```python
def _standard_public_cache_warmup_targets() -> tuple[PublicCacheWarmupTarget, ...]:
    return (
        PublicCacheWarmupTarget("GET /api/readiness", _produce_readiness_payload),
        PublicCacheWarmupTarget("GET /api/risk/latest", _produce_risk_latest_payload),
        PublicCacheWarmupTarget("GET /api/risk/history?limit=2000", _risk_history_producer(limit=2000)),
        PublicCacheWarmupTarget("GET /api/risk/levels", _produce_risk_levels_payload),
        PublicCacheWarmupTarget("GET /api/brief/latest", _produce_brief_latest_payload),
    )


async def warm_public_read_cache_on_startup() -> PublicCacheWarmupResult:
    data_version = await fetch_public_data_version(get_pool())
    if data_version == "validation:empty":
        logger.info("public_cache_warmup_skipped reason=no_validation")
        return PublicCacheWarmupResult((), ())

    try:
        readiness_payload, readiness_status = await _produce_readiness_payload()
    except Exception:
        logger.exception("public_cache_warmup_skipped reason=readiness_probe_failed")
        return PublicCacheWarmupResult((), ())

    if readiness_status != 200:
        logger.warning(
            "public_cache_warmup_skipped reason=readiness_not_ready status=%d payload_status=%s",
            readiness_status,
            readiness_payload.get("status"),
        )
        return PublicCacheWarmupResult((), ())

    result = await warm_public_endpoint_cache(
        public_read_cache,
        data_version,
        _standard_public_cache_warmup_targets(),
        logger=logger,
    )
    logger.info(
        "public_cache_warmup_complete warmed=%d failed=%d",
        len(result.warmed_keys),
        len(result.failed_keys),
    )
    return result
```

Update `lifespan`:

```python
@asynccontextmanager
async def lifespan(_app: FastAPI):
    await connect()
    try:
        await warm_public_read_cache_on_startup()
    except Exception:
        logger.exception("public_cache_warmup_failed phase=startup")
    try:
        yield
    finally:
        await disconnect()
```

- [ ] **Step 5: Run startup warmup tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache_warmup.py' -v
```

Expected: PASS.

## Task 3: Add Endpoint HIT, No-Store, And Schema Regression Tests

**Files:**
- Modify: `backend/tests/test_public_cache_warmup.py`
- Modify as needed: `backend/app/main.py`

- [ ] **Step 1: Write failing test that warmed endpoint returns `X-Cache: HIT` without rebuilding**

Add a fake request class:

```python
class FakeRequest:
    method = "GET"
    headers: dict[str, str] = {}

    def __init__(self, path: str, query: str = "") -> None:
        self.url = SimpleNamespace(path=path, query=query)
        self.client = None
```

Add the test:

```python
class WarmedEndpointResponseTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_warmed_endpoint_returns_hit_without_rebuilding(self) -> None:
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)
        self.patch_main("public_read_cache", cache)
        self.patch_main("get_pool", lambda: object())

        async def data_version(_pool):
            return "validation:ready"

        self.patch_main("fetch_public_data_version", data_version)
        calls = 0

        async def producer():
            nonlocal calls
            calls += 1
            return {"data": {"risk": 0.42}}, 200

        await warm_public_endpoint_cache(
            cache,
            "validation:ready",
            [main.PublicCacheWarmupTarget("GET /api/risk/latest", producer)],
        )

        response = await main._cached_public_json_response(FakeRequest("/api/risk/latest"), producer)

        self.assertEqual(response.headers["x-cache"], "HIT")
        self.assertEqual(response.headers["x-cache-version"], "validation:ready")
        self.assertEqual(calls, 1)
```

- [ ] **Step 2: Write waitlist no-store regression tests**

Add:

```python
class WaitlistNoStoreRegressionTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_waitlist_handler_remains_no_store(self) -> None:
        async def fake_upsert(_pool, *, contact: str, locale: str, source: str):
            return {"contact_type": "email", "locale": locale, "created": True}

        self.patch_main("get_pool", lambda: object())
        self.patch_main("upsert_waitlist_lead", fake_upsert)

        response = await main.waitlist_join(
            main.WaitlistRequest(contact="user@example.com", locale="en", source="landing")
        )

        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["pragma"], "no-cache")

    async def test_waitlist_rate_limit_response_remains_no_store(self) -> None:
        class DenyLimiter:
            def allow(self, _key: str, *, now: float) -> bool:
                return False

        self.patch_main("waitlist_rate_limiter", DenyLimiter())
        request = SimpleNamespace(
            method="POST",
            url=SimpleNamespace(path="/api/waitlist"),
            headers={},
            client=None,
        )

        async def call_next(_request):
            raise AssertionError("rate-limited request should not reach handler")

        response = await main.waitlist_rate_limit_middleware(request, call_next)

        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["pragma"], "no-cache")
```

- [ ] **Step 3: Write response schema regression tests for risk history and risk levels**

Add:

```python
class PublicPayloadSchemaRegressionTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_risk_history_payload_shape_is_unchanged(self) -> None:
        async def fake_history(_pool, *, start_date, end_date, limit):
            self.assertIsNone(start_date)
            self.assertIsNone(end_date)
            self.assertEqual(limit, 2000)
            return [
                {"timestamp": "2026-06-24T00:00:00+00:00", "risk": 0.31, "risk_state": "low"},
                {"timestamp": "2026-06-25T00:00:00+00:00", "risk": 0.32, "risk_state": "low"},
            ]

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_risk_history", fake_history)

        payload, status = await main._risk_history_producer(limit=2000)()

        self.assertEqual(status, 200)
        self.assertEqual(set(payload.keys()), {"data", "meta"})
        self.assertEqual(payload["meta"], {"returned_points": 2})
        self.assertEqual(payload["data"][0]["timestamp"], "2026-06-24T00:00:00+00:00")

    async def test_risk_levels_payload_shape_is_unchanged(self) -> None:
        latest = {
            "timestamp": "2026-06-25T00:00:00+00:00",
            "risk": 0.3025,
            "turnover_enabled": True,
        }
        source_rows = [{"date": "2026-06-24"}, {"date": "2026-06-25"}]

        async def fake_latest(_pool):
            return latest

        async def fake_source_rows(_pool):
            return source_rows

        def fake_levels(_rows, _validation):
            return {
                "risk_level_rows": [{"risk": 0.0, "price": 10000.123}, {"risk": 0.025, "price": 11000.456}],
                "evaluation_date": SimpleNamespace(isoformat=lambda: "2026-06-25"),
                "current_price": 60100.0,
                "current_risk": 0.3025,
                "turnover_enabled": True,
            }

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_latest_risk", fake_latest)
        self.patch_main("fetch_ohlcv_history", fake_source_rows)
        self.patch_main("build_risk_levels", fake_levels)

        payload, status = await main._produce_risk_levels_payload()

        self.assertEqual(status, 200)
        self.assertEqual(payload["data"], [{"risk": 0.0, "price_usd": 10000.12}, {"risk": 0.025, "price_usd": 11000.46}])
        self.assertEqual(
            set(payload["meta"].keys()),
            {
                "base",
                "methodology_version",
                "evaluation_date",
                "current_price",
                "current_risk",
                "turnover_enabled",
                "risk_step",
                "source_row_count",
            },
        )
        self.assertEqual(payload["meta"]["base"], latest)
        self.assertEqual(payload["meta"]["source_row_count"], 2)
```

- [ ] **Step 4: Run the focused backend warmup tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache*.py' -v
```

Expected: PASS, including:

- warmup populates standard cache keys;
- warmed endpoint returns `X-Cache: HIT` without rebuilding;
- validation-version changes invalidate warmed payloads;
- startup warmup skips/logs when data is absent;
- `POST /api/waitlist` remains no-store;
- risk levels/history response schemas remain unchanged.

## Task 4: Add Local-Origin Operator Warmup Command When Post-Import Warming Is Needed

**Files:**
- Create: `scripts/warm-public-cache.sh`
- Modify: `scripts/manage.sh`
- Modify: `docs/operations.md`
- Modify: `docs/production-readiness.md`
- Modify if cache semantics wording changes: `docs/api-reference.md`

This task is selected when startup-only warmup is not enough for the production workflow after manual or scheduled imports. Task 11 already showed user-visible MISS latency, so the recommended implementation is the operator command, not a public admin endpoint.

- [ ] **Step 1: Create the local-origin warmup script**

Create `scripts/warm-public-cache.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

base_url="${PUBLIC_BASE_URL:-http://localhost:3001}"
base_url="${base_url%/}"

paths=(
  "/api/readiness"
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

Make it executable:

```bash
chmod +x scripts/warm-public-cache.sh
```

The script intentionally uses normal public GET endpoints against a local/private base URL. It does not add or call an admin endpoint. The readiness request runs first with `curl -f`; if readiness is HTTP 503, the command fails before warming stale standard payloads.

- [ ] **Step 2: Add a manage subcommand**

In `scripts/manage.sh`, add:

```bash
  warm-public-cache)
    ./scripts/warm-public-cache.sh
    ;;
```

Update the usage line to include `warm-public-cache`.

- [ ] **Step 3: Verify the shell changes**

Run:

```bash
bash -n scripts/manage.sh scripts/warm-public-cache.sh
```

Expected: no syntax errors.

- [ ] **Step 4: Document post-import usage**

In `docs/operations.md`, document the local production flow:

```bash
./scripts/manage.sh run-now
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
```

For public-download or operator-downloaded CSV flows:

```bash
./scripts/manage.sh download-cmc-csv "${EXPECTED_END_DATE}"
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
```

```bash
./scripts/manage.sh import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv "${EXPECTED_END_DATE}"
PUBLIC_BASE_URL=http://127.0.0.1:3001 ./scripts/manage.sh warm-public-cache
```

State that readiness must be HTTP 200 before warming succeeds and that production stale/degraded readiness remains a blocker.

- [ ] **Step 5: Document API/cache behavior without changing response contracts**

In `docs/api-reference.md`, keep the existing public cache header contract and add one sentence to the public read caching section:

```markdown
The backend may warm these same cache keys during startup or via an operator command, but the response body shape and cache headers are the same as a normal request.
```

In `docs/production-readiness.md`, record the implementation evidence after tests pass and keep the current production data freshness blocker separate until public readiness returns HTTP 200.

## Task 5: Full Verification

**Files:**
- All files changed by Tasks 1-4.

- [ ] **Step 1: Run targeted backend tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache*.py' -v
```

Expected: PASS.

- [ ] **Step 2: Run all Python tests**

Run:

```bash
./scripts/manage.sh test-python
```

Expected: backend and collector unit tests pass.

- [ ] **Step 3: Compile Python sources**

Run:

```bash
python3 -m compileall backend collector
```

Expected: compileall completes without syntax errors.

- [ ] **Step 4: Validate compose configuration**

Run:

```bash
./scripts/manage.sh validate
```

Expected: `compose config ok`.

- [ ] **Step 5: Inspect the implementation diff**

Run:

```bash
git diff -- backend/app/public_cache.py backend/app/main.py backend/tests/test_public_cache.py backend/tests/test_public_cache_warmup.py scripts/warm-public-cache.sh scripts/manage.sh docs/operations.md docs/production-readiness.md docs/api-reference.md
git diff --check -- backend/app/public_cache.py backend/app/main.py backend/tests/test_public_cache.py backend/tests/test_public_cache_warmup.py scripts/warm-public-cache.sh scripts/manage.sh docs/operations.md docs/production-readiness.md docs/api-reference.md
```

Expected:

- no whitespace errors;
- no endpoint response shape changes;
- no public admin endpoint;
- no waitlist cache behavior change;
- docs describe local implementation and verification, not deployment completion.

## Completion Criteria

- Startup warmup runs after DB pool readiness and does not break backend startup when risk/validation data is absent.
- Warmup populates the exact standard public cache keys listed in this plan.
- A warmed public endpoint returns `X-Cache: HIT` without rebuilding the payload.
- Changing `fetch_public_data_version` output invalidates warmed payloads.
- Warmup failure is logged and isolated to the failing key or startup probe.
- `POST /api/waitlist` remains `Cache-Control: no-store`.
- `/api/risk/history` and `/api/risk/levels` response schemas are unchanged.
- Verification commands in Task 5 pass or any blocker is reported with exact command output.
- No runtime risk recomputation is moved into public request handlers.
- No commit or push is performed without a separate operator command.
