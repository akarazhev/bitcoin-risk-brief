#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse


COMMIT_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
RISK_STATES = {"low", "neutral", "high"}
STATUS_VALUES = {"present", "pending", "accepted_limitation", "blocked"}
FIRST_TRAFFIC_STATUS_VALUES = {"not_run", "passed"}
REQUIRED_EVIDENCE_CATEGORIES = (
    "readiness",
    "latest_risk",
    "public_endpoint_monitor_probe",
    "waitlist_smoke",
    "import_provenance",
    "backup_freshness",
    "accessibility",
    "browser",
    "metadata",
)
DEFAULT_OPERATOR_DECISIONS = {
    "waitlist_owner": "pending",
    "waitlist_review_cadence": "pending",
    "waitlist_retention": "pending",
    "deletion_unsubscribe_path": "pending",
    "support_contact_identity": "pending",
    "credential_account_ownership": "pending",
    "data_source_terms_review": "pending",
}
UNSAFE_KEY_PATTERN = re.compile(
    r"(secret|token|password|api[_-]?key|\.env|email|phone|contact|dashboard|raw[_-]?(logs?|dumps?)|"
    r"account|private[_-]?path)",
    re.IGNORECASE,
)
UNSAFE_VALUE_PATTERN = re.compile(
    r"(secret|token|password|api[\s_-]?key|bearer|private[\s_-]?key|\.env|"
    r"raw\s+(?:log|logs|dump|dumps|response|responses)|"
    r"log\s+(?:tail|dump|contents)|dashboard\s+url|account\s+(?:id|details|export)|"
    r"(?:raw|private)\s+contacts?|waitlist\s+contact|email\s+address|phone\s+number)",
    re.IGNORECASE,
)
ABSOLUTE_PATH_PATTERN = re.compile(r"(^|[\s\"'=:(])/(?!/)[^\s\"']*")
WINDOWS_PATH_PATTERN = re.compile(r"(^|[\s\"'=:(])[A-Za-z]:\\")
HOME_PATH_PATTERN = re.compile(r"(^|[\s\"'=:(])~(?:/|$)")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_NUMBER_PATTERN = re.compile(r"(?<![\w-])\+?\d(?:[\s().-]*\d){9,}(?![\w-])")
ENV_ASSIGNMENT_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*[^\s,]+")
PRIVATE_HOST_PATTERN = re.compile(
    r"(^|\.)("
    r"localhost|local|internal|intranet|lan|home|test|invalid|example"
    r")$",
    re.IGNORECASE,
)
URL_TEXT_PATTERN = re.compile(r"https?://[^\s\"')]+", re.IGNORECASE)
FIRST_TRAFFIC_PASSED_PATTERN = re.compile(
    r"first[-_\s]+traffic\s+(?:passed|complete|completed|ran|run|succeeded|done)",
    re.IGNORECASE,
)


class LaunchSnapshotPacketError(Exception):
    exit_code = 1
    status = "ERROR"


class LaunchSnapshotPacketConfigError(LaunchSnapshotPacketError):
    exit_code = 2
    status = "CONFIG"


def format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LaunchSnapshotPacketConfigError(f"{field_name} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None:
        raise LaunchSnapshotPacketConfigError(f"{field_name} must include UTC timezone information")
    return parsed.astimezone(timezone.utc)


def normalize_packet_created_at(value: str | None) -> str:
    if value is None:
        return format_utc_timestamp(datetime.now(timezone.utc))
    return format_utc_timestamp(parse_utc_timestamp(value, "packet_created_at_utc"))


def parse_iso_date(value: str, field_name: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise LaunchSnapshotPacketConfigError(f"{field_name} must be YYYY-MM-DD") from exc


def normalize_optional_timestamp(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return format_utc_timestamp(parse_utc_timestamp(value, field_name))


def parse_bool(value: str, field_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise LaunchSnapshotPacketConfigError(f"{field_name} must be true or false")


def validate_status(value: str, field_name: str) -> str:
    if value not in STATUS_VALUES:
        allowed = ", ".join(sorted(STATUS_VALUES))
        raise LaunchSnapshotPacketConfigError(f"{field_name} must be one of: {allowed}")
    return value


def validate_basename(value: str, field_name: str) -> None:
    if not value or value in {".", ".."}:
        raise LaunchSnapshotPacketError(f"{field_name} must be a basename")
    if Path(value).name != value or "/" in value or "\\" in value:
        raise LaunchSnapshotPacketError(f"{field_name} must be a basename, not a path")


def evidence_basename(path_value: str | None, field_name: str) -> str | None:
    if path_value is None:
        return None
    path = Path(path_value)
    if not path.is_file():
        raise LaunchSnapshotPacketError(f"missing {field_name} evidence file: {path.name}")
    validate_basename(path.name, field_name)
    return path.name


def normalize_commit(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if not COMMIT_PATTERN.match(normalized):
        raise LaunchSnapshotPacketConfigError("production_commit must be a git commit hex prefix or full hash")
    return normalized


def normalize_base_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
        raise LaunchSnapshotPacketConfigError("base_url must be an https origin URL without a path")
    if parsed.username or parsed.password or parsed.params or parsed.query or parsed.fragment:
        raise LaunchSnapshotPacketConfigError("base_url must not include credentials, query, or fragment")
    hostname = parsed.hostname or ""
    if is_private_hostname(hostname) or is_dashboard_hostname(hostname):
        raise LaunchSnapshotPacketConfigError("base_url must not use a private, placeholder, or dashboard hostname")
    normalized = f"https://{parsed.netloc.rstrip('/')}"
    return normalized


def is_private_hostname(hostname: str) -> bool:
    lowered = hostname.lower().strip(".")
    if not lowered:
        return True
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        pass
    else:
        return (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_unspecified
        )
    return bool(PRIVATE_HOST_PATTERN.search(lowered))


def is_dashboard_hostname(hostname: str) -> bool:
    lowered = hostname.lower().strip(".")
    first_label = lowered.split(".", 1)[0]
    return "dashboard" in lowered or first_label == "dash"


def public_hostname_from_base_url(value: str | None) -> str | None:
    if value is None:
        return None
    return urlparse(value).hostname


def url_safety_error(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return None
    hostname = parsed.hostname or ""
    if is_private_hostname(hostname) or is_dashboard_hostname(hostname):
        return "private or dashboard URL"
    return "URL"


def safety_error_for_string(value: str) -> str | None:
    for match in URL_TEXT_PATTERN.finditer(value):
        reason = url_safety_error(match.group(0))
        if reason is not None:
            return reason
    reason = url_safety_error(value)
    if reason is not None:
        return reason
    if ABSOLUTE_PATH_PATTERN.search(value) or WINDOWS_PATH_PATTERN.search(value) or HOME_PATH_PATTERN.search(value):
        return "absolute or private path"
    if EMAIL_PATTERN.search(value):
        return "email address"
    if PHONE_NUMBER_PATTERN.search(value):
        return "phone number"
    if ENV_ASSIGNMENT_PATTERN.search(value):
        return "environment assignment"
    if UNSAFE_VALUE_PATTERN.search(value):
        return "sensitive evidence text"
    if ".env" in value:
        return ".env reference"
    return None


def is_allowed_schema_key(path: str, key: str) -> bool:
    if path == "packet.operator_decisions" and key in DEFAULT_OPERATOR_DECISIONS:
        return True
    return False


def validate_safety(value: Any, path: str = "packet") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise LaunchSnapshotPacketError(f"unsafe packet field at {path}: non-string key")
            if UNSAFE_KEY_PATTERN.search(key) and not is_allowed_schema_key(path, key):
                raise LaunchSnapshotPacketError(f"unsafe packet field at {path}.{key}")
            validate_safety(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_safety(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        if path == "packet.base_url":
            return
        reason = safety_error_for_string(value)
        if reason is not None:
            raise LaunchSnapshotPacketError(f"unsafe packet value at {path}: contains {reason}")


def assert_no_implicit_first_traffic_pass_claim(value: Any, first_traffic_status: str, path: str = "packet") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert_no_implicit_first_traffic_pass_claim(item, first_traffic_status, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_implicit_first_traffic_pass_claim(item, first_traffic_status, f"{path}[{index}]")
        return
    if isinstance(value, str) and FIRST_TRAFFIC_PASSED_PATTERN.search(value) and first_traffic_status != "passed":
        raise LaunchSnapshotPacketError(
            f"unsafe first traffic claim at {path}: first_traffic_status must be explicitly passed with evidence"
        )


def make_evidence_entry(status: str, basename: str | None = None, **fields: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {"status": validate_status(status, "status")}
    if basename is not None:
        entry["basename"] = basename
    for key, value in fields.items():
        if value is not None:
            entry[key] = value
    return entry


def build_evidence(args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    readiness_status = validate_status(args.readiness_status, "readiness_status")
    readiness_data_fresh = None
    if args.readiness_data_fresh is not None:
        readiness_data_fresh = parse_bool(args.readiness_data_fresh, "readiness_data_fresh")

    latest_risk_timestamp = normalize_optional_timestamp(args.latest_risk_timestamp, "latest_risk_timestamp")
    latest_risk_state = args.latest_risk_state
    if latest_risk_state is not None and latest_risk_state not in RISK_STATES:
        allowed = ", ".join(sorted(RISK_STATES))
        raise LaunchSnapshotPacketConfigError(f"latest_risk_state must be one of: {allowed}")

    return {
        "readiness": make_evidence_entry(
            readiness_status,
            evidence_basename(args.readiness_evidence, "readiness"),
            latest_date=parse_iso_date(args.readiness_latest_date, "readiness_latest_date")
            if args.readiness_latest_date
            else None,
            data_fresh=readiness_data_fresh,
        ),
        "latest_risk": make_evidence_entry(
            validate_status(args.latest_risk_status, "latest_risk_status"),
            evidence_basename(args.latest_risk_evidence, "latest_risk"),
            timestamp=latest_risk_timestamp,
            risk_state=latest_risk_state,
        ),
        "public_endpoint_monitor_probe": make_evidence_entry(
            validate_status(args.public_endpoint_monitor_probe_status, "public_endpoint_monitor_probe_status"),
            evidence_basename(args.public_endpoint_monitor_probe_evidence, "public_endpoint_monitor_probe"),
            summary=args.public_endpoint_monitor_probe_summary,
        ),
        "waitlist_smoke": make_evidence_entry(
            validate_status(args.waitlist_smoke_status, "waitlist_smoke_status"),
            None,
            summary=args.waitlist_smoke_summary,
        ),
        "import_provenance": make_evidence_entry(
            validate_status(args.import_provenance_status, "import_provenance_status"),
            evidence_basename(args.import_provenance_packet, "import_provenance"),
        ),
        "backup_freshness": make_evidence_entry(
            validate_status(args.backup_freshness_status, "backup_freshness_status"),
            evidence_basename(args.backup_freshness_evidence, "backup_freshness"),
        ),
        "accessibility": make_evidence_entry(validate_status(args.accessibility_status, "accessibility_status")),
        "browser": make_evidence_entry(validate_status(args.browser_status, "browser_status")),
        "metadata": make_evidence_entry(validate_status(args.metadata_status, "metadata_status")),
    }


def normalize_operator_decisions(values: list[str]) -> dict[str, str]:
    decisions = dict(DEFAULT_OPERATOR_DECISIONS)
    for value in values:
        if "=" not in value:
            raise LaunchSnapshotPacketConfigError("operator decisions must use name=status")
        name, status = value.split("=", 1)
        key = name.strip()
        if key not in DEFAULT_OPERATOR_DECISIONS:
            allowed = ", ".join(sorted(DEFAULT_OPERATOR_DECISIONS))
            raise LaunchSnapshotPacketConfigError(f"unsupported operator decision {key}; allowed: {allowed}")
        decisions[key] = validate_status(status.strip(), f"operator_decisions.{key}")
    return decisions


def normalize_first_traffic_status(args: argparse.Namespace) -> str:
    status = args.first_traffic_status
    if status not in FIRST_TRAFFIC_STATUS_VALUES:
        allowed = ", ".join(sorted(FIRST_TRAFFIC_STATUS_VALUES))
        raise LaunchSnapshotPacketConfigError(f"first_traffic_status must be one of: {allowed}")
    if status == "passed" and args.first_traffic_evidence is None:
        raise LaunchSnapshotPacketConfigError("first_traffic_status=passed requires --first-traffic-evidence")
    return status


def missing_present_fields(category: str, item: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if category == "readiness":
        if not item.get("basename"):
            missing.append("basename")
        if not item.get("latest_date"):
            missing.append("latest_date")
        if item.get("data_fresh") is not True:
            missing.append("data_fresh=true")
    elif category == "latest_risk":
        if not item.get("basename"):
            missing.append("basename")
        if not item.get("timestamp"):
            missing.append("timestamp")
        if not item.get("risk_state"):
            missing.append("risk_state")
    elif category == "public_endpoint_monitor_probe":
        if not item.get("basename") and not item.get("summary"):
            missing.append("basename_or_summary")
    elif category == "waitlist_smoke":
        if not item.get("summary"):
            missing.append("summary")
    elif category in {"import_provenance", "backup_freshness"} and not item.get("basename"):
        missing.append("basename")
    return missing


def gate_messages(packet: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    evidence = packet.get("evidence")
    if not isinstance(evidence, dict):
        return ["evidence is missing; all launch evidence categories are pending"]

    for category in REQUIRED_EVIDENCE_CATEGORIES:
        item = evidence.get(category)
        if not isinstance(item, dict):
            messages.append(f"{category} is pending: category missing from packet")
            continue
        status = item.get("status")
        if status == "pending":
            messages.append(f"{category} is pending")
        elif status == "blocked":
            messages.append(f"{category} is blocked")
        elif status == "accepted_limitation":
            messages.append(f"{category} is accepted as a limitation")
        elif status == "present":
            missing = missing_present_fields(category, item)
            if missing:
                messages.append(f"{category} missing required present fields: {', '.join(missing)}")

    operator_decisions = packet.get("operator_decisions")
    if not isinstance(operator_decisions, dict):
        messages.append("operator_decisions are pending: category missing from packet")
    else:
        pending_decisions = [
            key
            for key, value in sorted(operator_decisions.items())
            if value in {"pending", "blocked", "accepted_limitation"}
        ]
        if pending_decisions:
            messages.append("operator_decisions pending_or_limited: " + ", ".join(pending_decisions))

    first_traffic_status = packet.get("first_traffic_status")
    if first_traffic_status != "not_run":
        messages.append("first_traffic_status is not not_run; verify explicit first-traffic evidence separately")
    else:
        messages.append("first_traffic_status is not_run")

    if packet.get("accepted_limitations"):
        messages.append("accepted_limitations recorded; launch remains pending for operator review")

    return messages


def readiness_status_from_gates(messages: list[str], packet: dict[str, Any]) -> str:
    if not messages:
        return "ready_for_operator_review"
    if messages == ["first_traffic_status is not_run"]:
        return "ready_for_operator_review"
    return "pending"


def refresh_gate_fields(packet: dict[str, Any]) -> dict[str, Any]:
    messages = gate_messages(packet)
    packet["blocked_or_pending_gates"] = messages
    packet["launch_readiness_status"] = readiness_status_from_gates(messages, packet)
    return packet


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    first_traffic_status = normalize_first_traffic_status(args)
    base_url = normalize_base_url(args.base_url)
    packet: dict[str, Any] = {
        "packet_schema_version": 1,
        "generated_by": "scripts/launch_snapshot_packet.py",
        "packet_created_at_utc": normalize_packet_created_at(args.packet_created_at_utc),
        "first_traffic_status": first_traffic_status,
        "operator_decisions": normalize_operator_decisions(args.operator_decision),
        "accepted_limitations": [value.strip() for value in args.accepted_limitation if value.strip()],
        "evidence": build_evidence(args),
    }
    production_commit = normalize_commit(args.production_commit)
    if production_commit is not None:
        packet["production_commit"] = production_commit
    if base_url is not None:
        packet["base_url"] = base_url
        packet["public_hostname"] = public_hostname_from_base_url(base_url)
    if args.first_traffic_evidence is not None:
        packet["first_traffic_evidence_basename"] = evidence_basename(args.first_traffic_evidence, "first_traffic")

    validate_packet_data(packet)
    return refresh_gate_fields(packet)


def require_field(packet: dict[str, Any], field_name: str, expected_type: type) -> Any:
    if field_name not in packet:
        raise LaunchSnapshotPacketError(f"packet missing required field: {field_name}")
    value = packet[field_name]
    if not isinstance(value, expected_type):
        raise LaunchSnapshotPacketError(f"packet field {field_name} has wrong type")
    return value


def validate_evidence_data(packet: dict[str, Any]) -> None:
    evidence = require_field(packet, "evidence", dict)
    for category, item in evidence.items():
        if not isinstance(category, str):
            raise LaunchSnapshotPacketError("evidence categories must be strings")
        if category not in REQUIRED_EVIDENCE_CATEGORIES:
            raise LaunchSnapshotPacketError(f"unsupported evidence category: {category}")
        if not isinstance(item, dict):
            raise LaunchSnapshotPacketError(f"evidence.{category} must be an object")
        status = require_field(item, "status", str)
        validate_status(status, f"evidence.{category}.status")
        if "basename" in item:
            validate_basename(require_field(item, "basename", str), f"evidence.{category}.basename")

    readiness = evidence.get("readiness")
    if isinstance(readiness, dict):
        if "latest_date" in readiness:
            parse_iso_date(require_field(readiness, "latest_date", str), "evidence.readiness.latest_date")
        if "data_fresh" in readiness and not isinstance(readiness["data_fresh"], bool):
            raise LaunchSnapshotPacketError("evidence.readiness.data_fresh must be a boolean")

    latest_risk = evidence.get("latest_risk")
    if isinstance(latest_risk, dict):
        if "timestamp" in latest_risk:
            parse_utc_timestamp(require_field(latest_risk, "timestamp", str), "evidence.latest_risk.timestamp")
        if "risk_state" in latest_risk and require_field(latest_risk, "risk_state", str) not in RISK_STATES:
            raise LaunchSnapshotPacketError("evidence.latest_risk.risk_state is unsupported")


def validate_operator_decisions(packet: dict[str, Any]) -> None:
    decisions = require_field(packet, "operator_decisions", dict)
    for key, value in decisions.items():
        if not isinstance(key, str) or key not in DEFAULT_OPERATOR_DECISIONS:
            raise LaunchSnapshotPacketError(f"unsupported operator decision: {key}")
        if not isinstance(value, str):
            raise LaunchSnapshotPacketError(f"operator_decisions.{key} must be a status string")
        validate_status(value, f"operator_decisions.{key}")


def validate_packet_data(packet: dict[str, Any]) -> None:
    validate_safety(packet)
    if require_field(packet, "packet_schema_version", int) != 1:
        raise LaunchSnapshotPacketError("packet_schema_version must be 1")
    parse_utc_timestamp(require_field(packet, "packet_created_at_utc", str), "packet_created_at_utc")
    if "production_commit" in packet:
        normalize_commit(require_field(packet, "production_commit", str))
    if "base_url" in packet:
        normalize_base_url(require_field(packet, "base_url", str))
    if "public_hostname" in packet:
        hostname = require_field(packet, "public_hostname", str)
        if is_private_hostname(hostname) or is_dashboard_hostname(hostname):
            raise LaunchSnapshotPacketError("public_hostname must not be private, placeholder, or dashboard")
    validate_evidence_data(packet)
    validate_operator_decisions(packet)
    accepted_limitations = require_field(packet, "accepted_limitations", list)
    if not all(isinstance(value, str) for value in accepted_limitations):
        raise LaunchSnapshotPacketError("accepted_limitations must contain only strings")
    first_traffic_status = require_field(packet, "first_traffic_status", str)
    if first_traffic_status not in FIRST_TRAFFIC_STATUS_VALUES:
        raise LaunchSnapshotPacketError("first_traffic_status is unsupported")
    if first_traffic_status == "passed":
        validate_basename(require_field(packet, "first_traffic_evidence_basename", str), "first_traffic_evidence_basename")
    elif "first_traffic_evidence_basename" in packet:
        raise LaunchSnapshotPacketError("first_traffic_evidence_basename requires first_traffic_status=passed")
    assert_no_implicit_first_traffic_pass_claim(packet, first_traffic_status)


def load_packet(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise LaunchSnapshotPacketError(f"missing packet file: {path.name}")
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LaunchSnapshotPacketError(f"packet {path.name} is not valid JSON") from exc
    if not isinstance(packet, dict):
        raise LaunchSnapshotPacketError("packet root must be a JSON object")
    return packet


def write_packet(path: Path, packet: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def status_line(packet: dict[str, Any]) -> str:
    gates = packet.get("blocked_or_pending_gates", [])
    gate_text = "; ".join(gates[:5]) if isinstance(gates, list) else "gate summary unavailable"
    if isinstance(gates, list) and len(gates) > 5:
        gate_text += f"; +{len(gates) - 5} more"
    prefix = "OK" if packet.get("launch_readiness_status") != "pending" else "PENDING"
    return (
        f"{prefix} launch snapshot packet "
        f"launch_readiness_status={packet.get('launch_readiness_status')} "
        f"first_traffic_status={packet.get('first_traffic_status')} "
        f"gate_summary={gate_text}"
    )


def run_create(args: argparse.Namespace) -> str:
    packet = build_packet(args)
    if args.output is None:
        return json.dumps(packet, indent=2, sort_keys=True)
    output_path = Path(args.output)
    write_packet(output_path, packet)
    return f"{status_line(packet)} wrote {output_path.name}"


def run_validate(args: argparse.Namespace) -> str:
    packet_path = Path(args.packet)
    packet = load_packet(packet_path)
    validate_packet_data(packet)
    refresh_gate_fields(packet)
    return f"{status_line(packet)} validated {packet_path.name}"


def add_common_create_arguments(create: argparse.ArgumentParser) -> None:
    create.add_argument("--output", help="Optional packet output path. Without it, JSON is printed to stdout.")
    create.add_argument("--packet-created-at-utc", help="UTC packet timestamp. Defaults to current UTC.")
    create.add_argument("--production-commit", help="Production commit hash or prefix for the snapshot candidate.")
    create.add_argument("--base-url", help="Public https origin URL, stored with public_hostname.")
    create.add_argument("--accepted-limitation", action="append", default=[], help="Sanitized accepted limitation.")
    create.add_argument(
        "--operator-decision",
        action="append",
        default=[],
        help="Sanitized operator decision status as name=status. Defaults remain pending.",
    )
    create.add_argument(
        "--first-traffic-status",
        default="not_run",
        choices=sorted(FIRST_TRAFFIC_STATUS_VALUES),
        help="Defaults to not_run. passed requires --first-traffic-evidence.",
    )
    create.add_argument("--first-traffic-evidence", help="Explicit first-traffic evidence file when status is passed.")

    create.add_argument("--readiness-evidence", help="Readiness evidence file; only basename is stored.")
    create.add_argument("--readiness-status", default="pending", choices=sorted(STATUS_VALUES))
    create.add_argument("--readiness-latest-date", help="Readiness latest_date, YYYY-MM-DD.")
    create.add_argument("--readiness-data-fresh", help="Readiness data_fresh boolean.")

    create.add_argument("--latest-risk-evidence", help="Latest-risk evidence file; only basename is stored.")
    create.add_argument("--latest-risk-status", default="pending", choices=sorted(STATUS_VALUES))
    create.add_argument("--latest-risk-timestamp", help="Latest risk timestamp in UTC.")
    create.add_argument("--latest-risk-state", choices=sorted(RISK_STATES), help="Latest risk state.")

    create.add_argument(
        "--public-endpoint-monitor-probe-evidence",
        help="Public endpoint probe result file; only basename is stored.",
    )
    create.add_argument("--public-endpoint-monitor-probe-status", default="pending", choices=sorted(STATUS_VALUES))
    create.add_argument("--public-endpoint-monitor-probe-summary", help="Sanitized endpoint probe summary.")

    create.add_argument("--waitlist-smoke-status", default="pending", choices=sorted(STATUS_VALUES))
    create.add_argument("--waitlist-smoke-summary", help="Sanitized waitlist smoke status without contact values.")

    create.add_argument("--import-provenance-packet", help="Import provenance packet file; only basename is stored.")
    create.add_argument("--import-provenance-status", default="pending", choices=sorted(STATUS_VALUES))

    create.add_argument("--backup-freshness-evidence", help="Backup freshness evidence file; only basename is stored.")
    create.add_argument("--backup-freshness-status", default="pending", choices=sorted(STATUS_VALUES))

    create.add_argument("--accessibility-status", default="pending", choices=sorted(STATUS_VALUES))
    create.add_argument("--browser-status", default="pending", choices=sorted(STATUS_VALUES))
    create.add_argument("--metadata-status", default="pending", choices=sorted(STATUS_VALUES))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create or validate a sanitized local launch snapshot packet template. "
            "The helper reads local files only and never contacts the network."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Build a sanitized launch snapshot packet from local evidence.")
    add_common_create_arguments(create)
    create.set_defaults(func=run_create)

    validate = subparsers.add_parser("validate", help="Validate an existing launch snapshot packet.")
    validate.add_argument("--packet", required=True, help="Launch snapshot packet JSON path.")
    validate.set_defaults(func=run_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(args.func(args))
    except LaunchSnapshotPacketError as exc:
        print(f"{exc.status}: {exc}", file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
