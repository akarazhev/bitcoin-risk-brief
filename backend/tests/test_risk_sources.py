from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.risk_sources import (
    build_csv_risk_dataset,
    load_btc_usd_daily_csv,
    merge_daily_rows,
    write_btc_usd_daily_csv,
)


CSV_PATH = Path(__file__).resolve().parents[2] / "collector/btc-csv/btc_usd_daily.csv"


class RiskSourceTest(unittest.TestCase):
    def test_load_btc_usd_daily_csv_uses_full_local_history_without_gaps(self) -> None:
        rows = load_btc_usd_daily_csv(CSV_PATH)

        self.assertEqual(rows[0]["date"], date(2010, 7, 13))
        self.assertGreaterEqual(rows[-1]["date"], date(2026, 6, 25))
        self.assertEqual(len(rows), (rows[-1]["date"] - rows[0]["date"]).days + 1)
        self.assertEqual({row["date"] for row in rows}, {rows[0]["date"] + (rows[index]["date"] - rows[0]["date"]) for index in range(len(rows))})
        self.assertTrue(all(row["source"] == "coinmarketcap_csv" for row in rows))
        self.assertTrue(all(row["market_cap"] > 0 for row in rows))
        self.assertTrue(all(row["circulating_supply"] > 0 for row in rows))

    def test_build_csv_risk_dataset_uses_csv_as_single_canonical_source(self) -> None:
        dataset = build_csv_risk_dataset(CSV_PATH)

        self.assertEqual(dataset["source_rows"][0]["date"], date(2010, 7, 13))
        self.assertGreaterEqual(dataset["source_rows"][-1]["date"], date(2026, 6, 25))
        self.assertEqual(len(dataset["risk_points"]), len(dataset["source_rows"]))
        self.assertTrue(dataset["validation"]["risk_range_ok"])
        self.assertEqual(dataset["validation"]["missing_date_count"], 0)
        self.assertTrue(dataset["validation"]["turnover_enabled"])
        self.assertEqual(dataset["source_strategy"], "coinmarketcap_csv")
        self.assertTrue(any(point.turnover is not None for point in dataset["risk_points"]))

    def test_write_csv_replaces_duplicate_dates_with_newer_rows(self) -> None:
        original = load_btc_usd_daily_csv(CSV_PATH)[:3]
        replacement = {**original[1], "close": original[1]["close"] + 10.0, "source": "coinmarketcap_api"}
        merged = merge_daily_rows(original, [replacement])

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "btc_usd_daily.csv"
            write_btc_usd_daily_csv(target, merged)
            reloaded = load_btc_usd_daily_csv(target)

        self.assertEqual(len(reloaded), 3)
        self.assertEqual(reloaded[1]["close"], replacement["close"])
        self.assertEqual([row["date"] for row in reloaded], sorted(row["date"] for row in reloaded))


if __name__ == "__main__":
    unittest.main()
