#!/usr/bin/env python3
"""Validate the Telegram subset of a Compose .env file without evaluating it."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


EXPECTED_CHANNEL_ID = "@bitcoinriskbrief"
REQUIRED_KEYS = (
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHANNEL_ID",
)
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
ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
BOT_TOKEN = re.compile(r"\d{6,14}:[A-Za-z0-9_-]{30,80}")


class InvalidTelegramEnvironment(Exception):
    pass


def _is_relevant_malformed_assignment(line: str) -> bool:
    stripped = line.lstrip()
    return any(
        re.match(rf"(?:export\s+)?{re.escape(key)}(?:\s|=|:|$)", stripped)
        for key in REQUIRED_KEYS
    )


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
                    raise InvalidTelegramEnvironment
                return value[1:index]
            escaped = character == "\\" and not escaped
            if character != "\\":
                escaped = False
        raise InvalidTelegramEnvironment

    return re.split(r"[ \t]+#", value, maxsplit=1)[0].strip()


def _read_telegram_values(env_file: Path) -> dict[str, str]:
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InvalidTelegramEnvironment from exc

    values: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = ASSIGNMENT.match(line)
        if match is None:
            if _is_relevant_malformed_assignment(line):
                raise InvalidTelegramEnvironment
            continue
        key, raw_value = match.groups()
        if key not in REQUIRED_KEYS:
            continue
        if key in values:
            raise InvalidTelegramEnvironment
        values[key] = _parse_compose_value(raw_value)

    if set(values) != set(REQUIRED_KEYS):
        raise InvalidTelegramEnvironment
    return values


def _is_safe_bot_token(value: str) -> bool:
    normalized = value.lower()
    return (
        bool(BOT_TOKEN.fullmatch(value))
        and not any(marker in normalized for marker in PLACEHOLDER_MARKERS)
    )


def validate_telegram_environment(env_file: Path) -> None:
    values = _read_telegram_values(env_file)
    if not _is_safe_bot_token(values["TELEGRAM_BOT_TOKEN"]):
        raise InvalidTelegramEnvironment
    if values["TELEGRAM_CHANNEL_ID"] != EXPECTED_CHANNEL_ID:
        raise InvalidTelegramEnvironment


def main() -> int:
    argument_parser = argparse.ArgumentParser(add_help=False)
    argument_parser.add_argument("--env-file", type=Path, required=True)
    arguments = argument_parser.parse_args()
    try:
        validate_telegram_environment(arguments.env_file)
    except InvalidTelegramEnvironment:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
