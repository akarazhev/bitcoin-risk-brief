from __future__ import annotations

import unittest

from app.brief import build_brief


SUPPORTED_LOCALES = {"en", "ru", "zh", "de", "fr", "es", "ar"}


class BriefTest(unittest.TestCase):
    def test_brief_mentions_risk_state_and_change(self) -> None:
        latest = {"risk": 0.72, "risk_state": "high", "price_usd": 100000, "timestamp": "2026-06-26T00:00:00Z"}
        previous = {"risk": 0.61, "risk_state": "neutral", "price_usd": 92000, "timestamp": "2026-06-25T00:00:00Z"}
        brief = build_brief(latest, previous)
        self.assertEqual(brief["risk_state"], "high")
        self.assertEqual(set(brief["sections"].keys()), SUPPORTED_LOCALES)
        self.assertTrue(brief["delta_risk"] > 0)

    def test_brief_sections_are_conservative_in_every_locale(self) -> None:
        latest = {"risk": 0.28, "risk_state": "low", "price_usd": 62000, "timestamp": "2026-06-26T00:00:00Z"}
        previous = {"risk": 0.35, "risk_state": "neutral", "price_usd": 64000, "timestamp": "2026-06-25T00:00:00Z"}
        brief = build_brief(latest, previous)

        for locale in SUPPORTED_LOCALES:
            with self.subTest(locale=locale):
                section = brief["sections"][locale]
                self.assertTrue(section["summary"])
                self.assertTrue(section["what_changed"])
                self.assertTrue(section["avoid_now"])
                self.assertTrue(section["confirm_next"])
                for field in ("summary", "what_changed", "avoid_now", "confirm_next"):
                    copy = section[field].lower()
                    self.assertNotIn("buy now", copy)
                    self.assertNotIn("sell now", copy)

        self.assertIn("Risk cooled", brief["sections"]["en"]["what_changed"])
        self.assertIn("Риск снизился", brief["sections"]["ru"]["what_changed"])
        self.assertIn("风险下降", brief["sections"]["zh"]["what_changed"])
        self.assertIn("Risiko ging zurück", brief["sections"]["de"]["what_changed"])
        self.assertIn("Le risque a reculé", brief["sections"]["fr"]["what_changed"])
        self.assertIn("El riesgo bajó", brief["sections"]["es"]["what_changed"])
        self.assertIn("انخفضت المخاطر", brief["sections"]["ar"]["what_changed"])


if __name__ == "__main__":
    unittest.main()
