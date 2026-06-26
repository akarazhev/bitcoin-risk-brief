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


def validate_fetched_delta(fetched_rows: list[dict[str, Any]], *, start_date: date, end_date: date) -> None:
    if not fetched_rows:
        return
    dates = [row["date"] for row in fetched_rows]
    expected_dates = [start_date + timedelta(days=offset) for offset in range((end_date - start_date).days + 1)]
    if dates != expected_dates:
        missing_dates = sorted(set(expected_dates) - set(dates))
        extra_dates = sorted(set(dates) - set(expected_dates))
        details = []
        if missing_dates:
            details.append("missing daily dates: " + ", ".join(day.isoformat() for day in missing_dates[:5]))
        if extra_dates:
            details.append("unexpected daily dates: " + ", ".join(day.isoformat() for day in extra_dates[:5]))
        raise ValueError("CoinMarketCap delta is not contiguous for requested range; " + "; ".join(details))


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
    validate_fetched_delta(fetched_rows, start_date=start_date, end_date=end_date)

    merged_rows = merge_daily_rows(existing_rows, fetched_rows)
    write_btc_usd_daily_csv(path, merged_rows)
    logger.info("BTC CSV updated with %d CoinMarketCap rows through %s", len(fetched_rows), merged_rows[-1]["date"].isoformat())
    return len(fetched_rows)
