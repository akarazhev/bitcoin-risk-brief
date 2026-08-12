from __future__ import annotations

from datetime import date, datetime, timedelta
import html
import math

from app.risk import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD


_LEVEL_TOLERANCE = 1e-9


def band_boundary(risk_state: str, risk: float) -> float | None:
    if risk_state == "low":
        return LOW_RISK_THRESHOLD
    if risk_state == "high":
        return HIGH_RISK_THRESHOLD
    if risk_state == "neutral":
        return min(LOW_RISK_THRESHOLD, HIGH_RISK_THRESHOLD, key=lambda boundary: abs(risk - boundary))
    return None


def _parse_day(value: object) -> date | datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _format_day(value: object) -> str:
    return _parse_day(value).strftime("%Y-%m-%d")


def _is_previous_day(previous_value: object, latest_value: object) -> bool:
    previous_day = _parse_day(previous_value)
    latest_day = _parse_day(latest_value)
    if isinstance(previous_day, datetime):
        previous_day = previous_day.date()
    if isinstance(latest_day, datetime):
        latest_day = latest_day.date()
    return latest_day - previous_day == timedelta(days=1)


def _report_date(value: object) -> date | datetime:
    return _parse_day(value) + timedelta(days=1)


def _band_entered(risk_state: str, boundary: float) -> str | None:
    if risk_state == "low" and boundary == LOW_RISK_THRESHOLD:
        return "Neutral"
    if risk_state == "neutral" and boundary == LOW_RISK_THRESHOLD:
        return "Low"
    if risk_state == "neutral" and boundary == HIGH_RISK_THRESHOLD:
        return "High"
    if risk_state == "high" and boundary == HIGH_RISK_THRESHOLD:
        return "Neutral"
    return None


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
    report_day = _format_day(_report_date(latest["timestamp"]))
    latest_risk = float(latest["risk"])
    latest_state = str(latest["risk_state"])
    escaped_latest_state = html.escape(latest_state)
    escaped_methodology_version = html.escape(methodology_version)

    if previous is not None and str(previous["risk_state"]) != latest_state:
        escaped_previous_state = html.escape(str(previous["risk_state"]))
        first_line = (
            f"<b>Bitcoin risk moved from {escaped_previous_state} to {escaped_latest_state}</b> — report date {report_day}"
        )
    else:
        first_line = f"<b>Bitcoin Risk Brief</b> — report date {report_day}"

    lines = [first_line, "", f"<b>Risk {latest_risk:.2f} — {escaped_latest_state}</b>"]
    if previous is not None:
        delta = latest_risk - float(previous["risk"])
        line = f"Change: {_signed_delta(delta)}"
        if not _is_previous_day(previous["timestamp"], latest["timestamp"]):
            line += f" from {_format_day(previous['timestamp'])}"
        lines.append(line)

    boundary = band_boundary(latest_state, latest_risk)
    if boundary is not None:
        price = _level_price(levels, boundary)
        band = _band_entered(latest_state, boundary)
        if price is not None and band is not None:
            lines.append(
                f"{band} band at risk {boundary:.2f} — model price ${price:,.0f}"
            )

    lines.extend(
        [
            f"Coverage through {latest_day} · {escaped_methodology_version}",
            "",
            "bitcoinriskbrief.minihub.app",
            "",
            "<i>Analytics and research context, not financial advice.</i>",
        ]
    )
    return "\n".join(lines)
