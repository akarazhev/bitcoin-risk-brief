from __future__ import annotations

import unittest

from collector.coingecko import market_chart_to_daily_rows


class CoinGeckoTransformTest(unittest.TestCase):
    def test_market_chart_payload_becomes_sorted_daily_rows(self) -> None:
        payload = {
            "prices": [[1577836800000, 7200.0], [1577923200000, 7300.0]],
            "market_caps": [[1577836800000, 130_000_000_000.0], [1577923200000, 132_000_000_000.0]],
            "total_volumes": [[1577836800000, 20_000_000_000.0], [1577923200000, 21_000_000_000.0]],
        }
        rows = market_chart_to_daily_rows(payload)
        self.assertEqual([row["date"].isoformat() for row in rows], ["2020-01-01", "2020-01-02"])
        self.assertEqual(rows[0]["close"], 7200.0)
        self.assertGreater(rows[0]["circulating_supply"], 0)


if __name__ == "__main__":
    unittest.main()
