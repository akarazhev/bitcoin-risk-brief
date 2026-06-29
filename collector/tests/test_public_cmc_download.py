from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import Any

from app.risk_sources import write_btc_usd_daily_csv
from collector.downloaded_csv import load_coinmarketcap_downloaded_csv
from collector.public_cmc_download import PublicCoinMarketCapClient, download_public_coinmarketcap_csv


def daily_row(day: date, close: float) -> dict[str, Any]:
    return {
        "date": day,
        "open": close - 1.0,
        "high": close + 2.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1_000_000.0,
        "market_cap": close * 19_000_000.0,
        "circulating_supply": 19_000_000.0,
        "source": "coinmarketcap_csv",
    }


def public_quote(day: date, close: float) -> dict[str, Any]:
    return {
        "timeOpen": f"{day.isoformat()}T00:00:00.000Z",
        "timeClose": f"{day.isoformat()}T23:59:59.999Z",
        "timeHigh": f"{day.isoformat()}T07:00:00.000Z",
        "timeLow": f"{day.isoformat()}T12:00:00.000Z",
        "quote": {
            "name": "2781",
            "open": close - 1.0,
            "high": close + 2.0,
            "low": close - 2.0,
            "close": close,
            "volume": 2_000_000.0,
            "marketCap": close * 19_000_000.0,
            "circulatingSupply": 19_000_000.0,
            "timestamp": f"{day.isoformat()}T23:59:59.999Z",
        },
    }


def public_payload(quotes: list[dict[str, Any]], *, error_code: str = "0") -> dict[str, Any]:
    return {
        "data": {"id": 1, "name": "Bitcoin", "symbol": "BTC", "quotes": quotes},
        "status": {"error_code": error_code, "error_message": "SUCCESS" if error_code == "0" else "blocked"},
    }


class FakePublicTransport:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    async def get_json(self, *, base_url: str, path: str, timeout: float, headers: dict[str, str], params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"base_url": base_url, "path": path, "headers": headers, "params": params, "timeout": timeout})
        return self.payload


class SequencePublicTransport:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = payloads
        self.calls: list[dict[str, Any]] = []

    async def get_json(self, *, base_url: str, path: str, timeout: float, headers: dict[str, str], params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"base_url": base_url, "path": path, "headers": headers, "params": params, "timeout": timeout})
        return self.payloads[len(self.calls) - 1]


class PublicCoinMarketCapDownloadTest(unittest.IsolatedAsyncioTestCase):
    async def test_download_stages_filtered_missing_range_as_csv(self) -> None:
        transport = FakePublicTransport(
            public_payload(
                [
                    public_quote(date(2026, 6, 24), 101.0),
                    public_quote(date(2026, 6, 25), 102.0),
                    public_quote(date(2026, 6, 26), 103.0),
                ]
            )
        )
        client = PublicCoinMarketCapClient(transport=transport)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            incoming_dir = temp_path / "incoming"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 24), 101.0)])

            result = await download_public_coinmarketcap_csv(
                canonical_path,
                incoming_dir,
                expected_end_date=date(2026, 6, 26),
                client=client,
            )
            downloaded_rows = load_coinmarketcap_downloaded_csv(result.downloaded_csv_path)

        self.assertEqual(result.row_count, 2)
        self.assertEqual(result.start_date, date(2026, 6, 25))
        self.assertEqual(result.end_date, date(2026, 6, 26))
        self.assertEqual(result.downloaded_csv_path.name, "coinmarketcap-public-btc-20260625-20260626.csv")
        self.assertEqual([row["date"] for row in downloaded_rows], [date(2026, 6, 25), date(2026, 6, 26)])
        self.assertEqual(downloaded_rows[-1]["close"], 103.0)
        self.assertEqual(transport.calls[0]["path"], "/data-api/v3.1/cryptocurrency/historical")
        self.assertEqual(transport.calls[0]["params"]["id"], 1)
        self.assertEqual(transport.calls[0]["params"]["convertId"], "2781")
        self.assertEqual(transport.calls[0]["params"]["interval"], "1d")

    async def test_download_paginates_public_windows_until_requested_start(self) -> None:
        transport = SequencePublicTransport(
            [
                public_payload([public_quote(date(2026, 6, 26), 103.0), public_quote(date(2026, 6, 27), 104.0)]),
                public_payload([public_quote(date(2026, 6, 25), 102.0)]),
            ]
        )
        client = PublicCoinMarketCapClient(transport=transport)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            incoming_dir = temp_path / "incoming"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 24), 101.0)])

            result = await download_public_coinmarketcap_csv(
                canonical_path,
                incoming_dir,
                expected_end_date=date(2026, 6, 27),
                client=client,
            )
            downloaded_rows = load_coinmarketcap_downloaded_csv(result.downloaded_csv_path)

        self.assertEqual(result.row_count, 3)
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual([row["date"] for row in downloaded_rows], [date(2026, 6, 25), date(2026, 6, 26), date(2026, 6, 27)])
        self.assertLess(int(transport.calls[1]["params"]["timeEnd"]), int(transport.calls[0]["params"]["timeEnd"]))

    async def test_download_skips_when_canonical_csv_is_current(self) -> None:
        transport = FakePublicTransport(public_payload([]))
        client = PublicCoinMarketCapClient(transport=transport)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 26), 103.0)])

            result = await download_public_coinmarketcap_csv(
                canonical_path,
                temp_path / "incoming",
                expected_end_date=date(2026, 6, 26),
                client=client,
            )

        self.assertIsNone(result)
        self.assertEqual(transport.calls, [])

    async def test_download_rejects_endpoint_status_error_without_writing_csv(self) -> None:
        transport = FakePublicTransport(public_payload([], error_code="500"))
        client = PublicCoinMarketCapClient(transport=transport)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            incoming_dir = temp_path / "incoming"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 24), 101.0)])

            with self.assertRaisesRegex(ValueError, "public historical endpoint returned error 500"):
                await download_public_coinmarketcap_csv(
                    canonical_path,
                    incoming_dir,
                    expected_end_date=date(2026, 6, 25),
                    client=client,
                )

            self.assertFalse(any(incoming_dir.glob("*.csv")) if incoming_dir.exists() else False)

    async def test_download_rejects_non_contiguous_filtered_range_without_writing_csv(self) -> None:
        transport = FakePublicTransport(public_payload([public_quote(date(2026, 6, 26), 103.0)]))
        client = PublicCoinMarketCapClient(transport=transport)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            incoming_dir = temp_path / "incoming"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 24), 101.0)])

            with self.assertRaisesRegex(ValueError, "missing daily dates"):
                await download_public_coinmarketcap_csv(
                    canonical_path,
                    incoming_dir,
                    expected_end_date=date(2026, 6, 26),
                    client=client,
                )

            self.assertFalse(any(incoming_dir.glob("*.csv")) if incoming_dir.exists() else False)


if __name__ == "__main__":
    unittest.main()
