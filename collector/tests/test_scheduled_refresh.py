from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.risk_sources import write_btc_usd_daily_csv
import collector.main as collector_main


def daily_row(day: date, close: float) -> dict:
    return {
        "date": day,
        "open": close - 1.0,
        "high": close + 2.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1_000_000.0,
        "market_cap": close * 19_000_000.0,
        "circulating_supply": 19_000_000.0,
        "source": "coinmarketcap_csv",
    }


def no_key_settings() -> SimpleNamespace:
    return SimpleNamespace(coinmarketcap_api_key="")


def api_key_settings() -> SimpleNamespace:
    return SimpleNamespace(coinmarketcap_api_key="cmc-key")


class ScheduledPublicCmcRefreshTest(unittest.IsolatedAsyncioTestCase):
    async def test_scheduled_no_key_stale_csv_calls_public_download_for_last_completed_utc_day(self) -> None:
        now = datetime(2026, 6, 27, 3, 0, tzinfo=timezone.utc)
        pool = object()

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "btc_usd_daily.csv"
            incoming_dir = Path(temp_dir) / "incoming"
            write_btc_usd_daily_csv(csv_path, [daily_row(date(2026, 6, 24), 101.0)])
            download_public = AsyncMock()

            with (
                patch.object(collector_main, "BTC_CSV_PATH", csv_path),
                patch.object(collector_main, "CMC_INCOMING_DIR", incoming_dir),
                patch.object(collector_main, "settings", no_key_settings()),
                patch.object(collector_main, "download_public_cmc_csv_once", download_public),
            ):
                await collector_main.scheduled_refresh_once(pool, now=now)

        download_public.assert_awaited_once_with(pool, expected_end_date=date(2026, 6, 26))

    async def test_scheduled_no_key_current_csv_imports_without_public_download(self) -> None:
        now = datetime(2026, 6, 27, 3, 0, tzinfo=timezone.utc)
        pool = object()

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "btc_usd_daily.csv"
            incoming_dir = Path(temp_dir) / "incoming"
            write_btc_usd_daily_csv(csv_path, [daily_row(date(2026, 6, 26), 103.0)])
            download_public = AsyncMock()
            import_csv = AsyncMock()

            with (
                patch.object(collector_main, "BTC_CSV_PATH", csv_path),
                patch.object(collector_main, "CMC_INCOMING_DIR", incoming_dir),
                patch.object(collector_main, "settings", no_key_settings()),
                patch.object(collector_main, "download_public_cmc_csv_once", download_public),
                patch.object(collector_main, "import_csv_once", import_csv),
            ):
                await collector_main.scheduled_refresh_once(pool, now=now)

        download_public.assert_not_called()
        import_csv.assert_awaited_once_with(pool, refresh_remote=False)

    async def test_scheduled_no_key_failed_public_download_preserves_csv_and_fails(self) -> None:
        now = datetime(2026, 6, 27, 3, 0, tzinfo=timezone.utc)
        pool = object()

        async def fail_public_download(_pool, *, expected_end_date):
            raise RuntimeError(f"public unavailable through {expected_end_date.isoformat()}")

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "btc_usd_daily.csv"
            incoming_dir = Path(temp_dir) / "incoming"
            write_btc_usd_daily_csv(csv_path, [daily_row(date(2026, 6, 24), 101.0)])
            original_content = csv_path.read_text(encoding="utf-8")
            import_csv = AsyncMock()

            with (
                patch.object(collector_main, "BTC_CSV_PATH", csv_path),
                patch.object(collector_main, "CMC_INCOMING_DIR", incoming_dir),
                patch.object(collector_main, "settings", no_key_settings()),
                patch.object(collector_main, "download_public_cmc_csv_once", fail_public_download),
                patch.object(collector_main, "import_csv_once", import_csv),
            ):
                with self.assertRaisesRegex(RuntimeError, "public unavailable through 2026-06-26"):
                    await collector_main.scheduled_refresh_once(pool, now=now)

            self.assertEqual(csv_path.read_text(encoding="utf-8"), original_content)

        import_csv.assert_not_called()

    async def test_scheduled_public_download_failure_uses_api_fallback_only_when_key_configured(self) -> None:
        now = datetime(2026, 6, 27, 3, 0, tzinfo=timezone.utc)
        pool = object()

        async def fail_public_download(_pool, *, expected_end_date):
            raise RuntimeError(f"public unavailable through {expected_end_date.isoformat()}")

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "btc_usd_daily.csv"
            incoming_dir = Path(temp_dir) / "incoming"
            write_btc_usd_daily_csv(csv_path, [daily_row(date(2026, 6, 24), 101.0)])
            import_csv = AsyncMock()

            with (
                patch.object(collector_main, "BTC_CSV_PATH", csv_path),
                patch.object(collector_main, "CMC_INCOMING_DIR", incoming_dir),
                patch.object(collector_main, "settings", api_key_settings()),
                patch.object(collector_main, "download_public_cmc_csv_once", fail_public_download),
                patch.object(collector_main, "import_csv_once", import_csv),
            ):
                await collector_main.scheduled_refresh_once(pool, now=now)

        import_csv.assert_awaited_once_with(pool, refresh_remote=True, now=now)


if __name__ == "__main__":
    unittest.main()
