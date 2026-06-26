from __future__ import annotations

import csv
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any

from app.risk import (
    METHODOLOGY_VERSION,
    ROBUST_Z_MIN_PERIODS,
    ROBUST_Z_WINDOW,
    RiskPoint,
    calculate_risk_series,
)

EPSILON = 1e-12
EARLY_HISTORY_END = date(2013, 12, 31)
STITCH_THRESHOLDS = {
    "hlc3": 0.03,
    "close": 0.03,
    "market_cap": 0.05,
    "circulating_supply": 0.005,
    "volume": 0.25,
}
REQUIRED_DAILY_COLUMNS = (
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "market_cap",
    "circulating_supply",
)


def _parse_utc_date(value: str) -> date:
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).date()


def _normalize_csv_headers(headers: list[str]) -> list[str]:
    return [header.lstrip("\ufeff").strip() for header in headers]


def _parse_float(value: str) -> float:
    return float(value.strip().replace(",", "")) if value.strip() else 0.0


def _date_range(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _normalize_timestamp_to_date(timestamp_ms: float | int) -> date:
    return datetime.fromtimestamp(float(timestamp_ms) / 1000, tz=timezone.utc).date()


def _is_within_bounds(day: date, *, start_date: date | None, end_date: date | None) -> bool:
    if start_date is not None and day < start_date:
        return False
    if end_date is not None and day > end_date:
        return False
    return True


def _fill_internal_daily_series_gaps(
    series_by_date: dict[date, float],
    *,
    start_date: date | None,
    end_date: date | None,
) -> dict[date, float]:
    bounded_days = sorted(
        day
        for day in series_by_date
        if _is_within_bounds(day, start_date=start_date, end_date=end_date)
    )
    filled_series = {day: float(series_by_date[day]) for day in bounded_days}
    for current_index in range(len(bounded_days) - 1):
        left_day = bounded_days[current_index]
        right_day = bounded_days[current_index + 1]
        gap_days = (right_day - left_day).days
        if gap_days <= 1:
            continue

        left_value = float(series_by_date[left_day])
        right_value = float(series_by_date[right_day])
        for offset in range(1, gap_days):
            interpolated_day = left_day + timedelta(days=offset)
            interpolation_ratio = offset / gap_days
            filled_series[interpolated_day] = left_value + ((right_value - left_value) * interpolation_ratio)

    return filled_series


def _clone_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items()}


def _compute_hlc3(row: dict[str, Any]) -> float:
    return (float(row["high"]) + float(row["low"]) + float(row["close"])) / 3.0


def _validate_daily_rows(rows: list[dict[str, Any]], *, label: str) -> None:
    if not rows:
        raise ValueError(f"{label} dataset is empty")

    dates = [row["date"] for row in rows]
    if dates != sorted(dates):
        raise ValueError(f"{label} dataset must be sorted ascending by date")
    if len(set(dates)) != len(dates):
        raise ValueError(f"{label} dataset must not contain duplicate dates")

    for row in rows:
        for field_name in REQUIRED_DAILY_COLUMNS:
            if field_name not in row:
                raise ValueError(f"{label} dataset row is missing required field {field_name}")
        if min(float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])) <= 0:
            raise ValueError(f"{label} dataset has non-positive price on {row['date']}")
        if float(row["market_cap"]) <= 0:
            raise ValueError(f"{label} dataset has non-positive market cap on {row['date']}")
        if float(row["circulating_supply"]) <= 0:
            raise ValueError(f"{label} dataset has non-positive circulating supply on {row['date']}")


def _find_missing_dates(rows: list[dict[str, Any]]) -> list[date]:
    if not rows:
        return []
    expected = set(_date_range(rows[0]["date"], rows[-1]["date"]))
    actual = {row["date"] for row in rows}
    return sorted(expected - actual)


def load_early_btc_history(csv_dir: str | Path) -> list[dict[str, Any]]:
    csv_path = Path(csv_dir)
    if not csv_path.exists():
        raise FileNotFoundError(f"BTC CSV directory not found: {csv_path}")

    rows_by_date: dict[date, dict[str, Any]] = {}
    for file_path in sorted(csv_path.glob("*.csv")):
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=";")
            try:
                headers = _normalize_csv_headers(next(reader))
            except StopIteration as exc:
                raise ValueError(f"CSV file is empty: {file_path}") from exc

            for raw_row in reader:
                if not raw_row:
                    continue
                row = {headers[index]: raw_row[index] for index in range(min(len(headers), len(raw_row)))}
                day = _parse_utc_date(row["timeOpen"])
                if day not in rows_by_date:
                    rows_by_date[day] = {
                        "date": day,
                        "open": _parse_float(row["open"]),
                        "high": _parse_float(row["high"]),
                        "low": _parse_float(row["low"]),
                        "close": _parse_float(row["close"]),
                        "volume": _parse_float(row["volume"]),
                        "market_cap": _parse_float(row["marketCap"]),
                        "circulating_supply": _parse_float(row["circulatingSupply"]),
                        "source": "csv",
                    }

    rows = [rows_by_date[day] for day in sorted(rows_by_date)]
    _validate_daily_rows(rows, label="early BTC CSV")
    missing_dates = _find_missing_dates(rows)
    if missing_dates:
        raise ValueError(
            "Early BTC CSV history has missing daily dates: "
            + ", ".join(day.isoformat() for day in missing_dates[:5])
        )
    return rows


def _series_to_map(rows: list[list[float]]) -> dict[date, float]:
    mapped: dict[date, float] = {}
    for timestamp_ms, value in rows:
        mapped[_normalize_timestamp_to_date(timestamp_ms)] = float(value)
    return mapped


def build_coingecko_daily_rows(
    market_chart: dict[str, list[list[float]]],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    prices_by_date = _fill_internal_daily_series_gaps(
        _series_to_map(market_chart.get("prices", [])),
        start_date=start_date,
        end_date=end_date,
    )
    market_caps_by_date = _fill_internal_daily_series_gaps(
        _series_to_map(market_chart.get("market_caps", [])),
        start_date=start_date,
        end_date=end_date,
    )
    volumes_by_date = _fill_internal_daily_series_gaps(
        _series_to_map(market_chart.get("total_volumes", [])),
        start_date=start_date,
        end_date=end_date,
    )

    candidate_dates = sorted(set(prices_by_date) & set(market_caps_by_date) & set(volumes_by_date))
    rows: list[dict[str, Any]] = []
    for day in candidate_dates:
        if not _is_within_bounds(day, start_date=start_date, end_date=end_date):
            continue
        close_price = prices_by_date[day]
        market_cap = market_caps_by_date[day]
        volume = volumes_by_date[day]
        if close_price <= 0:
            raise ValueError(f"CoinGecko close price must be positive on {day}")
        rows.append(
            {
                "date": day,
                "open": close_price,
                "high": close_price,
                "low": close_price,
                "close": close_price,
                "volume": volume,
                "market_cap": market_cap,
                "circulating_supply": market_cap / close_price,
                "source": "coingecko",
                "ohlc_source": "synthetic_close_only",
            }
        )

    _validate_daily_rows(rows, label="CoinGecko BTC history")
    missing_dates = _find_missing_dates(rows)
    if missing_dates:
        raise ValueError(
            "CoinGecko BTC history has missing daily dates: "
            + ", ".join(day.isoformat() for day in missing_dates[:5])
        )
    return rows


def validate_source_stitch(
    early_rows: list[dict[str, Any]],
    later_rows: list[dict[str, Any]],
    manual_audit_signoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    early_by_date = {row["date"]: row for row in early_rows}
    later_by_date = {row["date"]: row for row in later_rows}
    overlap_dates = sorted(set(early_by_date) & set(later_by_date))

    if not overlap_dates:
        if manual_audit_signoff and manual_audit_signoff.get("approved"):
            return {
                "status": "passed",
                "has_overlap": False,
                "overlap_days": 0,
                "manual_audit_required": False,
                "manual_audit_approved": True,
                "manual_audit_signoff": {
                    "approved_by": manual_audit_signoff["approved_by"],
                    "approved_at": manual_audit_signoff["approved_at"],
                    "note": manual_audit_signoff.get("note", ""),
                },
                "turnover_enabled": True,
                "price_features_accepted": True,
                "diagnostics": {},
                "reason": (
                    "No overlapping dates between local BTC CSV history and CoinGecko history; "
                    "manual audit approved for the first CoinGecko rows and turnover is enabled."
                ),
            }
        return {
            "status": "provisional_price_only",
            "has_overlap": False,
            "overlap_days": 0,
            "manual_audit_required": True,
            "manual_audit_approved": False,
            "turnover_enabled": False,
            "price_features_accepted": True,
            "diagnostics": {},
            "reason": (
                "No overlapping dates between local BTC CSV history and CoinGecko history; "
                "price-based stitch accepted provisionally, but turnover is disabled until a manual audit is completed."
            ),
        }

    def _median_relative_diff(left_values: list[float], right_values: list[float]) -> float:
        relative_diffs = [
            abs(left - right) / max(abs(left), abs(right), EPSILON)
            for left, right in zip(left_values, right_values)
        ]
        return median(relative_diffs) if relative_diffs else 0.0

    fields = {
        "hlc3": _compute_hlc3,
        "close": lambda row: row["close"],
        "market_cap": lambda row: row["market_cap"],
        "circulating_supply": lambda row: row["circulating_supply"],
        "volume": lambda row: row["volume"],
    }
    diagnostics: dict[str, dict[str, Any]] = {}
    for field_name, extractor in fields.items():
        early_values = [float(extractor(early_by_date[day])) for day in overlap_dates]
        later_values = [float(extractor(later_by_date[day])) for day in overlap_dates]
        diff = _median_relative_diff(early_values, later_values)
        threshold = STITCH_THRESHOLDS[field_name]
        diagnostics[field_name] = {
            "median_relative_diff": diff,
            "threshold": threshold,
            "passed": diff <= threshold,
        }

    price_features_accepted = all(
        diagnostics[field_name]["passed"]
        for field_name in ("hlc3", "close", "market_cap", "circulating_supply")
    )
    turnover_enabled = price_features_accepted and diagnostics["volume"]["passed"]
    if turnover_enabled:
        status = "passed"
        reason = "Overlap diagnostics passed for price, market cap, circulating supply, and volume."
    elif price_features_accepted:
        status = "failed"
        reason = "Volume overlap diagnostics exceeded the stitch threshold; turnover disabled."
    else:
        status = "failed"
        failed_fields = [
            field_name
            for field_name, diagnostic in diagnostics.items()
            if not diagnostic["passed"]
        ]
        reason = "Stitch diagnostics failed for " + ", ".join(sorted(failed_fields)) + "; turnover disabled."

    return {
        "status": status,
        "has_overlap": True,
        "overlap_days": len(overlap_dates),
        "manual_audit_required": False,
        "manual_audit_approved": False,
        "turnover_enabled": turnover_enabled,
        "price_features_accepted": price_features_accepted,
        "diagnostics": diagnostics,
        "reason": reason,
    }


def merge_daily_datasets(
    early_rows: list[dict[str, Any]],
    later_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    _validate_daily_rows(early_rows, label="early BTC CSV")
    _validate_daily_rows(later_rows, label="CoinGecko BTC history")

    early_last_date = early_rows[-1]["date"]
    merged_rows = [_clone_row(row) for row in early_rows]
    merged_rows.extend(_clone_row(row) for row in later_rows if row["date"] > early_last_date)

    missing_dates = _find_missing_dates(merged_rows)
    if missing_dates:
        raise ValueError(
            "Merged BTC dataset has missing daily dates: "
            + ", ".join(day.isoformat() for day in missing_dates[:5])
        )
    _validate_daily_rows(merged_rows, label="merged BTC history")
    return merged_rows


def validate_risk_dataset(
    source_rows: list[dict[str, Any]],
    risk_points: list[RiskPoint],
    *,
    turnover_enabled: bool,
) -> dict[str, Any]:
    missing_dates = _find_missing_dates(source_rows)
    invalid_risk_points = [
        point.day
        for point in risk_points
        if not math.isfinite(point.risk) or point.risk < 0.0 or point.risk > 1.0
    ]
    return {
        "methodology_version": METHODOLOGY_VERSION,
        "covered_start": source_rows[0]["date"],
        "covered_end": source_rows[-1]["date"],
        "missing_date_count": len(missing_dates),
        "missing_dates": missing_dates,
        "invalid_risk_value_count": len(invalid_risk_points),
        "invalid_risk_dates": invalid_risk_points,
        "risk_range_ok": len(invalid_risk_points) == 0,
        "turnover_enabled": turnover_enabled,
        "robust_z_window": ROBUST_Z_WINDOW,
        "robust_z_min_periods": ROBUST_Z_MIN_PERIODS,
    }


def render_validation_summary(dataset: dict[str, Any]) -> str:
    stitch = dataset["stitch_validation"]
    validation = dataset["validation"]
    return "\n".join(
        [
            f"Methodology: {METHODOLOGY_VERSION}",
            f"Stitch status: {stitch['status']}",
            f"Turnover: {'enabled' if stitch['turnover_enabled'] else 'disabled'}",
            f"Reason: {stitch['reason']}",
            f"Coverage: {validation['covered_start'].isoformat()} -> {validation['covered_end'].isoformat()}",
            f"Missing dates: {validation['missing_date_count']}",
            f"Invalid risk values: {validation['invalid_risk_value_count']}",
            f"Risk range ok: {'yes' if validation['risk_range_ok'] else 'no'}",
        ]
    )


def build_merged_risk_dataset(
    *,
    csv_dir: str | Path,
    coingecko_market_chart: dict[str, list[list[float]]],
    coingecko_start_date: date | None = None,
    coingecko_end_date: date | None = None,
    manual_audit_signoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    early_rows = load_early_btc_history(csv_dir)
    later_rows = build_coingecko_daily_rows(
        coingecko_market_chart,
        start_date=coingecko_start_date,
        end_date=coingecko_end_date,
    )
    stitch_validation = validate_source_stitch(early_rows, later_rows, manual_audit_signoff)
    source_rows = merge_daily_datasets(early_rows, later_rows)
    turnover_enabled = bool(stitch_validation["turnover_enabled"])
    risk_points = calculate_risk_series(source_rows, turnover_enabled=turnover_enabled)
    validation = validate_risk_dataset(source_rows, risk_points, turnover_enabled=turnover_enabled)
    dataset = {
        "source_rows": source_rows,
        "risk_points": risk_points,
        "validation": validation,
        "stitch_validation": stitch_validation,
    }
    dataset["validation_summary"] = render_validation_summary(dataset)
    return dataset
