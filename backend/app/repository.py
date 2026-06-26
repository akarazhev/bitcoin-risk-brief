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


def _serialize_ohlcv_row(row: asyncpg.Record) -> dict[str, Any]:
    timestamp = row["timestamp"]
    return {
        "date": timestamp.date(),
        "open": float(row["open_usd"]),
        "high": float(row["high_usd"]),
        "low": float(row["low_usd"]),
        "close": float(row["close_usd"]),
        "volume": float(row["volume_usd"]),
        "market_cap": float(row["market_cap_usd"]),
        "circulating_supply": float(row["circulating_supply"]),
        "source": row["source"],
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


async def fetch_ohlcv_history(pool: asyncpg.Pool, *, limit: int | None = None) -> list[dict[str, Any]]:
    if limit is None:
        rows = await pool.fetch(
            """
            SELECT
              timestamp, open_usd, high_usd, low_usd, close_usd, volume_usd,
              market_cap_usd, circulating_supply, source
            FROM btc_ohlcv_daily
            ORDER BY timestamp ASC
            """
        )
        return [_serialize_ohlcv_row(row) for row in rows]

    rows = await pool.fetch(
        """
        SELECT
          timestamp, open_usd, high_usd, low_usd, close_usd, volume_usd,
          market_cap_usd, circulating_supply, source
        FROM btc_ohlcv_daily
        ORDER BY timestamp DESC
        LIMIT $1
        """,
        limit,
    )
    return [_serialize_ohlcv_row(row) for row in reversed(rows)]


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


async def upsert_waitlist_lead(
    pool: asyncpg.Pool,
    *,
    contact: str,
    locale: str = "en",
    source: str = "landing",
) -> dict[str, Any]:
    from app.waitlist import normalize_locale, normalize_source, normalize_waitlist_contact

    normalized = normalize_waitlist_contact(contact)
    clean_locale = normalize_locale(locale)
    clean_source = normalize_source(source)
    row = await pool.fetchrow(
        """
        INSERT INTO waitlist_leads (contact, normalized_contact, contact_type, locale, source, status)
        VALUES ($1, $2, $3, $4, $5, 'active')
        ON CONFLICT (normalized_contact) DO UPDATE SET
          contact = EXCLUDED.contact,
          contact_type = EXCLUDED.contact_type,
          locale = EXCLUDED.locale,
          source = EXCLUDED.source,
          status = 'active',
          updated_at = now()
        RETURNING
          id::text, contact, normalized_contact, contact_type, locale, source, status,
          (created_at = updated_at) AS created
        """,
        normalized.contact,
        normalized.normalized_contact,
        normalized.contact_type,
        clean_locale,
        clean_source,
    )
    return {
        "id": row["id"],
        "contact": row["contact"],
        "normalized_contact": row["normalized_contact"],
        "contact_type": row["contact_type"],
        "locale": row["locale"],
        "source": row["source"],
        "status": row["status"],
        "created": bool(row["created"]),
    }

