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
    bitcoin_risk_manual_audit_approved: bool = os.getenv("BITCOIN_RISK_MANUAL_AUDIT_APPROVED", "false").lower() == "true"
    bitcoin_risk_manual_audit_approved_by: str = os.getenv("BITCOIN_RISK_MANUAL_AUDIT_APPROVED_BY", "")
    bitcoin_risk_manual_audit_approved_at: str = os.getenv("BITCOIN_RISK_MANUAL_AUDIT_APPROVED_AT", "")
    bitcoin_risk_manual_audit_note: str = os.getenv("BITCOIN_RISK_MANUAL_AUDIT_NOTE", "")

    def manual_audit_signoff(self) -> dict[str, str | bool] | None:
        if not self.bitcoin_risk_manual_audit_approved:
            return None
        return {
            "approved": True,
            "approved_by": self.bitcoin_risk_manual_audit_approved_by,
            "approved_at": self.bitcoin_risk_manual_audit_approved_at,
            "note": self.bitcoin_risk_manual_audit_note,
        }


settings = Settings()
