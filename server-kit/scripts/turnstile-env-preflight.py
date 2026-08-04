#!/usr/bin/env python3
"""Validate the Turnstile subset of a Compose .env file without evaluating it."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


EXPECTED_HOSTNAME = "bitcoinriskbrief.minihub.app"
REQUIRED_KEYS = (
    "VITE_TURNSTILE_SITE_KEY",
    "TURNSTILE_SECRET",
    "TURNSTILE_HOSTNAMES",
)
OFFICIAL_DUMMY_SITEKEYS = frozenset({
    "1x00000000000000000000AA",
    "2x00000000000000000000AB",
    "1x00000000000000000000BB",
    "2x00000000000000000000BB",
    "3x00000000000000000000FF",
})
OFFICIAL_DUMMY_SECRETS = frozenset({
    "1x0000000000000000000000000000000AA",
    "2x0000000000000000000000000000000AA",
    "3x0000000000000000000000000000000AA",
})
PLACEHOLDER_MARKERS = (
    "replace-with-",
    "placeholder",
    "example",
    "your-",
    "your_",
    "changeme",
    "<",
    ">",
)
ASSIGNMENT = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(=|:)\s*(.*)$")
SAFE_CREDENTIAL = re.compile(r"[A-Za-z0-9_-]{16,}")


class InvalidTurnstileEnvironment(Exception):
    pass


def _is_relevant_malformed_assignment(line: str) -> bool:
    stripped = line.lstrip()
    return any(re.match(rf"{re.escape(key)}(?:\s|=|:|$)", stripped) for key in REQUIRED_KEYS)


def _parse_compose_value(raw_value: str) -> str:
    value = raw_value.lstrip()
    if not value or value.startswith("#"):
        return ""

    if value[0] in {"'", '"'}:
        quote = value[0]
        escaped = False
        for index, character in enumerate(value[1:], start=1):
            if character == quote and not escaped:
                trailing = value[index + 1 :].strip()
                if trailing and not trailing.startswith("#"):
                    raise InvalidTurnstileEnvironment
                return value[1:index]
            escaped = character == "\\" and not escaped
            if character != "\\":
                escaped = False
        raise InvalidTurnstileEnvironment

    return re.split(r"[ \t]+#", value, maxsplit=1)[0].strip()


def _read_turnstile_values(env_file: Path) -> dict[str, str]:
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InvalidTurnstileEnvironment from exc

    values: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = ASSIGNMENT.match(line)
        if match is None:
            if _is_relevant_malformed_assignment(line):
                raise InvalidTurnstileEnvironment
            continue
        key, _delimiter, raw_value = match.groups()
        if key not in REQUIRED_KEYS:
            continue
        if key in values:
            raise InvalidTurnstileEnvironment
        values[key] = _parse_compose_value(raw_value)

    if set(values) != set(REQUIRED_KEYS):
        raise InvalidTurnstileEnvironment
    return values


def _is_safe_production_credential(value: str, dummy_values: frozenset[str]) -> bool:
    normalized = value.lower()
    return (
        bool(SAFE_CREDENTIAL.fullmatch(value))
        and value not in dummy_values
        and not any(marker in normalized for marker in PLACEHOLDER_MARKERS)
    )


def validate_turnstile_environment(env_file: Path) -> None:
    values = _read_turnstile_values(env_file)
    if not _is_safe_production_credential(values["VITE_TURNSTILE_SITE_KEY"], OFFICIAL_DUMMY_SITEKEYS):
        raise InvalidTurnstileEnvironment
    if not _is_safe_production_credential(values["TURNSTILE_SECRET"], OFFICIAL_DUMMY_SECRETS):
        raise InvalidTurnstileEnvironment
    if values["TURNSTILE_HOSTNAMES"] != EXPECTED_HOSTNAME:
        raise InvalidTurnstileEnvironment


def main() -> int:
    argument_parser = argparse.ArgumentParser(add_help=False)
    argument_parser.add_argument("--env-file", type=Path, required=True)
    arguments = argument_parser.parse_args()
    try:
        validate_turnstile_environment(arguments.env_file)
    except InvalidTurnstileEnvironment:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
