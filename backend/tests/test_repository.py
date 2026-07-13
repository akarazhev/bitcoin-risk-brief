from __future__ import annotations

import sys
import types
import unittest
from datetime import datetime, timezone

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Record=dict, Pool=object))

from app.repository import (
    fetch_latest_risk,
    fetch_latest_risk_level_snapshot,
    fetch_ohlcv_history,
    fetch_public_data_version,
)


class FakePool:
    def __init__(self) -> None:
        self.query = ""
        self.params = ()

    async def fetch(self, query: str, *params):
        self.query = query
        self.params = params
        return [
            {
                "timestamp": datetime(2026, 6, 25, tzinfo=timezone.utc),
                "open_usd": 100.0,
                "high_usd": 110.0,
                "low_usd": 90.0,
                "close_usd": 105.0,
                "volume_usd": 1_000_000.0,
                "market_cap_usd": 105.0 * 19_000_000.0,
                "circulating_supply": 19_000_000.0,
                "source": "coinmarketcap_csv",
            }
        ]


class FakeVersionPool:
    def __init__(self, row) -> None:
        self.row = row
        self.query = ""

    async def fetchrow(self, query: str, *params):
        self.query = query
        return self.row


class FakeLatestRiskPool:
    def __init__(self, row) -> None:
        self.row = row
        self.query = ""
        self.params = ()

    async def fetchrow(self, query: str, *params):
        self.query = query
        self.params = params
        return self.row


class FakeSnapshotPool:
    def __init__(self, row) -> None:
        self.row = row
        self.query = ""
        self.params = ()

    async def fetchrow(self, query: str, *params):
        self.query = query
        self.params = params
        return self.row


def latest_risk_row(**overrides):
    row = {
        "timestamp": datetime(2026, 6, 26, tzinfo=timezone.utc),
        "price_hlc3": 100_000.0,
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
        "low_usd": 96_500.0,
        "high_usd": 104_250.0,
    }
    row.update(overrides)
    return row


class OhlcvHistoryRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_ohlcv_history_defaults_to_full_history(self) -> None:
        pool = FakePool()

        rows = await fetch_ohlcv_history(pool)

        self.assertEqual(len(rows), 1)
        self.assertNotIn("LIMIT", pool.query.upper())
        self.assertEqual(pool.params, ())


class LatestRiskRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_latest_risk_pairs_matching_ohlcv_by_timestamp(self) -> None:
        pool = FakeLatestRiskPool(latest_risk_row())

        latest = await fetch_latest_risk(pool)

        self.assertIsNotNone(latest)
        self.assertEqual(latest["price_usd"], 100_000.0)
        self.assertEqual(latest.get("model_price_usd"), 100_000.0)
        self.assertEqual(latest.get("low_usd"), 96_500.0)
        self.assertEqual(latest.get("high_usd"), 104_250.0)
        self.assertIn("LEFT JOIN btc_ohlcv_daily", pool.query)
        self.assertIn("o.timestamp = r.timestamp", pool.query)
        self.assertEqual(pool.params, ())

    async def test_fetch_latest_risk_returns_null_ohlcv_values_when_match_is_missing(self) -> None:
        pool = FakeLatestRiskPool(latest_risk_row(low_usd=None, high_usd=None))

        latest = await fetch_latest_risk(pool)

        self.assertIsNotNone(latest)
        self.assertEqual(latest["price_usd"], 100_000.0)
        self.assertEqual(latest.get("model_price_usd"), 100_000.0)
        self.assertIsNone(latest.get("low_usd"))
        self.assertIsNone(latest.get("high_usd"))


class PublicDataVersionRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_public_data_version_uses_latest_validation_marker(self) -> None:
        pool = FakeVersionPool(
            {
                "computed_at": datetime(2026, 6, 26, 1, 2, 3, tzinfo=timezone.utc),
                "covered_end": datetime(2026, 6, 26, tzinfo=timezone.utc),
                "row_count": 5827,
                "risk_range_ok": True,
            }
        )

        version = await fetch_public_data_version(pool)

        self.assertEqual(
            version,
            "validation:2026-06-26T01:02:03+00:00:2026-06-26T00:00:00+00:00:5827:true",
        )
        self.assertIn("btc_risk_validation", pool.query)

    async def test_public_data_version_is_empty_without_validation(self) -> None:
        pool = FakeVersionPool(None)

        version = await fetch_public_data_version(pool)

        self.assertEqual(version, "validation:empty")


class RiskLevelSnapshotRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_latest_risk_level_snapshot_is_bounded_by_validation_coverage(self) -> None:
        pool = FakeSnapshotPool({"payload_json": {"data": [], "meta": {"source_row_count": 2}}})

        snapshot = await fetch_latest_risk_level_snapshot(pool)

        self.assertEqual(snapshot, {"data": [], "meta": {"source_row_count": 2}})
        self.assertIn("btc_risk_validation", pool.query)
        self.assertIn("validation_key = 'latest'", pool.query)
        self.assertIn("s.as_of <= v.covered_end", pool.query)
        self.assertIn("ORDER BY s.as_of DESC", pool.query)
        self.assertEqual(pool.params, ())


if __name__ == "__main__":
    unittest.main()
