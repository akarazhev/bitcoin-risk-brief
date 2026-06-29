from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

CANONICAL_SOURCE = "coinmarketcap_csv"


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _as_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    parsed = _parse_datetime(value)
    return parsed.date() if parsed else None


def _validation_source(validation: dict[str, Any]) -> str | None:
    validation_json = validation.get("validation_json") or {}
    source = validation_json.get("source")
    if source:
        return str(source)
    nested_validation = validation_json.get("validation") or {}
    nested_source = nested_validation.get("source_strategy")
    return str(nested_source) if nested_source else None


def _methodology_version(validation: dict[str, Any]) -> str | None:
    validation_json = validation.get("validation_json") or {}
    version = validation_json.get("methodology_version")
    if version:
        return str(version)
    nested_validation = validation_json.get("validation") or {}
    nested_version = nested_validation.get("methodology_version")
    return str(nested_version) if nested_version else None


def build_readiness_payload(
    latest_risk: dict[str, Any] | None,
    validation: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    max_age_days: int,
) -> tuple[dict[str, Any], int]:
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    current_date = current_time.astimezone(timezone.utc).date()

    latest_day = _as_date(latest_risk.get("timestamp")) if latest_risk else None
    covered_end = _as_date(validation.get("covered_end")) if validation else None
    source = _validation_source(validation) if validation else None
    methodology_version = _methodology_version(validation) if validation else None
    row_count = int(validation.get("row_count", 0)) if validation else 0
    data_age_days = (current_date - latest_day).days if latest_day else None

    checks = {
        "risk_data_available": latest_risk is not None,
        "validation_available": validation is not None,
        "risk_range_ok": bool(validation and validation.get("risk_range_ok")),
        "validation_has_rows": row_count > 0,
        "latest_matches_validation_end": latest_day is not None and latest_day == covered_end,
        "source_is_canonical": source == CANONICAL_SOURCE,
        "data_fresh": data_age_days is not None and data_age_days <= max_age_days,
    }
    ready = all(checks.values())
    payload = {
        "status": "ready" if ready else "degraded",
        "checks": checks,
        "data": {
            "latest_date": latest_day.isoformat() if latest_day else None,
            "covered_end": covered_end.isoformat() if covered_end else None,
            "data_age_days": data_age_days,
            "max_age_days": max_age_days,
            "source": source,
            "row_count": row_count,
            "methodology_version": methodology_version,
        },
    }
    return payload, 200 if ready else 503
