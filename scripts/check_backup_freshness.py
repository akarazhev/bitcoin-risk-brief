#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


TIMESTAMP_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")
CHECKSUM_LINE_PATTERN = re.compile(r"^[0-9a-fA-F]{64}\s+[* ]?(.+)$")


class BackupCheckError(Exception):
    exit_code = 1
    status = "CRITICAL"


class BackupConfigError(BackupCheckError):
    exit_code = 2
    status = "CONFIG"


def parse_timestamp(basename: str) -> datetime:
    if not TIMESTAMP_PATTERN.match(basename):
        raise BackupCheckError(f"backup directory basename {basename} is not in YYYYMMDDTHHMMSSZ format")
    try:
        parsed = datetime.strptime(basename, "%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise BackupCheckError(f"backup directory basename {basename} is not a valid UTC timestamp") from exc
    return parsed.replace(tzinfo=timezone.utc)


def parse_max_age_hours(value: str | None) -> tuple[Decimal, timedelta]:
    if value is None or not value.strip():
        raise BackupConfigError(
            "max age hours must be provided with --max-age-hours or BACKUP_FRESHNESS_MAX_AGE_HOURS"
        )
    try:
        hours = Decimal(value)
    except InvalidOperation as exc:
        raise BackupConfigError("max age hours must be a positive number") from exc
    if not hours.is_finite():
        raise BackupConfigError("max age hours must be a finite positive number")
    if hours <= 0:
        raise BackupConfigError("max age hours must be greater than zero")
    return hours, timedelta(seconds=float(hours * Decimal(3600)))


def checksum_command() -> list[str]:
    if shutil.which("sha256sum"):
        return ["sha256sum", "-c", "SHA256SUMS"]
    if shutil.which("shasum"):
        return ["shasum", "-a", "256", "-c", "SHA256SUMS"]
    raise BackupConfigError("sha256sum or shasum -a 256 is required")


def is_non_local_checksum_name(name: str) -> bool:
    path = Path(name)
    return path.is_absolute() or path.name != name or ".." in path.parts


def checksum_entry_names(backup_dir: Path, timestamp: str) -> set[str]:
    checksum_file = backup_dir / "SHA256SUMS"
    names: set[str] = set()
    for line_number, line in enumerate(checksum_file.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        match = CHECKSUM_LINE_PATTERN.match(line)
        if not match:
            raise BackupCheckError(f"backup {timestamp} SHA256SUMS has a malformed checksum line")
        name = match.group(1)
        if is_non_local_checksum_name(name):
            raise BackupCheckError(f"backup {timestamp} SHA256SUMS has a non-local entry on line {line_number}")
        names.add(name)
    if not names:
        raise BackupCheckError(f"backup {timestamp} SHA256SUMS is empty")
    return names


def require_file(path: Path, timestamp: str, label: str, *, non_empty: bool) -> None:
    if not path.is_file():
        raise BackupCheckError(f"backup {timestamp} missing {label}")
    if non_empty and path.stat().st_size == 0:
        raise BackupCheckError(f"backup {timestamp} has empty {label}")


def required_matching_files(backup_dir: Path, timestamp: str, pattern: str) -> list[Path]:
    matches = [path for path in backup_dir.glob(pattern) if path.is_file() and path.stat().st_size > 0]
    if not matches:
        raise BackupCheckError(f"backup {timestamp} missing non-empty {pattern}")
    return matches


def ensure_checksum_covers_required_artifacts(
    checksum_names: set[str],
    timestamp: str,
    dump_files: list[Path],
    csv_files: list[Path],
) -> None:
    if not any(path.name in checksum_names for path in dump_files):
        raise BackupCheckError(f"backup {timestamp} SHA256SUMS does not include postgres_*.dump")
    if not any(path.name in checksum_names for path in csv_files):
        raise BackupCheckError(f"backup {timestamp} SHA256SUMS does not include btc_usd_daily_*.csv")
    if "manifest.txt" not in checksum_names:
        raise BackupCheckError(f"backup {timestamp} SHA256SUMS does not include manifest.txt")


def verify_checksums(backup_dir: Path, timestamp: str, context: str) -> None:
    result = subprocess.run(
        checksum_command(),
        cwd=backup_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        prefix = f"{context} " if context else ""
        raise BackupCheckError(f"{prefix}backup {timestamp} checksum verification failed")


def validate_backup_dir(backup_dir: Path, *, expected_timestamp: str | None = None, context: str = "") -> datetime:
    timestamp = backup_dir.name
    if expected_timestamp is not None and timestamp != expected_timestamp:
        raise BackupCheckError(f"backup basename {timestamp} does not match expected {expected_timestamp}")
    parsed_timestamp = parse_timestamp(timestamp)
    if not backup_dir.is_dir():
        prefix = f"{context} " if context else ""
        raise BackupCheckError(f"{prefix}backup {timestamp} is missing")

    dump_files = required_matching_files(backup_dir, timestamp, "postgres_*.dump")
    csv_files = required_matching_files(backup_dir, timestamp, "btc_usd_daily_*.csv")
    require_file(backup_dir / "manifest.txt", timestamp, "manifest.txt", non_empty=True)
    require_file(backup_dir / "SHA256SUMS", timestamp, "SHA256SUMS", non_empty=True)
    checksum_names = checksum_entry_names(backup_dir, timestamp)
    ensure_checksum_covers_required_artifacts(checksum_names, timestamp, dump_files, csv_files)
    verify_checksums(backup_dir, timestamp, context)
    return parsed_timestamp


def latest_backup_dir(backup_root: Path) -> tuple[Path, datetime]:
    if not backup_root.is_dir():
        raise BackupCheckError("backup root is missing or is not a directory")

    candidates: list[tuple[datetime, Path]] = []
    for child in backup_root.iterdir():
        if not child.is_dir():
            continue
        if not TIMESTAMP_PATTERN.match(child.name):
            continue
        candidates.append((parse_timestamp(child.name), child))

    if not candidates:
        raise BackupCheckError("no timestamped backup directories found under backup root")
    parsed_timestamp, backup_dir = max(candidates, key=lambda candidate: candidate[0])
    return backup_dir, parsed_timestamp


def check_freshness(parsed_timestamp: datetime, timestamp: str, now_utc: datetime, max_age: timedelta) -> timedelta:
    age = now_utc - parsed_timestamp
    if age < timedelta(0):
        raise BackupCheckError(f"backup {timestamp} timestamp is in the future")
    if age > max_age:
        raise BackupCheckError(
            f"backup {timestamp} is stale: age {format_age_hours(age)}h exceeds max {format_age_hours(max_age)}h"
        )
    return age


def format_age_hours(delta: timedelta) -> str:
    return f"{delta.total_seconds() / 3600:.2f}"


def normalize_now(now_utc: datetime | None) -> datetime:
    if now_utc is None:
        return datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        raise BackupConfigError("now_utc must include timezone information")
    return now_utc.astimezone(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check the newest timestamped local backup for freshness and SHA-256 validity.",
    )
    parser.add_argument(
        "--backup-root",
        default=os.environ.get("BACKUP_DIR", "./backups"),
        help="Root containing timestamped backup directories. Default: BACKUP_DIR or ./backups.",
    )
    parser.add_argument(
        "--max-age-hours",
        default=os.environ.get("BACKUP_FRESHNESS_MAX_AGE_HOURS"),
        help="Required freshness window in hours. Can also be set with BACKUP_FRESHNESS_MAX_AGE_HOURS.",
    )
    parser.add_argument(
        "--off-server-root",
        default=os.environ.get("OFFSERVER_BACKUP_ROOT") or None,
        help="Optional root that must contain the same timestamped backup basename.",
    )
    return parser


def run_check(args: argparse.Namespace, now_utc: datetime | None) -> str:
    if not args.backup_root:
        raise BackupConfigError("backup root must not be empty")

    max_age_hours, max_age = parse_max_age_hours(args.max_age_hours)
    now = normalize_now(now_utc)
    backup_root = Path(args.backup_root)
    backup_dir, parsed_timestamp = latest_backup_dir(backup_root)
    timestamp = backup_dir.name

    validate_backup_dir(backup_dir)
    age = check_freshness(parsed_timestamp, timestamp, now, max_age)

    off_server_text = ""
    if args.off_server_root is not None:
        if not str(args.off_server_root).strip():
            raise BackupConfigError("off-server root must not be empty")
        off_server_root = Path(args.off_server_root)
        if not off_server_root.is_dir():
            raise BackupCheckError("off-server root is missing or is not a directory")
        off_server_backup_dir = off_server_root / timestamp
        if not off_server_backup_dir.is_dir():
            raise BackupCheckError(f"off-server backup {timestamp} is missing")
        validate_backup_dir(off_server_backup_dir, expected_timestamp=timestamp, context="off-server")
        off_server_text = f"; off-server backup {timestamp} valid"

    return (
        f"OK backup {timestamp} valid and fresh "
        f"(age {format_age_hours(age)}h <= max {max_age_hours}h){off_server_text}"
    )


def main(argv: list[str] | None = None, *, now_utc: datetime | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(run_check(args, now_utc))
    except BackupCheckError as exc:
        print(f"{exc.status}: {exc}", file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
