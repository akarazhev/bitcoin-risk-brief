from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.risk_sources import build_csv_risk_dataset
from collector.config import settings
from collector.csv_refresh import refresh_csv_from_coinmarketcap
from collector.downloaded_csv import import_coinmarketcap_downloaded_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
BTC_CSV_PATH = Path(__file__).resolve().parents[1] / "btc-csv" / "btc_usd_daily.csv"


async def import_csv_once(pool: Any, *, refresh_remote: bool) -> None:
    from collector.db_writer import (
        delete_rows_after_csv_end,
        write_brief,
        write_ohlcv_rows,
        write_risk_rows,
        write_validation,
    )

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


def parse_cli_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


async def import_downloaded_csv_once(
    pool: Any,
    downloaded_csv_path: str | Path,
    *,
    expected_end_date: date | None,
) -> None:
    result = import_coinmarketcap_downloaded_csv(
        downloaded_csv_path,
        BTC_CSV_PATH,
        expected_end_date=expected_end_date,
    )
    logger.info(
        "Downloaded CoinMarketCap CSV accepted: %d downloaded rows, canonical coverage %s..%s (%d rows)",
        result.downloaded_row_count,
        result.covered_start.isoformat(),
        result.covered_end.isoformat(),
        result.written_row_count,
    )
    await import_csv_once(pool, refresh_remote=False)


async def main(
    *,
    run_now: bool = False,
    backfill: bool = False,
    import_cmc_csv: str | Path | None = None,
    expected_end_date: date | None = None,
) -> None:
    import asyncpg
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from collector.db_pool import create_pool_with_retry

    pool = await create_pool_with_retry(settings.database_url, create_pool=asyncpg.create_pool, min_size=1, max_size=3)
    try:
        if import_cmc_csv is not None:
            await import_downloaded_csv_once(pool, import_cmc_csv, expected_end_date=expected_end_date)
            return
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run-now", action="store_true", help="Refresh BTC CSV if possible, import CSV, recalculate risk, and exit")
    mode.add_argument("--backfill", action="store_true", help="Import the canonical BTC CSV, recalculate risk, and exit")
    mode.add_argument(
        "--import-cmc-csv",
        type=Path,
        help="Validate an operator-downloaded CoinMarketCap historical CSV, replace the canonical CSV, import it, and exit",
    )
    parser.add_argument(
        "--expected-end-date",
        type=parse_cli_date,
        help="Require the downloaded CSV merge to cover this UTC date in YYYY-MM-DD format",
    )
    args = parser.parse_args()
    asyncio.run(
        main(
            run_now=args.run_now,
            backfill=args.backfill,
            import_cmc_csv=args.import_cmc_csv,
            expected_end_date=args.expected_end_date,
        )
    )
