from __future__ import annotations

import unittest

from app.rate_limit import FixedWindowRateLimiter


class FixedWindowRateLimiterTest(unittest.TestCase):
    def test_allows_requests_up_to_limit_per_window(self) -> None:
        limiter = FixedWindowRateLimiter(limit=2, window_seconds=60)

        self.assertTrue(limiter.allow("client-a", now=100.0))
        self.assertTrue(limiter.allow("client-a", now=120.0))
        self.assertFalse(limiter.allow("client-a", now=130.0))

    def test_resets_after_window_expires(self) -> None:
        limiter = FixedWindowRateLimiter(limit=1, window_seconds=60)

        self.assertTrue(limiter.allow("client-a", now=100.0))
        self.assertFalse(limiter.allow("client-a", now=120.0))
        self.assertTrue(limiter.allow("client-a", now=161.0))


if __name__ == "__main__":
    unittest.main()
