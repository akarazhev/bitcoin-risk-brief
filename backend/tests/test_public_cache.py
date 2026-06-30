from __future__ import annotations

import unittest

from app.public_cache import (
    PublicEndpointCache,
    build_cache_headers,
    etag_matches,
    no_store_headers,
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


class CacheHeaderTest(unittest.TestCase):
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
