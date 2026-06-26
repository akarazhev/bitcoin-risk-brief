from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from statistics import median, pstdev
from typing import Any

EPSILON = 1e-12
EMA_PERIOD = 365
VOLATILITY_WINDOW = 30
ROBUST_Z_WINDOW = 365
ROBUST_Z_MIN_PERIODS = 60
ROBUST_Z_CLIP = 6.0
TREND_WEIGHT = 0.72
VOL_WEIGHT = 0.23
TURNOVER_WEIGHT = 0.05


@dataclass(frozen=True)
class RiskPoint:
    day: date
    price_hlc3: float
    risk: float
    score: float
    trend_dev: float
    vol_regime: float
    turnover: float | None
    z_trend_dev: float
    z_vol_regime: float
    z_turnover: float | None
    turnover_enabled: bool


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    raise TypeError(f"Unsupported date value: {value!r}")


def _to_float(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _compute_hlc3(row: dict[str, Any]) -> float:
    return (
        _to_float(row["high"], "high")
        + _to_float(row["low"], "low")
        + _to_float(row["close"], "close")
    ) / 3.0


def _validate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        day = _as_date(row["date"])
        item = {
            "date": day,
            "open": _to_float(row["open"], "open"),
            "high": _to_float(row["high"], "high"),
            "low": _to_float(row["low"], "low"),
            "close": _to_float(row["close"], "close"),
            "volume": _to_float(row.get("volume", 0.0), "volume"),
            "market_cap": _to_float(row.get("market_cap", 0.0), "market_cap"),
            "circulating_supply": _to_float(row.get("circulating_supply", 0.0), "circulating_supply"),
        }
        if min(item["open"], item["high"], item["low"], item["close"]) <= 0:
            raise ValueError(f"price fields must be positive on {day.isoformat()}")
        if item["market_cap"] <= 0:
            raise ValueError(f"market_cap must be positive on {day.isoformat()}")
        normalized.append(item)

    normalized.sort(key=lambda row: row["date"])
    dates = [row["date"] for row in normalized]
    if len(set(dates)) != len(dates):
        raise ValueError("risk rows must not contain duplicate dates")
    return normalized


def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    result = [values[0]]
    for value in values[1:]:
        result.append((alpha * value) + ((1.0 - alpha) * result[-1]))
    return result


def _rolling_std(values: list[float], window: int) -> list[float]:
    result: list[float] = []
    for index in range(len(values)):
        sample = values[max(0, index - window + 1) : index + 1]
        result.append(pstdev(sample) if len(sample) > 1 else 0.0)
    return result


def _robust_zscore(history: list[float], current: float) -> float:
    window = history[-(ROBUST_Z_WINDOW - 1) :] + [current]
    if len(window) < ROBUST_Z_MIN_PERIODS:
        return 0.0
    center = median(window)
    deviations = [abs(value - center) for value in window]
    mad = median(deviations)
    denominator = (1.4826 * mad) + EPSILON
    return max(-ROBUST_Z_CLIP, min(ROBUST_Z_CLIP, (current - center) / denominator))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def classify_risk(risk: float) -> str:
    if risk < 0.35:
        return "low"
    if risk >= 0.65:
        return "high"
    return "neutral"


def calculate_risk_series(rows: list[dict[str, Any]]) -> list[RiskPoint]:
    normalized = _validate_rows(rows)
    if not normalized:
        return []

    prices = [_compute_hlc3(row) for row in normalized]
    ema_values = _ema(prices, EMA_PERIOD)
    log_returns = [0.0]
    for index in range(1, len(prices)):
        log_returns.append(math.log(max(prices[index], EPSILON) / max(prices[index - 1], EPSILON)))
    vol_values = _rolling_std(log_returns, VOLATILITY_WINDOW)

    trend_history: list[float] = []
    vol_history: list[float] = []
    turnover_history: list[float] = []
    points: list[RiskPoint] = []

    for index, row in enumerate(normalized):
        price = prices[index]
        trend_dev = math.log(max(price, EPSILON) / max(ema_values[index], EPSILON))
        vol_regime = vol_values[index]
        turnover = None
        z_turnover = None
        turnover_enabled = row["volume"] > 0 and row["market_cap"] > 0
        if turnover_enabled:
            turnover = math.log(max(row["volume"], EPSILON) / max(row["market_cap"], EPSILON))

        z_trend = _robust_zscore(trend_history, trend_dev)
        z_vol = _robust_zscore(vol_history, vol_regime)
        score = (TREND_WEIGHT * z_trend) + (VOL_WEIGHT * z_vol)
        if turnover is not None:
            z_turnover = _robust_zscore(turnover_history, turnover)
            score += TURNOVER_WEIGHT * z_turnover
            turnover_history.append(turnover)

        risk = max(0.0, min(1.0, _sigmoid(score)))
        points.append(
            RiskPoint(
                day=row["date"],
                price_hlc3=price,
                risk=risk,
                score=score,
                trend_dev=trend_dev,
                vol_regime=vol_regime,
                turnover=turnover,
                z_trend_dev=z_trend,
                z_vol_regime=z_vol,
                z_turnover=z_turnover,
                turnover_enabled=turnover_enabled,
            )
        )
        trend_history.append(trend_dev)
        vol_history.append(vol_regime)

    return points
