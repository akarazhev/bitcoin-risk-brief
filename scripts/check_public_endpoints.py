#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import math
import sys
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


MAX_RESPONSE_BYTES = 1_048_576
PUBLIC_ENDPOINTS = (
    "/api/health",
    "/api/readiness",
    "/api/risk/latest",
)
CACHEABLE_ENDPOINTS = (
    "/api/readiness",
    "/api/risk/latest",
)
REQUIRED_READINESS_CHECKS = (
    "risk_data_available",
    "validation_available",
    "risk_range_ok",
    "validation_has_rows",
    "latest_matches_validation_end",
    "source_is_canonical",
    "data_fresh",
)
SUPPORTED_CACHE_HEADERS = (
    "Cache-Control",
    "ETag",
    "X-Cache-Version",
    "X-Cache",
)


class ProbeError(Exception):
    exit_code = 1
    status = "CRITICAL"


class ProbeConfigError(ProbeError):
    exit_code = 2
    status = "CONFIG"


@dataclass(frozen=True)
class EndpointResult:
    path: str
    payload: dict[str, Any]
    headers: dict[str, str]


@dataclass(frozen=True)
class ReadinessInfo:
    latest_date: date
    covered_end: date
    data_age_days: int
    max_age_days: int


@dataclass(frozen=True)
class LatestRiskInfo:
    latest_date: date
    risk: float


def positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return parsed


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def parse_expected_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be YYYY-MM-DD") from exc


def normalize_now(now_utc: datetime | None) -> datetime:
    if now_utc is None:
        return datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        raise ProbeConfigError("now_utc must include timezone information")
    return now_utc.astimezone(timezone.utc)


def normalize_base_url(base_url: str) -> str:
    value = base_url.strip()
    if not value:
        raise ProbeConfigError("base URL must not be empty")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ProbeConfigError("base URL must include http(s) scheme and host")
    if parsed.query or parsed.fragment:
        raise ProbeConfigError("base URL must not include query string or fragment")
    return value.rstrip("/")


def endpoint_url(base_url: str, path: str) -> str:
    return urljoin(f"{base_url}/", path.lstrip("/"))


def response_status(response: Any) -> int:
    status = getattr(response, "status", None)
    if status is not None:
        return int(status)
    getcode = getattr(response, "getcode", None)
    if callable(getcode):
        return int(getcode())
    raise ProbeError("response did not expose an HTTP status")


def response_headers(response: Any) -> dict[str, str]:
    raw_headers = getattr(response, "headers", None)
    if raw_headers is None:
        info = getattr(response, "info", None)
        raw_headers = info() if callable(info) else {}
    return {str(key).lower(): str(value) for key, value in raw_headers.items()}


def read_response_body(response: Any, path: str) -> bytes:
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ProbeError(f"GET {path} response body is too large")
    return body


def decode_json(body: bytes, path: str) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeError(f"GET {path} returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise ProbeError(f"GET {path} JSON payload is not an object")
    return payload


def fetch_json(
    base_url: str,
    path: str,
    *,
    opener: Callable[..., Any] | None,
    timeout: float,
) -> EndpointResult:
    request = Request(
        endpoint_url(base_url, path),
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "bitcoin-risk-brief-public-endpoint-probe/1.0",
        },
    )
    open_url = opener or urlopen
    response = None
    try:
        response = open_url(request, timeout=timeout)
        status = response_status(response)
        if status != 200:
            raise ProbeError(f"GET {path} returned HTTP {status}")
        headers = response_headers(response)
        payload = decode_json(read_response_body(response, path), path)
        return EndpointResult(path=path, payload=payload, headers=headers)
    except HTTPError as exc:
        raise ProbeError(f"GET {path} returned HTTP {exc.code}") from exc
    except (TimeoutError, URLError, OSError) as exc:
        raise ProbeError(f"GET {path} request failed") from exc
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()


def parse_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ProbeError(f"{label} is missing or not a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProbeError(f"{label} timestamp is malformed") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_payload_date(value: Any, label: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ProbeError(f"{label} is missing or not a string")
    try:
        return date.fromisoformat(value)
    except ValueError:
        return parse_datetime(value, label).date()


def require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProbeError(f"{label} is missing or not a string")
    return value


def require_non_negative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProbeError(f"{label} is missing or not an integer")
    if value < 0:
        raise ProbeError(f"{label} is negative")
    return value


def validate_health(payload: dict[str, Any]) -> None:
    if payload.get("status") != "ok":
        raise ProbeError("GET /api/health status is not ok")


def validate_readiness(payload: dict[str, Any]) -> ReadinessInfo:
    status = payload.get("status")
    if status != "ready":
        raise ProbeError(f"GET /api/readiness readiness status is {status if status is not None else 'missing'}")

    checks = payload.get("checks")
    if not isinstance(checks, dict):
        raise ProbeError("GET /api/readiness checks payload is missing")
    for check_name in REQUIRED_READINESS_CHECKS:
        if checks.get(check_name) is not True:
            raise ProbeError(f"GET /api/readiness checks.{check_name} is not true")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ProbeError("GET /api/readiness data payload is missing")
    latest_date = parse_payload_date(data.get("latest_date"), "GET /api/readiness data.latest_date")
    covered_end = parse_payload_date(data.get("covered_end"), "GET /api/readiness data.covered_end")
    data_age_days = require_non_negative_int(
        data.get("data_age_days"),
        "GET /api/readiness data.data_age_days",
    )
    max_age_days = require_non_negative_int(
        data.get("max_age_days"),
        "GET /api/readiness data.max_age_days",
    )
    require_non_empty_string(data.get("source"), "GET /api/readiness data.source")
    row_count = require_non_negative_int(data.get("row_count"), "GET /api/readiness data.row_count")
    if row_count == 0:
        raise ProbeError("GET /api/readiness data.row_count is zero")
    require_non_empty_string(data.get("methodology_version"), "GET /api/readiness data.methodology_version")
    if latest_date != covered_end:
        raise ProbeError("GET /api/readiness data.latest_date does not match data.covered_end")
    return ReadinessInfo(
        latest_date=latest_date,
        covered_end=covered_end,
        data_age_days=data_age_days,
        max_age_days=max_age_days,
    )


def validate_latest_risk(payload: dict[str, Any]) -> LatestRiskInfo:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ProbeError("GET /api/risk/latest data payload is missing")

    timestamp = parse_datetime(data.get("timestamp"), "GET /api/risk/latest data.timestamp")
    risk = data.get("risk")
    if isinstance(risk, bool) or not isinstance(risk, (int, float)):
        raise ProbeError("GET /api/risk/latest data.risk is missing or not numeric")
    risk_value = float(risk)
    if not math.isfinite(risk_value) or risk_value < 0 or risk_value > 1:
        raise ProbeError("GET /api/risk/latest data.risk is outside 0..1")
    return LatestRiskInfo(latest_date=timestamp.date(), risk=risk_value)


def validate_cache_headers(
    results: dict[str, EndpointResult],
    required_headers: tuple[str, ...],
) -> None:
    for header in required_headers:
        key = header.lower()
        for path in CACHEABLE_ENDPOINTS:
            if not results[path].headers.get(key):
                raise ProbeError(f"GET {path} missing {header}")


def validate_freshness_policy(
    readiness: ReadinessInfo,
    latest: LatestRiskInfo,
    *,
    expected_latest_date: date | None,
    max_data_age_days: int | None,
    now_utc: datetime,
) -> None:
    if readiness.latest_date != latest.latest_date:
        raise ProbeError(
            f"readiness latest date {readiness.latest_date.isoformat()} "
            f"does not match latest risk date {latest.latest_date.isoformat()}"
        )
    if readiness.covered_end != latest.latest_date:
        raise ProbeError(
            f"readiness covered_end {readiness.covered_end.isoformat()} "
            f"does not match latest risk date {latest.latest_date.isoformat()}"
        )

    if expected_latest_date is not None and latest.latest_date != expected_latest_date:
        raise ProbeError(
            f"expected latest date {expected_latest_date.isoformat()} "
            f"but saw {latest.latest_date.isoformat()}"
        )

    if max_data_age_days is not None:
        age_days = (now_utc.date() - latest.latest_date).days
        if age_days < 0:
            raise ProbeError(f"latest date {latest.latest_date.isoformat()} is in the future")
        if age_days > max_data_age_days:
            raise ProbeError(
                f"latest date {latest.latest_date.isoformat()} is stale: "
                f"age {age_days}d exceeds max {max_data_age_days}d"
            )
        if readiness.data_age_days > max_data_age_days:
            raise ProbeError(
                f"readiness data_age_days {readiness.data_age_days} exceeds max {max_data_age_days}d"
            )


def format_cache_header_summary(required_headers: tuple[str, ...]) -> str:
    return ",".join(required_headers) if required_headers else "none"


def format_freshness_summary(expected_latest_date: date | None, max_data_age_days: int | None) -> str:
    parts: list[str] = []
    if expected_latest_date is not None:
        parts.append(f"expected_latest_date:{expected_latest_date.isoformat()}")
    if max_data_age_days is not None:
        parts.append(f"max_data_age_days:{max_data_age_days}")
    return ",".join(parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check public Bitcoin Risk Brief health, readiness, latest-risk, freshness, "
            "and optional cache-header assertions."
        ),
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Public or local base URL to probe, for example https://bitcoinriskbrief.minihub.app.",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=10.0,
        help="Per-request timeout in seconds. Default: 10.",
    )
    parser.add_argument(
        "--max-data-age-days",
        type=positive_int,
        default=None,
        help="Explicit maximum latest-risk data age in UTC days. No default is assumed.",
    )
    parser.add_argument(
        "--expected-latest-date",
        type=parse_expected_date,
        default=None,
        help="Explicit latest-risk date expected from readiness and latest-risk payloads, in YYYY-MM-DD.",
    )
    parser.add_argument(
        "--require-cache-header",
        action="append",
        choices=SUPPORTED_CACHE_HEADERS,
        default=[],
        help=(
            "Require a cache header on /api/readiness and /api/risk/latest. "
            "Repeat for multiple headers. Choices: %(choices)s."
        ),
    )
    return parser


def run_check(args: argparse.Namespace, *, opener: Callable[..., Any] | None, now_utc: datetime | None) -> str:
    if args.max_data_age_days is None and args.expected_latest_date is None:
        raise ProbeConfigError("provide --max-data-age-days or --expected-latest-date")

    base_url = normalize_base_url(args.base_url)
    now = normalize_now(now_utc)
    required_cache_headers = tuple(dict.fromkeys(args.require_cache_header))

    results: dict[str, EndpointResult] = {}
    for path in PUBLIC_ENDPOINTS:
        results[path] = fetch_json(base_url, path, opener=opener, timeout=args.timeout)

    validate_health(results["/api/health"].payload)
    readiness = validate_readiness(results["/api/readiness"].payload)
    latest = validate_latest_risk(results["/api/risk/latest"].payload)
    validate_freshness_policy(
        readiness,
        latest,
        expected_latest_date=args.expected_latest_date,
        max_data_age_days=args.max_data_age_days,
        now_utc=now,
    )
    validate_cache_headers(results, required_cache_headers)

    return (
        "OK public endpoints healthy "
        f"latest_date={latest.latest_date.isoformat()} "
        f"risk={latest.risk:.4f} "
        f"freshness={format_freshness_summary(args.expected_latest_date, args.max_data_age_days)} "
        f"cache_headers={format_cache_header_summary(required_cache_headers)}"
    )


def main(
    argv: list[str] | None = None,
    *,
    opener: Callable[..., Any] | None = None,
    now_utc: datetime | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(run_check(args, opener=opener, now_utc=now_utc))
    except ProbeError as exc:
        print(f"{exc.status}: {exc}", file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
