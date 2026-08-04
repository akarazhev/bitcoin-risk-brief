from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx


SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_ACTION = "waitlist"
TURNSTILE_TIMEOUT_SECONDS = 10.0
TURNSTILE_TOKEN_MAX_LENGTH = 2048
TOKEN_FAILURE_CODES = frozenset({"invalid-input-response", "timeout-or-duplicate"})


class TurnstileRejected(Exception):
    pass


class TurnstileUnavailable(Exception):
    pass


async def verify_turnstile_token(
    token: str,
    *,
    secret: str,
    expected_hostnames: frozenset[str],
    client: httpx.AsyncClient | None = None,
) -> None:
    if not token or len(token) > TURNSTILE_TOKEN_MAX_LENGTH:
        raise TurnstileRejected("invalid token")
    if not secret or not expected_hostnames:
        raise TurnstileUnavailable("missing server configuration")

    active_client = client
    owns_client = active_client is None
    if active_client is None:
        active_client = httpx.AsyncClient(timeout=TURNSTILE_TIMEOUT_SECONDS)

    try:
        result = await active_client.post(
            SITEVERIFY_URL,
            data={"secret": secret, "response": token},
        )
        result.raise_for_status()
        payload: Any = result.json()
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        raise TurnstileUnavailable("siteverify unavailable") from exc
    finally:
        if owns_client:
            await active_client.aclose()

    if not isinstance(payload, Mapping) or not isinstance(payload.get("success"), bool):
        raise TurnstileUnavailable("siteverify returned a malformed payload")

    if payload["success"]:
        action = payload.get("action")
        hostname = payload.get("hostname")
        if not isinstance(action, str) or not isinstance(hostname, str):
            raise TurnstileUnavailable("siteverify returned a malformed success result")
        if action != TURNSTILE_ACTION or hostname not in expected_hostnames:
            raise TurnstileRejected("siteverify rejected the token")
        return

    error_codes = payload.get("error-codes")
    if not isinstance(error_codes, list) or not all(isinstance(code, str) for code in error_codes):
        raise TurnstileUnavailable("siteverify returned a malformed failure result")
    if error_codes and set(error_codes).issubset(TOKEN_FAILURE_CODES):
        raise TurnstileRejected("siteverify rejected the token")
    raise TurnstileUnavailable("siteverify returned an unavailable failure result")
