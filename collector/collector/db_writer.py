from __future__ import annotations

import json
from datetime import datetime, time, timezone
from typing import Any

import asyncpg

from app.brief import build_brief
from app.risk import METHODOLOGY_VERSION, ROBUST_Z_MIN_PERIODS, ROBUST_Z_WINDOW, RiskPoint, classify_risk


def _as_timestamp(day) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


async def write_ohlcv_rows(pool: asyncpg.Pool, rows: list[dict[str, Any]]) -> int:
    records = [
        (
            _as_timestamp(row["date"]),
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["volume"],
            row["market_cap"],
            row["circulating_supply"],
            "coingecko",
        )
        for row in rows
    ]
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


async def write_risk_rows(pool: asyncpg.Pool, points: list[RiskPoint]) -> int:
    records = [
        (
            _as_timestamp(point.day),
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
) -> None:
    if not points:
        return
    risk_range_ok = all(0.0 <= point.risk <= 1.0 for point in points)
    payload = {
        "source": "coingecko_with_persisted_history",
        "methodology_version": METHODOLOGY_VERSION,
        "robust_z_window": ROBUST_Z_WINDOW,
        "robust_z_min_periods": ROBUST_Z_MIN_PERIODS,
        "turnover_enabled": turnover_enabled,
        "source_row_count": source_row_count,
        "risk_row_count": len(points),
    }
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
        _as_timestamp(points[0].day),
        _as_timestamp(points[-1].day),
        len(points),
        risk_range_ok,
        (
            f"{len(points)} daily BTC risk rows computed with {METHODOLOGY_VERSION}; "
            f"turnover_enabled={turnover_enabled}; risk_range_ok={risk_range_ok}"
        ),
        json.dumps(payload),
    )


async def write_brief(pool: asyncpg.Pool, points: list[RiskPoint]) -> None:
    if not points:
        return
    latest = points[-1]
    previous = points[-2] if len(points) > 1 else None
    latest_payload = {
        "timestamp": _as_timestamp(latest.day).isoformat(),
        "risk": latest.risk,
        "risk_state": classify_risk(latest.risk),
        "price_usd": latest.price_hlc3,
    }
    previous_payload = None
    if previous is not None:
        previous_payload = {
            "timestamp": _as_timestamp(previous.day).isoformat(),
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
        _as_timestamp(latest.day),
        brief["snapshot_version"],
        json.dumps(brief),
    )
