from __future__ import annotations

from datetime import date, datetime
import math

from app.risk import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD


_LEVEL_TOLERANCE = 1e-9
_MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def band_boundary(risk_state: str, risk: float) -> float | None:
    if risk_state == "low":
        return LOW_RISK_THRESHOLD
    if risk_state == "high":
        return HIGH_RISK_THRESHOLD
    if risk_state == "neutral":
        return min(LOW_RISK_THRESHOLD, HIGH_RISK_THRESHOLD, key=lambda boundary: abs(risk - boundary))
    return None


def _format_day(value: object) -> str:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return f"{parsed.day} {_MONTH_NAMES[parsed.month - 1]} {parsed.year}"


def _signed_delta(value: float) -> str:
    rounded = round(value, 2)
    if rounded < 0:
        return f"−{abs(rounded):.2f}"
    return f"+{rounded:.2f}"


def _level_price(levels: dict | None, boundary: float) -> float | None:
    if levels is None:
        return None
    for point in levels.get("data", []):
        try:
            risk = float(point["risk"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(risk) and abs(risk - boundary) <= _LEVEL_TOLERANCE:
            try:
                price = float(point["price_usd"])
            except (KeyError, TypeError, ValueError):
                return None
            return price if math.isfinite(price) else None
    return None


def compose_daily_post(
    *,
    latest: dict,
    previous: dict | None,
    levels: dict | None,
    methodology_version: str,
) -> str:
    latest_day = _format_day(latest["timestamp"])
    latest_risk = float(latest["risk"])
    latest_state = str(latest["risk_state"])

    if previous is not None and str(previous["risk_state"]) != latest_state:
        first_line = (
            f"Bitcoin risk moved from {previous['risk_state']} to {latest_state} — {latest_day}"
        )
    else:
        first_line = f"Bitcoin Risk Brief — {latest_day}"

    lines = [first_line, "", f"Risk {latest_risk:.2f} — {latest_state}"]
    if previous is not None:
        delta = latest_risk - float(previous["risk"])
        lines.append(f"Change: {_signed_delta(delta)} from {_format_day(previous['timestamp'])}")

    boundary = band_boundary(latest_state, latest_risk)
    if boundary is not None:
        price = _level_price(levels, boundary)
        if price is not None:
            lines.append(
                f"Neutral band begins at risk {boundary:.2f} — model price ${price:,.0f}"
            )

    lines.extend(
        [
            f"Data: fresh through {latest_day} · {methodology_version}",
            "",
            "bitcoinriskbrief.minihub.app",
            "",
            "Analytics and research context, not financial advice.",
        ]
    )
    return "\n".join(lines)
