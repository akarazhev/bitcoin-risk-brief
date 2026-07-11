#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, NamedTuple


ALLOWED_SOURCE_TYPES = {
    "automatic_public_cmc",
    "manual_cmc_csv",
    "optional_cmc_api",
    "restore",
    "correction",
}
DATE_COLUMN_ALIASES = {"date", "timeopen", "timeclose", "timestamp"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
UNSAFE_KEY_PATTERN = re.compile(
    r"(secret|token|password|api[_-]?key|\.env|waitlist|contact|email|phone|dashboard|"
    r"raw[_-]?(rows?|logs?)|log[_-]?contents|account)",
    re.IGNORECASE,
)
UNSAFE_VALUE_PATTERN = re.compile(
    r"(secret|token|password|api[\s_-]?key|bearer|private[\s_-]?key|\.env|"
    r"waitlist\s+contact|raw\s+(?:source\s+)?rows?|raw\s+logs?|"
    r"log\s+(?:tail|dump|contents)|account\s+(?:id|details|export)|"
    r"phone\s+number|email\s+address)",
    re.IGNORECASE,
)
RAW_CSV_ROW_PATTERN = re.compile(
    r"^\s*(?:"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}"
    r"|\d{4}-\d{2}-\d{2}(?:T[^,;\s]+)?"
    r"|\d{1,2}/\d{1,2}/\d{4}"
    r")\s*[,;](?:[^,;\n]*[,;]){3,}[^,;\n]*\s*$",
    re.IGNORECASE,
)
ABSOLUTE_PATH_PATTERN = re.compile(r"(^|[\s\"'=:(])/(?!/)[^\s\"']*")
WINDOWS_PATH_PATTERN = re.compile(r"(^|[\s\"'=:(])[A-Za-z]:\\")
HOME_PATH_PATTERN = re.compile(r"(^|[\s\"'=:(])~(?:/|$)")
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
ENV_ASSIGNMENT_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*[^\s,]+")
PHONE_NUMBER_PATTERN = re.compile(r"(?<![\w-])\+?\d(?:[\s().-]*\d){9,}(?![\w-])")


class ProvenancePacketError(Exception):
    exit_code = 1
    status = "ERROR"


class ProvenancePacketConfigError(ProvenancePacketError):
    exit_code = 2
    status = "CONFIG"


class CsvObservation(NamedTuple):
    row_count: int
    start_date: date
    end_date: date


def normalize_column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lstrip("\ufeff").strip().lower())


def parse_date_value(value: str) -> date:
    text = value.strip()
    if not text:
        raise ValueError("empty date")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for date_format in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise ValueError(f"unsupported date value {value!r}")


def parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ProvenancePacketConfigError(f"{field_name} must be YYYY-MM-DD") from exc


def format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProvenancePacketConfigError(f"{field_name} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None:
        raise ProvenancePacketConfigError(f"{field_name} must include UTC timezone information")
    normalized = parsed.astimezone(timezone.utc)
    if normalized.utcoffset() is None:
        raise ProvenancePacketConfigError(f"{field_name} must include UTC timezone information")
    return normalized


def normalize_optional_timestamp(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return format_utc_timestamp(parse_utc_timestamp(value, field_name))


def normalize_evidence_created_at(value: str | None) -> str:
    if value is None:
        return format_utc_timestamp(datetime.now(timezone.utc))
    return format_utc_timestamp(parse_utc_timestamp(value, "evidence_created_at_utc"))


def detect_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;")
    except csv.Error:
        class FallbackDialect(csv.excel):
            delimiter = "," if sample.splitlines()[0].count(",") >= sample.splitlines()[0].count(";") else ";"

        return FallbackDialect


def resolve_date_column(headers: list[str], path: Path) -> int:
    for index, header in enumerate(headers):
        if normalize_column_name(header) in DATE_COLUMN_ALIASES:
            return index
    raise ProvenancePacketError(f"malformed CSV {path.name}: missing date/time column")


def repair_unquoted_cmc_date(headers: list[str], values: list[str], date_column: int) -> list[str]:
    if len(values) == len(headers) + 1 and date_column == 0:
        candidate = f"{values[0].strip()}, {values[1].strip()}"
        try:
            parse_date_value(candidate)
        except ValueError:
            return values
        return [candidate, *values[2:]]
    return values


def observe_csv_dates(csv_path: Path) -> CsvObservation:
    if not csv_path.is_file():
        raise ProvenancePacketError(f"missing source file: {csv_path.name}")
    sample = csv_path.read_text(encoding="utf-8-sig")
    if not sample.strip():
        raise ProvenancePacketError(f"malformed CSV {csv_path.name}: file is empty")
    dialect = detect_dialect(sample)

    parsed_dates: list[date] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, dialect=dialect)
        try:
            headers = [header.strip() for header in next(reader)]
        except StopIteration as exc:
            raise ProvenancePacketError(f"malformed CSV {csv_path.name}: file is empty") from exc
        date_column = resolve_date_column(headers, csv_path)
        for row_number, values in enumerate(reader, start=2):
            if not values or not any(value.strip() for value in values):
                continue
            repaired_values = repair_unquoted_cmc_date(headers, values, date_column)
            if date_column >= len(repaired_values):
                raise ProvenancePacketError(f"malformed CSV {csv_path.name}: missing date on row {row_number}")
            try:
                parsed_dates.append(parse_date_value(repaired_values[date_column]))
            except ValueError as exc:
                raise ProvenancePacketError(
                    f"malformed CSV {csv_path.name}: invalid date on row {row_number}"
                ) from exc

    if not parsed_dates:
        raise ProvenancePacketError(f"malformed CSV {csv_path.name}: no data rows")
    return CsvObservation(
        row_count=len(parsed_dates),
        start_date=min(parsed_dates),
        end_date=max(parsed_dates),
    )


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise ProvenancePacketError(f"missing source file: {path.name}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_sha256(value: str, field_name: str) -> str:
    normalized = value.strip().lower()
    if not SHA256_PATTERN.match(normalized):
        raise ProvenancePacketConfigError(f"{field_name} must be a 64-character SHA-256 hex digest")
    return normalized


def validate_basename(value: str, field_name: str) -> None:
    if not value or value in {".", ".."}:
        raise ProvenancePacketError(f"{field_name} must be a basename")
    if Path(value).name != value or "/" in value or "\\" in value:
        raise ProvenancePacketError(f"{field_name} must be a basename, not a path")


def require_source_type(value: str) -> str:
    if value not in ALLOWED_SOURCE_TYPES:
        raise ProvenancePacketConfigError(f"unsupported source_type: {value}")
    return value


def safety_error_for_string(value: str) -> str | None:
    if URL_PATTERN.search(value):
        return "URL"
    if ABSOLUTE_PATH_PATTERN.search(value) or WINDOWS_PATH_PATTERN.search(value) or HOME_PATH_PATTERN.search(value):
        return "absolute or private path"
    if EMAIL_PATTERN.search(value):
        return "email address"
    if RAW_CSV_ROW_PATTERN.search(value):
        return "raw CSV row"
    if PHONE_NUMBER_PATTERN.search(value):
        return "phone number"
    if ENV_ASSIGNMENT_PATTERN.search(value):
        return "environment assignment"
    if UNSAFE_VALUE_PATTERN.search(value):
        return "sensitive evidence text"
    if ".env" in value:
        return ".env reference"
    return None


def validate_safety(value: Any, path: str = "manifest") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ProvenancePacketError(f"unsafe manifest field at {path}: non-string key")
            if UNSAFE_KEY_PATTERN.search(key):
                raise ProvenancePacketError(f"unsafe manifest field at {path}.{key}")
            validate_safety(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_safety(item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        reason = safety_error_for_string(value)
        if reason is not None:
            raise ProvenancePacketError(f"unsafe manifest value at {path}: contains {reason}")


def compare_expected_dates(
    observation: CsvObservation,
    expected_start_date: str | None,
    expected_end_date: str | None,
) -> None:
    if expected_start_date is not None:
        expected_start = parse_iso_date(expected_start_date, "expected_start_date")
        if observation.start_date != expected_start:
            raise ProvenancePacketError(
                "expected_start_date mismatch: "
                f"expected {expected_start.isoformat()}, observed {observation.start_date.isoformat()}"
            )
    if expected_end_date is not None:
        expected_end = parse_iso_date(expected_end_date, "expected_end_date")
        if observation.end_date != expected_end:
            raise ProvenancePacketError(
                "expected_end_date mismatch: "
                f"expected {expected_end.isoformat()}, observed {observation.end_date.isoformat()}"
            )


def evidence_file_basenames(args: argparse.Namespace) -> dict[str, str]:
    evidence_files: dict[str, str] = {}
    for field_name, label in (
        ("readiness_evidence", "readiness"),
        ("validation_evidence", "validation"),
        ("cache_evidence", "cache"),
    ):
        value = getattr(args, field_name)
        if value is None:
            continue
        path = Path(value)
        if not path.is_file():
            raise ProvenancePacketError(f"missing {label} evidence file: {path.name}")
        evidence_files[label] = path.name
    return evidence_files


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    source_type = require_source_type(args.source_type)
    source_path = Path(args.source_csv)
    source_observation = observe_csv_dates(source_path)
    source_sha256 = sha256_file(source_path)
    if args.expected_source_sha256 is not None:
        expected_sha256 = validate_sha256(args.expected_source_sha256, "expected_source_sha256")
        if source_sha256 != expected_sha256:
            raise ProvenancePacketError("checksum mismatch: source_sha256 does not match expected_source_sha256")
    compare_expected_dates(source_observation, args.expected_start_date, args.expected_end_date)

    manifest: dict[str, Any] = {
        "manifest_schema_version": 1,
        "generated_by": "scripts/import_provenance_packet.py",
        "evidence_created_at_utc": normalize_evidence_created_at(args.evidence_created_at_utc),
        "source_type": source_type,
        "source_basename": source_path.name,
        "source_sha256": source_sha256,
        "source_byte_size": source_path.stat().st_size,
        "observed_row_count": source_observation.row_count,
        "observed_start_date": source_observation.start_date.isoformat(),
        "observed_end_date": source_observation.end_date.isoformat(),
    }

    for arg_name, manifest_name in (
        ("retrieval_started_at_utc", "retrieval_started_at_utc"),
        ("retrieval_completed_at_utc", "retrieval_completed_at_utc"),
    ):
        normalized = normalize_optional_timestamp(getattr(args, arg_name), manifest_name)
        if normalized is not None:
            manifest[manifest_name] = normalized

    if args.expected_start_date is not None:
        manifest["expected_start_date"] = parse_iso_date(args.expected_start_date, "expected_start_date").isoformat()
    if args.expected_end_date is not None:
        manifest["expected_end_date"] = parse_iso_date(args.expected_end_date, "expected_end_date").isoformat()

    if args.canonical_csv is not None:
        canonical_path = Path(args.canonical_csv)
        canonical_observation = observe_csv_dates(canonical_path)
        manifest["canonical_csv_basename"] = canonical_path.name
        manifest["canonical_csv_sha256"] = sha256_file(canonical_path)
        manifest["canonical_csv_tail_date"] = canonical_observation.end_date.isoformat()

    evidence_files = evidence_file_basenames(args)
    if evidence_files:
        manifest["evidence_file_basenames"] = evidence_files

    if args.production_commit is not None:
        production_commit = args.production_commit.strip().lower()
        if not COMMIT_PATTERN.match(production_commit):
            raise ProvenancePacketConfigError("production_commit must be a git commit hex prefix or full hash")
        manifest["production_commit"] = production_commit
    if args.note:
        manifest["notes"] = [note.strip() for note in args.note if note.strip()]
    if args.limitation:
        manifest["limitations"] = [limitation.strip() for limitation in args.limitation if limitation.strip()]

    validate_manifest_data(manifest)
    return manifest


def require_field(manifest: dict[str, Any], field_name: str, expected_type: type) -> Any:
    if field_name not in manifest:
        raise ProvenancePacketError(f"manifest missing required field: {field_name}")
    value = manifest[field_name]
    if not isinstance(value, expected_type):
        raise ProvenancePacketError(f"manifest field {field_name} has wrong type")
    return value


def validate_manifest_dates(manifest: dict[str, Any]) -> None:
    observed_start = parse_iso_date(require_field(manifest, "observed_start_date", str), "observed_start_date")
    observed_end = parse_iso_date(require_field(manifest, "observed_end_date", str), "observed_end_date")
    if observed_start > observed_end:
        raise ProvenancePacketError("observed_start_date must not be after observed_end_date")
    canonical_tail = None
    if "canonical_csv_tail_date" in manifest:
        canonical_tail = parse_iso_date(
            require_field(manifest, "canonical_csv_tail_date", str),
            "canonical_csv_tail_date",
        )
    if "expected_start_date" in manifest:
        expected_start = parse_iso_date(require_field(manifest, "expected_start_date", str), "expected_start_date")
        if expected_start != observed_start:
            raise ProvenancePacketError("expected_start_date mismatch in manifest")
    if "expected_end_date" in manifest:
        expected_end = parse_iso_date(require_field(manifest, "expected_end_date", str), "expected_end_date")
        if expected_end != observed_end:
            raise ProvenancePacketError("expected_end_date mismatch in manifest")
        if canonical_tail is not None and canonical_tail != expected_end:
            raise ProvenancePacketError("canonical_csv_tail_date mismatch in manifest")


def validate_manifest_timestamps(manifest: dict[str, Any]) -> None:
    parse_utc_timestamp(require_field(manifest, "evidence_created_at_utc", str), "evidence_created_at_utc")
    started = None
    completed = None
    if "retrieval_started_at_utc" in manifest:
        started = parse_utc_timestamp(
            require_field(manifest, "retrieval_started_at_utc", str),
            "retrieval_started_at_utc",
        )
    if "retrieval_completed_at_utc" in manifest:
        completed = parse_utc_timestamp(
            require_field(manifest, "retrieval_completed_at_utc", str),
            "retrieval_completed_at_utc",
        )
    if started is not None and completed is not None and started > completed:
        raise ProvenancePacketError("retrieval_started_at_utc must not be after retrieval_completed_at_utc")


def validate_manifest_data(
    manifest: dict[str, Any],
    *,
    source_csv: Path | None = None,
    expected_source_sha256: str | None = None,
) -> None:
    validate_safety(manifest)
    require_source_type(require_field(manifest, "source_type", str))
    validate_basename(require_field(manifest, "source_basename", str), "source_basename")
    validate_sha256(require_field(manifest, "source_sha256", str), "source_sha256")
    row_count = require_field(manifest, "observed_row_count", int)
    if row_count <= 0:
        raise ProvenancePacketError("observed_row_count must be positive")
    validate_manifest_dates(manifest)
    validate_manifest_timestamps(manifest)

    if "canonical_csv_basename" in manifest:
        validate_basename(require_field(manifest, "canonical_csv_basename", str), "canonical_csv_basename")
    if "canonical_csv_sha256" in manifest:
        validate_sha256(require_field(manifest, "canonical_csv_sha256", str), "canonical_csv_sha256")
    if "production_commit" in manifest:
        production_commit = require_field(manifest, "production_commit", str).strip().lower()
        if not COMMIT_PATTERN.match(production_commit):
            raise ProvenancePacketError("production_commit must be a git commit hex prefix or full hash")
    if "evidence_file_basenames" in manifest:
        evidence_files = require_field(manifest, "evidence_file_basenames", dict)
        for label, basename in evidence_files.items():
            if not isinstance(label, str) or not isinstance(basename, str):
                raise ProvenancePacketError("evidence_file_basenames must map strings to strings")
            validate_basename(basename, f"evidence_file_basenames.{label}")
    for field_name in ("notes", "limitations"):
        if field_name in manifest:
            values = require_field(manifest, field_name, list)
            if not all(isinstance(value, str) for value in values):
                raise ProvenancePacketError(f"{field_name} must contain only strings")

    if expected_source_sha256 is not None:
        expected_sha256 = validate_sha256(expected_source_sha256, "expected_source_sha256")
        if manifest["source_sha256"].lower() != expected_sha256:
            raise ProvenancePacketError("checksum mismatch: manifest source_sha256 does not match expected")

    if source_csv is not None:
        source_observation = observe_csv_dates(source_csv)
        actual_sha256 = sha256_file(source_csv)
        if source_csv.name != manifest["source_basename"]:
            raise ProvenancePacketError("source_basename mismatch between manifest and source file")
        if actual_sha256 != manifest["source_sha256"].lower():
            raise ProvenancePacketError("checksum mismatch: source file does not match manifest source_sha256")
        if source_observation.row_count != manifest["observed_row_count"]:
            raise ProvenancePacketError("observed_row_count mismatch between manifest and source file")
        if source_observation.start_date.isoformat() != manifest["observed_start_date"]:
            raise ProvenancePacketError("observed_start_date mismatch between manifest and source file")
        if source_observation.end_date.isoformat() != manifest["observed_end_date"]:
            raise ProvenancePacketError("observed_end_date mismatch between manifest and source file")


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ProvenancePacketError(f"missing manifest file: {path.name}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProvenancePacketError(f"manifest {path.name} is not valid JSON") from exc
    if not isinstance(manifest, dict):
        raise ProvenancePacketError("manifest root must be a JSON object")
    return manifest


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_create(args: argparse.Namespace) -> str:
    manifest = build_manifest(args)
    if args.output is None:
        return json.dumps(manifest, indent=2, sort_keys=True)
    output_path = Path(args.output)
    write_manifest(output_path, manifest)
    return f"OK wrote sanitized import provenance manifest {output_path.name}"


def run_validate(args: argparse.Namespace) -> str:
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    source_csv = Path(args.source_csv) if args.source_csv is not None else None
    validate_manifest_data(
        manifest,
        source_csv=source_csv,
        expected_source_sha256=args.expected_source_sha256,
    )
    return f"OK import provenance manifest {manifest_path.name} is valid"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create or validate a sanitized local import provenance evidence manifest. "
            "The helper reads local files only and never contacts the network."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Build a sanitized manifest from local files and metadata.")
    create.add_argument("--source-type", required=True, help="Import source type.")
    create.add_argument("--source-csv", required=True, help="Local source CSV to hash and observe.")
    create.add_argument("--canonical-csv", help="Optional canonical CSV to hash and inspect for its tail date.")
    create.add_argument("--output", help="Optional manifest output path. Without it, JSON is printed to stdout.")
    create.add_argument("--evidence-created-at-utc", help="UTC evidence creation timestamp. Defaults to current UTC.")
    create.add_argument("--retrieval-started-at-utc", help="Optional UTC source retrieval start timestamp.")
    create.add_argument("--retrieval-completed-at-utc", help="Optional UTC source retrieval completion timestamp.")
    create.add_argument("--expected-start-date", help="Optional expected source coverage start date, YYYY-MM-DD.")
    create.add_argument("--expected-end-date", help="Optional expected source coverage end date, YYYY-MM-DD.")
    create.add_argument("--expected-source-sha256", help="Optional expected source SHA-256 digest.")
    create.add_argument("--readiness-evidence", help="Optional readiness evidence file; only basename is stored.")
    create.add_argument("--validation-evidence", help="Optional validation/import evidence file; only basename is stored.")
    create.add_argument("--cache-evidence", help="Optional cache/header evidence file; only basename is stored.")
    create.add_argument("--production-commit", help="Optional production git commit hash or prefix.")
    create.add_argument("--note", action="append", default=[], help="Sanitized note to include. May be repeated.")
    create.add_argument("--limitation", action="append", default=[], help="Sanitized limitation to include. May be repeated.")
    create.set_defaults(func=run_create)

    validate = subparsers.add_parser("validate", help="Validate an existing sanitized manifest.")
    validate.add_argument("--manifest", required=True, help="Manifest JSON path.")
    validate.add_argument("--source-csv", help="Optional source CSV to compare against the manifest hash and range.")
    validate.add_argument("--expected-source-sha256", help="Optional expected source SHA-256 digest.")
    validate.set_defaults(func=run_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(args.func(args))
    except ProvenancePacketError as exc:
        print(f"{exc.status}: {exc}", file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
