from __future__ import annotations

import unittest

from collector.db_pool import create_pool_with_retry


class FlakyPoolFactory:
    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, database_url: str, *, min_size: int, max_size: int):
        self.calls += 1
        if self.calls < 3:
            raise ConnectionRefusedError("database not ready")
        return {"database_url": database_url, "min_size": min_size, "max_size": max_size}


class DbPoolRetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_pool_retries_transient_connection_failures(self) -> None:
        factory = FlakyPoolFactory()
        sleeps: list[float] = []

        async def fake_sleep(delay: float) -> None:
            sleeps.append(delay)

        pool = await create_pool_with_retry(
            "postgresql://example",
            create_pool=factory,
            sleep=fake_sleep,
            attempts=3,
            backoff_seconds=0.25,
            min_size=1,
            max_size=3,
        )

        self.assertEqual(factory.calls, 3)
        self.assertEqual(sleeps, [0.25, 0.5])
        self.assertEqual(pool["database_url"], "postgresql://example")


if __name__ == "__main__":
    unittest.main()
