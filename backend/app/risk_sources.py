from __future__ import annotations

import csv
import math
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from app.risk import (
    METHODOLOGY_VERSION,
    ROBUST_Z_MIN_PERIODS,
    ROBUST_Z_WINDOW,
    RiskPoint,
    calculate_risk_series,
)

BTC_USD_DAILY_HEADER = (
    "timeOpen",
    "timeClose",
    "timeHigh",
    "timeLow",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "marketCap",
    "circulatingSupply",
    "timestamp",
)
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


def _format_cmc_timestamp(value: Any, *, end_of_day: bool = False) -> str:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    if isinstance(value, date):
        clock = time(23, 59, 59, 999000) if end_of_day else time.min
        return datetime.combine(value, clock, tzinfo=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    raise TypeError(f"Unsupported timestamp value: {value!r}")


def _parse_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        return float(value.strip().replace(",", "")) if value.strip() else 0.0
    return float(value)


def _normalize_csv_headers(headers: list[str]) -> list[str]:
    return [header.lstrip("\ufeff").strip() for header in headers]


def _date_range(start: date, end: date) -> set[date]:
    return {start.fromordinal(ordinal) for ordinal in range(start.toordinal(), end.toordinal() + 1)}


def _clone_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items()}


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


def find_missing_dates(rows: list[dict[str, Any]]) -> list[date]:
    if not rows:
        return []
    return sorted(_date_range(rows[0]["date"], rows[-1]["date"]) - {row["date"] for row in rows})


def load_btc_usd_daily_csv(csv_path: str | Path) -> list[dict[str, Any]]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"BTC USD CSV not found: {path}")

    rows_by_date: dict[date, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        try:
            headers = _normalize_csv_headers(next(reader))
        except StopIteration as exc:
            raise ValueError(f"CSV file is empty: {path}") from exc

        for raw_row in reader:
            if not raw_row:
                continue
            item = {headers[index]: raw_row[index] for index in range(min(len(headers), len(raw_row)))}
            day = _parse_utc_date(item["timeOpen"] or item["timestamp"] or item["timeClose"])
            close = _parse_float(item["close"])
            market_cap = _parse_float(item["marketCap"])
            circulating_supply = _parse_float(item.get("circulatingSupply"))
            if circulating_supply <= 0 and close > 0:
                circulating_supply = market_cap / close
            rows_by_date[day] = {
                "date": day,
                "time_open": item.get("timeOpen") or _format_cmc_timestamp(day),
                "time_close": item.get("timeClose") or _format_cmc_timestamp(day, end_of_day=True),
                "time_high": item.get("timeHigh") or item.get("timeOpen") or _format_cmc_timestamp(day),
                "time_low": item.get("timeLow") or item.get("timeOpen") or _format_cmc_timestamp(day),
                "timestamp": item.get("timestamp") or item.get("timeClose") or _format_cmc_timestamp(day, end_of_day=True),
                "open": _parse_float(item["open"]),
                "high": _parse_float(item["high"]),
                "low": _parse_float(item["low"]),
                "close": close,
                "volume": _parse_float(item["volume"]),
                "market_cap": market_cap,
                "circulating_supply": circulating_supply,
                "source": "coinmarketcap_csv",
            }

    rows = [rows_by_date[day] for day in sorted(rows_by_date)]
    _validate_daily_rows(rows, label="CoinMarketCap BTC USD CSV")
    missing_dates = find_missing_dates(rows)
    if missing_dates:
        raise ValueError(
            "CoinMarketCap BTC USD CSV has missing daily dates: "
            + ", ".join(day.isoformat() for day in missing_dates[:5])
        )
    return rows


def merge_daily_rows(
    existing_rows: list[dict[str, Any]],
    fetched_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_date = {row["date"]: _clone_row(row) for row in existing_rows}
    for row in fetched_rows:
        rows_by_date[row["date"]] = _clone_row(row)
    return [rows_by_date[day] for day in sorted(rows_by_date)]


def _serialize_number(value: float) -> str:
    return f"{float(value):.12g}"


def write_btc_usd_daily_csv(csv_path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _validate_daily_rows(rows, label="CoinMarketCap BTC USD CSV")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", lineterminator="\n")
        writer.writerow(BTC_USD_DAILY_HEADER)
        for row in rows:
            day = row["date"]
            writer.writerow(
                [
                    _format_cmc_timestamp(row.get("time_open", day)),
                    _format_cmc_timestamp(row.get("time_close", day), end_of_day=True),
                    _format_cmc_timestamp(row.get("time_high", row.get("time_open", day))),
                    _format_cmc_timestamp(row.get("time_low", row.get("time_open", day))),
                    _serialize_number(row["open"]),
                    _serialize_number(row["high"]),
                    _serialize_number(row["low"]),
                    _serialize_number(row["close"]),
                    _serialize_number(row["volume"]),
                    _serialize_number(row["market_cap"]),
                    _serialize_number(row["circulating_supply"]),
                    _format_cmc_timestamp(row.get("timestamp", row.get("time_close", day)), end_of_day=True),
                ]
            )


def validate_risk_dataset(
    source_rows: list[dict[str, Any]],
    risk_points: list[RiskPoint],
    *,
    turnover_enabled: bool,
) -> dict[str, Any]:
    missing_dates = find_missing_dates(source_rows)
    invalid_risk_points = [
        point.day
        for point in risk_points
        if not math.isfinite(point.risk) or point.risk < 0.0 or point.risk > 1.0
    ]
    return {
        "methodology_version": METHODOLOGY_VERSION,
        "source_strategy": "coinmarketcap_csv",
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
    validation = dataset["validation"]
    return "\n".join(
        [
            f"Methodology: {METHODOLOGY_VERSION}",
            "Source: coinmarketcap_csv",
            f"Turnover: {'enabled' if validation['turnover_enabled'] else 'disabled'}",
            f"Coverage: {validation['covered_start'].isoformat()} -> {validation['covered_end'].isoformat()}",
            f"Missing dates: {validation['missing_date_count']}",
            f"Invalid risk values: {validation['invalid_risk_value_count']}",
            f"Risk range ok: {'yes' if validation['risk_range_ok'] else 'no'}",
        ]
    )


def build_csv_risk_dataset(csv_path: str | Path) -> dict[str, Any]:
    source_rows = load_btc_usd_daily_csv(csv_path)
    turnover_enabled = True
    risk_points = calculate_risk_series(source_rows, turnover_enabled=turnover_enabled)
    validation = validate_risk_dataset(source_rows, risk_points, turnover_enabled=turnover_enabled)
    dataset = {
        "source_strategy": "coinmarketcap_csv",
        "source_rows": source_rows,
        "risk_points": risk_points,
        "validation": validation,
    }
    dataset["validation_summary"] = render_validation_summary(dataset)
    return dataset
