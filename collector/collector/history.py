from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    raise TypeError(f"Unsupported date value: {value!r}")


def merge_ohlcv_rows(
    persisted_rows: list[dict[str, Any]],
    fetched_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_date: dict[date, dict[str, Any]] = {}
    for source_rows in (persisted_rows, fetched_rows):
        for row in source_rows:
            day = _as_date(row["date"])
            rows_by_date[day] = {**row, "date": day}
    return [rows_by_date[day] for day in sorted(rows_by_date)]


def has_valid_turnover(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(float(row.get("volume", 0.0)) > 0 and float(row.get("market_cap", 0.0)) > 0 for row in rows)
