from __future__ import annotations

import importlib
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "004_telegram_posts.sql"
COMPOSE = ROOT / "podman-compose.yml"


class TelegramConfigTests(unittest.TestCase):
    def _reload_settings(self):
        import collector.config as config

        return importlib.reload(config).settings

    def test_publication_is_disabled_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = self._reload_settings()
        self.assertEqual("", settings.telegram_bot_token)
        self.assertEqual("", settings.telegram_channel_id)

    def test_settings_read_the_environment(self) -> None:
        env = {"TELEGRAM_BOT_TOKEN": "t0ken", "TELEGRAM_CHANNEL_ID": "@bitcoinriskbrief"}
        with patch.dict(os.environ, env, clear=True):
            settings = self._reload_settings()
        self.assertEqual("t0ken", settings.telegram_bot_token)
        self.assertEqual("@bitcoinriskbrief", settings.telegram_channel_id)

    def test_freshness_window_matches_the_backend_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = self._reload_settings()
        self.assertEqual(2, settings.data_freshness_max_age_days)


class TelegramMigrationTests(unittest.TestCase):
    def test_migration_exists_and_is_idempotent(self) -> None:
        self.assertTrue(MIGRATION.is_file())
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS telegram_posts", sql)

    def test_covered_date_is_the_primary_key(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("as_of DATE PRIMARY KEY", sql)

    def test_migration_stores_no_personal_data(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        for forbidden in ("contact", "email", "telegram_handle", "chat_id"):
            self.assertNotIn(forbidden, sql)

    def test_claim_is_unconfirmed_until_telegram_confirms_it(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("posted_at TIMESTAMPTZ,", sql)
        self.assertNotRegex(sql, r"posted_at\s+TIMESTAMPTZ[^\n]*DEFAULT")


class TelegramComposeConfigTests(unittest.TestCase):
    def test_collector_receives_telegram_and_freshness_settings(self) -> None:
        compose = COMPOSE.read_text(encoding="utf-8")
        match = re.search(
            r"^  data-collector:\n(?P<body>.*?)(?=^  [\w-]+:\n|\Z)",
            compose,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match)
        collector = match.group("body")
        self.assertIn("TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-}", collector)
        self.assertIn("TELEGRAM_CHANNEL_ID: ${TELEGRAM_CHANNEL_ID:-}", collector)
        self.assertIn(
            "DATA_FRESHNESS_MAX_AGE_DAYS: ${DATA_FRESHNESS_MAX_AGE_DAYS:-2}",
            collector,
        )
