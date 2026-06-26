from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

from app.risk_sources import load_btc_usd_daily_csv, merge_daily_rows, write_btc_usd_daily_csv
from collector.coinmarketcap import CoinMarketCapClient

logger = logging.getLogger(__name__)


class CoinMarketCapClientFactory(Protocol):
    def __call__(self, *, api_key: str, base_url: str) -> Any:
        ...


def last_completed_utc_day(now: datetime | None = None) -> date:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).date() - timedelta(days=1)


async def refresh_csv_from_coinmarketcap(
    csv_path: str | Path,
    *,
    api_key: str,
    base_url: str,
    bitcoin_id: int,
    convert: str,
    now: datetime | None = None,
    client_factory: CoinMarketCapClientFactory = CoinMarketCapClient,
) -> int:
    path = Path(csv_path)
    existing_rows = load_btc_usd_daily_csv(path)
    start_date = existing_rows[-1]["date"] + timedelta(days=1)
    end_date = last_completed_utc_day(now)

    if start_date > end_date:
        logger.info("BTC CSV is current through %s; no remote refresh needed", existing_rows[-1]["date"].isoformat())
        return 0
    if not api_key.strip():
        logger.info(
            "COINMARKETCAP_API_KEY is empty; skipping remote refresh for %s..%s and importing existing CSV",
            start_date.isoformat(),
            end_date.isoformat(),
        )
        return 0

    logger.info("Fetching CoinMarketCap BTC OHLCV delta: %s..%s", start_date.isoformat(), end_date.isoformat())
    client = client_factory(api_key=api_key, base_url=base_url)
    fetched_rows = await client.fetch_bitcoin_ohlcv_historical(
        time_start=start_date,
        time_end=end_date,
        convert=convert,
        bitcoin_id=bitcoin_id,
    )
    if not fetched_rows:
        logger.info("CoinMarketCap returned no BTC OHLCV rows for %s..%s", start_date.isoformat(), end_date.isoformat())
        return 0

    merged_rows = merge_daily_rows(existing_rows, fetched_rows)
    write_btc_usd_daily_csv(path, merged_rows)
    logger.info("BTC CSV updated with %d CoinMarketCap rows through %s", len(fetched_rows), merged_rows[-1]["date"].isoformat())
    return len(fetched_rows)
