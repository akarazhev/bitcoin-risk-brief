from __future__ import annotations

import unittest
from datetime import date

from collector.history import merge_ohlcv_rows


def row(day: date, close: float, source: str) -> dict:
    return {
        "date": day,
        "open": close * 0.99,
        "high": close * 1.01,
        "low": close * 0.98,
        "close": close,
        "volume": 1_000_000.0,
        "market_cap": close * 19_000_000.0,
        "circulating_supply": 19_000_000.0,
        "source": source,
    }


class HistoryMergeTest(unittest.TestCase):
    def test_fetched_rows_override_persisted_rows_by_date(self) -> None:
        persisted = [
            row(date(2024, 1, 1), 40_000.0, "persisted"),
            row(date(2024, 1, 2), 41_000.0, "persisted"),
        ]
        fetched = [
            row(date(2024, 1, 2), 42_500.0, "fetched"),
            row(date(2024, 1, 3), 43_000.0, "fetched"),
        ]

        merged = merge_ohlcv_rows(persisted, fetched)

        self.assertEqual([item["date"] for item in merged], [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)])
        self.assertEqual(merged[1]["close"], 42_500.0)
        self.assertEqual(merged[1]["source"], "fetched")

    def test_merge_output_is_sorted_and_duplicate_free(self) -> None:
        persisted = [row(date(2024, 1, 3), 43_000.0, "persisted"), row(date(2024, 1, 1), 40_000.0, "persisted")]
        fetched = [row(date(2024, 1, 2), 42_000.0, "fetched"), row(date(2024, 1, 3), 44_000.0, "fetched")]

        merged = merge_ohlcv_rows(persisted, fetched)

        days = [item["date"] for item in merged]
        self.assertEqual(days, sorted(days))
        self.assertEqual(len(days), len(set(days)))
        self.assertEqual(merged[-1]["close"], 44_000.0)


if __name__ == "__main__":
    unittest.main()
