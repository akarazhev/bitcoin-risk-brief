from __future__ import annotations

import sys
import types
import unittest
from datetime import date, datetime, timezone

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object))

from collector.db_writer import delete_rows_after_csv_end


class FakePool:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    async def execute(self, query: str, *params):
        self.calls.append((query, params))
        return "DELETE 1"


class DbWriterCleanupTest(unittest.IsolatedAsyncioTestCase):
    async def test_delete_rows_after_csv_end_removes_future_canonical_rows(self) -> None:
        pool = FakePool()

        deleted = await delete_rows_after_csv_end(pool, date(2026, 6, 25))

        self.assertEqual(deleted, {"ohlcv": 1, "risk": 1, "brief": 1})
        self.assertEqual(len(pool.calls), 3)
        self.assertIn("btc_ohlcv_daily", pool.calls[0][0])
        self.assertIn("btc_risk_daily", pool.calls[1][0])
        self.assertIn("brief_snapshots", pool.calls[2][0])
        self.assertEqual(pool.calls[0][1][0], datetime(2026, 6, 25, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
