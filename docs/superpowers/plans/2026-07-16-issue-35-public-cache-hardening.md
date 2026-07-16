# Issue 35 Public Cache Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden backend public endpoint cache warmup and cold-miss behavior for GitHub issue #35 while keeping production verification deferred until the next deploy/import window.

**Architecture:** Keep the cache local and in-process. Version cache storage and in-flight rebuilds by `(public cache key, data version)`, run startup warmup targets concurrently with isolated per-target failures, log deterministic warmup summaries, and explicitly document that backend in-process stale-while-revalidate is deferred. Do not introduce Redis, a public admin endpoint, or response body/header contract changes.

**Tech Stack:** Python 3.13, FastAPI, `unittest`, async functions, existing `backend/app/public_cache.py`, existing public cache tests.

---

## Scope Boundaries

Implement locally verifiable parts of #35:

- coalesce concurrent cold misses for the same `(cache key, data version)`;
- preserve strict validation-version boundaries;
- run backend startup warmup targets concurrently;
- record per-target warmup durations and log slowest targets;
- preserve existing public response bodies and cache headers;
- keep `POST /api/waitlist` uncached with `Cache-Control: no-store` and `Pragma: no-cache`;
- document backend in-process stale-while-revalidate as deferred.

Do not close GitHub issue #35. Final status must say local implementation and tests are complete, with production GET-only verification pending until the next deploy/import window.

Do not implement #36 in this plan. If `/api/risk/levels` shows up as a slow warmup target, mention that as evidence for prioritizing #36 later.

## Files

- Modify: `backend/app/public_cache.py`
  - Add in-flight build coalescing.
  - Store cache entries by `(key, data_version)`.
  - Add warmup target result timing data.
  - Run warmup targets concurrently.
  - Add slowest-target formatting helper on the warmup result.
- Modify: `backend/app/main.py`
  - Log startup warmup summary with warmed count, failed count, total duration, and slowest targets.
  - Keep readiness and waitlist behavior unchanged.
- Modify: `backend/tests/test_public_cache.py`
  - Add cold-miss coalescing tests.
  - Add version-boundary tests.
  - Update warmup tests for concurrent execution, target durations, and failure isolation.
- Modify: `backend/tests/test_public_cache_warmup.py`
  - Add startup warmup logging test.
  - Keep existing waitlist no-store and response-shape regressions.
- Modify: `docs/api-reference.md`
  - Clarify backend cache TTL, in-flight coalescing, validation-version rebuilds, and deferred backend stale-while-revalidate.
- Modify: `docs/operations.md`
  - Document concurrent startup warmup logging and production verification still required after deploy.

---

### Task 1: Add Public Cache Coalescing Tests

**Files:**
- Modify: `backend/tests/test_public_cache.py`
- Test: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Add async imports**

At the top of `backend/tests/test_public_cache.py`, replace the import block:

```python
from __future__ import annotations

import unittest
```

with:

```python
from __future__ import annotations

import asyncio
import contextlib
import unittest
```

- [ ] **Step 2: Add a failing concurrent cold-miss coalescing test**

In `PublicEndpointCacheTest`, after `test_refreshes_payload_after_ttl_expires`, add:

```python
    async def test_coalesces_concurrent_cold_misses_for_same_key_and_data_version(self) -> None:
        calls = 0
        producer_started = asyncio.Event()
        release_producer = asyncio.Event()
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)

        async def producer():
            nonlocal calls
            calls += 1
            producer_started.set()
            await release_producer.wait()
            return {"data": {"risk": 0.42}}, 200

        first_task = asyncio.create_task(
            cache.get_or_build("GET /api/risk/latest", "validation:ready", producer)
        )
        await producer_started.wait()
        second_task = asyncio.create_task(
            cache.get_or_build("GET /api/risk/latest", "validation:ready", producer)
        )
        await asyncio.sleep(0)

        release_producer.set()
        first_result, second_result = await asyncio.gather(first_task, second_task)
        first_entry, first_hit = first_result
        second_entry, second_hit = second_result

        self.assertEqual(calls, 1)
        self.assertFalse(first_hit)
        self.assertTrue(second_hit)
        self.assertEqual(second_entry.content, first_entry.content)
        self.assertEqual(second_entry.etag, first_entry.etag)
```

- [ ] **Step 3: Add a failing test that failures are shared but do not poison retries**

In `PublicEndpointCacheTest`, after the coalescing test, add:

```python
    async def test_coalesced_failure_does_not_poison_later_retry(self) -> None:
        calls = 0
        producer_started = asyncio.Event()
        release_producer = asyncio.Event()
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)

        async def failing_producer():
            nonlocal calls
            calls += 1
            producer_started.set()
            await release_producer.wait()
            raise RuntimeError("temporary build failure")

        first_task = asyncio.create_task(
            cache.get_or_build("GET /api/risk/latest", "validation:ready", failing_producer)
        )
        await producer_started.wait()
        second_task = asyncio.create_task(
            cache.get_or_build("GET /api/risk/latest", "validation:ready", failing_producer)
        )
        await asyncio.sleep(0)

        release_producer.set()
        with self.assertRaisesRegex(RuntimeError, "temporary build failure"):
            await first_task
        with self.assertRaisesRegex(RuntimeError, "temporary build failure"):
            await second_task
        self.assertEqual(calls, 1)

        async def successful_producer():
            nonlocal calls
            calls += 1
            return {"data": {"risk": 0.43}}, 200

        entry, hit = await cache.get_or_build(
            "GET /api/risk/latest",
            "validation:ready",
            successful_producer,
        )

        self.assertFalse(hit)
        self.assertEqual(calls, 2)
        self.assertEqual(entry.content["data"]["risk"], 0.43)
```

- [ ] **Step 4: Add a failing version-boundary test**

In `PublicEndpointCacheTest`, after the retry test, add:

```python
    async def test_new_data_version_rebuilds_without_waiting_for_old_version_build(self) -> None:
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)
        old_started = asyncio.Event()
        release_old = asyncio.Event()
        old_calls = 0
        new_calls = 0

        async def old_producer():
            nonlocal old_calls
            old_calls += 1
            old_started.set()
            await release_old.wait()
            return {"data": {"risk": 0.41}}, 200

        old_task = asyncio.create_task(
            cache.get_or_build("GET /api/risk/latest", "validation:old", old_producer)
        )
        await old_started.wait()

        async def new_producer():
            nonlocal new_calls
            new_calls += 1
            return {"data": {"risk": 0.44}}, 200

        new_entry, new_hit = await cache.get_or_build(
            "GET /api/risk/latest",
            "validation:new",
            new_producer,
        )

        release_old.set()
        old_entry, old_hit = await old_task

        self.assertFalse(new_hit)
        self.assertFalse(old_hit)
        self.assertEqual(old_calls, 1)
        self.assertEqual(new_calls, 1)
        self.assertEqual(old_entry.data_version, "validation:old")
        self.assertEqual(new_entry.data_version, "validation:new")
        self.assertEqual(new_entry.content["data"]["risk"], 0.44)

        async def rebuild_should_not_run():
            raise AssertionError("new version cache entry was not retained")

        retained_entry, retained_hit = await cache.get_or_build(
            "GET /api/risk/latest",
            "validation:new",
            rebuild_should_not_run,
        )

        self.assertTrue(retained_hit)
        self.assertEqual(retained_entry.content["data"]["risk"], 0.44)
```

- [ ] **Step 5: Run the focused cache test and verify it fails**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache.PublicEndpointCacheTest -v
```

Expected: FAIL before implementation. At least `test_coalesces_concurrent_cold_misses_for_same_key_and_data_version` should fail because `calls` is `2`, or the version-boundary retention test should fail with a rebuild assertion if an old in-flight build overwrites a newer entry.

---

### Task 2: Implement Public Cache In-Flight Coalescing

**Files:**
- Modify: `backend/app/public_cache.py`
- Test: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Add `asyncio` import**

In `backend/app/public_cache.py`, replace:

```python
import hashlib
import json
import logging
import time
```

with:

```python
import asyncio
import hashlib
import json
import logging
import time
```

- [ ] **Step 2: Add cache storage key type**

After `PayloadProducer = Callable[[], Awaitable[tuple[Any, int]]]`, add:

```python
CacheStorageKey = tuple[str, str]
```

- [ ] **Step 3: Update `PublicEndpointCache.__init__`**

Replace the existing `__init__` method body:

```python
    def __init__(self, *, ttl_seconds: int, clock: Callable[[], float] | None = None) -> None:
        self.ttl_seconds = max(0, ttl_seconds)
        self._clock = clock or time.monotonic
        self._entries: dict[str, CachedEndpointPayload] = {}
```

with:

```python
    def __init__(self, *, ttl_seconds: int, clock: Callable[[], float] | None = None) -> None:
        self.ttl_seconds = max(0, ttl_seconds)
        self._clock = clock or time.monotonic
        self._entries: dict[CacheStorageKey, CachedEndpointPayload] = {}
        self._inflight_builds: dict[CacheStorageKey, asyncio.Task[CachedEndpointPayload]] = {}
```

- [ ] **Step 4: Replace `get_or_build` with coalescing implementation**

Replace the full `get_or_build` method with:

```python
    async def get_or_build(
        self,
        key: str,
        data_version: str,
        producer: PayloadProducer,
    ) -> tuple[CachedEndpointPayload, bool]:
        storage_key = (key, data_version)
        now = self._clock()
        entry = self._entries.get(storage_key)
        if entry and entry.expires_at > now:
            return entry, True

        inflight = self._inflight_builds.get(storage_key)
        if inflight is not None:
            return await inflight, True

        task = asyncio.create_task(self._build_and_store(storage_key, key, data_version, producer))
        self._inflight_builds[storage_key] = task
        try:
            return await task, False
        finally:
            if self._inflight_builds.get(storage_key) is task:
                del self._inflight_builds[storage_key]
```

- [ ] **Step 5: Add `_build_and_store` helper**

Inside `PublicEndpointCache`, after `get_or_build` and before `invalidate`, add:

```python
    async def _build_and_store(
        self,
        storage_key: CacheStorageKey,
        key: str,
        data_version: str,
        producer: PayloadProducer,
    ) -> CachedEndpointPayload:
        content, status_code = await producer()
        now = self._clock()
        entry = CachedEndpointPayload(
            content=content,
            status_code=status_code,
            data_version=data_version,
            etag=_build_etag(key, data_version, content),
            expires_at=now + self.ttl_seconds,
        )
        self._entries[storage_key] = entry
        self._prune(now)
        return entry
```

- [ ] **Step 6: Update `_prune` for tuple storage keys**

Replace `_prune` with:

```python
    def _prune(self, now: float) -> None:
        expired_keys = [
            storage_key
            for storage_key, entry in self._entries.items()
            if entry.expires_at <= now
        ]
        for storage_key in expired_keys:
            del self._entries[storage_key]
```

Keep `invalidate()` as:

```python
    def invalidate(self) -> None:
        self._entries.clear()
```

- [ ] **Step 7: Run the coalescing test**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache.PublicEndpointCacheTest -v
```

Expected: PASS for all `PublicEndpointCacheTest` tests.

- [ ] **Step 8: Commit**

Run:

```bash
git add backend/app/public_cache.py backend/tests/test_public_cache.py
git commit -m "feat: coalesce public cache cold misses"
```

---

### Task 3: Add Warmup Result Timing Tests

**Files:**
- Modify: `backend/tests/test_public_cache.py`
- Test: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Import new result type in the test**

Update the import from `app.public_cache` in `backend/tests/test_public_cache.py` from:

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

to:

```python
from app.public_cache import (
    PublicCacheWarmupResult,
    PublicCacheWarmupTarget,
    PublicCacheWarmupTargetResult,
    PublicEndpointCache,
    build_cache_headers,
    etag_matches,
    no_store_headers,
    warm_public_endpoint_cache,
)
```

- [ ] **Step 2: Add a failing slowest-target formatting test**

In `CacheHeaderTest`, before `test_build_cache_headers_marks_hit_and_validator`, add:

```python
    def test_warmup_result_formats_slowest_targets(self) -> None:
        result = PublicCacheWarmupResult(
            warmed_keys=("fast", "slow", "medium"),
            failed_keys=(),
            total_duration_ms=20.0,
            target_results=(
                PublicCacheWarmupTargetResult("fast", 1.2, cache_hit=False),
                PublicCacheWarmupTargetResult("slow", 12.4, cache_hit=False),
                PublicCacheWarmupTargetResult("medium", 6.8, cache_hit=True),
            ),
        )

        self.assertEqual(result.slowest_summary(limit=2), "slow:12.4ms,medium:6.8ms")
```

- [ ] **Step 3: Add a failing empty slowest-target formatting test**

In `CacheHeaderTest`, after the previous test, add:

```python
    def test_warmup_result_formats_empty_slowest_targets(self) -> None:
        result = PublicCacheWarmupResult(warmed_keys=(), failed_keys=())

        self.assertEqual(result.slowest_summary(), "none")
```

- [ ] **Step 4: Run the focused formatting tests and verify they fail**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache.CacheHeaderTest -v
```

Expected: FAIL because `PublicCacheWarmupTargetResult`, `total_duration_ms`, `target_results`, or `slowest_summary` does not exist yet.

---

### Task 4: Add Warmup Result Timing Types

**Files:**
- Modify: `backend/app/public_cache.py`
- Test: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Add target result dataclass**

In `backend/app/public_cache.py`, after `PublicCacheWarmupTarget`, add:

```python
@dataclass(frozen=True)
class PublicCacheWarmupTargetResult:
    key: str
    duration_ms: float
    cache_hit: bool
    error: str | None = None
```

- [ ] **Step 2: Extend `PublicCacheWarmupResult`**

Replace:

```python
@dataclass(frozen=True)
class PublicCacheWarmupResult:
    warmed_keys: tuple[str, ...]
    failed_keys: tuple[str, ...]
```

with:

```python
@dataclass(frozen=True)
class PublicCacheWarmupResult:
    warmed_keys: tuple[str, ...]
    failed_keys: tuple[str, ...]
    total_duration_ms: float = 0.0
    target_results: tuple[PublicCacheWarmupTargetResult, ...] = ()

    def slowest_summary(self, *, limit: int = 3) -> str:
        if not self.target_results:
            return "none"
        slowest = sorted(
            self.target_results,
            key=lambda target_result: target_result.duration_ms,
            reverse=True,
        )[: max(0, limit)]
        if not slowest:
            return "none"
        return ",".join(
            f"{target_result.key}:{target_result.duration_ms:.1f}ms"
            for target_result in slowest
        )
```

- [ ] **Step 3: Run formatting tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache.CacheHeaderTest -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add backend/app/public_cache.py backend/tests/test_public_cache.py
git commit -m "feat: add public cache warmup timing result"
```

---

### Task 5: Add Concurrent Warmup Tests

**Files:**
- Modify: `backend/tests/test_public_cache.py`
- Test: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Update warmup order assertion for concurrency**

In `PublicEndpointCacheWarmupTest.test_warmup_populates_standard_cache_keys`, replace:

```python
        self.assertEqual(calls, ["readiness", "latest", "history", "levels", "brief"])
```

with:

```python
        self.assertCountEqual(calls, ["readiness", "latest", "history", "levels", "brief"])
```

- [ ] **Step 2: Add a failing concurrent warmup test**

In `PublicEndpointCacheWarmupTest`, after `test_warmup_populates_standard_cache_keys`, add:

```python
    async def test_warmup_runs_independent_targets_concurrently(self) -> None:
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)
        started: list[str] = []
        both_started = asyncio.Event()
        release = asyncio.Event()

        def make_blocking_producer(name: str):
            async def producer():
                started.append(name)
                if len(started) == 2:
                    both_started.set()
                await release.wait()
                return {"data": {"name": name}}, 200

            return producer

        warmup_task = asyncio.create_task(
            warm_public_endpoint_cache(
                cache,
                "validation:ready",
                [
                    PublicCacheWarmupTarget("GET /api/risk/latest", make_blocking_producer("latest")),
                    PublicCacheWarmupTarget("GET /api/brief/latest", make_blocking_producer("brief")),
                ],
            )
        )

        try:
            await asyncio.wait_for(both_started.wait(), timeout=0.2)
        except asyncio.TimeoutError as exc:
            release.set()
            with contextlib.suppress(Exception):
                await warmup_task
            raise AssertionError("warmup targets did not start concurrently") from exc

        release.set()
        result = await warmup_task

        self.assertEqual(result.warmed_keys, ("GET /api/risk/latest", "GET /api/brief/latest"))
        self.assertEqual(result.failed_keys, ())
        self.assertEqual([target.key for target in result.target_results], list(result.warmed_keys))
        self.assertTrue(all(target.duration_ms >= 0.0 for target in result.target_results))
```

- [ ] **Step 3: Update failure-isolation test expectations**

In `PublicEndpointCacheWarmupTest.test_warmup_logs_failure_and_keeps_warming_other_keys`, replace:

```python
        self.assertIn("public_cache_warmup_failed key=GET /api/risk/latest", "\n".join(logs.output))
```

with:

```python
        self.assertIn("public_cache_warmup_failed key=GET /api/risk/latest", "\n".join(logs.output))
        self.assertIn("duration_ms=", "\n".join(logs.output))
        self.assertEqual([target.key for target in result.target_results], [
            "GET /api/risk/latest",
            "GET /api/brief/latest",
        ])
        self.assertEqual(result.target_results[0].error, "Risk data has not been collected yet")
        self.assertIsNone(result.target_results[1].error)
```

- [ ] **Step 4: Run the warmup tests and verify they fail**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache.PublicEndpointCacheWarmupTest -v
```

Expected: FAIL before implementation. The concurrency test should fail with `warmup targets did not start concurrently`, and result timing assertions should fail because `target_results` is still empty.

---

### Task 6: Implement Concurrent Warmup With Per-Target Timing

**Files:**
- Modify: `backend/app/public_cache.py`
- Test: `backend/tests/test_public_cache.py`

- [ ] **Step 1: Add private target warm helper**

In `backend/app/public_cache.py`, after `PublicEndpointCache._prune`, add:

```python
async def _warm_public_cache_target(
    cache: PublicEndpointCache,
    data_version: str,
    target: PublicCacheWarmupTarget,
    *,
    logger: logging.Logger,
    timer: Callable[[], float],
) -> PublicCacheWarmupTargetResult:
    start = timer()
    try:
        _entry, cache_hit = await cache.get_or_build(target.key, data_version, target.producer)
    except Exception as exc:
        duration_ms = max(0.0, (timer() - start) * 1000.0)
        logger.warning(
            "public_cache_warmup_failed key=%s duration_ms=%.1f error=%s",
            target.key,
            duration_ms,
            exc,
            exc_info=True,
        )
        return PublicCacheWarmupTargetResult(
            target.key,
            duration_ms,
            cache_hit=False,
            error=str(exc),
        )

    duration_ms = max(0.0, (timer() - start) * 1000.0)
    return PublicCacheWarmupTargetResult(
        target.key,
        duration_ms,
        cache_hit=cache_hit,
    )
```

- [ ] **Step 2: Replace `warm_public_endpoint_cache` with concurrent implementation**

Replace the full `warm_public_endpoint_cache` function with:

```python
async def warm_public_endpoint_cache(
    cache: PublicEndpointCache,
    data_version: str,
    targets: list[PublicCacheWarmupTarget] | tuple[PublicCacheWarmupTarget, ...],
    *,
    logger: logging.Logger | None = None,
    timer: Callable[[], float] | None = None,
) -> PublicCacheWarmupResult:
    active_logger = logger or logging.getLogger(__name__)
    active_timer = timer or time.perf_counter
    start = active_timer()

    target_results = tuple(
        await asyncio.gather(
            *(
                _warm_public_cache_target(
                    cache,
                    data_version,
                    target,
                    logger=active_logger,
                    timer=active_timer,
                )
                for target in targets
            )
        )
    )

    total_duration_ms = max(0.0, (active_timer() - start) * 1000.0)
    warmed_keys = tuple(
        target_result.key for target_result in target_results if target_result.error is None
    )
    failed_keys = tuple(
        target_result.key for target_result in target_results if target_result.error is not None
    )
    return PublicCacheWarmupResult(
        warmed_keys,
        failed_keys,
        total_duration_ms=total_duration_ms,
        target_results=target_results,
    )
```

- [ ] **Step 3: Run public cache tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add backend/app/public_cache.py backend/tests/test_public_cache.py
git commit -m "feat: run public cache warmup concurrently"
```

---

### Task 7: Add Startup Warmup Summary Logging Test

**Files:**
- Modify: `backend/tests/test_public_cache_warmup.py`
- Test: `backend/tests/test_public_cache_warmup.py`

- [ ] **Step 1: Import `PublicCacheWarmupTargetResult`**

In `backend/tests/test_public_cache_warmup.py`, replace:

```python
from app.public_cache import (
    PublicCacheWarmupResult,
    PublicEndpointCache,
    warm_public_endpoint_cache,
)
```

with:

```python
from app.public_cache import (
    PublicCacheWarmupResult,
    PublicCacheWarmupTargetResult,
    PublicEndpointCache,
    warm_public_endpoint_cache,
)
```

- [ ] **Step 2: Add a failing startup logging test**

In `StandardPublicWarmupTargetTest`, after `test_startup_warmup_skips_without_validation_data`, add:

```python
    async def test_startup_warmup_logs_duration_and_slowest_targets(self) -> None:
        self.patch_main("get_pool", lambda: object())

        async def ready_version(_pool):
            return "validation:ready"

        async def healthy_readiness():
            return {"status": "ready"}, 200

        async def fake_warmup(_cache, _data_version, _targets, *, logger, **_kwargs):
            return PublicCacheWarmupResult(
                warmed_keys=("GET /api/risk/latest",),
                failed_keys=("GET /api/risk/levels",),
                total_duration_ms=18.5,
                target_results=(
                    PublicCacheWarmupTargetResult("GET /api/risk/latest", 3.2, cache_hit=False),
                    PublicCacheWarmupTargetResult(
                        "GET /api/risk/levels",
                        15.3,
                        cache_hit=False,
                        error="solver unavailable",
                    ),
                ),
            )

        self.patch_main("fetch_public_data_version", ready_version)
        self.patch_main("_produce_readiness_payload", healthy_readiness)
        self.patch_main("warm_public_endpoint_cache", fake_warmup)

        with self.assertLogs("app.access", level="INFO") as logs:
            result = await main.warm_public_read_cache_on_startup()

        self.assertEqual(result.total_duration_ms, 18.5)
        log_output = "\n".join(logs.output)
        self.assertIn("public_cache_warmup_complete warmed=1 failed=1", log_output)
        self.assertIn("duration_ms=18.5", log_output)
        self.assertIn(
            "slowest=GET /api/risk/levels:15.3ms,GET /api/risk/latest:3.2ms",
            log_output,
        )
```

- [ ] **Step 3: Run the startup warmup tests and verify they fail**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache_warmup.StandardPublicWarmupTargetTest -v
```

Expected: FAIL because `warm_public_read_cache_on_startup()` still logs only warmed and failed counts.

---

### Task 8: Implement Startup Warmup Summary Logging

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_public_cache_warmup.py`

- [ ] **Step 1: Update startup warmup log statement**

In `backend/app/main.py`, replace:

```python
    logger.info(
        "public_cache_warmup_complete warmed=%d failed=%d",
        len(result.warmed_keys),
        len(result.failed_keys),
    )
```

with:

```python
    logger.info(
        "public_cache_warmup_complete warmed=%d failed=%d duration_ms=%.1f slowest=%s",
        len(result.warmed_keys),
        len(result.failed_keys),
        result.total_duration_ms,
        result.slowest_summary(),
    )
```

- [ ] **Step 2: Run startup warmup tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache_warmup.StandardPublicWarmupTargetTest -v
```

Expected: PASS.

- [ ] **Step 3: Run all public cache tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache*.py' -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add backend/app/main.py backend/tests/test_public_cache_warmup.py
git commit -m "feat: log public cache warmup timings"
```

---

### Task 9: Document Cache Semantics And Deferred Backend SWR

**Files:**
- Modify: `docs/api-reference.md`
- Modify: `docs/operations.md`

- [ ] **Step 1: Update API reference cache semantics**

In `docs/api-reference.md`, replace lines in the "Public Read Caching" section that currently say:

```markdown
| `Cache-Control` | Defaults to `public, max-age=60, stale-while-revalidate=300`; tune with `PUBLIC_CACHE_MAX_AGE_SECONDS` and `PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS`. |
```

with:

```markdown
| `Cache-Control` | Defaults to `public, max-age=60, stale-while-revalidate=300`; tune with `PUBLIC_CACHE_MAX_AGE_SECONDS` and `PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS`. The stale-while-revalidate directive is for browser and edge caches; backend in-process stale-while-revalidate is intentionally deferred. |
```

- [ ] **Step 2: Add backend TTL and version-boundary paragraph**

In `docs/api-reference.md`, after:

```markdown
Clients may send `If-None-Match` with the last `ETag`; unchanged responses return HTTP 304. The backend cache TTL is
controlled by `PUBLIC_CACHE_TTL_SECONDS` and defaults to 300 seconds. The cache key includes the full request path and
query string, so filtered history requests are cached separately.
```

add:

```markdown
Concurrent backend cold misses for the same request key and `X-Cache-Version` are coalesced so one rebuild is shared by
matching requests. When an in-process entry expires and the validation marker is unchanged, the backend rebuilds
synchronously rather than serving an expired in-process payload. When the validation marker changes, the next matching
public read also rebuilds synchronously for the new version; stale in-process data is not served across
`X-Cache-Version` boundaries.
```

- [ ] **Step 3: Update operations warmup section**

In `docs/operations.md`, replace:

```markdown
The backend warms standard public product payloads during startup after the database pool is ready and readiness is
healthy. If validation data is missing, readiness cannot be probed, or readiness returns a non-200 status, startup
warmup is skipped and logged so degraded or stale data is not hidden.
```

with:

```markdown
The backend warms standard public product payloads during startup after the database pool is ready and readiness is
healthy. Startup warmup runs the standard product targets concurrently, isolates per-target failures, and logs
`public_cache_warmup_complete` with warmed count, failed count, total duration, and the slowest targets. If validation
data is missing, readiness cannot be probed, or readiness returns a non-200 status, startup warmup is skipped and logged
so degraded or stale data is not hidden.
```

- [ ] **Step 4: Add deferred production verification note**

In `docs/operations.md`, after:

```markdown
`POST /api/waitlist` must remain uncached. Confirm it returns `Cache-Control: no-store` during launch checks.
```

add:

```markdown
For issue #35, local verification can cover backend cache correctness, warmup timing, and header behavior. Keep the issue
open until a deployed production version has been checked with GET-only public endpoint smoke tests and startup/import
warmup log review.
```

- [ ] **Step 5: Review docs diff**

Run:

```bash
git diff -- docs/api-reference.md docs/operations.md
```

Expected: diff only clarifies cache semantics and production verification. It must not claim production verification is complete.

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/api-reference.md docs/operations.md
git commit -m "docs: clarify public cache hardening semantics"
```

---

### Task 10: Final Local Verification

**Files:**
- Verify: `backend/app/public_cache.py`
- Verify: `backend/app/main.py`
- Verify: `backend/tests/test_public_cache.py`
- Verify: `backend/tests/test_public_cache_warmup.py`
- Verify: `docs/api-reference.md`
- Verify: `docs/operations.md`

- [ ] **Step 1: Run required public-cache verification**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache*.py' -v
```

Expected: PASS. This is the required issue #35 verification command.

- [ ] **Step 2: Run broader backend tests if local dependencies allow**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -v
```

Expected: PASS. If unrelated tests fail because optional local dependencies or services are unavailable, record the exact failing tests and keep the public-cache verification from Step 1 as the required gate.

- [ ] **Step 3: Check formatting-sensitive diff**

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 4: Review changed files**

Run:

```bash
git diff --stat HEAD~3..HEAD
git diff -- backend/app/public_cache.py backend/app/main.py backend/tests/test_public_cache.py backend/tests/test_public_cache_warmup.py docs/api-reference.md docs/operations.md
```

Expected:

- `PublicEndpointCache` stores entries and in-flight tasks by `(key, data_version)`;
- concurrent cold misses for the same key/version share one producer call;
- validation-version changes rebuild synchronously and do not serve old entries;
- `warm_public_endpoint_cache` gathers targets concurrently and preserves per-target failure isolation;
- startup warmup logs `duration_ms` and `slowest=...`;
- public response headers remain generated by `build_cache_headers()` with the same names and values;
- waitlist no-store tests still pass;
- docs state backend in-process stale-while-revalidate is deferred;
- docs state production verification is still pending.

- [ ] **Step 5: Final status for the user**

Report:

```text
Implemented local #35 cache hardening and verified with:
- PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache*.py' -v
- git diff --check

Production verification is still pending. Keep GitHub issue #35 open until the next deploy/import window confirms readiness no-store, public cache headers, repeated-read HIT behavior, and startup/import warmup logs in production.
```

Do not claim issue #35 is fully complete until production verification is done.

---

## Production Verification Later

When the implementation is deployed later, run GET-only production checks:

```bash
curl -sD - -o /tmp/bitcoin-risk-readiness.json https://<production-host>/api/readiness
curl -sD - -o /tmp/bitcoin-risk-latest-1.json https://<production-host>/api/risk/latest
curl -sD - -o /tmp/bitcoin-risk-latest-2.json https://<production-host>/api/risk/latest
curl -sD - -o /tmp/bitcoin-risk-history.json 'https://<production-host>/api/risk/history?limit=2000'
curl -sD - -o /tmp/bitcoin-risk-levels.json https://<production-host>/api/risk/levels
curl -sD - -o /tmp/bitcoin-risk-brief.json https://<production-host>/api/brief/latest
```

Expected:

- `/api/readiness` returns `Cache-Control: no-store` and `Pragma: no-cache`;
- public product reads return `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`;
- repeated public reads return `X-Cache: HIT` after the backend cache is warmed;
- startup or import warmup logs include warmed count, failed count, total duration, and slowest targets;
- no production waitlist POST is performed unless the operator explicitly approves a test contact.
