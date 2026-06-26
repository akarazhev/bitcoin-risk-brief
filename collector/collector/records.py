from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any

from app.risk import METHODOLOGY_VERSION, ROBUST_Z_MIN_PERIODS, ROBUST_Z_WINDOW, RiskPoint


def as_timestamp(day) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def build_ohlcv_records(rows: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
    return [
        (
            as_timestamp(row["date"]),
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["volume"],
            row["market_cap"],
            row["circulating_supply"],
            row.get("source", "coingecko"),
        )
        for row in rows
    ]


def build_validation_payload(
    points: list[RiskPoint],
    *,
    turnover_enabled: bool,
    source_row_count: int,
    stitch_validation: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "source": "csv_coingecko_merged" if stitch_validation else "coingecko_with_persisted_history",
        "methodology_version": METHODOLOGY_VERSION,
        "robust_z_window": ROBUST_Z_WINDOW,
        "robust_z_min_periods": ROBUST_Z_MIN_PERIODS,
        "turnover_enabled": turnover_enabled,
        "source_row_count": source_row_count,
        "risk_row_count": len(points),
    }
    if stitch_validation is not None:
        payload["stitch_validation"] = stitch_validation
    if validation is not None:
        payload["validation"] = validation
    return payload
