from __future__ import annotations

import logging
from typing import Any

import httpx

API_BASE = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 15.0


class TelegramSendError(RuntimeError):
    """Telegram refused the message. Never carries the bot token."""


class TelegramDeliveryUnknown(RuntimeError):
    """The request may have reached Telegram. Never carries the bot token."""


class _TelegramTokenLogRedactor(logging.Filter):
    def __init__(self, token: str) -> None:
        super().__init__()
        self._token = token

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if self._token in message:
            record.msg = message.replace(self._token, "[REDACTED]")
            record.args = ()
        return True


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
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    url = f"{API_BASE}/bot{token}/sendMessage"

    owned = client is None
    active = client if client is not None else httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
    httpx_logger = logging.getLogger("httpx")
    token_redactor = _TelegramTokenLogRedactor(token)
    httpx_logger.addFilter(token_redactor)
    try:
        try:
            response = await active.post(url, json=payload)
        except httpx.HTTPError:
            raise TelegramDeliveryUnknown("telegram delivery outcome is unknown") from None
        finally:
            httpx_logger.removeFilter(token_redactor)
    finally:
        if owned:
            await active.aclose()

    body: Any
    try:
        body = response.json()
    except ValueError:
        raise TelegramDeliveryUnknown(
            f"telegram returned a non-JSON response, status={response.status_code}"
        ) from None

    if not isinstance(body, dict):
        raise TelegramDeliveryUnknown("telegram returned an invalid JSON response")

    if body.get("ok") is False:
        description = str(body.get("description", "unknown error"))
        description = description.replace(token, "[REDACTED]")
        raise TelegramSendError(f"telegram rejected the post: {description}")

    result = body.get("result")
    message_id = result.get("message_id") if isinstance(result, dict) else None
    if body.get("ok") is not True or type(message_id) is not int:
        raise TelegramDeliveryUnknown("telegram returned an incomplete success response")

    return message_id
