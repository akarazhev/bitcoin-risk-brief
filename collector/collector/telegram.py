from __future__ import annotations

from typing import Any

import httpx

API_BASE = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 15.0


class TelegramSendError(RuntimeError):
    """Telegram refused the message. Never carries the bot token."""


async def send_channel_post(
    *,
    token: str,
    chat_id: str,
    text: str,
    client: httpx.AsyncClient | None = None,
) -> int:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    url = f"{API_BASE}/bot{token}/sendMessage"

    owned = client is None
    active = client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        response = await active.post(url, json=payload)
    finally:
        if owned:
            await active.aclose()

    body: dict[str, Any]
    try:
        body = response.json()
    except ValueError:
        raise TelegramSendError(f"telegram returned a non-JSON response, status={response.status_code}") from None

    if not body.get("ok"):
        description = str(body.get("description", "unknown error"))
        raise TelegramSendError(f"telegram rejected the post: {description}")

    return int(body["result"]["message_id"])
