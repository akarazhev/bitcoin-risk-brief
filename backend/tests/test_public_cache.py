from __future__ import annotations

import asyncio
import contextlib
import unittest

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


class PublicEndpointCacheTest(unittest.IsolatedAsyncioTestCase):
    async def test_reuses_payload_for_same_key_and_data_version(self) -> None:
        calls = 0
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)

        async def producer():
            nonlocal calls
            calls += 1
            return {"data": {"risk": 0.42}}, 200

        first_entry, first_hit = await cache.get_or_build(
            "GET /api/risk/latest",
            "validation:2026-06-26T00:00:00Z",
            producer,
        )
        second_entry, second_hit = await cache.get_or_build(
            "GET /api/risk/latest",
            "validation:2026-06-26T00:00:00Z",
            producer,
        )

        self.assertFalse(first_hit)
        self.assertTrue(second_hit)
        self.assertEqual(calls, 1)
        self.assertEqual(second_entry.content, first_entry.content)
        self.assertEqual(second_entry.etag, first_entry.etag)

    async def test_refreshes_payload_when_data_version_changes(self) -> None:
        values = [{"data": {"risk": 0.42}}, {"data": {"risk": 0.45}}]
        cache = PublicEndpointCache(ttl_seconds=60, clock=lambda: 100.0)

        async def producer():
            return values.pop(0), 200

        first_entry, first_hit = await cache.get_or_build(
            "GET /api/risk/latest",
            "validation:2026-06-26T00:00:00Z",
            producer,
        )
        second_entry, second_hit = await cache.get_or_build(
            "GET /api/risk/latest",
            "validation:2026-06-27T00:00:00Z",
            producer,
        )

        self.assertFalse(first_hit)
        self.assertFalse(second_hit)
        self.assertNotEqual(second_entry.content, first_entry.content)
        self.assertNotEqual(second_entry.etag, first_entry.etag)

    async def test_refreshes_payload_after_ttl_expires(self) -> None:
        now = 100.0
        values = [{"data": {"risk": 0.42}}, {"data": {"risk": 0.43}}]
        cache = PublicEndpointCache(ttl_seconds=30, clock=lambda: now)

        async def producer():
            return values.pop(0), 200

        await cache.get_or_build("GET /api/risk/latest", "version-a", producer)
        now = 131.0
        entry, hit = await cache.get_or_build("GET /api/risk/latest", "version-a", producer)

        self.assertFalse(hit)
        self.assertEqual(entry.content["data"]["risk"], 0.43)

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


class CacheHeaderTest(unittest.TestCase):
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

    def test_warmup_result_formats_empty_slowest_targets(self) -> None:
        result = PublicCacheWarmupResult(warmed_keys=(), failed_keys=())

        self.assertEqual(result.slowest_summary(), "none")

    def test_build_cache_headers_marks_hit_and_validator(self) -> None:
        headers = build_cache_headers(
            etag='"abc123"',
            data_version="validation:2026-06-26T00:00:00Z",
            cache_hit=True,
            max_age_seconds=60,
            stale_while_revalidate_seconds=300,
        )

        self.assertEqual(headers["ETag"], '"abc123"')
        self.assertEqual(headers["X-Cache"], "HIT")
        self.assertEqual(headers["X-Cache-Version"], "validation:2026-06-26T00:00:00Z")
        self.assertEqual(headers["Cache-Control"], "public, max-age=60, stale-while-revalidate=300")

    def test_etag_matches_single_or_listed_if_none_match_value(self) -> None:
        self.assertTrue(etag_matches('"abc123"', '"abc123"'))
        self.assertTrue(etag_matches('"abc123"', '"stale", "abc123"'))
        self.assertTrue(etag_matches('"abc123"', "*"))
        self.assertFalse(etag_matches('"abc123"', '"stale"'))

    def test_no_store_headers_prevent_waitlist_caching(self) -> None:
        headers = no_store_headers()

        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Pragma"], "no-cache")


if __name__ == "__main__":
    unittest.main()
