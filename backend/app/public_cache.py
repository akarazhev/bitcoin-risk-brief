from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


PayloadProducer = Callable[[], Awaitable[tuple[Any, int]]]
CacheStorageKey = tuple[str, str]


@dataclass(frozen=True)
class CachedEndpointPayload:
    content: Any
    status_code: int
    data_version: str
    etag: str
    expires_at: float


@dataclass(frozen=True)
class PublicCacheWarmupTarget:
    key: str
    producer: PayloadProducer


@dataclass(frozen=True)
class PublicCacheWarmupTargetResult:
    key: str
    duration_ms: float
    cache_hit: bool
    error: str | None = None


@dataclass(frozen=True)
class PublicCacheWarmupResult:
    warmed_keys: tuple[str, ...]
    failed_keys: tuple[str, ...]
    total_duration_ms: float = 0.0
    target_results: tuple[PublicCacheWarmupTargetResult, ...] = ()

    def slowest_summary(self, *, limit: int = 3) -> str:
        if not self.target_results:
            return "none"
        slowest = sorted(
            self.target_results,
            key=lambda target_result: target_result.duration_ms,
            reverse=True,
        )[: max(0, limit)]
        if not slowest:
            return "none"
        return ",".join(
            f"{target_result.key}:{target_result.duration_ms:.1f}ms"
            for target_result in slowest
        )


class PublicEndpointCache:
    def __init__(self, *, ttl_seconds: int, clock: Callable[[], float] | None = None) -> None:
        self.ttl_seconds = max(0, ttl_seconds)
        self._clock = clock or time.monotonic
        self._entries: dict[CacheStorageKey, CachedEndpointPayload] = {}
        self._inflight_builds: dict[CacheStorageKey, asyncio.Task[CachedEndpointPayload]] = {}

    async def get_or_build(
        self,
        key: str,
        data_version: str,
        producer: PayloadProducer,
    ) -> tuple[CachedEndpointPayload, bool]:
        storage_key = (key, data_version)
        now = self._clock()
        entry = self._entries.get(storage_key)
        if entry and entry.expires_at > now:
            return entry, True

        inflight = self._inflight_builds.get(storage_key)
        if inflight is not None:
            return await inflight, True

        task = asyncio.create_task(self._build_and_store(storage_key, key, data_version, producer))
        self._inflight_builds[storage_key] = task
        try:
            return await task, False
        finally:
            if self._inflight_builds.get(storage_key) is task:
                del self._inflight_builds[storage_key]

    async def _build_and_store(
        self,
        storage_key: CacheStorageKey,
        key: str,
        data_version: str,
        producer: PayloadProducer,
    ) -> CachedEndpointPayload:
        content, status_code = await producer()
        now = self._clock()
        entry = CachedEndpointPayload(
            content=content,
            status_code=status_code,
            data_version=data_version,
            etag=_build_etag(key, data_version, content),
            expires_at=now + self.ttl_seconds,
        )
        self._entries[storage_key] = entry
        self._prune(now)
        return entry

    def invalidate(self) -> None:
        self._entries.clear()

    def _prune(self, now: float) -> None:
        expired_keys = [
            storage_key
            for storage_key, entry in self._entries.items()
            if entry.expires_at <= now
        ]
        for storage_key in expired_keys:
            del self._entries[storage_key]


async def warm_public_endpoint_cache(
    cache: PublicEndpointCache,
    data_version: str,
    targets: list[PublicCacheWarmupTarget] | tuple[PublicCacheWarmupTarget, ...],
    *,
    logger: logging.Logger | None = None,
) -> PublicCacheWarmupResult:
    active_logger = logger or logging.getLogger(__name__)
    warmed_keys: list[str] = []
    failed_keys: list[str] = []

    for target in targets:
        try:
            await cache.get_or_build(target.key, data_version, target.producer)
        except Exception as exc:
            failed_keys.append(target.key)
            active_logger.warning(
                "public_cache_warmup_failed key=%s error=%s",
                target.key,
                exc,
                exc_info=True,
            )
            continue
        warmed_keys.append(target.key)

    return PublicCacheWarmupResult(tuple(warmed_keys), tuple(failed_keys))


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
