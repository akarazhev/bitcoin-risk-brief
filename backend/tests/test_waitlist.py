from __future__ import annotations

from pathlib import Path
import re
import sys
import types
import unittest

from pydantic import ValidationError

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object, Record=dict))

from app.main import WaitlistRequest
from app.repository import upsert_waitlist_lead
from app.waitlist import InvalidWaitlistContact, normalize_locale, normalize_waitlist_contact

ROOT = Path(__file__).resolve().parents[2]
ISSUE_28_LOCALES = {"en", "ru", "zh", "de", "fr", "es", "ar"}


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

    def test_rejects_telegram_contact(self) -> None:
        with self.assertRaises(InvalidWaitlistContact):
            normalize_waitlist_contact(" @RiskScout_42 ")

    def test_rejects_invalid_contact(self) -> None:
        with self.assertRaises(InvalidWaitlistContact):
            normalize_waitlist_contact("not a contact")

    def test_accepts_issue_28_locales(self) -> None:
        for locale in ISSUE_28_LOCALES:
            with self.subTest(locale=locale):
                self.assertEqual(normalize_locale(locale), locale)

    def test_unknown_locale_falls_back_to_english(self) -> None:
        self.assertEqual(normalize_locale("it"), "en")
        self.assertEqual(normalize_locale(""), "en")
        self.assertEqual(normalize_locale(None), "en")


class WaitlistRequestModelTest(unittest.TestCase):
    def test_model_requires_turnstile_token_and_accepts_maximum_length_token(self) -> None:
        with self.assertRaises(ValidationError):
            WaitlistRequest(
                contact="user@example.com",
                locale="unsupported-locale-value",
                source="landing",
            )

        payload = WaitlistRequest(
            contact="user@example.com",
            locale="unsupported-locale-value",
            source="landing",
            turnstile_token="x" * 2048,
        )

        self.assertEqual(payload.locale, "unsupported-locale-value")
        self.assertEqual(payload.turnstile_token, "x" * 2048)


class WaitlistSchemaTest(unittest.TestCase):
    def assert_schema_accepts_issue_28_waitlist_locales(self, relative_path: str) -> None:
        sql = (ROOT / relative_path).read_text(encoding="utf-8")
        match = re.search(r"waitlist_leads_locale_check CHECK \(locale IN \(([^)]+)\)\)", sql)

        self.assertIsNotNone(match)
        assert match is not None
        schema_locales = {token.strip().strip("'") for token in match.group(1).split(",")}
        self.assertEqual(schema_locales, ISSUE_28_LOCALES)

    def test_initial_schema_accepts_issue_28_waitlist_locales(self) -> None:
        self.assert_schema_accepts_issue_28_waitlist_locales("migrations/001_initial_schema.sql")

    def test_existing_schema_migration_accepts_issue_28_waitlist_locales(self) -> None:
        self.assert_schema_accepts_issue_28_waitlist_locales("migrations/003_expand_waitlist_locales.sql")


class WaitlistRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_upsert_waitlist_lead_uses_normalized_unique_contact(self) -> None:
        pool = FakePool()
        result = await upsert_waitlist_lead(pool, contact="USER@Example.COM", locale="ar", source="landing")

        self.assertEqual(result["normalized_contact"], "user@example.com")
        self.assertEqual(result["contact_type"], "email")
        self.assertEqual(result["locale"], "ar")
        query, args = pool.calls[0]
        self.assertIn("ON CONFLICT (normalized_contact) DO UPDATE", query)
        self.assertEqual(args[:5], ("USER@Example.COM", "user@example.com", "email", "ar", "landing"))


class EmailOnlyContactTests(unittest.TestCase):
    def test_a_telegram_handle_is_rejected(self) -> None:
        with self.assertRaises(InvalidWaitlistContact):
            normalize_waitlist_contact("@someholder")

    def test_an_email_is_still_accepted_and_normalised(self) -> None:
        result = normalize_waitlist_contact("USER@Example.COM")
        self.assertEqual("email", result.contact_type)
        self.assertEqual("user@example.com", result.normalized_contact)
        self.assertEqual("USER@Example.COM", result.contact)

    def test_no_input_can_produce_the_telegram_contact_type(self) -> None:
        for candidate in ("@bitcoinriskbrief", "@a_user_name", "@12345678"):
            with self.subTest(candidate=candidate):
                with self.assertRaises(InvalidWaitlistContact):
                    normalize_waitlist_contact(candidate)


if __name__ == "__main__":
    unittest.main()
