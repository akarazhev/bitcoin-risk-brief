from __future__ import annotations

import sys
import types
import unittest
from datetime import datetime, timezone

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Record=dict, Pool=object))

from app.repository import fetch_ohlcv_history


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


class OhlcvHistoryRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_ohlcv_history_defaults_to_full_history(self) -> None:
        pool = FakePool()

        rows = await fetch_ohlcv_history(pool)

        self.assertEqual(len(rows), 1)
        self.assertNotIn("LIMIT", pool.query.upper())
        self.assertEqual(pool.params, ())


if __name__ == "__main__":
    unittest.main()
