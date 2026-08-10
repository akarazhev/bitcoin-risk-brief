from __future__ import annotations

from datetime import datetime, timezone
import unittest

from collector.daily_post import band_boundary, compose_daily_post


def risk_row(day: str, risk: float, state: str) -> dict:
    return {
        "timestamp": datetime.fromisoformat(day).replace(tzinfo=timezone.utc),
        "risk": risk,
        "risk_state": state,
    }


LEVELS = {
    "data": [
        {"risk": 0.30, "price_usd": 71400.0},
        {"risk": 0.70, "price_usd": 118250.0},
    ]
}


class BandBoundaryTests(unittest.TestCase):
    def test_low_points_at_the_neutral_entry(self) -> None:
        self.assertEqual(0.30, band_boundary("low", 0.24))

    def test_high_points_at_the_return_to_neutral(self) -> None:
        self.assertEqual(0.70, band_boundary("high", 0.82))

    def test_neutral_picks_the_nearer_boundary(self) -> None:
        self.assertEqual(0.30, band_boundary("neutral", 0.34))
        self.assertEqual(0.70, band_boundary("neutral", 0.66))

    def test_unknown_state_has_no_boundary(self) -> None:
        self.assertIsNone(band_boundary("unknown", 0.5))


class ComposeDailyPostTests(unittest.TestCase):
    def test_a_stable_day_states_the_value_the_delta_and_the_boundary(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("0.24", text)
        self.assertIn("low", text)
        self.assertIn("9 August 2026", text)
        self.assertIn("71,400", text)
        self.assertIn("crypto-scout-canonical-v1.1", text)
        self.assertIn("not financial advice", text.lower())
        self.assertIn("bitcoinriskbrief.minihub.app", text)

    def test_a_band_change_leads_with_the_change(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.31, "neutral"),
            previous=risk_row("2026-08-08", 0.29, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertEqual(
            "Bitcoin risk moved from low to neutral — 9 August 2026",
            text.splitlines()[0],
        )

    def test_dates_use_english_months_and_portable_single_digit_days(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-01", 0.24, "low"),
            previous=None,
            levels=None,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Bitcoin Risk Brief — 1 August 2026", text)
        self.assertNotIn("August 01", text)

    def test_a_missing_level_snapshot_omits_the_boundary_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels=None,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("band begins", text.lower())
        self.assertIn("0.24", text)

    def test_a_snapshot_without_the_needed_point_omits_the_boundary_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels={"data": [{"risk": 0.70, "price_usd": 118250.0}]},
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("band begins", text.lower())

    def test_the_first_observation_has_no_delta_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("Change:", text)

    def test_the_post_never_recommends_an_action(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.82, "high"),
            previous=risk_row("2026-08-08", 0.68, "neutral"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        ).lower()
        for word in ("buy", "sell", "cheap", "expensive", "bottom", "top", "safe", "guaranteed"):
            self.assertNotIn(word, text)
