from __future__ import annotations

from dataclasses import dataclass
import re

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
VALID_LOCALES = {"en", "ru", "zh", "de", "fr", "es", "ar"}
VALID_SOURCE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


class InvalidWaitlistContact(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedWaitlistContact:
    contact: str
    normalized_contact: str
    contact_type: str


def normalize_locale(value: str | None) -> str:
    locale = (value or "en").strip().lower()
    return locale if locale in VALID_LOCALES else "en"


def normalize_source(value: str | None) -> str:
    source = (value or "landing").strip().lower()
    return source if VALID_SOURCE_RE.match(source) else "landing"


def normalize_waitlist_contact(value: str) -> NormalizedWaitlistContact:
    contact = value.strip()
    if not contact or len(contact) > 254:
        raise InvalidWaitlistContact("Enter a valid email address")

    if EMAIL_RE.match(contact):
        return NormalizedWaitlistContact(
            contact=contact,
            normalized_contact=contact.lower(),
            contact_type="email",
        )

    raise InvalidWaitlistContact("Enter a valid email address")
