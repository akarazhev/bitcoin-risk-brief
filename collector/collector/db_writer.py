from __future__ import annotations

import json
from typing import Any

import asyncpg

from app.brief import build_brief
from app.risk import METHODOLOGY_VERSION, RiskPoint, classify_risk
from app.risk_levels import build_risk_levels, build_risk_levels_public_payload
from collector.records import as_timestamp, build_ohlcv_records, build_validation_payload


async def write_ohlcv_rows(pool: asyncpg.Pool, rows: list[dict[str, Any]]) -> int:
    records = build_ohlcv_records(rows)
    await pool.executemany(
        """
        INSERT INTO btc_ohlcv_daily (
          timestamp, open_usd, high_usd, low_usd, close_usd, volume_usd,
          market_cap_usd, circulating_supply, source
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        ON CONFLICT (timestamp) DO UPDATE SET
          open_usd = EXCLUDED.open_usd,
          high_usd = EXCLUDED.high_usd,
          low_usd = EXCLUDED.low_usd,
          close_usd = EXCLUDED.close_usd,
          volume_usd = EXCLUDED.volume_usd,
          market_cap_usd = EXCLUDED.market_cap_usd,
          circulating_supply = EXCLUDED.circulating_supply,
          source = EXCLUDED.source,
          updated_at = now()
        """,
        records,
    )
    return len(records)


async def fetch_ohlcv_rows(pool: asyncpg.Pool) -> list[dict[str, Any]]:
    rows = await pool.fetch(
        """
        SELECT
          timestamp, open_usd, high_usd, low_usd, close_usd, volume_usd,
          market_cap_usd, circulating_supply, source
        FROM btc_ohlcv_daily
        ORDER BY timestamp ASC
        """
    )
    return [
        {
            "date": row["timestamp"].date(),
            "open": float(row["open_usd"]),
            "high": float(row["high_usd"]),
            "low": float(row["low_usd"]),
            "close": float(row["close_usd"]),
            "volume": float(row["volume_usd"]),
            "market_cap": float(row["market_cap_usd"]),
            "circulating_supply": float(row["circulating_supply"]),
            "source": row["source"],
        }
        for row in rows
    ]


async def fetch_latest_turnover_enabled(pool: asyncpg.Pool) -> bool | None:
    row = await pool.fetchrow(
        """
        SELECT turnover_enabled
        FROM btc_risk_daily
        ORDER BY timestamp DESC
        LIMIT 1
        """
    )
    return bool(row["turnover_enabled"]) if row else None


def _parse_delete_count(status: str) -> int:
    parts = status.split()
    if len(parts) == 2 and parts[0].upper() == "DELETE":
        return int(parts[1])
    return 0


async def delete_rows_after_csv_end(pool: asyncpg.Pool, latest_day) -> dict[str, int]:
    cutoff = as_timestamp(latest_day)
    ohlcv_status = await pool.execute(
        """
        DELETE FROM btc_ohlcv_daily
        WHERE timestamp > $1
        """,
        cutoff,
    )
    risk_status = await pool.execute(
        """
        DELETE FROM btc_risk_daily
        WHERE timestamp > $1
        """,
        cutoff,
    )
    brief_status = await pool.execute(
        """
        DELETE FROM brief_snapshots
        WHERE as_of > $1
        """,
        cutoff,
    )
    levels_status = await pool.execute(
        """
        DELETE FROM risk_level_snapshots
        WHERE as_of > $1
        """,
        cutoff,
    )
    return {
        "ohlcv": _parse_delete_count(ohlcv_status),
        "risk": _parse_delete_count(risk_status),
        "brief": _parse_delete_count(brief_status),
        "levels": _parse_delete_count(levels_status),
    }


async def write_risk_rows(pool: asyncpg.Pool, points: list[RiskPoint]) -> int:
    records = [
        (
            as_timestamp(point.day),
            point.price_hlc3,
            point.risk,
            point.score,
            point.trend_dev,
            point.vol_regime,
            point.turnover,
            point.z_trend_dev,
            point.z_vol_regime,
            point.z_turnover,
            point.turnover_enabled,
            classify_risk(point.risk),
        )
        for point in points
    ]
    await pool.executemany(
        """
        INSERT INTO btc_risk_daily (
          timestamp, price_hlc3, risk, score, trend_dev, vol_regime, turnover,
          z_trend_dev, z_vol_regime, z_turnover, turnover_enabled, risk_state
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
        ON CONFLICT (timestamp) DO UPDATE SET
          price_hlc3 = EXCLUDED.price_hlc3,
          risk = EXCLUDED.risk,
          score = EXCLUDED.score,
          trend_dev = EXCLUDED.trend_dev,
          vol_regime = EXCLUDED.vol_regime,
          turnover = EXCLUDED.turnover,
          z_trend_dev = EXCLUDED.z_trend_dev,
          z_vol_regime = EXCLUDED.z_vol_regime,
          z_turnover = EXCLUDED.z_turnover,
          turnover_enabled = EXCLUDED.turnover_enabled,
          risk_state = EXCLUDED.risk_state,
          updated_at = now()
        """,
        records,
    )
    return len(records)


async def write_validation(
    pool: asyncpg.Pool,
    points: list[RiskPoint],
    *,
    turnover_enabled: bool,
    source_row_count: int,
    stitch_validation: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    validation_summary: str | None = None,
) -> None:
    if not points:
        return
    risk_range_ok = all(0.0 <= point.risk <= 1.0 for point in points)
    payload = build_validation_payload(
        points,
        turnover_enabled=turnover_enabled,
        source_row_count=source_row_count,
        stitch_validation=stitch_validation,
        validation=validation,
    )
    summary = validation_summary or (
        f"{len(points)} daily BTC risk rows computed with {payload['methodology_version']}; "
        f"turnover_enabled={turnover_enabled}; risk_range_ok={risk_range_ok}"
    )
    await pool.execute(
        """
        INSERT INTO btc_risk_validation (
          validation_key, computed_at, covered_start, covered_end, row_count,
          risk_range_ok, validation_summary, validation_json
        ) VALUES ('latest', now(), $1, $2, $3, $4, $5, $6::jsonb)
        ON CONFLICT (validation_key) DO UPDATE SET
          computed_at = EXCLUDED.computed_at,
          covered_start = EXCLUDED.covered_start,
          covered_end = EXCLUDED.covered_end,
          row_count = EXCLUDED.row_count,
          risk_range_ok = EXCLUDED.risk_range_ok,
          validation_summary = EXCLUDED.validation_summary,
          validation_json = EXCLUDED.validation_json
        """,
        as_timestamp(points[0].day),
        as_timestamp(points[-1].day),
        len(points),
        risk_range_ok,
        summary,
        json.dumps(payload, default=str),
    )


async def write_brief(pool: asyncpg.Pool, points: list[RiskPoint]) -> None:
    if not points:
        return
    latest = points[-1]
    previous = points[-2] if len(points) > 1 else None
    latest_payload = {
        "timestamp": as_timestamp(latest.day).isoformat(),
        "risk": latest.risk,
        "risk_state": classify_risk(latest.risk),
        "price_usd": latest.price_hlc3,
    }
    previous_payload = None
    if previous is not None:
        previous_payload = {
            "timestamp": as_timestamp(previous.day).isoformat(),
            "risk": previous.risk,
            "risk_state": classify_risk(previous.risk),
            "price_usd": previous.price_hlc3,
        }
    brief = build_brief(latest_payload, previous_payload)
    await pool.execute(
        """
        INSERT INTO brief_snapshots (as_of, snapshot_version, payload_json)
        VALUES ($1, $2, $3::jsonb)
        ON CONFLICT (as_of, snapshot_version) DO UPDATE SET
          payload_json = EXCLUDED.payload_json,
          created_at = now()
        """,
        as_timestamp(latest.day),
        brief["snapshot_version"],
        json.dumps(brief),
    )


def _risk_point_public_payload(point: RiskPoint, source_row: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "timestamp": as_timestamp(point.day).isoformat(),
        "price_usd": point.price_hlc3,
        "model_price_usd": point.price_hlc3,
        "low_usd": float(source_row["low"]) if source_row and "low" in source_row else None,
        "high_usd": float(source_row["high"]) if source_row and "high" in source_row else None,
        "risk": point.risk,
        "score": point.score,
        "risk_state": classify_risk(point.risk),
        "trend_dev": point.trend_dev,
        "vol_regime": point.vol_regime,
        "turnover": point.turnover,
        "z_trend_dev": point.z_trend_dev,
        "z_vol_regime": point.z_vol_regime,
        "z_turnover": point.z_turnover,
        "turnover_enabled": point.turnover_enabled,
    }


async def write_risk_level_snapshot(
    pool: asyncpg.Pool,
    source_rows: list[dict[str, Any]],
    points: list[RiskPoint],
) -> None:
    if len(source_rows) < 2 or not points:
        return
    latest = points[-1]
    latest_source_row = source_rows[-1] if source_rows else None
    levels = build_risk_levels(source_rows, {"turnover_enabled": latest.turnover_enabled})
    payload = build_risk_levels_public_payload(
        latest=_risk_point_public_payload(latest, latest_source_row),
        levels=levels,
        source_row_count=len(source_rows),
    )
    await pool.execute(
        """
        INSERT INTO risk_level_snapshots (as_of, snapshot_version, payload_json)
        VALUES ($1, $2, $3::jsonb)
        ON CONFLICT (as_of, snapshot_version) DO UPDATE SET
          payload_json = EXCLUDED.payload_json,
          created_at = now()
        """,
        as_timestamp(latest.day),
        METHODOLOGY_VERSION,
        json.dumps(payload, default=str),
    )
