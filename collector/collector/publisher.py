from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.readiness import build_readiness_payload
from app.repository import (
    fetch_latest_risk,
    fetch_latest_risk_level_snapshot,
    fetch_latest_validation,
    fetch_previous_risk,
)
from collector.config import settings
from collector.daily_post import compose_daily_post
from collector.db_writer import fetch_telegram_post, record_telegram_post
from collector.telegram import TelegramSendError, send_channel_post

logger = logging.getLogger(__name__)


async def publish_daily_post(pool: Any, *, now: datetime | None = None) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_channel_id:
        return False

    latest_risk = await fetch_latest_risk(pool)
    validation = await fetch_latest_validation(pool)
    readiness, _ = build_readiness_payload(
        latest_risk,
        validation,
        now=now,
        max_age_days=settings.data_freshness_max_age_days,
    )
    if readiness['status'] != 'ready' or latest_risk is None:
        return False

    as_of = latest_risk['timestamp'].date()
    if await fetch_telegram_post(pool, as_of):
        return False

    previous_risk = await fetch_previous_risk(pool)
    levels = await fetch_latest_risk_level_snapshot(pool)
    text = compose_daily_post(
        latest=latest_risk,
        previous=previous_risk,
        levels=levels,
        methodology_version=readiness['data']['methodology_version'],
    )
    try:
        message_id = await send_channel_post(
            token=settings.telegram_bot_token,
            chat_id=settings.telegram_channel_id,
            text=text,
        )
    except TelegramSendError:
        logger.exception('telegram_publish_failed')
        return False

    await record_telegram_post(
        pool,
        as_of=as_of,
        message_id=message_id,
        risk=float(latest_risk['risk']),
        risk_state=str(latest_risk['risk_state']),
    )
    return True
