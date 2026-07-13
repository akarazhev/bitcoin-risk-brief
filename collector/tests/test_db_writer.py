from __future__ import annotations

import json
import sys
import types
import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object))

from collector.db_writer import delete_rows_after_csv_end, write_risk_level_snapshot


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

        self.assertEqual(deleted, {"ohlcv": 1, "risk": 1, "brief": 1, "levels": 1})
        self.assertEqual(len(pool.calls), 4)
        self.assertIn("btc_ohlcv_daily", pool.calls[0][0])
        self.assertIn("btc_risk_daily", pool.calls[1][0])
        self.assertIn("brief_snapshots", pool.calls[2][0])
        self.assertIn("risk_level_snapshots", pool.calls[3][0])
        self.assertEqual(pool.calls[0][1][0], datetime(2026, 6, 25, tzinfo=timezone.utc))


class RiskLevelSnapshotWriterTest(unittest.IsolatedAsyncioTestCase):
    async def test_write_risk_level_snapshot_persists_public_payload(self) -> None:
        pool = FakePool()
        source_rows = [
            {
                "date": date(2026, 6, 24),
                "open": 98.0,
                "high": 102.0,
                "low": 95.0,
                "close": 100.0,
                "volume": 1_000_000.0,
                "market_cap": 100.0 * 19_000_000.0,
                "circulating_supply": 19_000_000.0,
            },
            {
                "date": date(2026, 6, 25),
                "open": 99.0,
                "high": 104.0,
                "low": 96.0,
                "close": 101.0,
                "volume": 1_000_000.0,
                "market_cap": 101.0 * 19_000_000.0,
                "circulating_supply": 19_000_000.0,
            },
        ]
        point = SimpleNamespace(
            day=date(2026, 6, 25),
            price_hlc3=100.33333333333333,
            risk=0.7,
            score=1.2,
            trend_dev=0.3,
            vol_regime=0.1,
            turnover=None,
            z_trend_dev=1.0,
            z_vol_regime=0.5,
            z_turnover=None,
            turnover_enabled=False,
        )

        with patch(
            "collector.db_writer.build_risk_levels",
            return_value={
                "risk_level_rows": [{"risk": 0.35, "price": 82000.125}],
                "evaluation_date": date(2026, 6, 25),
                "current_price": 100.33333333333333,
                "current_risk": 0.7,
                "turnover_enabled": False,
            },
        ):
            await write_risk_level_snapshot(pool, source_rows, [point])

        self.assertEqual(len(pool.calls), 1)
        query, params = pool.calls[0]
        self.assertIn("risk_level_snapshots", query)
        self.assertEqual(params[0], datetime(2026, 6, 25, tzinfo=timezone.utc))
        self.assertEqual(params[1], "crypto-scout-canonical-v1")
        payload = json.loads(params[2])
        self.assertEqual(payload["data"], [{"risk": 0.35, "price_usd": 82000.12}])
        self.assertEqual(payload["meta"]["base"]["timestamp"], "2026-06-25T00:00:00+00:00")
        self.assertEqual(payload["meta"]["base"]["model_price_usd"], 100.33333333333333)
        self.assertEqual(payload["meta"]["base"]["low_usd"], 96.0)
        self.assertEqual(payload["meta"]["base"]["high_usd"], 104.0)
        self.assertEqual(payload["meta"]["source_row_count"], 2)


if __name__ == "__main__":
    unittest.main()
