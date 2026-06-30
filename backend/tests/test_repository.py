from __future__ import annotations

import sys
import types
import unittest
from datetime import datetime, timezone

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Record=dict, Pool=object))

from app.repository import fetch_ohlcv_history, fetch_public_data_version


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


class OhlcvHistoryRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_ohlcv_history_defaults_to_full_history(self) -> None:
        pool = FakePool()

        rows = await fetch_ohlcv_history(pool)

        self.assertEqual(len(rows), 1)
        self.assertNotIn("LIMIT", pool.query.upper())
        self.assertEqual(pool.params, ())


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


if __name__ == "__main__":
    unittest.main()
