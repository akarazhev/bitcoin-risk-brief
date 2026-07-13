from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Any

from app.risk import (
    EMA_PERIOD,
    EPSILON,
    METHODOLOGY_VERSION,
    ROBUST_Z_CLIP,
    ROBUST_Z_MIN_PERIODS,
    ROBUST_Z_WINDOW,
    TURNOVER_DISABLED_WEIGHTS,
    TURNOVER_ENABLED_WEIGHTS,
    VOLATILITY_WINDOW,
    _compute_ema,
    _compute_hlc3,
    _rolling_std,
    _sigmoid,
)

PRICE_LADDER_TARGET_ROWS = 126
RISK_STEP = 0.025
SOLVER_MAX_EXPANSIONS = 24
SOLVER_BINARY_SEARCH_STEPS = 32


@dataclass(frozen=True)
class LevelContext:
    previous_ema: float
    trend_history: list[float]
    trend_weight: float
    fixed_non_price_score: float


def _turnover_enabled(stitch_validation: dict[str, Any]) -> bool:
    return bool(stitch_validation.get("turnover_enabled", False))


def _reachable_risk_bounds(context: LevelContext) -> tuple[float, float]:
    minimum_score = context.fixed_non_price_score + (context.trend_weight * -ROBUST_Z_CLIP)
    maximum_score = context.fixed_non_price_score + (context.trend_weight * ROBUST_Z_CLIP)
    return (_sigmoid(minimum_score), _sigmoid(maximum_score))


def _normalize_target_risk(target_risk: float, context: LevelContext) -> float:
    minimum_risk, maximum_risk = _reachable_risk_bounds(context)
    return max(minimum_risk, min(maximum_risk, target_risk))


def _robust_current_zscore(history: list[float], current_value: float) -> float:
    window_values = history[-(ROBUST_Z_WINDOW - 1) :] + [current_value]
    if len(window_values) < ROBUST_Z_MIN_PERIODS:
        return 0.0

    center = median(window_values)
    deviations = [abs(value - center) for value in window_values]
    mad = median(deviations)
    denominator = 1.4826 * mad + EPSILON
    zscore = (current_value - center) / denominator
    return max(-ROBUST_Z_CLIP, min(ROBUST_Z_CLIP, zscore))


def _build_level_context(rows: list[dict[str, Any]], stitch_validation: dict[str, Any]) -> LevelContext:
    if len(rows) < 2:
        raise ValueError("rows must contain at least two daily points")

    prices = [_compute_hlc3(row) for row in rows]
    historical_prices = prices[:-1]
    current_price = prices[-1]
    ema_history = _compute_ema(historical_prices, EMA_PERIOD)
    trend_history = [
        math.log(max(price, EPSILON) / max(ema_price, EPSILON))
        for price, ema_price in zip(historical_prices, ema_history)
    ]

    log_return_history: list[float] = [0.0]
    for index in range(1, len(historical_prices)):
        log_return_history.append(
            math.log(max(historical_prices[index], EPSILON) / max(historical_prices[index - 1], EPSILON))
        )

    vol_regime_history = _rolling_std(log_return_history, VOLATILITY_WINDOW)
    previous_price = historical_prices[-1]
    current_log_return = math.log(max(current_price, EPSILON) / max(previous_price, EPSILON))
    current_vol_regime = _rolling_std(
        log_return_history[-(VOLATILITY_WINDOW - 1) :] + [current_log_return],
        VOLATILITY_WINDOW,
    )[-1]
    current_vol_zscore = _robust_current_zscore(vol_regime_history, current_vol_regime)

    use_turnover = _turnover_enabled(stitch_validation)
    weights = TURNOVER_ENABLED_WEIGHTS if use_turnover else TURNOVER_DISABLED_WEIGHTS
    fixed_non_price_score = weights["vol_regime"] * current_vol_zscore
    if use_turnover:
        turnover_history = [
            math.log(max(float(row["volume"]), EPSILON) / max(float(row["market_cap"]), EPSILON))
            for row in rows[:-1]
        ]
        last_row = rows[-1]
        current_turnover = math.log(
            max(float(last_row["volume"]), EPSILON) / max(float(last_row["market_cap"]), EPSILON)
        )
        current_turnover_zscore = _robust_current_zscore(turnover_history, current_turnover)
        fixed_non_price_score += TURNOVER_ENABLED_WEIGHTS["turnover"] * current_turnover_zscore

    return LevelContext(
        previous_ema=ema_history[-1],
        trend_history=trend_history,
        trend_weight=weights["trend_dev"],
        fixed_non_price_score=fixed_non_price_score,
    )


def _round_price_step(price_range: float, *, target_rows: int) -> float:
    if price_range <= 0:
        return 1_000.0

    raw_step = price_range / max(target_rows - 1, 1)
    magnitude = 10 ** math.floor(math.log10(raw_step))
    for multiplier in (1, 2, 5, 10):
        step = multiplier * magnitude
        if step >= raw_step:
            return float(step)
    return float(10 * magnitude)


def _calculate_current_risk_from_context(context: LevelContext, hypothetical_price: float) -> float:
    alpha = 2.0 / (EMA_PERIOD + 1.0)
    ema_price = alpha * hypothetical_price + (1.0 - alpha) * context.previous_ema
    trend_dev = math.log(max(hypothetical_price, EPSILON) / max(ema_price, EPSILON))
    trend_zscore = _robust_current_zscore(context.trend_history, trend_dev)
    score = context.trend_weight * trend_zscore + context.fixed_non_price_score
    return float(_sigmoid(score))


def calculate_current_risk_for_price(
    rows: list[dict[str, Any]],
    stitch_validation: dict[str, Any],
    hypothetical_price: float,
) -> float:
    context = _build_level_context(rows, stitch_validation)
    return _calculate_current_risk_from_context(context, hypothetical_price)


def solve_price_for_target_risk(
    rows: list[dict[str, Any]],
    stitch_validation: dict[str, Any],
    target_risk: float,
) -> float:
    if not rows:
        raise ValueError("rows must not be empty")

    context = _build_level_context(rows, stitch_validation)
    effective_target_risk = _normalize_target_risk(target_risk, context)
    current_price = _compute_hlc3(rows[-1])
    current_risk = _calculate_current_risk_from_context(context, current_price)

    low_price = current_price
    low_risk = current_risk
    high_price = current_price
    high_risk = current_risk

    if effective_target_risk < current_risk:
        for _ in range(SOLVER_MAX_EXPANSIONS):
            low_price = max(low_price * 0.5, 1.0)
            low_risk = _calculate_current_risk_from_context(context, low_price)
            if low_risk <= effective_target_risk:
                break
    elif effective_target_risk > current_risk:
        for _ in range(SOLVER_MAX_EXPANSIONS):
            high_price = high_price * 1.5
            high_risk = _calculate_current_risk_from_context(context, high_price)
            if high_risk >= effective_target_risk:
                break

    if low_price == high_price:
        return float(current_price)

    for _ in range(SOLVER_BINARY_SEARCH_STEPS):
        midpoint_price = (low_price + high_price) / 2.0
        midpoint_risk = _calculate_current_risk_from_context(context, midpoint_price)
        if midpoint_risk < effective_target_risk:
            low_price = midpoint_price
            low_risk = midpoint_risk
        else:
            high_price = midpoint_price
            high_risk = midpoint_risk

    low_distance = abs(low_risk - effective_target_risk)
    high_distance = abs(high_risk - effective_target_risk)
    return float(low_price if low_distance <= high_distance else high_price)


def build_risk_levels(rows: list[dict[str, Any]], stitch_validation: dict[str, Any]) -> dict[str, Any]:
    if not rows:
        raise ValueError("rows must not be empty")

    evaluation_date = rows[-1]["date"]
    current_price = float(_compute_hlc3(rows[-1]))
    context = _build_level_context(rows, stitch_validation)
    current_risk = _calculate_current_risk_from_context(context, current_price)

    minimum_price = solve_price_for_target_risk(rows, stitch_validation, 0.0)
    maximum_price = solve_price_for_target_risk(rows, stitch_validation, 1.0)
    price_step = _round_price_step(maximum_price - minimum_price, target_rows=PRICE_LADDER_TARGET_ROWS)

    ladder_start = max(1.0, math.floor(minimum_price / price_step) * price_step)
    ladder_end = math.ceil(maximum_price / price_step) * price_step
    price_level_rows: list[dict[str, float]] = []
    current_ladder_price = ladder_start
    while current_ladder_price <= ladder_end + (price_step / 2):
        price_level_rows.append(
            {
                "price": float(round(current_ladder_price, 6)),
                "risk": float(_calculate_current_risk_from_context(context, current_ladder_price)),
            }
        )
        current_ladder_price += price_step

    risk_level_rows = [
        {
            "risk": float(round(step_index * RISK_STEP, 6)),
            "price": float(solve_price_for_target_risk(rows, stitch_validation, step_index * RISK_STEP)),
        }
        for step_index in range(int(round(1 / RISK_STEP)) + 1)
    ]

    return {
        "methodology_version": METHODOLOGY_VERSION,
        "evaluation_date": evaluation_date,
        "current_price": current_price,
        "current_risk": current_risk,
        "turnover_enabled": _turnover_enabled(stitch_validation),
        "price_step": price_step,
        "price_level_rows": price_level_rows,
        "risk_level_rows": risk_level_rows,
    }


def build_risk_levels_public_payload(
    *,
    latest: dict[str, Any],
    levels: dict[str, Any],
    source_row_count: int,
) -> dict[str, Any]:
    return {
        "data": [
            {"risk": row["risk"], "price_usd": round(row["price"], 2)}
            for row in levels["risk_level_rows"]
        ],
        "meta": {
            "base": latest,
            "methodology_version": METHODOLOGY_VERSION,
            "evaluation_date": levels["evaluation_date"].isoformat(),
            "current_price": levels["current_price"],
            "current_risk": levels["current_risk"],
            "turnover_enabled": levels["turnover_enabled"],
            "risk_step": RISK_STEP,
            "source_row_count": source_row_count,
        },
    }
