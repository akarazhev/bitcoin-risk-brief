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


from app.risk import RiskPoint
from collector.records import build_ohlcv_records, build_validation_payload


class CollectorRecordBuilderTest(unittest.TestCase):
    def test_ohlcv_records_preserve_row_source(self) -> None:
        rows = [
            row(date(2013, 12, 31), 800.0, "csv"),
            row(date(2014, 1, 1), 820.0, "coingecko"),
        ]

        records = build_ohlcv_records(rows)

        self.assertEqual(records[0][-1], "csv")
        self.assertEqual(records[1][-1], "coingecko")

    def test_validation_payload_includes_stitch_and_methodology_metadata(self) -> None:
        points = [
            RiskPoint(
                day=date(2014, 1, 1),
                price_hlc3=800.0,
                risk=0.5,
                score=0.0,
                trend_dev=0.0,
                vol_regime=0.0,
                turnover=None,
                z_trend_dev=0.0,
                z_vol_regime=0.0,
                z_turnover=0.0,
                turnover_enabled=False,
            )
        ]

        payload = build_validation_payload(
            points,
            turnover_enabled=False,
            source_row_count=1,
            stitch_validation={"status": "provisional_price_only", "turnover_enabled": False},
            validation={"missing_date_count": 0},
        )

        self.assertEqual(payload["methodology_version"], "crypto-scout-canonical-v1")
        self.assertEqual(payload["stitch_validation"]["status"], "provisional_price_only")
        self.assertEqual(payload["validation"]["missing_date_count"], 0)
