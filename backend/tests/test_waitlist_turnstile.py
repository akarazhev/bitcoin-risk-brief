from __future__ import annotations

import unittest

from fastapi import HTTPException
import httpx

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


class WaitlistAsgiNoStoreTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.persisted: list[str] = []

        class AllowLimiter:
            def allow(self, _key: str, *, now: float) -> bool:
                return True

        async def fake_verify(token: str, *, secret: str, expected_hostnames: frozenset[str]) -> None:
            if token == "rejected-token":
                raise main.TurnstileRejected("rejected")
            if token == "unavailable-token":
                raise main.TurnstileUnavailable("unavailable")

        async def fake_upsert(_pool, *, contact: str, locale: str, source: str):
            self.persisted.append(contact)
            return {"contact_type": "email", "locale": locale, "created": True}

        self.patch_main("waitlist_rate_limiter", AllowLimiter())
        self.patch_main("verify_turnstile_token", fake_verify)
        self.patch_main("upsert_waitlist_lead", fake_upsert)
        self.patch_main("get_pool", lambda: object())
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app),
            base_url="http://testserver",
        )
        self.addAsyncCleanup(self.client.aclose)

    async def test_all_waitlist_outcomes_are_no_store_and_failures_do_not_persist(self) -> None:
        cases = (
            ({"contact": "user@example.com", "locale": "en", "source": "landing"}, 422, []),
            ({"contact": "user@example.com", "locale": "en", "source": "landing", "turnstile_token": ""}, 422, []),
            ({"contact": "user@example.com", "locale": "en", "source": "landing", "turnstile_token": "rejected-token"}, 403, []),
            ({"contact": "user@example.com", "locale": "en", "source": "landing", "turnstile_token": "unavailable-token"}, 503, []),
            ({"contact": "user@example.com", "locale": "en", "source": "landing", "turnstile_token": "fresh-token"}, 201, ["user@example.com"]),
        )

        for payload, expected_status, expected_persisted in cases:
            with self.subTest(expected_status=expected_status):
                response = await self.client.post("/api/waitlist", json=payload)

                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(response.headers["pragma"], "no-cache")
                self.assertEqual(self.persisted, expected_persisted)


if __name__ == "__main__":
    unittest.main()
