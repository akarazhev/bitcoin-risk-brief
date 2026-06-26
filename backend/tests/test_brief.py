from __future__ import annotations

import unittest

from app.brief import build_brief


class BriefTest(unittest.TestCase):
    def test_brief_mentions_risk_state_and_change(self) -> None:
        latest = {"risk": 0.72, "risk_state": "high", "price_usd": 100000, "timestamp": "2026-06-26T00:00:00Z"}
        previous = {"risk": 0.61, "risk_state": "neutral", "price_usd": 92000, "timestamp": "2026-06-25T00:00:00Z"}
        brief = build_brief(latest, previous)
        self.assertEqual(brief["risk_state"], "high")
        self.assertIn("en", brief["sections"])
        self.assertIn("ru", brief["sections"])
        self.assertTrue(brief["delta_risk"] > 0)


if __name__ == "__main__":
    unittest.main()
