from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from app import main
from app.brief import SUPPORTED_BRIEF_LOCALES
from app.public_cache import (
    PublicCacheWarmupResult,
    PublicCacheWarmupTargetResult,
    PublicEndpointCache,
    warm_public_endpoint_cache,
)


class FakeRequest:
    method = "GET"
    headers: dict[str, str] = {}

    def __init__(self, path: str, query: str = "") -> None:
        self.url = SimpleNamespace(path=path, query=query)
        self.client = None


class MainPatchMixin:
    def patch_main(self, name: str, value) -> None:
        original = getattr(main, name)
        setattr(main, name, value)
        self.addCleanup(setattr, main, name, original)


class StandardPublicWarmupTargetTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_standard_warmup_targets_use_frontend_public_cache_keys(self) -> None:
        targets = main._standard_public_cache_warmup_targets()

        self.assertEqual(
            [target.key for target in targets],
            [
                "GET /api/risk/latest",
                "GET /api/risk/history?limit=730",
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


class PublicPayloadSchemaRegressionTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_risk_latest_payload_includes_model_price_and_daily_range(self) -> None:
        latest = {
            "timestamp": "2026-06-26T00:00:00+00:00",
            "price_usd": 100000.0,
            "model_price_usd": 100000.0,
            "low_usd": 96500.0,
            "high_usd": 104250.0,
            "risk": 0.7,
            "score": 1.0,
            "risk_state": "high",
            "trend_dev": 0.2,
            "vol_regime": 0.1,
            "turnover": None,
            "z_trend_dev": 1.1,
            "z_vol_regime": 0.8,
            "z_turnover": None,
            "turnover_enabled": False,
        }

        async def fake_latest(_pool):
            return latest

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_latest_risk", fake_latest)

        payload, status = await main._produce_risk_latest_payload()

        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["price_usd"], payload["data"]["model_price_usd"])
        self.assertEqual(payload["data"]["low_usd"], 96500.0)
        self.assertEqual(payload["data"]["high_usd"], 104250.0)

    async def test_risk_history_payload_shape_is_unchanged(self) -> None:
        async def fake_history(_pool, *, start_date, end_date, limit):
            self.assertIsNone(start_date)
            self.assertIsNone(end_date)
            self.assertEqual(limit, 2000)
            return [
                {"timestamp": "2026-06-24T00:00:00+00:00", "risk": 0.31, "risk_state": "neutral"},
                {"timestamp": "2026-06-25T00:00:00+00:00", "risk": 0.32, "risk_state": "neutral"},
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

        async def no_snapshot(_pool):
            return None

        def fake_levels(_rows, _validation):
            return {
                "risk_level_rows": [
                    {"risk": 0.0, "price": 10000.123},
                    {"risk": 0.025, "price": 11000.456},
                ],
                "evaluation_date": SimpleNamespace(isoformat=lambda: "2026-06-25"),
                "current_price": 60100.0,
                "current_risk": 0.3025,
                "turnover_enabled": True,
            }

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_latest_risk_level_snapshot", no_snapshot)
        self.patch_main("fetch_latest_risk", fake_latest)
        self.patch_main("fetch_ohlcv_history", fake_source_rows)
        self.patch_main("build_risk_levels", fake_levels)

        payload, status = await main._produce_risk_levels_payload()

        self.assertEqual(status, 200)
        self.assertEqual(
            payload["data"],
            [{"risk": 0.0, "price_usd": 10000.12}, {"risk": 0.025, "price_usd": 11000.46}],
        )
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

    async def test_risk_levels_payload_uses_persisted_snapshot_without_solver(self) -> None:
        snapshot = {
            "data": [{"risk": 0.35, "price_usd": 82000.0}],
            "meta": {
                "base": {"timestamp": "2026-06-26T00:00:00+00:00", "risk": 0.7},
                "methodology_version": "crypto-scout-canonical-v1.1",
                "evaluation_date": "2026-06-26",
                "current_price": 100000.0,
                "current_risk": 0.7,
                "turnover_enabled": False,
                "risk_step": 0.025,
                "source_row_count": 5827,
            },
        }

        async def fake_snapshot(_pool):
            return snapshot

        def fail_solver(_rows, _validation):
            raise AssertionError("request path must not call build_risk_levels when a snapshot exists")

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_latest_risk_level_snapshot", fake_snapshot)
        self.patch_main("build_risk_levels", fail_solver)

        payload, status = await main._produce_risk_levels_payload()

        self.assertEqual(status, 200)
        self.assertEqual(payload, snapshot)

    async def test_brief_payload_rebuilds_legacy_persisted_snapshot_missing_locales(self) -> None:
        persisted = {
            "snapshot_version": "bitcoin-risk-brief-v1",
            "as_of": "2026-07-12T00:00:00+00:00",
            "risk": 0.24,
            "risk_state": "low",
            "price_usd": 63869.39,
            "delta_risk": 0.02,
            "sections": {
                "en": {
                    "summary": "Risk is low. BTC is closer to a discounted or washed-out regime.",
                    "what_changed": "Risk increased by 0.02 points.",
                    "avoid_now": "Avoid assuming the low-risk zone is an immediate reversal signal.",
                    "confirm_next": "Confirm with improving trend, liquidity, and reduced forced-selling pressure.",
                },
                "ru": {
                    "summary": "Риск низкий. BTC ближе к зоне дисконта или капитуляции.",
                    "what_changed": "Риск вырос на 0.02 пункта.",
                    "avoid_now": "Не стоит считать низкий риск мгновенным сигналом разворота.",
                    "confirm_next": "Проверь восстановление тренда, ликвидность и снижение давления продавцов.",
                },
            },
        }
        latest = {
            "timestamp": "2026-07-12T00:00:00+00:00",
            "risk": 0.24,
            "risk_state": "low",
            "price_usd": 63869.39,
        }
        previous = {
            "timestamp": "2026-07-11T00:00:00+00:00",
            "risk": 0.22,
            "risk_state": "low",
            "price_usd": 63500.00,
        }

        async def fake_brief(_pool):
            return persisted

        async def fake_latest(_pool):
            return latest

        async def fake_previous(_pool):
            return previous

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_latest_brief", fake_brief)
        self.patch_main("fetch_latest_risk", fake_latest)
        self.patch_main("fetch_previous_risk", fake_previous)

        payload, status = await main._produce_brief_latest_payload()

        self.assertEqual(status, 200)
        self.assertEqual(set(payload["data"]["sections"].keys()), set(SUPPORTED_BRIEF_LOCALES))
        self.assertEqual(payload["data"]["sections"]["zh"]["summary"], "风险偏低。BTC 更接近折价或被充分释放压力的状态。")
        self.assertEqual(payload["data"]["sections"]["ar"]["summary"], "المخاطر منخفضة. BTC أقرب إلى حالة خصم أو ضغط بيعي مستنفد.")


if __name__ == "__main__":
    unittest.main()
