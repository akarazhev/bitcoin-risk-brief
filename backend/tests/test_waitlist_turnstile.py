from __future__ import annotations

import unittest

from fastapi import HTTPException

from app import main


class MainPatchMixin:
    def patch_main(self, name: str, value) -> None:
        missing = object()
        original = getattr(main, name, missing)
        setattr(main, name, value)
        if original is missing:
            self.addCleanup(delattr, main, name)
        else:
            self.addCleanup(setattr, main, name, original)


class WaitlistTurnstileTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_verifies_before_persisting(self) -> None:
        calls: list[str] = []

        async def fake_verify(token: str, *, secret: str, expected_hostnames: frozenset[str]) -> None:
            self.assertEqual(token, "fresh-token")
            calls.append("verify")

        async def fake_upsert(_pool, *, contact: str, locale: str, source: str):
            calls.append("persist")
            return {"contact_type": "email", "locale": locale, "created": True}

        self.patch_main("verify_turnstile_token", fake_verify)
        self.patch_main("upsert_waitlist_lead", fake_upsert)
        self.patch_main("get_pool", lambda: object())

        response = await main.waitlist_join(
            main.WaitlistRequest(
                contact="user@example.com",
                locale="en",
                source="landing",
                turnstile_token="fresh-token",
            )
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(calls, ["verify", "persist"])

    async def test_rejected_token_does_not_persist(self) -> None:
        async def reject(*_args, **_kwargs) -> None:
            raise main.TurnstileRejected("rejected")

        async def forbidden_upsert(*_args, **_kwargs):
            raise AssertionError("persistence must not run")

        self.patch_main("verify_turnstile_token", reject)
        self.patch_main("upsert_waitlist_lead", forbidden_upsert)
        self.patch_main("get_pool", lambda: object())

        with self.assertRaises(HTTPException) as raised:
            await main.waitlist_join(
                main.WaitlistRequest(
                    contact="user@example.com",
                    locale="en",
                    source="landing",
                    turnstile_token="bad-token",
                )
            )

        self.assertEqual(raised.exception.status_code, 403)

    async def test_unavailable_siteverify_does_not_persist(self) -> None:
        async def unavailable(*_args, **_kwargs) -> None:
            raise main.TurnstileUnavailable("offline")

        async def forbidden_upsert(*_args, **_kwargs):
            raise AssertionError("persistence must not run")

        self.patch_main("verify_turnstile_token", unavailable)
        self.patch_main("upsert_waitlist_lead", forbidden_upsert)
        self.patch_main("get_pool", lambda: object())

        with self.assertRaises(HTTPException) as raised:
            await main.waitlist_join(
                main.WaitlistRequest(
                    contact="user@example.com",
                    locale="en",
                    source="landing",
                    turnstile_token="token",
                )
            )

        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
