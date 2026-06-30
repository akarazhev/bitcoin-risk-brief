from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


PayloadProducer = Callable[[], Awaitable[tuple[Any, int]]]


@dataclass(frozen=True)
class CachedEndpointPayload:
    content: Any
    status_code: int
    data_version: str
    etag: str
    expires_at: float


class PublicEndpointCache:
    def __init__(self, *, ttl_seconds: int, clock: Callable[[], float] | None = None) -> None:
        self.ttl_seconds = max(0, ttl_seconds)
        self._clock = clock or time.monotonic
        self._entries: dict[str, CachedEndpointPayload] = {}

    async def get_or_build(
        self,
        key: str,
        data_version: str,
        producer: PayloadProducer,
    ) -> tuple[CachedEndpointPayload, bool]:
        now = self._clock()
        entry = self._entries.get(key)
        if entry and entry.data_version == data_version and entry.expires_at > now:
            return entry, True

        content, status_code = await producer()
        entry = CachedEndpointPayload(
            content=content,
            status_code=status_code,
            data_version=data_version,
            etag=_build_etag(key, data_version, content),
            expires_at=now + self.ttl_seconds,
        )
        self._entries[key] = entry
        self._prune(now)
        return entry, False

    def invalidate(self) -> None:
        self._entries.clear()

    def _prune(self, now: float) -> None:
        expired_keys = [
            key
            for key, entry in self._entries.items()
            if entry.expires_at <= now
        ]
        for key in expired_keys:
            del self._entries[key]


def _build_etag(key: str, data_version: str, content: Any) -> str:
    encoded = json.dumps(
        {"key": key, "data_version": data_version, "content": content},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return f'"{hashlib.sha256(encoded).hexdigest()[:24]}"'


def build_cache_headers(
    *,
    etag: str,
    data_version: str,
    cache_hit: bool,
    max_age_seconds: int,
    stale_while_revalidate_seconds: int,
) -> dict[str, str]:
    return {
        "Cache-Control": (
            f"public, max-age={max(0, max_age_seconds)}, "
            f"stale-while-revalidate={max(0, stale_while_revalidate_seconds)}"
        ),
        "ETag": etag,
        "X-Cache": "HIT" if cache_hit else "MISS",
        "X-Cache-Version": data_version,
    }


def etag_matches(etag: str, if_none_match: str | None) -> bool:
    if if_none_match is None:
        return False
    candidates = [candidate.strip() for candidate in if_none_match.split(",")]
    return "*" in candidates or etag in candidates


def no_store_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
    }
