from __future__ import annotations

import unittest

from app import main
from app.public_cache import PublicCacheWarmupResult


class MainPatchMixin:
    def patch_main(self, name: str, value) -> None:
        original = getattr(main, name)
        setattr(main, name, value)
        self.addCleanup(setattr, main, name, original)


class StandardPublicWarmupTargetTest(MainPatchMixin, unittest.IsolatedAsyncioTestCase):
    async def test_standard_warmup_targets_use_frontend_public_cache_keys(self) -> None:
        targets = main._standard_public_cache_warmup_targets()

        self.assertEqual(
            [target.key for target in targets],
            [
                "GET /api/readiness",
                "GET /api/risk/latest",
                "GET /api/risk/history?limit=2000",
                "GET /api/risk/levels",
                "GET /api/brief/latest",
            ],
        )

    async def test_startup_warmup_skips_without_validation_data(self) -> None:
        self.patch_main("get_pool", lambda: object())

        async def empty_version(_pool):
            return "validation:empty"

        self.patch_main("fetch_public_data_version", empty_version)

        with self.assertLogs("app.access", level="INFO") as logs:
            result = await main.warm_public_read_cache_on_startup()

        self.assertEqual(result, PublicCacheWarmupResult((), ()))
        self.assertIn("public_cache_warmup_skipped reason=no_validation", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
