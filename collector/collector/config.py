from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/bitcoin_risk_brief",
    )
    coingecko_api_key: str = os.getenv("COINGECKO_API_KEY", "")
    coingecko_backfill_days: str = os.getenv("COINGECKO_BACKFILL_DAYS", "max")
    coingecko_refresh_days: str = os.getenv("COINGECKO_REFRESH_DAYS", "365")
    schedule_cron_hour: int = int(os.getenv("SCHEDULE_CRON_HOUR", "1"))
    schedule_cron_minute: int = int(os.getenv("SCHEDULE_CRON_MINUTE", "0"))


settings = Settings()
