from __future__ import annotations

import json
from datetime import date, datetime, time, timezone
from typing import Any

import asyncpg


def _serialize_row(row: asyncpg.Record) -> dict[str, Any]:
    timestamp = row["timestamp"]
    return {
        "timestamp": timestamp.isoformat(),
        "price_usd": float(row["price_hlc3"]),
        "risk": float(row["risk"]),
        "score": float(row["score"]),
        "risk_state": row["risk_state"],
        "trend_dev": float(row["trend_dev"]),
        "vol_regime": float(row["vol_regime"]),
        "turnover": float(row["turnover"]) if row["turnover"] is not None else None,
        "z_trend_dev": float(row["z_trend_dev"]),
        "z_vol_regime": float(row["z_vol_regime"]),
        "z_turnover": float(row["z_turnover"]) if row["z_turnover"] is not None else None,
        "turnover_enabled": bool(row["turnover_enabled"]),
    }


async def fetch_latest_risk(pool: asyncpg.Pool) -> dict[str, Any] | None:
    row = await pool.fetchrow(
        """
        SELECT *
        FROM btc_risk_daily
        ORDER BY timestamp DESC
        LIMIT 1
        """
    )
    return _serialize_row(row) if row else None


async def fetch_previous_risk(pool: asyncpg.Pool) -> dict[str, Any] | None:
    row = await pool.fetchrow(
        """
        SELECT *
        FROM btc_risk_daily
        ORDER BY timestamp DESC
        OFFSET 1
        LIMIT 1
        """
    )
    return _serialize_row(row) if row else None


async def fetch_risk_history(
    pool: asyncpg.Pool,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 2000,
) -> list[dict[str, Any]]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc) if start_date else None
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc) if end_date else None
    rows = await pool.fetch(
        """
        SELECT *
        FROM btc_risk_daily
        WHERE ($1::timestamptz IS NULL OR timestamp >= $1)
          AND ($2::timestamptz IS NULL OR timestamp <= $2)
        ORDER BY timestamp DESC
        LIMIT $3
        """,
        start_dt,
        end_dt,
        limit,
    )
    return [_serialize_row(row) for row in reversed(rows)]


async def fetch_latest_brief(pool: asyncpg.Pool) -> dict[str, Any] | None:
    row = await pool.fetchrow(
        """
        SELECT payload_json
        FROM brief_snapshots
        ORDER BY as_of DESC
        LIMIT 1
        """
    )
    if not row:
        return None
    payload = row["payload_json"]
    return json.loads(payload) if isinstance(payload, str) else dict(payload)
