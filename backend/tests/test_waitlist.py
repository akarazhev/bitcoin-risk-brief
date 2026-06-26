from __future__ import annotations

import sys
import types
import unittest

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object, Record=dict))

from app.repository import upsert_waitlist_lead
from app.waitlist import InvalidWaitlistContact, normalize_waitlist_contact


class FakePool:
    def __init__(self) -> None:
        self.calls = []

    async def fetchrow(self, query: str, *args):
        self.calls.append((query, args))
        return {
            "id": "lead-1",
            "contact": args[0],
            "normalized_contact": args[1],
            "contact_type": args[2],
            "locale": args[3],
            "source": args[4],
            "status": "active",
            "created": True,
        }


class WaitlistValidationTest(unittest.TestCase):
    def test_normalizes_email_contact(self) -> None:
        normalized = normalize_waitlist_contact("  USER@Example.COM  ")
        self.assertEqual(normalized.contact, "USER@Example.COM")
        self.assertEqual(normalized.normalized_contact, "user@example.com")
        self.assertEqual(normalized.contact_type, "email")

    def test_normalizes_telegram_contact(self) -> None:
        normalized = normalize_waitlist_contact(" @RiskScout_42 ")
        self.assertEqual(normalized.contact, "@RiskScout_42")
        self.assertEqual(normalized.normalized_contact, "@riskscout_42")
        self.assertEqual(normalized.contact_type, "telegram")

    def test_rejects_invalid_contact(self) -> None:
        with self.assertRaises(InvalidWaitlistContact):
            normalize_waitlist_contact("not a contact")


class WaitlistRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_upsert_waitlist_lead_uses_normalized_unique_contact(self) -> None:
        pool = FakePool()
        result = await upsert_waitlist_lead(pool, contact="USER@Example.COM", locale="ru", source="landing")

        self.assertEqual(result["normalized_contact"], "user@example.com")
        self.assertEqual(result["contact_type"], "email")
        self.assertEqual(result["locale"], "ru")
        query, args = pool.calls[0]
        self.assertIn("ON CONFLICT (normalized_contact) DO UPDATE", query)
        self.assertEqual(args[:5], ("USER@Example.COM", "user@example.com", "email", "ru", "landing"))


if __name__ == "__main__":
    unittest.main()
