from __future__ import annotations

import argparse
import asyncio
import logging
import signal

import asyncpg
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.risk import calculate_risk_series
from collector.coingecko import CoinGeckoClient, market_chart_to_daily_rows
from collector.config import settings
from collector.history import has_valid_turnover, merge_ohlcv_rows
from collector.db_writer import fetch_ohlcv_rows, write_brief, write_ohlcv_rows, write_risk_rows, write_validation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def collect_once(pool: asyncpg.Pool, *, days: str) -> None:
    logger.info("Fetching BTC market chart from CoinGecko: days=%s", days)
    client = CoinGeckoClient(api_key=settings.coingecko_api_key)
    payload = await client.fetch_bitcoin_market_chart(days=days)
    rows = market_chart_to_daily_rows(payload)
    ohlcv_count = await write_ohlcv_rows(pool, rows)
    persisted_rows = await fetch_ohlcv_rows(pool)
    merged_rows = merge_ohlcv_rows(persisted_rows, rows)
    turnover_enabled = has_valid_turnover(merged_rows)
    risk_points = calculate_risk_series(merged_rows, turnover_enabled=turnover_enabled)
    risk_count = await write_risk_rows(pool, risk_points)
    await write_validation(
        pool,
        risk_points,
        turnover_enabled=turnover_enabled,
        source_row_count=len(merged_rows),
    )
    await write_brief(pool, risk_points)
    logger.info(
        "Collection complete: %d refreshed ohlcv rows, %d merged rows, %d risk rows",
        ohlcv_count,
        len(merged_rows),
        risk_count,
    )


async def main(*, run_now: bool = False, backfill: bool = False) -> None:
    pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=3)
    try:
        if backfill:
            await collect_once(pool, days=settings.coingecko_backfill_days)
            return
        if run_now:
            await collect_once(pool, days=settings.coingecko_refresh_days)
            return

        scheduler = AsyncIOScheduler(timezone="UTC")
        scheduler.add_job(
            collect_once,
            "cron",
            args=[pool],
            kwargs={"days": settings.coingecko_refresh_days},
            hour=settings.schedule_cron_hour,
            minute=settings.schedule_cron_minute,
            id="btc_risk_collection",
        )
        scheduler.start()
        logger.info("Scheduler started: %02d:%02d UTC daily", settings.schedule_cron_hour, settings.schedule_cron_minute)
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
        scheduler.shutdown(wait=False)
    finally:
        await pool.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bitcoin Risk Brief collector")
    parser.add_argument("--run-now", action="store_true", help="Run a rolling refresh and exit")
    parser.add_argument("--backfill", action="store_true", help="Run all-time configured backfill and exit")
    args = parser.parse_args()
    asyncio.run(main(run_now=args.run_now, backfill=args.backfill))
