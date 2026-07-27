from __future__ import annotations

import unittest
from datetime import date, timedelta
from unittest.mock import patch

from app.risk import (
    METHODOLOGY_VERSION,
    ROBUST_Z_MIN_PERIODS,
    ROBUST_Z_WINDOW,
    TURNOVER_DISABLED_WEIGHTS,
    TURNOVER_ENABLED_WEIGHTS,
    calculate_risk_series,
    classify_risk,
)
import app.risk_levels as risk_levels_module
from app.risk_levels import (
    RISK_STEP,
    build_risk_levels,
    calculate_current_risk_for_price,
    solve_price_for_target_risk,
)


def make_rows(*, days: int = 1500, final_multiplier: float = 1.0) -> list[dict]:
    start = date(2020, 1, 1)
    rows = []
    price = 7000.0
    for index in range(days):
        day = start + timedelta(days=index)
        price *= 1.0015
        adjusted = price * (final_multiplier if index == days - 1 else 1.0)
        rows.append(
            {
                "date": day,
                "open": adjusted * 0.99,
                "high": adjusted * 1.02,
                "low": adjusted * 0.98,
                "close": adjusted,
                "volume": 10_000_000_000.0 + (index * 1000.0),
                "market_cap": adjusted * 19_000_000.0,
                "circulating_supply": 19_000_000.0,
            }
        )
    return rows


class RiskCalculationTest(unittest.TestCase):
    def test_canonical_constants_match_crypto_scout_methodology(self) -> None:
        self.assertEqual(METHODOLOGY_VERSION, "crypto-scout-canonical-v1.1")
        self.assertEqual(ROBUST_Z_WINDOW, 1460)
        self.assertEqual(ROBUST_Z_MIN_PERIODS, 365)
        self.assertEqual(TURNOVER_ENABLED_WEIGHTS, {"trend_dev": 0.60, "vol_regime": 0.25, "turnover": 0.15})
        self.assertEqual(TURNOVER_DISABLED_WEIGHTS, {"trend_dev": 0.70, "vol_regime": 0.30})

    def test_risk_series_is_bounded_and_sorted(self) -> None:
        series = calculate_risk_series(make_rows(days=420))
        self.assertEqual(len(series), 420)
        self.assertLessEqual(max(point.risk for point in series), 1.0)
        self.assertGreaterEqual(min(point.risk for point in series), 0.0)
        self.assertEqual([point.day for point in series], sorted(point.day for point in series))

    def test_turnover_disabled_uses_canonical_two_factor_fallback(self) -> None:
        latest = calculate_risk_series(make_rows(days=500), turnover_enabled=False)[-1]
        self.assertFalse(latest.turnover_enabled)
        self.assertIsNone(latest.turnover)
        self.assertEqual(latest.z_turnover, 0.0)
        expected_score = (
            TURNOVER_DISABLED_WEIGHTS["trend_dev"] * latest.z_trend_dev
            + TURNOVER_DISABLED_WEIGHTS["vol_regime"] * latest.z_vol_regime
        )
        self.assertAlmostEqual(latest.score, expected_score, places=12)

    def test_final_price_shock_increases_latest_risk(self) -> None:
        baseline = calculate_risk_series(make_rows(days=1500))[-1]
        shocked = calculate_risk_series(make_rows(days=1500, final_multiplier=1.8))[-1]
        self.assertGreater(shocked.risk, baseline.risk)

    def test_classify_risk_uses_stable_buckets(self) -> None:
        self.assertEqual(classify_risk(0.299999), "low")
        self.assertEqual(classify_risk(0.30), "neutral")
        self.assertEqual(classify_risk(0.50), "neutral")
        self.assertEqual(classify_risk(0.699999), "neutral")
        self.assertEqual(classify_risk(0.70), "high")


class RiskLevelSolverTest(unittest.TestCase):
    def test_risk_levels_use_canonical_risk_step(self) -> None:
        levels = build_risk_levels(make_rows(days=1500), {"turnover_enabled": True})
        risk_rows = levels["risk_level_rows"]
        self.assertEqual(len(risk_rows), 41)
        self.assertEqual(risk_rows[0]["risk"], 0.0)
        self.assertEqual(risk_rows[-1]["risk"], 1.0)
        self.assertAlmostEqual(risk_rows[1]["risk"] - risk_rows[0]["risk"], RISK_STEP)

    def test_build_risk_levels_reuses_solver_context_for_all_targets(self) -> None:
        rows = make_rows(days=1500)
        stitch_validation = {"turnover_enabled": True}

        with patch(
            "app.risk_levels._build_level_context",
            wraps=risk_levels_module._build_level_context,
        ) as build_context:
            levels = build_risk_levels(rows, stitch_validation)

        self.assertEqual(build_context.call_count, 1)
        self.assertEqual(len(levels["risk_level_rows"]), 41)
        self.assertGreater(len(levels["price_level_rows"]), 0)

    def test_solver_verifies_target_risk_through_same_formula(self) -> None:
        rows = make_rows(days=1500)
        stitch_validation = {"turnover_enabled": True}
        current_price = (rows[-1]["high"] + rows[-1]["low"] + rows[-1]["close"]) / 3.0
        current_risk = calculate_current_risk_for_price(rows, stitch_validation, current_price)
        target_risk = min(0.95, current_risk + 0.05)
        solved_price = solve_price_for_target_risk(rows, stitch_validation, target_risk)
        verified_risk = calculate_current_risk_for_price(rows, stitch_validation, solved_price)
        self.assertGreater(solved_price, current_price)
        self.assertAlmostEqual(verified_risk, target_risk, delta=0.01)


if __name__ == "__main__":
    unittest.main()
