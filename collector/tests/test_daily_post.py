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
        self.assertIn("report date 2026-08-10", text)
        self.assertIn("Change: −0.01\n", text)
        self.assertIn("Coverage through 2026-08-09", text)
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
            "<b>Bitcoin risk moved from low to neutral</b> — report date 2026-08-10",
            text.splitlines()[0],
        )

    def test_dates_use_iso_format(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-01", 0.24, "low"),
            previous=None,
            levels=None,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("<b>Bitcoin Risk Brief</b> — report date 2026-08-02", text)
        self.assertIn("Coverage through 2026-08-01", text)

    def test_a_missing_level_snapshot_omits_the_boundary_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels=None,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("band at risk", text.lower())
        self.assertIn("0.24", text)

    def test_a_snapshot_without_the_needed_point_omits_the_boundary_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels={"data": [{"risk": 0.70, "price_usd": 118250.0}]},
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("band at risk", text.lower())

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


class ReportDateTests(unittest.TestCase):
    def test_the_headline_carries_the_report_date_one_day_after_coverage(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=risk_row("2026-08-09", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertTrue(text.startswith("<b>Bitcoin Risk Brief</b> — report date 2026-08-11"))

    def test_every_date_is_iso(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=risk_row("2026-08-09", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Change: +0.03\n", text)
        self.assertIn("Coverage through 2026-08-10", text)
        for month in ("January", "August", "December"):
            self.assertNotIn(month, text)

    def test_a_band_change_headline_also_carries_the_report_date(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.31, "neutral"),
            previous=risk_row("2026-08-09", 0.29, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertTrue(
            text.startswith(
                "<b>Bitcoin risk moved from low to neutral</b> — report date 2026-08-11"
            )
        )

    def test_a_report_date_crossing_a_month_end_is_correct(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-31", 0.24, "low"),
            previous=risk_row("2026-08-30", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("report date 2026-09-01", text)


class BandNameTests(unittest.TestCase):
    def test_from_low_the_next_band_is_neutral(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Neutral band at risk 0.30", text)

    def test_from_neutral_near_the_upper_edge_the_next_band_is_high(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.66, "neutral"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("High band at risk 0.70", text)
        self.assertNotIn("Neutral band at risk 0.70", text)

    def test_from_neutral_near_the_lower_edge_the_next_band_is_low(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.34, "neutral"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Low band at risk 0.30", text)

    def test_from_high_the_next_band_is_neutral(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.82, "high"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Neutral band at risk 0.70", text)


class FormattingTests(unittest.TestCase):
    def test_the_headline_and_the_risk_value_are_bold(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=risk_row("2026-08-09", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("<b>Bitcoin Risk Brief</b>", text)
        self.assertIn("<b>Risk 0.24 — low</b>", text)
        self.assertEqual(2, text.count("<b>"))
        self.assertEqual(2, text.count("</b>"))
        self.assertEqual(1, text.count("<i>"))
        self.assertEqual(1, text.count("</i>"))

    def test_the_advice_line_is_italic(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("<i>Analytics and research context, not financial advice.</i>", text)

    def test_data_derived_values_are_html_escaped(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1 <script>",
        )
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)

    def test_no_status_emoji_is_used(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.82, "high"),
            previous=risk_row("2026-08-09", 0.68, "neutral"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        for glyph in ("🟢", "🟡", "🔴", "🚨", "⚠️", "📈", "📉"):
            self.assertNotIn(glyph, text)

    def test_only_permitted_tags_appear(self) -> None:
        import re

        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=risk_row("2026-08-09", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        tags = set(re.findall(r"</?([a-zA-Z]+)>", text))
        self.assertLessEqual(tags, {"b", "i"})


class ChangeLineTests(unittest.TestCase):
    def test_consecutive_days_omit_the_comparison_date(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-11", 0.23, "low"),
            previous=risk_row("2026-08-10", 0.24, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Change: −0.01\n", text)
        self.assertNotIn("from 2026-08-10", text)

    def test_a_gap_names_the_day_being_compared(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-11", 0.23, "low"),
            previous=risk_row("2026-08-09", 0.24, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Change: −0.01 from 2026-08-09", text)

    def test_a_month_boundary_still_counts_as_consecutive(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-09-01", 0.23, "low"),
            previous=risk_row("2026-08-31", 0.24, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("from 2026-08-31", text)

    def test_no_previous_observation_still_omits_the_change_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-11", 0.23, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("Change:", text)
