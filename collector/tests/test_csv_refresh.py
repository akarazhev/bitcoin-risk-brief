from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from app.risk_sources import load_btc_usd_daily_csv, write_btc_usd_daily_csv
from collector.csv_refresh import refresh_csv_from_coinmarketcap


def daily_row(day: date, close: float, source: str = "coinmarketcap_csv") -> dict:
    return {
        "date": day,
        "open": close - 1.0,
        "high": close + 2.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1_000_000.0,
        "market_cap": close * 19_000_000.0,
        "circulating_supply": 19_000_000.0,
        "source": source,
    }


class FakeCoinMarketCapClient:
    calls: list[dict] = []

    def __init__(self, *, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url

    async def fetch_bitcoin_ohlcv_historical(self, *, time_start, time_end, convert, bitcoin_id):
        self.calls.append({
            "time_start": time_start,
            "time_end": time_end,
            "convert": convert,
            "bitcoin_id": bitcoin_id,
        })
        return [
            daily_row(date(2026, 6, 25), 102.0, "coinmarketcap_api"),
            daily_row(date(2026, 6, 26), 103.0, "coinmarketcap_api"),
        ]


class CoinMarketCapCsvRefreshTest(unittest.IsolatedAsyncioTestCase):
    async def test_refresh_fetches_missing_completed_days_and_updates_csv(self) -> None:
        FakeCoinMarketCapClient.calls = []
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "btc_usd_daily.csv"
            write_btc_usd_daily_csv(
                csv_path,
                [
                    daily_row(date(2026, 6, 23), 100.0),
                    daily_row(date(2026, 6, 24), 101.0),
                ],
            )

            refreshed = await refresh_csv_from_coinmarketcap(
                csv_path,
                api_key="cmc-key",
                base_url="https://sandbox-api.coinmarketcap.com",
                bitcoin_id=1,
                convert="USD",
                now=datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc),
                client_factory=FakeCoinMarketCapClient,
            )
            rows = load_btc_usd_daily_csv(csv_path)

        self.assertEqual(refreshed, 2)
        self.assertEqual(FakeCoinMarketCapClient.calls[0]["time_start"], date(2026, 6, 25))
        self.assertEqual(FakeCoinMarketCapClient.calls[0]["time_end"], date(2026, 6, 26))
        self.assertEqual([row["date"] for row in rows], [date(2026, 6, 23), date(2026, 6, 24), date(2026, 6, 25), date(2026, 6, 26)])
        self.assertEqual(rows[-1]["close"], 103.0)

    async def test_refresh_skips_remote_fetch_without_api_key(self) -> None:
        FakeCoinMarketCapClient.calls = []
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "btc_usd_daily.csv"
            write_btc_usd_daily_csv(csv_path, [daily_row(date(2026, 6, 25), 100.0)])

            refreshed = await refresh_csv_from_coinmarketcap(
                csv_path,
                api_key="",
                base_url="https://sandbox-api.coinmarketcap.com",
                bitcoin_id=1,
                convert="USD",
                now=datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc),
                client_factory=FakeCoinMarketCapClient,
            )
            rows = load_btc_usd_daily_csv(csv_path)

        self.assertEqual(refreshed, 0)
        self.assertEqual(FakeCoinMarketCapClient.calls, [])
        self.assertEqual([row["date"] for row in rows], [date(2026, 6, 25)])


class GapCoinMarketCapClient:
    calls: list[dict] = []

    def __init__(self, *, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url

    async def fetch_bitcoin_ohlcv_historical(self, *, time_start, time_end, convert, bitcoin_id):
        self.calls.append({"time_start": time_start, "time_end": time_end})
        return [daily_row(date(2026, 6, 26), 103.0, "coinmarketcap_api")]


class CoinMarketCapCsvDeltaValidationTest(unittest.IsolatedAsyncioTestCase):
    async def test_refresh_rejects_non_contiguous_remote_delta_without_rewriting_csv(self) -> None:
        GapCoinMarketCapClient.calls = []
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "btc_usd_daily.csv"
            write_btc_usd_daily_csv(csv_path, [daily_row(date(2026, 6, 24), 101.0)])
            original_content = csv_path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing daily dates"):
                await refresh_csv_from_coinmarketcap(
                    csv_path,
                    api_key="cmc-key",
                    base_url="https://sandbox-api.coinmarketcap.com",
                    bitcoin_id=1,
                    convert="USD",
                    now=datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc),
                    client_factory=GapCoinMarketCapClient,
                )

            self.assertEqual(csv_path.read_text(encoding="utf-8"), original_content)


if __name__ == "__main__":
    unittest.main()
