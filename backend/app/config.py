from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    data_freshness_max_age_days: int = int(os.getenv("DATA_FRESHNESS_MAX_AGE_DAYS", "2"))
    waitlist_rate_limit_per_hour: int = int(os.getenv("WAITLIST_RATE_LIMIT_PER_HOUR", "20"))
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/bitcoin_risk_brief",
    )
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3001").split(",")
        if origin.strip()
    )


settings = Settings()
