from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.readiness import build_readiness_payload


class ReadinessPayloadTest(unittest.TestCase):
    def test_ready_when_latest_risk_matches_fresh_validation(self) -> None:
        latest = {
            "timestamp": "2026-06-25T00:00:00+00:00",
            "risk": 0.3025,
        }
        validation = {
            "covered_end": datetime(2026, 6, 25, tzinfo=timezone.utc),
            "row_count": 5827,
            "risk_range_ok": True,
            "validation_json": {
                "source": "coinmarketcap_csv",
                "methodology_version": "crypto-scout-canonical-v1",
                "validation": {
                    "source_strategy": "coinmarketcap_csv",
                    "methodology_version": "crypto-scout-canonical-v1",
                },
            },
        }

        payload, status_code = build_readiness_payload(
            latest,
            validation,
            now=datetime(2026, 6, 26, 12, tzinfo=timezone.utc),
            max_age_days=2,
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["status"], "ready")
        self.assertTrue(all(payload["checks"].values()))
        self.assertEqual(payload["data"]["source"], "coinmarketcap_csv")
        self.assertEqual(payload["data"]["methodology_version"], "crypto-scout-canonical-v1")
        self.assertEqual(payload["data"]["data_age_days"], 1)

    def test_degraded_when_data_is_stale_or_source_is_wrong(self) -> None:
        latest = {"timestamp": "2026-06-20T00:00:00+00:00", "risk": 0.3}
        validation = {
            "covered_end": datetime(2026, 6, 20, tzinfo=timezone.utc),
            "row_count": 5827,
            "risk_range_ok": True,
            "validation_json": {"source": "legacy_source", "validation": {"source_strategy": "legacy_source"}},
        }

        payload, status_code = build_readiness_payload(
            latest,
            validation,
            now=datetime(2026, 6, 26, 12, tzinfo=timezone.utc),
            max_age_days=2,
        )

        self.assertEqual(status_code, 503)
        self.assertEqual(payload["status"], "degraded")
        self.assertFalse(payload["checks"]["data_fresh"])
        self.assertFalse(payload["checks"]["source_is_canonical"])

    def test_degraded_without_risk_or_validation_rows(self) -> None:
        payload, status_code = build_readiness_payload(
            None,
            None,
            now=datetime(2026, 6, 26, 12, tzinfo=timezone.utc),
            max_age_days=2,
        )

        self.assertEqual(status_code, 503)
        self.assertFalse(payload["checks"]["risk_data_available"])
        self.assertFalse(payload["checks"]["validation_available"])


if __name__ == "__main__":
    unittest.main()
