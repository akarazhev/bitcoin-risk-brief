from __future__ import annotations

import math
import unittest
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from app.risk_sources import build_merged_risk_dataset, load_early_btc_history


CSV_DIR = Path(__file__).resolve().parents[2] / "collector/btc-csv"


def _timestamp_ms(day: date) -> int:
    return int(datetime.combine(day, time.min, tzinfo=timezone.utc).timestamp() * 1000)


def _market_chart(start: date, end: date, *, seed_close: float, seed_supply: float) -> dict[str, list[list[float]]]:
    prices: list[list[float]] = []
    market_caps: list[list[float]] = []
    volumes: list[list[float]] = []
    close = seed_close
    supply = seed_supply
    current = start
    index = 0
    while current <= end:
        close = max(close * (1.001 + 0.01 * math.sin(index / 11)), 0.01)
        supply += 900.0
        market_cap = close * supply
        volume = market_cap * 0.025
        ts = _timestamp_ms(current)
        prices.append([ts, close])
        market_caps.append([ts, market_cap])
        volumes.append([ts, volume])
        current += timedelta(days=1)
        index += 1
    return {"prices": prices, "market_caps": market_caps, "total_volumes": volumes}


class RiskSourceTest(unittest.TestCase):
    def test_load_early_btc_history_uses_local_csv_without_gaps(self) -> None:
        rows = load_early_btc_history(CSV_DIR)

        self.assertEqual(rows[0]["date"], date(2010, 7, 13))
        self.assertEqual(rows[-1]["date"], date(2013, 12, 31))
        self.assertEqual(len(rows), (date(2013, 12, 31) - date(2010, 7, 13)).days + 1)
        self.assertEqual(
            {row["date"] for row in rows},
            {date(2010, 7, 13) + timedelta(days=offset) for offset in range(len(rows))},
        )
        self.assertTrue(all(row["source"] == "csv" for row in rows))
        self.assertTrue(all(row["market_cap"] > 0 for row in rows))
        self.assertTrue(all(row["circulating_supply"] > 0 for row in rows))

    def test_merged_dataset_disables_turnover_without_overlap_or_manual_audit(self) -> None:
        early_rows = load_early_btc_history(CSV_DIR)
        last = early_rows[-1]
        dataset = build_merged_risk_dataset(
            csv_dir=CSV_DIR,
            coingecko_market_chart=_market_chart(
                date(2014, 1, 1),
                date(2015, 12, 31),
                seed_close=last["close"],
                seed_supply=last["circulating_supply"],
            ),
        )

        self.assertEqual(dataset["source_rows"][0]["date"], date(2010, 7, 13))
        self.assertEqual(dataset["source_rows"][-1]["date"], date(2015, 12, 31))
        self.assertEqual(dataset["stitch_validation"]["status"], "provisional_price_only")
        self.assertFalse(dataset["stitch_validation"]["turnover_enabled"])
        self.assertIn("manual audit", dataset["stitch_validation"]["reason"].lower())
        self.assertTrue(dataset["validation"]["risk_range_ok"])
        self.assertEqual(dataset["validation"]["missing_date_count"], 0)
        self.assertEqual(len(dataset["risk_points"]), len(dataset["source_rows"]))
        self.assertTrue(all(point.turnover is None for point in dataset["risk_points"]))
        self.assertTrue(all(0.0 <= point.risk <= 1.0 for point in dataset["risk_points"]))

    def test_manual_audit_signoff_enables_turnover_without_overlap(self) -> None:
        early_rows = load_early_btc_history(CSV_DIR)
        last = early_rows[-1]
        dataset = build_merged_risk_dataset(
            csv_dir=CSV_DIR,
            coingecko_market_chart=_market_chart(
                date(2014, 1, 1),
                date(2015, 12, 31),
                seed_close=last["close"],
                seed_supply=last["circulating_supply"],
            ),
            manual_audit_signoff={
                "approved": True,
                "approved_by": "ops@example.com",
                "approved_at": "2026-06-26T00:00:00Z",
                "note": "Audited first CoinGecko rows against independent source.",
            },
        )

        self.assertEqual(dataset["stitch_validation"]["status"], "passed")
        self.assertTrue(dataset["stitch_validation"]["turnover_enabled"])
        self.assertTrue(dataset["validation"]["turnover_enabled"])
        self.assertTrue(any(point.turnover is not None for point in dataset["risk_points"]))


if __name__ == "__main__":
    unittest.main()
