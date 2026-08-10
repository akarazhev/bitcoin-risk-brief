from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/bitcoin_risk_brief",
    )
    coinmarketcap_api_key: str = os.getenv("COINMARKETCAP_API_KEY", "")
    coinmarketcap_base_url: str = os.getenv("COINMARKETCAP_BASE_URL", "https://pro-api.coinmarketcap.com")
    coinmarketcap_bitcoin_id: int = int(os.getenv("COINMARKETCAP_BITCOIN_ID", "1"))
    coinmarketcap_convert: str = os.getenv("COINMARKETCAP_CONVERT", "USD")
    schedule_cron_hour: int = int(os.getenv("SCHEDULE_CRON_HOUR", "1"))
    schedule_cron_minute: int = int(os.getenv("SCHEDULE_CRON_MINUTE", "0"))
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_channel_id: str = os.getenv("TELEGRAM_CHANNEL_ID", "")
    data_freshness_max_age_days: int = int(os.getenv("DATA_FRESHNESS_MAX_AGE_DAYS", "2"))


settings = Settings()
