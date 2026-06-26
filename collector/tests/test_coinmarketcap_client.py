from __future__ import annotations

import unittest
from datetime import date

from collector.coinmarketcap import CoinMarketCapClient, CoinMarketCapPermanentError, CoinMarketCapTransientError


def payload() -> dict:
    return {
        "data": {
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
                }
            ]
        }
    }


class FlakyTransport:
    def __init__(self) -> None:
        self.calls = 0

    async def get_json(self, *, base_url, timeout, headers, params):
        self.calls += 1
        if self.calls < 3:
            raise CoinMarketCapTransientError("rate limited")
        return payload()


class PermanentFailureTransport:
    def __init__(self) -> None:
        self.calls = 0

    async def get_json(self, *, base_url, timeout, headers, params):
        self.calls += 1
        raise CoinMarketCapPermanentError("bad request")


class CoinMarketCapClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_retries_transient_errors_with_exponential_backoff(self) -> None:
        transport = FlakyTransport()
        sleeps: list[float] = []

        async def fake_sleep(delay: float) -> None:
            sleeps.append(delay)

        client = CoinMarketCapClient(
            api_key="cmc-key",
            transport=transport,
            sleep=fake_sleep,
            max_attempts=3,
            backoff_seconds=0.5,
        )

        rows = await client.fetch_bitcoin_ohlcv_historical(
            time_start=date(2026, 6, 25),
            time_end=date(2026, 6, 25),
        )

        self.assertEqual(transport.calls, 3)
        self.assertEqual(sleeps, [0.5, 1.0])
        self.assertEqual(rows[0]["source"], "coinmarketcap_api")

    async def test_does_not_retry_permanent_errors(self) -> None:
        transport = PermanentFailureTransport()
        client = CoinMarketCapClient(api_key="cmc-key", transport=transport, max_attempts=3)

        with self.assertRaises(CoinMarketCapPermanentError):
            await client.fetch_bitcoin_ohlcv_historical(
                time_start=date(2026, 6, 25),
                time_end=date(2026, 6, 25),
            )

        self.assertEqual(transport.calls, 1)


if __name__ == "__main__":
    unittest.main()
