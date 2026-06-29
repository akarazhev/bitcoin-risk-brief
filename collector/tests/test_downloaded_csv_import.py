from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.risk_sources import load_btc_usd_daily_csv, write_btc_usd_daily_csv
from collector.downloaded_csv import import_coinmarketcap_downloaded_csv


def daily_row(day: date, close: float) -> dict:
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


class CoinMarketCapDownloadedCsvImportTest(unittest.TestCase):
    def test_import_merges_downloaded_historical_csv_and_replaces_canonical_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            downloaded_path = temp_path / "bitcoin-historical-data.csv"
            write_btc_usd_daily_csv(
                canonical_path,
                [
                    daily_row(date(2026, 6, 23), 100.0),
                    daily_row(date(2026, 6, 24), 101.0),
                ],
            )
            downloaded_path.write_text(
                "\n".join(
                    [
                        "Date,Open,High,Low,Close,Volume,Market Cap",
                        "Jun 26, 2026,102,105,101,104,\"2,000,000\",\"1,976,000,000\"",
                        "Jun 25, 2026,101,104,100,103,\"1,500,000\",\"1,957,000,000\"",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = import_coinmarketcap_downloaded_csv(
                downloaded_path,
                canonical_path,
                expected_end_date=date(2026, 6, 26),
            )
            rows = load_btc_usd_daily_csv(canonical_path)

        self.assertEqual(result.downloaded_row_count, 2)
        self.assertEqual(result.written_row_count, 4)
        self.assertEqual(result.covered_end, date(2026, 6, 26))
        self.assertEqual([row["date"] for row in rows], [date(2026, 6, 23), date(2026, 6, 24), date(2026, 6, 25), date(2026, 6, 26)])
        self.assertEqual(rows[-1]["close"], 104.0)
        self.assertEqual(rows[-1]["circulating_supply"], 19_000_000.0)

    def test_import_rejects_non_contiguous_download_without_replacing_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            downloaded_path = temp_path / "bitcoin-historical-data.csv"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 24), 101.0)])
            original_content = canonical_path.read_text(encoding="utf-8")
            downloaded_path.write_text(
                "\n".join(
                    [
                        "Date,Open,High,Low,Close,Volume,Market Cap",
                        "Jun 26, 2026,102,105,101,104,\"2,000,000\",\"1,976,000,000\"",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing daily dates"):
                import_coinmarketcap_downloaded_csv(downloaded_path, canonical_path)

            self.assertEqual(canonical_path.read_text(encoding="utf-8"), original_content)

    def test_import_rejects_partial_historical_download_without_replacing_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            downloaded_path = temp_path / "bitcoin-historical-data.csv"
            write_btc_usd_daily_csv(
                canonical_path,
                [
                    daily_row(date(2026, 6, 23), 100.0),
                    daily_row(date(2026, 6, 24), 101.0),
                    daily_row(date(2026, 6, 25), 102.0),
                ],
            )
            original_content = canonical_path.read_text(encoding="utf-8")
            downloaded_path.write_text(
                "\n".join(
                    [
                        "Date,Open,High,Low,Close,Volume,Market Cap",
                        "Jun 24, 2026,101,104,100,103,\"1,500,000\",\"1,957,000,000\"",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "partial"):
                import_coinmarketcap_downloaded_csv(downloaded_path, canonical_path)

            self.assertEqual(canonical_path.read_text(encoding="utf-8"), original_content)

    def test_import_rejects_download_that_misses_expected_tail_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            downloaded_path = temp_path / "bitcoin-historical-data.csv"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 24), 101.0)])
            original_content = canonical_path.read_text(encoding="utf-8")
            downloaded_path.write_text(
                "\n".join(
                    [
                        "Date,Open,High,Low,Close,Volume,Market Cap",
                        "Jun 25, 2026,101,104,100,103,\"1,500,000\",\"1,957,000,000\"",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "expected coverage through 2026-06-26"):
                import_coinmarketcap_downloaded_csv(
                    downloaded_path,
                    canonical_path,
                    expected_end_date=date(2026, 6, 26),
                )

            self.assertEqual(canonical_path.read_text(encoding="utf-8"), original_content)

    def test_import_rejects_schema_incompatible_download_without_replacing_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            canonical_path = temp_path / "btc_usd_daily.csv"
            downloaded_path = temp_path / "bitcoin-historical-data.csv"
            write_btc_usd_daily_csv(canonical_path, [daily_row(date(2026, 6, 24), 101.0)])
            original_content = canonical_path.read_text(encoding="utf-8")
            downloaded_path.write_text(
                "Date,Open,High,Low,Close,Volume\nJun 25, 2026,101,104,100,103,\"1,500,000\"\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing required columns"):
                import_coinmarketcap_downloaded_csv(downloaded_path, canonical_path)

            self.assertEqual(canonical_path.read_text(encoding="utf-8"), original_content)


if __name__ == "__main__":
    unittest.main()
