from __future__ import annotations

import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

sys.modules.setdefault('asyncpg', types.SimpleNamespace(Pool=object))

import collector.publisher as publisher
from collector.telegram import TelegramSendError

LATEST = {
    'timestamp': datetime(2026, 8, 9, tzinfo=timezone.utc),
    'risk': 0.24,
    'risk_state': 'low',
}
PREVIOUS = {
    'timestamp': datetime(2026, 8, 8, tzinfo=timezone.utc),
    'risk': 0.25,
    'risk_state': 'low',
}
VALIDATION = {
    'covered_end': datetime(2026, 8, 9, tzinfo=timezone.utc),
    'row_count': 5872,
    'risk_range_ok': True,
    'validation_json': {
        'source': 'coinmarketcap_csv',
        'methodology_version': 'crypto-scout-canonical-v1.1',
    },
}
LEVELS = {'data': [{'risk': 0.30, 'price_usd': 71400.0}]}
NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def enabled(**overrides):
    '''Patch settings so publication is switched on unless a test says otherwise.'''
    values = {
        'telegram_bot_token': 't0ken',
        'telegram_channel_id': '@bitcoinriskbrief',
        'data_freshness_max_age_days': 2,
    }
    values.update(overrides)
    return patch.object(publisher, 'settings', types.SimpleNamespace(**values))


def repository(existing_post=None):
    '''Patch every repository and ledger call the publisher makes.'''
    return (
        patch.object(publisher, 'fetch_latest_risk', AsyncMock(return_value=LATEST)),
        patch.object(publisher, 'fetch_previous_risk', AsyncMock(return_value=PREVIOUS)),
        patch.object(publisher, 'fetch_latest_validation', AsyncMock(return_value=VALIDATION)),
        patch.object(publisher, 'fetch_latest_risk_level_snapshot', AsyncMock(return_value=LEVELS)),
        patch.object(publisher, 'fetch_telegram_post', AsyncMock(return_value=existing_post)),
        patch.object(publisher, 'record_telegram_post', AsyncMock()),
    )


class PublisherTests(unittest.IsolatedAsyncioTestCase):
    async def test_an_empty_token_publishes_nothing(self) -> None:
        send = AsyncMock()
        with enabled(telegram_bot_token=''), patch.object(publisher, 'send_channel_post', send):
            published = await publisher.publish_daily_post(object())

        self.assertFalse(published)
        send.assert_not_awaited()

    async def test_an_empty_channel_id_publishes_nothing(self) -> None:
        send = AsyncMock()
        with enabled(telegram_channel_id=''), patch.object(publisher, 'send_channel_post', send):
            published = await publisher.publish_daily_post(object())

        self.assertFalse(published)
        send.assert_not_awaited()

    async def test_a_new_covered_date_posts_once_and_records_it(self) -> None:
        send = AsyncMock(return_value=4242)
        patches = repository()
        record = patches[-1].new
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for current_patch in patches:
                current_patch.start()
            try:
                published = await publisher.publish_daily_post(object(), now=NOW)
            finally:
                for current_patch in patches:
                    current_patch.stop()

        self.assertTrue(published)
        self.assertEqual(1, send.await_count)
        record.assert_awaited_once_with(
            unittest.mock.ANY,
            as_of=LATEST['timestamp'].date(),
            message_id=4242,
            risk=0.24,
            risk_state='low',
        )

    async def test_an_already_posted_covered_date_sends_nothing(self) -> None:
        send = AsyncMock()
        patches = repository(existing_post={'as_of': LATEST['timestamp'].date()})
        record = patches[-1].new
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for current_patch in patches:
                current_patch.start()
            try:
                published = await publisher.publish_daily_post(object(), now=NOW)
            finally:
                for current_patch in patches:
                    current_patch.stop()

        self.assertFalse(published)
        send.assert_not_awaited()
        record.assert_not_awaited()

    async def test_degraded_readiness_sends_nothing_and_records_nothing(self) -> None:
        send = AsyncMock()
        record = AsyncMock()
        with (
            enabled(),
            patch.object(publisher, 'fetch_latest_risk', AsyncMock(return_value=LATEST)),
            patch.object(publisher, 'fetch_latest_validation', AsyncMock(return_value=None)),
            patch.object(publisher, 'send_channel_post', send),
            patch.object(publisher, 'record_telegram_post', record),
        ):
            published = await publisher.publish_daily_post(object(), now=NOW)

        self.assertFalse(published)
        send.assert_not_awaited()
        record.assert_not_awaited()

    async def test_a_telegram_error_does_not_record_the_date(self) -> None:
        send = AsyncMock(side_effect=TelegramSendError('rejected'))
        patches = repository()
        record = patches[-1].new
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for current_patch in patches:
                current_patch.start()
            try:
                await publisher.publish_daily_post(object(), now=NOW)
            finally:
                for current_patch in patches:
                    current_patch.stop()

        record.assert_not_awaited()

    async def test_a_telegram_error_returns_false_without_propagating(self) -> None:
        send = AsyncMock(side_effect=TelegramSendError('rejected'))
        patches = repository()
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for current_patch in patches:
                current_patch.start()
            try:
                published = await publisher.publish_daily_post(object(), now=NOW)
            finally:
                for current_patch in patches:
                    current_patch.stop()

        self.assertFalse(published)

    async def test_the_recorded_date_is_the_latest_risk_date_not_today(self) -> None:
        send = AsyncMock(return_value=4242)
        record = AsyncMock()
        patches = repository()
        patches = (*patches[:-1], patch.object(publisher, 'record_telegram_post', record))
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for current_patch in patches:
                current_patch.start()
            try:
                await publisher.publish_daily_post(object(), now=NOW)
            finally:
                for current_patch in patches:
                    current_patch.stop()

        self.assertEqual(LATEST['timestamp'].date(), record.await_args.kwargs['as_of'])


if __name__ == '__main__':
    unittest.main()
