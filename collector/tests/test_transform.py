from __future__ import annotations

import unittest
from datetime import date

from collector.coinmarketcap import cmc_ohlcv_payload_to_daily_rows


class CoinMarketCapTransformTest(unittest.TestCase):
    def test_ohlcv_historical_payload_becomes_sorted_daily_rows(self) -> None:
        payload = {
            "data": {
                "id": 1,
                "name": "Bitcoin",
                "symbol": "BTC",
                "quotes": [
                    {
                        "time_open": "2026-06-25T00:00:00.000Z",
                        "time_close": "2026-06-25T23:59:59.999Z",
                        "time_high": "2026-06-25T07:43:00.000Z",
                        "time_low": "2026-06-25T14:00:00.000Z",
                        "quote": {
                            "USD": {
                                "open": 60992.07,
                                "high": 61868.90,
                                "low": 58075.92,
                                "close": 59721.67,
                                "volume": 40625024717.76,
                                "market_cap": 1197115487201.03,
                                "timestamp": "2026-06-25T23:59:59.999Z",
                            }
                        },
                    },
                    {
                        "time_open": "2026-06-24T00:00:00.000Z",
                        "time_close": "2026-06-24T23:59:59.999Z",
                        "time_high": "2026-06-24T11:50:00.000Z",
                        "time_low": "2026-06-24T17:49:00.000Z",
                        "quote": {
                            "USD": {
                                "open": 62663.03,
                                "high": 63097.75,
                                "low": 59029.85,
                                "close": 60995.13,
                                "volume": 42644106535.13,
                                "market_cap": 1222745567462.8,
                                "timestamp": "2026-06-24T23:59:59.999Z",
                            }
                        },
                    },
                ],
            }
        }

        rows = cmc_ohlcv_payload_to_daily_rows(payload)

        self.assertEqual([row["date"] for row in rows], [date(2026, 6, 24), date(2026, 6, 25)])
        self.assertEqual(rows[0]["open"], 62663.03)
        self.assertEqual(rows[1]["close"], 59721.67)
        self.assertGreater(rows[1]["circulating_supply"], 0)
        self.assertEqual(rows[1]["source"], "coinmarketcap_api")


if __name__ == "__main__":
    unittest.main()
