from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

TRANSIENT_DB_ERRORS = (ConnectionError, OSError)


async def create_pool_with_retry(
    database_url: str,
    *,
    create_pool: Callable[..., Awaitable[Any]],
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    attempts: int = 5,
    backoff_seconds: float = 1.0,
    min_size: int = 1,
    max_size: int = 3,
) -> Any:
    last_error: BaseException | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            return await create_pool(database_url, min_size=min_size, max_size=max_size)
        except TRANSIENT_DB_ERRORS as exc:
            last_error = exc
            if attempt >= attempts:
                raise
            await sleep(max(0.0, backoff_seconds) * (2 ** (attempt - 1)))
    if last_error is not None:
        raise last_error
    raise ConnectionError("Failed to create database pool")
