from __future__ import annotations

import unittest
from datetime import date, timedelta

from app.risk import calculate_risk_series, classify_risk


def make_rows(price_multiplier: float = 1.0) -> list[dict]:
    start = date(2020, 1, 1)
    rows = []
    price = 7000.0
    for index in range(420):
        day = start + timedelta(days=index)
        price *= 1.002
        adjusted = price * (price_multiplier if index == 419 else 1.0)
        rows.append(
            {
                "date": day,
                "open": adjusted * 0.99,
                "high": adjusted * 1.02,
                "low": adjusted * 0.98,
                "close": adjusted,
                "volume": 10_000_000_000.0 + index,
                "market_cap": adjusted * 19_000_000.0,
                "circulating_supply": 19_000_000.0,
            }
        )
    return rows


class RiskCalculationTest(unittest.TestCase):
    def test_risk_series_is_bounded_and_sorted(self) -> None:
        series = calculate_risk_series(make_rows())
        self.assertEqual(len(series), 420)
        self.assertLessEqual(max(point.risk for point in series), 1.0)
        self.assertGreaterEqual(min(point.risk for point in series), 0.0)
        self.assertEqual([point.day for point in series], sorted(point.day for point in series))

    def test_final_price_shock_increases_latest_risk(self) -> None:
        baseline = calculate_risk_series(make_rows())[-1]
        shocked = calculate_risk_series(make_rows(price_multiplier=1.8))[-1]
        self.assertGreater(shocked.risk, baseline.risk)

    def test_classify_risk_uses_stable_buckets(self) -> None:
        self.assertEqual(classify_risk(0.20), "low")
        self.assertEqual(classify_risk(0.50), "neutral")
        self.assertEqual(classify_risk(0.82), "high")


if __name__ == "__main__":
    unittest.main()
