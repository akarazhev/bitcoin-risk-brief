from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    data_freshness_max_age_days: int = int(os.getenv("DATA_FRESHNESS_MAX_AGE_DAYS", "2"))
    waitlist_rate_limit_per_hour: int = int(os.getenv("WAITLIST_RATE_LIMIT_PER_HOUR", "20"))
    public_cache_ttl_seconds: int = int(os.getenv("PUBLIC_CACHE_TTL_SECONDS", "300"))
    public_cache_max_age_seconds: int = int(os.getenv("PUBLIC_CACHE_MAX_AGE_SECONDS", "60"))
    public_cache_stale_while_revalidate_seconds: int = int(
        os.getenv("PUBLIC_CACHE_STALE_WHILE_REVALIDATE_SECONDS", "300")
    )
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
