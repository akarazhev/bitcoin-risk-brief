from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from statistics import median, pstdev
from typing import Any

EPSILON = 1e-12
METHODOLOGY_VERSION = "crypto-scout-canonical-v1"
ROBUST_Z_WINDOW = 1460
ROBUST_Z_MIN_PERIODS = 365
ROBUST_Z_CLIP = 6.0
EMA_PERIOD = 365
VOLATILITY_WINDOW = 30
TURNOVER_ENABLED_WEIGHTS = {
    "trend_dev": 0.60,
    "vol_regime": 0.25,
    "turnover": 0.15,
}
TURNOVER_DISABLED_WEIGHTS = {
    "trend_dev": 0.70,
    "vol_regime": 0.30,
}


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


def _serialize_float(value: float | None) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value):
        raise ValueError(f"Encountered non-finite numeric value: {value}")
    return float(value)


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
        if item["circulating_supply"] <= 0:
            raise ValueError(f"circulating_supply must be positive on {day.isoformat()}")
        normalized.append(item)

    normalized.sort(key=lambda row: row["date"])
    dates = [row["date"] for row in normalized]
    if len(set(dates)) != len(dates):
        raise ValueError("risk rows must not contain duplicate dates")
    return normalized


def _compute_hlc3(row: dict[str, Any]) -> float:
    return (
        _to_float(row["high"], "high")
        + _to_float(row["low"], "low")
        + _to_float(row["close"], "close")
    ) / 3.0


def _compute_ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    ema_values: list[float] = []
    current_ema = values[0]
    for value in values:
        current_ema = alpha * value + (1.0 - alpha) * current_ema
        ema_values.append(current_ema)
    return ema_values


def _rolling_std(values: list[float], window: int) -> list[float]:
    std_values: list[float] = []
    for index in range(len(values)):
        start = max(0, index - window + 1)
        window_values = [value for value in values[start : index + 1] if math.isfinite(value)]
        std_values.append(pstdev(window_values) if len(window_values) >= 2 else 0.0)
    return std_values


def _robust_rolling_zscores(
    values: list[float | None],
    *,
    window: int = ROBUST_Z_WINDOW,
    min_periods: int = ROBUST_Z_MIN_PERIODS,
    clip: float = ROBUST_Z_CLIP,
) -> list[float]:
    zscores: list[float] = []
    for index, current_value in enumerate(values):
        if current_value is None or not math.isfinite(current_value):
            zscores.append(0.0)
            continue

        start = max(0, index - window + 1)
        window_values = [
            float(value)
            for value in values[start : index + 1]
            if value is not None and math.isfinite(value)
        ]
        if len(window_values) < min_periods:
            zscores.append(0.0)
            continue

        center = median(window_values)
        deviations = [abs(value - center) for value in window_values]
        mad = median(deviations)
        denominator = 1.4826 * mad + EPSILON
        zscore = (float(current_value) - center) / denominator
        zscores.append(max(-clip, min(clip, zscore)))

    return zscores


def _sigmoid(value: float) -> float:
    if value >= 0:
        exponent = math.exp(-value)
        return 1.0 / (1.0 + exponent)
    exponent = math.exp(value)
    return exponent / (1.0 + exponent)


def classify_risk(risk: float) -> str:
    if risk < 0.35:
        return "low"
    if risk >= 0.65:
        return "high"
    return "neutral"


def calculate_risk_series(rows: list[dict[str, Any]], *, turnover_enabled: bool = True) -> list[RiskPoint]:
    normalized = _validate_rows(rows)
    if not normalized:
        return []

    effective_turnover_enabled = turnover_enabled and all(
        row["volume"] > 0 and row["market_cap"] > 0 for row in normalized
    )
    weights = TURNOVER_ENABLED_WEIGHTS if effective_turnover_enabled else TURNOVER_DISABLED_WEIGHTS

    prices = [_compute_hlc3(row) for row in normalized]
    ema_prices = _compute_ema(prices, EMA_PERIOD)
    trend_dev = [
        math.log(max(price, EPSILON) / max(ema_price, EPSILON))
        for price, ema_price in zip(prices, ema_prices)
    ]

    log_returns: list[float] = [0.0]
    for index in range(1, len(prices)):
        log_returns.append(math.log(max(prices[index], EPSILON) / max(prices[index - 1], EPSILON)))
    vol_regime = _rolling_std(log_returns, VOLATILITY_WINDOW)

    turnover_values: list[float | None] = [
        math.log(max(row["volume"], EPSILON) / max(row["market_cap"], EPSILON))
        for row in normalized
    ]

    z_trend_dev = _robust_rolling_zscores(trend_dev)
    z_vol_regime = _robust_rolling_zscores(vol_regime)
    z_turnover = (
        _robust_rolling_zscores(turnover_values)
        if effective_turnover_enabled
        else [0.0 for _ in normalized]
    )

    points: list[RiskPoint] = []
    for index, row in enumerate(normalized):
        score = (
            weights["trend_dev"] * z_trend_dev[index]
            + weights["vol_regime"] * z_vol_regime[index]
        )
        if effective_turnover_enabled:
            score += TURNOVER_ENABLED_WEIGHTS["turnover"] * z_turnover[index]

        points.append(
            RiskPoint(
                day=row["date"],
                price_hlc3=_serialize_float(prices[index]) or 0.0,
                risk=_serialize_float(_sigmoid(score)) or 0.0,
                score=_serialize_float(score) or 0.0,
                trend_dev=_serialize_float(trend_dev[index]) or 0.0,
                vol_regime=_serialize_float(vol_regime[index]) or 0.0,
                turnover=_serialize_float(turnover_values[index]) if effective_turnover_enabled else None,
                z_trend_dev=_serialize_float(z_trend_dev[index]) or 0.0,
                z_vol_regime=_serialize_float(z_vol_regime[index]) or 0.0,
                z_turnover=_serialize_float(z_turnover[index]) if effective_turnover_enabled else 0.0,
                turnover_enabled=effective_turnover_enabled,
            )
        )

    return points
