from __future__ import annotations

import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

sys.modules.setdefault('asyncpg', types.SimpleNamespace(Pool=object))

import collector.db_writer as db_writer
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


def repository(claim_granted=True):
    '''Patch every repository and ledger call the publisher makes.'''
    return (
        patch.object(publisher, 'fetch_latest_risk', AsyncMock(return_value=LATEST)),
        patch.object(publisher, 'fetch_previous_risk', AsyncMock(return_value=PREVIOUS)),
        patch.object(publisher, 'fetch_latest_validation', AsyncMock(return_value=VALIDATION)),
        patch.object(publisher, 'fetch_latest_risk_level_snapshot', AsyncMock(return_value=LEVELS)),
        patch.object(publisher, 'claim_telegram_post', AsyncMock(return_value=claim_granted)),
        patch.object(publisher, 'confirm_telegram_post', AsyncMock()),
        patch.object(publisher, 'release_telegram_post', AsyncMock()),
    )


class FakeTelegramPool:
    def __init__(self) -> None:
        self.rows: dict[object, dict[str, object]] = {}

    def acquire(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False

    async def fetchrow(self, query: str, *params):
        if 'INSERT INTO telegram_posts (as_of, risk, risk_state)' not in query:
            raise AssertionError(f'Unexpected fetchrow query: {query}')
        as_of, risk, risk_state = params
        if as_of in self.rows:
            return None
        self.rows[as_of] = {
            'as_of': as_of,
            'risk': risk,
            'risk_state': risk_state,
            'message_id': None,
        }
        return {'as_of': as_of}

    async def execute(self, query: str, *params):
        if 'UPDATE telegram_posts SET message_id' in query:
            as_of, message_id = params
            self.rows[as_of]['message_id'] = message_id
        elif 'DELETE FROM telegram_posts' in query:
            (as_of,) = params
            if self.rows[as_of]['message_id'] is None:
                del self.rows[as_of]
        else:
            raise AssertionError(f'Unexpected execute query: {query}')


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

    async def test_a_new_covered_date_posts_once_and_confirms_it(self) -> None:
        send = AsyncMock(return_value=4242)
        patches = repository()
        confirm = patches[-2].new
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
        confirm.assert_awaited_once_with(
            unittest.mock.ANY,
            as_of=LATEST['timestamp'].date(),
            message_id=4242,
        )

    async def test_a_refused_claim_sends_nothing_and_returns_false(self) -> None:
        send = AsyncMock()
        patches = repository(claim_granted=False)
        confirm = patches[-2].new
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
        confirm.assert_not_awaited()

    async def test_degraded_readiness_sends_nothing_and_records_nothing(self) -> None:
        send = AsyncMock()
        claim = AsyncMock()
        with (
            enabled(),
            patch.object(publisher, 'fetch_latest_risk', AsyncMock(return_value=LATEST)),
            patch.object(publisher, 'fetch_latest_validation', AsyncMock(return_value=None)),
            patch.object(publisher, 'send_channel_post', send),
            patch.object(publisher, 'claim_telegram_post', claim),
        ):
            published = await publisher.publish_daily_post(object(), now=NOW)

        self.assertFalse(published)
        send.assert_not_awaited()
        claim.assert_not_awaited()

    async def test_a_telegram_error_releases_the_claim(self) -> None:
        pool = FakeTelegramPool()
        send = AsyncMock(side_effect=TelegramSendError('rejected'))
        with (
            enabled(),
            patch.object(publisher, 'fetch_latest_risk', AsyncMock(return_value=LATEST)),
            patch.object(publisher, 'fetch_previous_risk', AsyncMock(return_value=PREVIOUS)),
            patch.object(publisher, 'fetch_latest_validation', AsyncMock(return_value=VALIDATION)),
            patch.object(publisher, 'fetch_latest_risk_level_snapshot', AsyncMock(return_value=LEVELS)),
            patch.object(publisher, 'send_channel_post', send),
        ):
            published = await publisher.publish_daily_post(pool, now=NOW)

        self.assertFalse(published)
        self.assertNotIn(LATEST['timestamp'].date(), pool.rows)

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

    async def test_the_confirmed_date_is_the_latest_risk_date_not_today(self) -> None:
        send = AsyncMock(return_value=4242)
        confirm = AsyncMock()
        patches = repository()
        patches = (*patches[:-2], patch.object(publisher, 'confirm_telegram_post', confirm), patches[-1])
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for current_patch in patches:
                current_patch.start()
            try:
                await publisher.publish_daily_post(object(), now=NOW)
            finally:
                for current_patch in patches:
                    current_patch.stop()

        self.assertEqual(LATEST['timestamp'].date(), confirm.await_args.kwargs['as_of'])

    async def test_an_empty_token_does_not_read_the_repository(self) -> None:
        latest = AsyncMock()
        with enabled(telegram_bot_token=''), patch.object(publisher, 'fetch_latest_risk', latest):
            published = await publisher.publish_daily_post(object())

        self.assertFalse(published)
        latest.assert_not_awaited()

    async def test_an_empty_channel_id_does_not_read_the_repository(self) -> None:
        latest = AsyncMock()
        with enabled(telegram_channel_id=''), patch.object(publisher, 'fetch_latest_risk', latest):
            published = await publisher.publish_daily_post(object())

        self.assertFalse(published)
        latest.assert_not_awaited()

    async def test_release_does_not_delete_a_confirmed_row(self) -> None:
        pool = FakeTelegramPool()
        as_of = LATEST['timestamp'].date()
        pool.rows[as_of] = {'as_of': as_of, 'message_id': 4242}

        await db_writer.release_telegram_post(pool, as_of=as_of)

        self.assertEqual(4242, pool.rows[as_of]['message_id'])

    async def test_a_successful_send_stores_the_returned_message_id(self) -> None:
        pool = FakeTelegramPool()
        send = AsyncMock(return_value=4242)
        with (
            enabled(),
            patch.object(publisher, 'fetch_latest_risk', AsyncMock(return_value=LATEST)),
            patch.object(publisher, 'fetch_previous_risk', AsyncMock(return_value=PREVIOUS)),
            patch.object(publisher, 'fetch_latest_validation', AsyncMock(return_value=VALIDATION)),
            patch.object(publisher, 'fetch_latest_risk_level_snapshot', AsyncMock(return_value=LEVELS)),
            patch.object(publisher, 'send_channel_post', send),
        ):
            published = await publisher.publish_daily_post(pool, now=NOW)

        self.assertTrue(published)
        self.assertEqual(4242, pool.rows[LATEST['timestamp'].date()]['message_id'])


if __name__ == '__main__':
    unittest.main()
