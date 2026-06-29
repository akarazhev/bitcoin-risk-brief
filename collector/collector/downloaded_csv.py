from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.risk_sources import find_missing_dates, load_btc_usd_daily_csv, merge_daily_rows, write_btc_usd_daily_csv


_REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume", "market_cap")
_COLUMN_ALIASES = {
    "date": {"date", "timeopen", "timestamp"},
    "open": {"open", "openusd"},
    "high": {"high", "highusd"},
    "low": {"low", "lowusd"},
    "close": {"close", "closeusd"},
    "volume": {"volume", "volumeusd"},
    "market_cap": {"marketcap", "marketcapusd"},
    "circulating_supply": {"circulatingsupply", "circulatingsupplybtc"},
}
_NULL_VALUES = {"", "--", "-", "n/a", "na", "null", "none"}


@dataclass(frozen=True)
class DownloadedCsvImportResult:
    downloaded_row_count: int
    written_row_count: int
    covered_start: date
    covered_end: date
    downloaded_start: date
    downloaded_end: date


def _normalize_column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lstrip("\ufeff").strip().lower())


def _parse_date(value: str) -> date:
    text = value.strip()
    if not text:
        raise ValueError("Downloaded CoinMarketCap CSV row has an empty date")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for date_format in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"Downloaded CoinMarketCap CSV row has unsupported date value: {value!r}")


def _parse_number(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip()
    if text.lower() in _NULL_VALUES:
        return 0.0
    text = text.replace(",", "").replace("$", "")
    return float(text)


def _detect_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;")
    except csv.Error:
        class FallbackDialect(csv.excel):
            delimiter = "," if sample.splitlines()[0].count(",") >= sample.splitlines()[0].count(";") else ";"

        return FallbackDialect


def _resolve_columns(headers: list[str]) -> dict[str, int]:
    normalized_headers = [_normalize_column_name(header) for header in headers]
    resolved: dict[str, int] = {}
    for field_name, aliases in _COLUMN_ALIASES.items():
        for index, normalized in enumerate(normalized_headers):
            if normalized in aliases:
                resolved[field_name] = index
                break

    missing_columns = [field_name for field_name in _REQUIRED_COLUMNS if field_name not in resolved]
    if missing_columns:
        raise ValueError(
            "Downloaded CoinMarketCap CSV is missing required columns: " + ", ".join(missing_columns)
        )
    return resolved


def _repair_unquoted_date_value(headers: list[str], values: list[str], columns: dict[str, int]) -> list[str]:
    if len(values) == len(headers) + 1 and columns["date"] == 0:
        try:
            _parse_date(f"{values[0].strip()}, {values[1].strip()}")
        except ValueError:
            return values
        return [f"{values[0].strip()}, {values[1].strip()}", *values[2:]]
    return values


def _row_value(values: list[str], column_index: int) -> str:
    return values[column_index] if column_index < len(values) else ""


def _validate_downloaded_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Downloaded CoinMarketCap CSV dataset is empty")

    dates = [row["date"] for row in rows]
    if dates != sorted(dates):
        raise ValueError("Downloaded CoinMarketCap CSV dataset must be sorted ascending by date")
    if len(set(dates)) != len(dates):
        raise ValueError("Downloaded CoinMarketCap CSV dataset must not contain duplicate dates")

    for row in rows:
        if min(float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])) <= 0:
            raise ValueError(f"Downloaded CoinMarketCap CSV has non-positive price on {row['date']}")
        if float(row["market_cap"]) <= 0:
            raise ValueError(f"Downloaded CoinMarketCap CSV has non-positive market cap on {row['date']}")
        if float(row["circulating_supply"]) <= 0:
            raise ValueError(f"Downloaded CoinMarketCap CSV has non-positive circulating supply on {row['date']}")

    missing_dates = find_missing_dates(rows)
    if missing_dates:
        raise ValueError(
            "Downloaded CoinMarketCap CSV has missing daily dates: "
            + ", ".join(day.isoformat() for day in missing_dates[:5])
        )


def load_coinmarketcap_downloaded_csv(downloaded_csv_path: str | Path) -> list[dict[str, Any]]:
    path = Path(downloaded_csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Downloaded CoinMarketCap CSV not found: {path}")

    sample = path.read_text(encoding="utf-8-sig")
    if not sample.strip():
        raise ValueError(f"Downloaded CoinMarketCap CSV is empty: {path}")

    dialect = _detect_dialect(sample)
    rows_by_date: dict[date, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, dialect=dialect)
        try:
            headers = [header.strip() for header in next(reader)]
        except StopIteration as exc:
            raise ValueError(f"Downloaded CoinMarketCap CSV is empty: {path}") from exc
        columns = _resolve_columns(headers)

        for values in reader:
            if not values or not any(value.strip() for value in values):
                continue
            values = _repair_unquoted_date_value(headers, values, columns)
            day = _parse_date(_row_value(values, columns["date"]))
            if day in rows_by_date:
                raise ValueError(f"Downloaded CoinMarketCap CSV contains duplicate date {day.isoformat()}")

            close = _parse_number(_row_value(values, columns["close"]))
            market_cap = _parse_number(_row_value(values, columns["market_cap"]))
            circulating_supply = 0.0
            if "circulating_supply" in columns:
                circulating_supply = _parse_number(_row_value(values, columns["circulating_supply"]))
            if circulating_supply <= 0 and close > 0:
                circulating_supply = market_cap / close

            rows_by_date[day] = {
                "date": day,
                "open": _parse_number(_row_value(values, columns["open"])),
                "high": _parse_number(_row_value(values, columns["high"])),
                "low": _parse_number(_row_value(values, columns["low"])),
                "close": close,
                "volume": _parse_number(_row_value(values, columns["volume"])),
                "market_cap": market_cap,
                "circulating_supply": circulating_supply,
                "source": "coinmarketcap_csv",
            }

    rows = [rows_by_date[day] for day in sorted(rows_by_date)]
    _validate_downloaded_rows(rows)
    return rows


def _merge_downloaded_rows(
    existing_rows: list[dict[str, Any]],
    downloaded_rows: list[dict[str, Any]],
    *,
    expected_end_date: date | None,
) -> list[dict[str, Any]]:
    existing_start = existing_rows[0]["date"]
    existing_end = existing_rows[-1]["date"]
    downloaded_start = downloaded_rows[0]["date"]
    downloaded_end = downloaded_rows[-1]["date"]

    if downloaded_end < existing_end:
        raise ValueError(
            "Downloaded CoinMarketCap CSV is partial: "
            f"it ends at {downloaded_end.isoformat()} before canonical tail {existing_end.isoformat()}"
        )
    if downloaded_start > existing_end + timedelta(days=1):
        missing_start = existing_end + timedelta(days=1)
        missing_end = downloaded_start - timedelta(days=1)
        raise ValueError(
            "Downloaded CoinMarketCap CSV has missing daily dates between canonical tail and download: "
            f"{missing_start.isoformat()}..{missing_end.isoformat()}"
        )
    if downloaded_start > existing_start and downloaded_end == existing_end:
        raise ValueError(
            "Downloaded CoinMarketCap CSV is partial: "
            "it overlaps the canonical tail but does not extend it"
        )

    merged_rows = merge_daily_rows(existing_rows, downloaded_rows)
    missing_dates = find_missing_dates(merged_rows)
    if missing_dates:
        raise ValueError(
            "Downloaded CoinMarketCap CSV would create missing daily dates: "
            + ", ".join(day.isoformat() for day in missing_dates[:5])
        )
    if expected_end_date is not None and merged_rows[-1]["date"] < expected_end_date:
        raise ValueError(
            "Downloaded CoinMarketCap CSV is partial: "
            f"expected coverage through {expected_end_date.isoformat()}, got {merged_rows[-1]['date'].isoformat()}"
        )
    return merged_rows


def import_coinmarketcap_downloaded_csv(
    downloaded_csv_path: str | Path,
    canonical_csv_path: str | Path,
    *,
    expected_end_date: date | None = None,
) -> DownloadedCsvImportResult:
    existing_rows = load_btc_usd_daily_csv(canonical_csv_path)
    downloaded_rows = load_coinmarketcap_downloaded_csv(downloaded_csv_path)
    merged_rows = _merge_downloaded_rows(
        existing_rows,
        downloaded_rows,
        expected_end_date=expected_end_date,
    )
    write_btc_usd_daily_csv(canonical_csv_path, merged_rows)
    return DownloadedCsvImportResult(
        downloaded_row_count=len(downloaded_rows),
        written_row_count=len(merged_rows),
        covered_start=merged_rows[0]["date"],
        covered_end=merged_rows[-1]["date"],
        downloaded_start=downloaded_rows[0]["date"],
        downloaded_end=downloaded_rows[-1]["date"],
    )
