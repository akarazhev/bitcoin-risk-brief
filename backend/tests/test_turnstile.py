from __future__ import annotations

import unittest

import httpx

from app.turnstile import TurnstileRejected, TurnstileUnavailable, verify_turnstile_token


class FakeClient:
    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def post(self, url: str, *, data: dict[str, str]) -> httpx.Response:
        self.calls.append((url, data))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def response(status: int, payload: dict[str, object] | None = None, raw: bytes | None = None) -> httpx.Response:
    request = httpx.Request("POST", "https://challenges.cloudflare.com/turnstile/v0/siteverify")
    if raw is not None:
        return httpx.Response(status, content=raw, request=request)
    return httpx.Response(status, json=payload, request=request)


class TurnstileVerifierTest(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_success_for_expected_action_and_hostname(self) -> None:
        client = FakeClient(response(200, {
            "success": True,
            "action": "waitlist",
            "hostname": "bitcoinriskbrief.minihub.app",
        }))
        await verify_turnstile_token(
            "fresh-token",
            secret="test-secret",
            expected_hostnames=frozenset({"bitcoinriskbrief.minihub.app"}),
            client=client,
        )
        self.assertEqual(client.calls[0][1], {"secret": "test-secret", "response": "fresh-token"})

    async def test_rejects_failed_wrong_action_and_wrong_hostname_results(self) -> None:
        payloads = (
            {"success": False, "action": "waitlist", "hostname": "bitcoinriskbrief.minihub.app"},
            {"success": True, "action": "login", "hostname": "bitcoinriskbrief.minihub.app"},
            {"success": True, "action": "waitlist", "hostname": "localhost"},
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(TurnstileRejected):
                    await verify_turnstile_token(
                        "token",
                        secret="secret",
                        expected_hostnames=frozenset({"bitcoinriskbrief.minihub.app"}),
                        client=FakeClient(response(200, payload)),
                    )

    async def test_rejects_empty_and_oversized_tokens(self) -> None:
        for token in ("", "x" * 2049):
            with self.subTest(length=len(token)):
                with self.assertRaises(TurnstileRejected):
                    await verify_turnstile_token(
                        token,
                        secret="secret",
                        expected_hostnames=frozenset({"localhost"}),
                        client=FakeClient(),
                    )

    async def test_treats_missing_server_configuration_as_unavailable(self) -> None:
        for secret, hostnames in (("", frozenset({"localhost"})), ("secret", frozenset())):
            with self.subTest(secret=bool(secret), hostnames=hostnames):
                with self.assertRaises(TurnstileUnavailable):
                    await verify_turnstile_token(
                        "token", secret=secret, expected_hostnames=hostnames, client=FakeClient()
                    )

    async def test_treats_network_http_and_json_failures_as_unavailable(self) -> None:
        clients = (
            FakeClient(error=httpx.ConnectError("offline")),
            FakeClient(response(502, {"success": False})),
            FakeClient(response(200, raw=b"not-json")),
        )
        for client in clients:
            with self.subTest(client=client):
                with self.assertRaises(TurnstileUnavailable):
                    await verify_turnstile_token(
                        "token",
                        secret="secret",
                        expected_hostnames=frozenset({"localhost"}),
                        client=client,
                    )
