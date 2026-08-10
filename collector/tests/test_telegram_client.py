from __future__ import annotations

import unittest

import httpx

from collector.telegram import TelegramSendError, send_channel_post


def transport(handler):
    return httpx.MockTransport(handler)


class TelegramClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_posts_to_the_channel_and_returns_the_message_id(self) -> None:
        seen: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = request.content.decode()
            return httpx.Response(200, json={"ok": True, "result": {"message_id": 4242}})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            message_id = await send_channel_post(
                token="t0ken", chat_id="@bitcoinriskbrief", text="hello", client=client
            )

        self.assertEqual(4242, message_id)
        self.assertIn("/bott0ken/sendMessage", str(seen["url"]))
        self.assertIn("bitcoinriskbrief", str(seen["body"]))

    async def test_raises_on_a_telegram_level_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"ok": False, "description": "chat not found"})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            with self.assertRaises(TelegramSendError) as caught:
                await send_channel_post(
                    token="t0ken", chat_id="@nope", text="hello", client=client
                )

        self.assertIn("chat not found", str(caught.exception))

    async def test_raises_when_ok_is_false_despite_http_200(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"ok": False, "description": "not enough rights"})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            with self.assertRaises(TelegramSendError):
                await send_channel_post(
                    token="t0ken", chat_id="@bitcoinriskbrief", text="hello", client=client
                )

    async def test_never_puts_the_token_in_the_error_message(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"ok": False, "description": "Unauthorized"})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            with self.assertRaises(TelegramSendError) as caught:
                await send_channel_post(
                    token="sup3rs3cret", chat_id="@bitcoinriskbrief", text="hello", client=client
                )

        self.assertNotIn("sup3rs3cret", str(caught.exception))
