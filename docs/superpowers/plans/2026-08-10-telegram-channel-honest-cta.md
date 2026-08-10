# Telegram Channel And Honest CTA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the daily risk observation to a public Telegram channel automatically, and replace the waitlist copy that promises delivery the product does not perform.

**Architecture:** The publisher lives in the collector, hooked in after `write_validation` inside `import_csv_once`, wrapped so a Telegram failure can never fail an import. Freshness reuses `build_readiness_payload` rather than reimplementing it. Idempotency is a new single-table migration keyed on the covered date.

**Tech Stack:** Python 3.13, asyncpg, httpx (already a collector dependency), React/Vite, Vitest, `unittest`.

Design: [Telegram Channel And Honest CTA Design](../specs/2026-08-07-telegram-channel-honest-cta-design.md).

## Global Constraints

- **The channel is `@bitcoinriskbrief`, public, at `https://t.me/bitcoinriskbrief`.** It is a channel, never a group.
- **An empty `TELEGRAM_BOT_TOKEN` disables publication entirely.** Local development, CI, and the test suite must never make an outbound Telegram request. A test that posts to a public channel is a defect that cannot be undone.
- **Publication is best-effort.** It runs after `write_validation` inside `try`/`except` and can never fail an import. A Telegram outage must not stop data collection.
- **Never weaken the Content-Security-Policy.** `backend/tests/test_frontend_security_headers.py` pins it verbatim. Nothing here needs a CSP change.
- No new dependency anywhere. `httpx==0.28.1` is already in `collector/requirements.txt`.
- No change to risk methodology, band thresholds, the collector's data paths, or nginx.
- Band thresholds live in `backend/app/risk.py` as `LOW_RISK_THRESHOLD = 0.30` and `HIGH_RISK_THRESHOLD = 0.70`. Import them; never redefine them.
- All seven locales stay complete: `en`, `ru`, `zh`, `de`, `fr`, `es`, `ar`. Arabic is RTL.
- The product is free and is not a pilot. No copy may describe it as a pilot, a trial, or a limited preview, and no copy may present the already-public history or risk-level views as something earned by giving a contact.
- Public artifacts never embed a stale risk reading, and every post carries the analytics-not-advice framing.

---

### Task 1: Migration and configuration

**Files:**
- Create: `migrations/004_telegram_posts.sql`
- Modify: `collector/collector/config.py`
- Modify: `.env.example`, `.env.production.example`
- Test: `collector/tests/test_telegram_config.py`

**Interfaces:**
- Produces: `settings.telegram_bot_token`, `settings.telegram_channel_id`, `settings.data_freshness_max_age_days` on the collector `Settings` dataclass, and the `telegram_posts` table.

- [ ] **Step 1: Write the failing test**

Create `collector/tests/test_telegram_config.py`:

```python
from __future__ import annotations

import importlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "004_telegram_posts.sql"


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_telegram_config -v`
Expected: FAIL — `Settings` has no `telegram_bot_token`.

- [ ] **Step 3: Add the migration and the settings**

Create `migrations/004_telegram_posts.sql`:

```sql
CREATE TABLE IF NOT EXISTS telegram_posts (
    as_of DATE PRIMARY KEY,
    posted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    message_id BIGINT,
    risk DOUBLE PRECISION NOT NULL,
    risk_state TEXT NOT NULL
);
```

The primary key on `as_of` is what enforces one post per covered date — the guarantee lives in the schema, not in application logic. The table holds no personal data.

In `collector/collector/config.py`, add three fields to the frozen `Settings` dataclass, following the existing `os.getenv` pattern:

```python
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_channel_id: str = os.getenv("TELEGRAM_CHANNEL_ID", "")
    data_freshness_max_age_days: int = int(os.getenv("DATA_FRESHNESS_MAX_AGE_DAYS", "2"))
```

`DATA_FRESHNESS_MAX_AGE_DAYS` is the same variable the backend already reads in `backend/app/config.py`; the default must stay `2` so both services agree.

Add to both `.env.example` and `.env.production.example`, with a comment noting that an empty token disables publication:

```bash
# Telegram channel publication. Empty TELEGRAM_BOT_TOKEN disables it entirely.
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=@bitcoinriskbrief
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_telegram_config -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add migrations/004_telegram_posts.sql collector/collector/config.py .env.example .env.production.example collector/tests/test_telegram_config.py
git commit -m "feat: add telegram post ledger and configuration"
```

---

### Task 2: Telegram client

**Files:**
- Create: `collector/collector/telegram.py`
- Test: `collector/tests/test_telegram_client.py`

**Interfaces:**
- Produces: `async def send_channel_post(*, token: str, chat_id: str, text: str, client: httpx.AsyncClient | None = None) -> int` returning the Telegram `message_id`, and `class TelegramSendError(RuntimeError)`.

- [ ] **Step 1: Write the failing test**

Create `collector/tests/test_telegram_client.py`:

```python
from __future__ import annotations

import unittest

import httpx

from collector.telegram import TelegramSendError, send_channel_post


def transport(handler):
    return httpx.MockTransport(handler)


class TelegramClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_posts_to_the_channel_and_returns_the_message_id(self) -> None:
        seen: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = request.content.decode()
            return httpx.Response(200, json={"ok": True, "result": {"message_id": 4242}})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            message_id = await send_channel_post(
                token="t0ken", chat_id="@bitcoinriskbrief", text="hello", client=client
            )

        self.assertEqual(4242, message_id)
        self.assertIn("/bott0ken/sendMessage", str(seen["url"]))
        self.assertIn("bitcoinriskbrief", str(seen["body"]))

    async def test_raises_on_a_telegram_level_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"ok": False, "description": "chat not found"})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            with self.assertRaises(TelegramSendError) as caught:
                await send_channel_post(
                    token="t0ken", chat_id="@nope", text="hello", client=client
                )

        self.assertIn("chat not found", str(caught.exception))

    async def test_raises_when_ok_is_false_despite_http_200(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"ok": False, "description": "not enough rights"})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            with self.assertRaises(TelegramSendError):
                await send_channel_post(
                    token="t0ken", chat_id="@bitcoinriskbrief", text="hello", client=client
                )

    async def test_never_puts_the_token_in_the_error_message(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"ok": False, "description": "Unauthorized"})

        async with httpx.AsyncClient(transport=transport(handler)) as client:
            with self.assertRaises(TelegramSendError) as caught:
                await send_channel_post(
                    token="sup3rs3cret", chat_id="@bitcoinriskbrief", text="hello", client=client
                )

        self.assertNotIn("sup3rs3cret", str(caught.exception))
```

The last test matters: an exception message ends up in logs, and logs are shared in issues and evidence packets.

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_telegram_client -v`
Expected: FAIL — `No module named 'collector.telegram'`.

- [ ] **Step 3: Write the client**

Create `collector/collector/telegram.py`:

```python
from __future__ import annotations

from typing import Any

import httpx

API_BASE = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 15.0


class TelegramSendError(RuntimeError):
    """Telegram refused the message. Never carries the bot token."""


async def send_channel_post(
    *,
    token: str,
    chat_id: str,
    text: str,
    client: httpx.AsyncClient | None = None,
) -> int:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    url = f"{API_BASE}/bot{token}/sendMessage"

    owned = client is None
    active = client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        response = await active.post(url, json=payload)
    finally:
        if owned:
            await active.aclose()

    body: dict[str, Any]
    try:
        body = response.json()
    except ValueError:
        raise TelegramSendError(f"telegram returned a non-JSON response, status={response.status_code}") from None

    if not body.get("ok"):
        description = str(body.get("description", "unknown error"))
        raise TelegramSendError(f"telegram rejected the post: {description}")

    return int(body["result"]["message_id"])
```

The token appears only in the URL, never in an exception message. `disable_web_page_preview` keeps the post compact — the link is a reference, not the content.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_telegram_client -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add collector/collector/telegram.py collector/tests/test_telegram_client.py
git commit -m "feat: add the telegram channel client"
```

---

### Task 3: Compose the daily post

**Files:**
- Create: `collector/collector/daily_post.py`
- Test: `collector/tests/test_daily_post.py`

**Interfaces:**
- Produces: `def compose_daily_post(*, latest: dict, previous: dict | None, levels: dict | None, methodology_version: str) -> str`, and `def band_boundary(risk_state: str, risk: float) -> float | None`.

This is a pure function with no I/O, which is why it is its own task: every content rule is testable without touching a database or a network.

- [ ] **Step 1: Write the failing test**

Create `collector/tests/test_daily_post.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
import unittest

from collector.daily_post import band_boundary, compose_daily_post


def risk_row(day: str, risk: float, state: str) -> dict:
    return {
        "timestamp": datetime.fromisoformat(day).replace(tzinfo=timezone.utc),
        "risk": risk,
        "risk_state": state,
    }


LEVELS = {
    "data": [
        {"risk": 0.30, "price_usd": 71400.0},
        {"risk": 0.70, "price_usd": 118250.0},
    ]
}


class BandBoundaryTests(unittest.TestCase):
    def test_low_points_at_the_neutral_entry(self) -> None:
        self.assertEqual(0.30, band_boundary("low", 0.24))

    def test_high_points_at_the_return_to_neutral(self) -> None:
        self.assertEqual(0.70, band_boundary("high", 0.82))

    def test_neutral_picks_the_nearer_boundary(self) -> None:
        self.assertEqual(0.30, band_boundary("neutral", 0.34))
        self.assertEqual(0.70, band_boundary("neutral", 0.66))

    def test_unknown_state_has_no_boundary(self) -> None:
        self.assertIsNone(band_boundary("unknown", 0.5))


class ComposeDailyPostTests(unittest.TestCase):
    def test_a_stable_day_states_the_value_the_delta_and_the_boundary(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("0.24", text)
        self.assertIn("low", text)
        self.assertIn("9 August 2026", text)
        self.assertIn("71,400", text)
        self.assertIn("crypto-scout-canonical-v1.1", text)
        self.assertIn("not financial advice", text.lower())
        self.assertIn("bitcoinriskbrief.minihub.app", text)

    def test_a_band_change_leads_with_the_change(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.31, "neutral"),
            previous=risk_row("2026-08-08", 0.29, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        first_line = text.splitlines()[0].lower()
        self.assertIn("band", first_line)
        self.assertIn("low", first_line)
        self.assertIn("neutral", first_line)

    def test_a_missing_level_snapshot_omits_the_boundary_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels=None,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("band begins", text.lower())
        self.assertIn("0.24", text)

    def test_a_snapshot_without_the_needed_point_omits_the_boundary_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=risk_row("2026-08-08", 0.25, "low"),
            levels={"data": [{"risk": 0.70, "price_usd": 118250.0}]},
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("band begins", text.lower())

    def test_the_first_observation_has_no_delta_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.24, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("Change:", text)

    def test_the_post_never_recommends_an_action(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-09", 0.82, "high"),
            previous=risk_row("2026-08-08", 0.68, "neutral"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        ).lower()
        for word in ("buy", "sell", "cheap", "expensive", "bottom", "top", "safe", "guaranteed"):
            self.assertNotIn(word, text)
```

The last test encodes the vocabulary ban that `docs/operations/marketing-and-growth.md` already applies to published values. Note `top` appears inside no legitimate word used here; if a future wording trips it, change the wording rather than the test.

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Expected: FAIL — `No module named 'collector.daily_post'`.

- [ ] **Step 3: Write the composer**

Create `collector/collector/daily_post.py`. Import the thresholds rather than redefining them:

```python
from app.risk import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD
```

`band_boundary` returns `LOW_RISK_THRESHOLD` for `low`, `HIGH_RISK_THRESHOLD` for `high`, and for `neutral` whichever of the two is nearer to the current risk. Any other state returns `None`.

`compose_daily_post` builds this shape, with the first line replaced by the band-change sentence when `previous` has a different `risk_state`:

```text
Bitcoin Risk Brief — 9 August 2026

Risk 0.24 — low
Change: −0.01 from 8 August

Neutral band begins at risk 0.30 — model price $71,400
Data: fresh through 9 August · crypto-scout-canonical-v1.1

bitcoinriskbrief.minihub.app

Analytics and research context, not financial advice.
```

Rules:

- the boundary line is omitted when `levels` is `None` or lacks the exact ladder point; the ladder step is `0.025`, so `0.30` and `0.70` are exact and need no interpolation, and a float comparison should allow a small tolerance rather than exact equality;
- the delta line is omitted when `previous` is `None`;
- the delta uses a true minus sign `−` for negative values, and the risk value is rounded to two decimals;
- prices use thousands separators and no decimals;
- on a band-change day the first line reads, for example, `Bitcoin risk moved from low to neutral — 9 August 2026`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Expected: PASS (10 tests).

- [ ] **Step 5: Commit**

```bash
git add collector/collector/daily_post.py collector/tests/test_daily_post.py
git commit -m "feat: compose the daily channel post"
```

---

### Task 4: Publish with a readiness gate and idempotency

**Files:**
- Create: `collector/collector/publisher.py`
- Modify: `collector/collector/main.py` (inside `import_csv_once`, after `write_validation`)
- Modify: `collector/collector/db_writer.py`
- Test: `collector/tests/test_publisher.py`

**Interfaces:**
- Consumes: `send_channel_post` from Task 2, `compose_daily_post` from Task 3, `settings` from Task 1.
- Produces: `async def publish_daily_post(pool, *, now: datetime | None = None) -> bool`, returning `True` when a post was published. `now` is passed straight through to `build_readiness_payload` so the freshness check is deterministic under test rather than dependent on the wall clock. Adds `async def record_telegram_post(pool, *, as_of, message_id, risk, risk_state) -> None` and `async def fetch_telegram_post(pool, as_of) -> dict | None` to `db_writer.py`.

- [ ] **Step 1: Write the failing test**

Create `collector/tests/test_publisher.py`. Follow the pattern in `collector/tests/test_scheduled_refresh.py`: stub `asyncpg` before importing collector modules, and drive everything with `AsyncMock` and `patch`.

This is the exact scaffolding and the first two cases; write the remaining six against the same helpers:

```python
from __future__ import annotations

import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object))

import collector.publisher as publisher
from collector.telegram import TelegramSendError

LATEST = {
    "timestamp": datetime(2026, 8, 9, tzinfo=timezone.utc),
    "risk": 0.24,
    "risk_state": "low",
}
PREVIOUS = {
    "timestamp": datetime(2026, 8, 8, tzinfo=timezone.utc),
    "risk": 0.25,
    "risk_state": "low",
}
VALIDATION = {"covered_end": datetime(2026, 8, 9, tzinfo=timezone.utc), "row_count": 5872}
LEVELS = {"data": [{"risk": 0.30, "price_usd": 71400.0}]}


def enabled(**overrides):
    """Patch settings so publication is switched on unless a test says otherwise."""
    values = {
        "telegram_bot_token": "t0ken",
        "telegram_channel_id": "@bitcoinriskbrief",
        "data_freshness_max_age_days": 2,
    }
    values.update(overrides)
    return patch.object(publisher, "settings", types.SimpleNamespace(**values))


def repository(existing_post=None):
    """Patch every repository and ledger call the publisher makes."""
    return (
        patch.object(publisher, "fetch_latest_risk", AsyncMock(return_value=LATEST)),
        patch.object(publisher, "fetch_previous_risk", AsyncMock(return_value=PREVIOUS)),
        patch.object(publisher, "fetch_latest_validation", AsyncMock(return_value=VALIDATION)),
        patch.object(publisher, "fetch_latest_risk_level_snapshot", AsyncMock(return_value=LEVELS)),
        patch.object(publisher, "fetch_telegram_post", AsyncMock(return_value=existing_post)),
        patch.object(publisher, "record_telegram_post", AsyncMock()),
    )


class PublisherTests(unittest.IsolatedAsyncioTestCase):
    async def test_an_empty_token_publishes_nothing(self) -> None:
        send = AsyncMock()
        with enabled(telegram_bot_token=""), patch.object(publisher, "send_channel_post", send):
            published = await publisher.publish_daily_post(object())

        self.assertFalse(published)
        send.assert_not_awaited()

    async def test_a_new_covered_date_posts_once_and_records_it(self) -> None:
        send = AsyncMock(return_value=4242)
        patches = repository()
        with enabled(), patch.object(publisher, "send_channel_post", send):
            for p in patches:
                p.start()
            try:
                published = await publisher.publish_daily_post(object())
            finally:
                for p in patches:
                    p.stop()

        self.assertTrue(published)
        self.assertEqual(1, send.await_count)
```

Tests that depend on freshness pass `now=datetime(2026, 8, 10, tzinfo=timezone.utc)` so the covered date is one day old and the readiness verdict is deterministic.

Write the remaining six cases against the same helpers:

1. an empty `TELEGRAM_BOT_TOKEN` publishes nothing and makes no outbound call — assert `send_channel_post` was never awaited;
2. an empty `TELEGRAM_CHANNEL_ID` behaves the same way;
3. a fresh import for a new covered date sends exactly once and records the row;
4. a covered date already present in `telegram_posts` sends nothing;
5. degraded readiness — the payload's status is not `ready` — sends nothing and records nothing;
6. a `TelegramSendError` records no row, so the next run retries the same date;
7. a `TelegramSendError` propagates no exception out of `publish_daily_post`; it returns `False`;
8. the recorded `as_of` equals the covered date of the latest risk row, not today's date.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_publisher -v`
Expected: FAIL — `No module named 'collector.publisher'`.

- [ ] **Step 3: Write the publisher and the ledger helpers**

Add to `collector/collector/db_writer.py`, matching the existing `pool.acquire()` style used by `write_validation`:

```python
async def fetch_telegram_post(pool: asyncpg.Pool, as_of: date) -> dict[str, Any] | None:
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT as_of, posted_at, message_id, risk, risk_state FROM telegram_posts WHERE as_of = $1",
            as_of,
        )
    return dict(row) if row else None


async def record_telegram_post(
    pool: asyncpg.Pool,
    *,
    as_of: date,
    message_id: int | None,
    risk: float,
    risk_state: str,
) -> None:
    async with pool.acquire() as connection:
        await connection.execute(
            """
            INSERT INTO telegram_posts (as_of, message_id, risk, risk_state)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (as_of) DO NOTHING
            """,
            as_of,
            message_id,
            risk,
            risk_state,
        )
```

`ON CONFLICT DO NOTHING` makes a concurrent double-run harmless: the primary key decides, not a read-then-write race.

Create `collector/collector/publisher.py` with `publish_daily_post(pool)` doing, in order:

1. return `False` immediately when either setting is empty — this check comes first so nothing else runs in local development or CI;
2. read `fetch_latest_risk`, `fetch_latest_validation` from `app.repository`;
3. call `build_readiness_payload(latest_risk, validation, now=now, max_age_days=settings.data_freshness_max_age_days)` and return `False` unless the payload's `status` is `ready`;
4. derive `as_of` as the date of the latest risk row's `timestamp`;
5. return `False` when `fetch_telegram_post(pool, as_of)` already returns a row;
6. read `fetch_previous_risk` and `fetch_latest_risk_level_snapshot`;
7. compose the text and send it;
8. on success, `record_telegram_post(...)` and return `True`;
9. on `TelegramSendError`, log with `logger.exception` and return `False` without recording.

Then hook it into `collector/collector/main.py`, immediately after the existing `write_validation(...)` call and before the summary log line:

```python
    try:
        from collector.publisher import publish_daily_post

        await publish_daily_post(pool)
    except Exception:
        logger.exception("telegram_publish_failed")
```

The broad `except` is deliberate and is the whole point: publication is best-effort and must never fail an import.

- [ ] **Step 4: Run the checks**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_publisher -v`
Expected: PASS (8 tests).

Run: `./scripts/manage.sh test-python`
Expected: PASS — confirm the existing collector suites still pass, since `import_csv_once` changed.

- [ ] **Step 5: Commit**

```bash
git add collector/collector/publisher.py collector/collector/db_writer.py collector/collector/main.py collector/tests/test_publisher.py
git commit -m "feat: publish the daily post to the telegram channel"
```

---

### Task 5: Honest CTA across seven locales

**Files:**
- Modify: `frontend/src/locales.ts`
- Modify: `frontend/src/App.tsx` (the waitlist block, and `source` at line 478)
- Modify: `frontend/src/App.css`
- Test: `frontend/src/App.test.tsx`, `frontend/src/locales.test.ts`

**Interfaces:**
- Produces: two new locale keys, `channelBody` and `channelCta`; changed `waitlistBody`, `join`, `joined`.

**What is wrong today.** The page says *"Leave an email or Telegram handle. The first test cohort gets the BTC risk alert free, plus access to the 2-year risk history and risk-level views during the pilot."* No alert is sent. The history and risk-level views are already public to everyone. And the product is no longer described as a pilot anywhere else.

**What replaces it.** The title stays — it is now true, because the channel delivers exactly that. Below it, a link to the channel. The form survives for a different and honest ask: whether a band-change alert to a personal contact would be useful, with the manual-follow-up boundary stated plainly.

**Blast radius — read this before starting.** Changing the `join` label and the `source` value breaks existing assertions in two files. This is mechanical, but it is not optional and it is not small:

| Where | What breaks | Count |
| --- | --- | --- |
| `frontend/src/App.test.tsx` | `getByRole('button', { name: /join waitlist/i })` | 12 occurrences |
| `frontend/src/App.test.tsx` | `name: /rejoindre la liste/i` (the French label, line 640) | 1 |
| `frontend/src/App.test.tsx` | `source: 'landing'` assertions at lines 660, 787, 1508, 1530 | 4 |
| `frontend/e2e/frontend-quality.spec.ts` | `name: /join waitlist/i` at line 262 | 1 |
| `frontend/e2e/frontend-quality.spec.ts` | `source: 'landing'` at line 291 | 1 |

The e2e file is the one that gets forgotten: it is exercised by `npm run smoke`, not by `npm test`, so a green unit run proves nothing about it. Update all of these to the new label and the new source value.

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/App.test.tsx`, following the file's flat `test(...)` style. The file already mocks `./api` through `apiMocks.joinWaitlist`, and has `verifyTurnstile()` and `selectLanguage()` helpers — use them rather than inventing new ones:

```tsx
test('offers the telegram channel as the way to get the daily signal', async () => {
  render(<App />)

  const link = await screen.findByRole('link', { name: /telegram channel/i })
  expect(link).toHaveAttribute('href', 'https://t.me/bitcoinriskbrief')
  expect(link).toHaveAttribute('target', '_blank')
  expect(link).toHaveAttribute('rel', 'noreferrer')
})

test('no longer presents public views as something earned by giving a contact', async () => {
  render(<App />)
  await screen.findByRole('link', { name: /telegram channel/i })

  const body = document.body.textContent ?? ''
  expect(body).not.toMatch(/first test cohort/i)
  expect(body).not.toMatch(/during the pilot/i)
  expect(body).not.toMatch(/2-year risk history and risk-level views/i)
})

test('submits the band-alert interest under its own source value', async () => {
  render(<App />)

  const input = await screen.findByPlaceholderText('email or @telegram')
  fireEvent.change(input, { target: { value: 'user@example.com' } })
  verifyTurnstile()
  fireEvent.click(screen.getByRole('button', { name: /register interest/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({
      contact: 'user@example.com',
      locale: 'en',
      source: 'risk_band_alert',
      turnstile_token: 'fresh-token',
    })
  })
})
```

Append to `frontend/src/locales.test.ts`:

```typescript
it('gives every locale the channel copy and no pilot framing', () => {
  for (const [code, value] of Object.entries(locales)) {
    expect(value.channelBody, `${code} is missing channelBody`).toBeTruthy()
    expect(value.channelCta, `${code} is missing channelCta`).toBeTruthy()
    expect(value.waitlistBody, `${code} still frames the product as a pilot`).not.toMatch(/pilot|cohort|kohorte|cohorte|试点/i)
  }
})
```

Adapt the iteration to whatever the file already uses to enumerate locales.

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test --prefix frontend`
Expected: FAIL — no link named "Telegram channel".

- [ ] **Step 3: Apply the copy and the markup**

Add `channelBody: string` and `channelCta: string` to the locale type, then use exactly these values.

**English**
- `channelBody`: `The daily risk post goes to a free public Telegram channel. No signup, no contact needed.`
- `channelCta`: `Open the Telegram channel`
- `waitlistBody`: `Band changes are rare. Leave an email or Telegram handle to hear about one. This is a manual follow-up — automated delivery does not exist yet.`
- `join`: `Register interest`
- `joined`: `Saved. You will hear from us when the risk band changes.`

**Russian**
- `channelBody`: `Ежедневный отчёт о риске публикуется в бесплатном открытом канале Telegram. Без регистрации и без контактов.`
- `channelCta`: `Открыть канал в Telegram`
- `waitlistBody`: `Диапазон меняется редко. Оставьте email или Telegram, чтобы узнать о смене. Это ручная связь — автоматической рассылки пока нет.`
- `join`: `Оставить контакт`
- `joined`: `Сохранено. Мы напишем, когда диапазон риска изменится.`

**Simplified Chinese**
- `channelBody`: `每日风险报告发布在免费公开的 Telegram 频道。无需注册，无需留下联系方式。`
- `channelCta`: `打开 Telegram 频道`
- `waitlistBody`: `风险区间变化很少见。留下邮箱或 Telegram 以便获知变化。这是人工联系，目前没有自动推送。`
- `join`: `登记关注`
- `joined`: `已保存。风险区间变化时我们会联系您。`

**German**
- `channelBody`: `Der tägliche Risikobericht erscheint in einem kostenlosen öffentlichen Telegram-Kanal. Ohne Anmeldung, ohne Kontaktdaten.`
- `channelCta`: `Telegram-Kanal öffnen`
- `waitlistBody`: `Bandwechsel sind selten. Hinterlassen Sie eine E-Mail oder einen Telegram-Handle, um davon zu erfahren. Das ist eine manuelle Rückmeldung — einen automatischen Versand gibt es noch nicht.`
- `join`: `Interesse hinterlegen`
- `joined`: `Gespeichert. Wir melden uns, wenn das Risikoband wechselt.`

**French**
- `channelBody`: `Le rapport de risque quotidien est publié sur une chaîne Telegram publique et gratuite. Sans inscription, sans coordonnées.`
- `channelCta`: `Ouvrir la chaîne Telegram`
- `waitlistBody`: `Les changements de bande sont rares. Laissez un e-mail ou un identifiant Telegram pour en être informé. Il s’agit d’un suivi manuel — l’envoi automatique n’existe pas encore.`
- `join`: `Signaler mon intérêt`
- `joined`: `Enregistré. Nous vous écrirons lorsque la bande de risque changera.`

**Spanish**
- `channelBody`: `El informe diario de riesgo se publica en un canal público y gratuito de Telegram. Sin registro y sin datos de contacto.`
- `channelCta`: `Abrir el canal de Telegram`
- `waitlistBody`: `Los cambios de banda son poco frecuentes. Deja un correo o usuario de Telegram para enterarte. Es un seguimiento manual: todavía no existe el envío automático.`
- `join`: `Registrar interés`
- `joined`: `Guardado. Te escribiremos cuando cambie la banda de riesgo.`

**Arabic**
- `channelBody`: `يُنشر تقرير المخاطر اليومي في قناة Telegram عامة ومجانية. بدون تسجيل وبدون بيانات اتصال.`
- `channelCta`: `فتح قناة Telegram`
- `waitlistBody`: `تغيّر النطاق نادر. اترك بريدا إلكترونيا أو معرف Telegram لتعرف بذلك. هذه متابعة يدوية — لا يوجد إرسال تلقائي بعد.`
- `join`: `تسجيل الاهتمام`
- `joined`: `تم الحفظ. سنتواصل معك عند تغيّر نطاق المخاطر.`

> **Have a native speaker check `zh`, `de`, `fr`, `es` and `ar` before merge.** These were written without native review, and this copy is the product's most visible promise.

In `App.tsx`, render `channelBody` and a channel link styled as a primary action above the existing form, and change `source: 'landing'` at line 478 to `source: 'risk_band_alert'`. The link carries `target="_blank"`, `rel="noreferrer"` and `dir="ltr"` on its URL, matching the footer links added earlier.

Keep unchanged: contact validation, server-side storage, rate limiting, Turnstile, and the `Cache-Control: no-store` behaviour.

- [ ] **Step 4: Run the checks**

Run: `npm test --prefix frontend`
Expected: PASS.

Run: `npm run build --prefix frontend`
Expected: build succeeds.

Run: `npm run smoke --prefix frontend`
Expected: PASS, including no horizontal overflow at the 390px viewport and correct RTL behaviour for Arabic.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/locales.ts frontend/src/App.tsx frontend/src/App.css frontend/src/App.test.tsx frontend/src/locales.test.ts
git commit -m "feat: point the daily-signal CTA at the telegram channel"
```

---

## Verification Summary

All six must pass before this branch is proposed for merge:

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
npm run smoke --prefix frontend
./scripts/manage.sh validate
mkdocs build --strict
```

## Operator Steps After Merge

Not part of this plan; recorded so nothing is lost.

1. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID=@bitcoinriskbrief` to the server `.env`.
2. Run `./scripts/manage.sh migrate` so `004_telegram_posts.sql` is applied.
3. Deploy through the USB kit.
4. Watch the first scheduled collector run and confirm exactly one post appears.

## Out Of Scope

- Direct bot delivery to individual users, and any Telegram group — that is #52.
- Email delivery, consent, double opt-in, unsubscribe — also #52.
- Multi-locale channel posts; the first pass is English only.
- Back-filling historical observations into the channel.
- Any change to risk methodology, band thresholds, or the collector's data paths.
