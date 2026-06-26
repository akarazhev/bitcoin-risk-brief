from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from pathlib import Path

import asyncpg
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.risk_sources import build_csv_risk_dataset
from collector.config import settings
from collector.csv_refresh import refresh_csv_from_coinmarketcap
from collector.db_writer import delete_rows_after_csv_end, write_brief, write_ohlcv_rows, write_risk_rows, write_validation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
BTC_CSV_PATH = Path(__file__).resolve().parents[1] / "btc-csv" / "btc_usd_daily.csv"


async def import_csv_once(pool: asyncpg.Pool, *, refresh_remote: bool) -> None:
    refreshed_count = 0
    if refresh_remote:
        refreshed_count = await refresh_csv_from_coinmarketcap(
            BTC_CSV_PATH,
            api_key=settings.coinmarketcap_api_key,
            base_url=settings.coinmarketcap_base_url,
            bitcoin_id=settings.coinmarketcap_bitcoin_id,
            convert=settings.coinmarketcap_convert,
        )

    dataset = build_csv_risk_dataset(BTC_CSV_PATH)
    ohlcv_count = await write_ohlcv_rows(pool, dataset["source_rows"])
    risk_count = await write_risk_rows(pool, dataset["risk_points"])
    await write_validation(
        pool,
        dataset["risk_points"],
        turnover_enabled=dataset["validation"]["turnover_enabled"],
        source_row_count=len(dataset["source_rows"]),
        validation=dataset["validation"],
        validation_summary=dataset["validation_summary"],
    )
    await write_brief(pool, dataset["risk_points"])
    deleted_counts = await delete_rows_after_csv_end(pool, dataset["source_rows"][-1]["date"])
    logger.info(
        "CSV import complete: %d refreshed CSV rows, %d ohlcv rows, %d risk rows, deleted stale rows=%s",
        refreshed_count,
        ohlcv_count,
        risk_count,
        deleted_counts,
    )


async def main(*, run_now: bool = False, backfill: bool = False) -> None:
    pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=3)
    try:
        if backfill:
            await import_csv_once(pool, refresh_remote=False)
            return
        if run_now:
            await import_csv_once(pool, refresh_remote=True)
            return

        scheduler = AsyncIOScheduler(timezone="UTC")
        scheduler.add_job(
            import_csv_once,
            "cron",
            args=[pool],
            kwargs={"refresh_remote": True},
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
    parser.add_argument("--run-now", action="store_true", help="Refresh BTC CSV if possible, import CSV, recalculate risk, and exit")
    parser.add_argument("--backfill", action="store_true", help="Import the canonical BTC CSV, recalculate risk, and exit")
    args = parser.parse_args()
    asyncio.run(main(run_now=args.run_now, backfill=args.backfill))
