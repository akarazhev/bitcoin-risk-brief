# Channel Post Report Date Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Telegram post agree with the product page — same date vocabulary, same ISO format, never announcing an observation that has fallen behind — and fix a wrong band name in the published text.

**Architecture:** Two files in the collector. `publisher.py` gains one gate; `daily_post.py` changes its date formatting and the band-boundary line. Nothing else moves.

**Tech Stack:** Python 3.13, `unittest`.

## Global Constraints

- No new dependency, no schema change, no migration.
- No change to risk methodology, band thresholds, the readiness rule, or the claim-then-confirm protocol.
- An empty `TELEGRAM_BOT_TOKEN` must still disable publication before any database read.
- **Never make a real outbound Telegram request.** The channel is public and live. Every test uses `AsyncMock` or `httpx.MockTransport`.
- Every post keeps the analytics-not-advice line and the `bitcoinriskbrief.minihub.app` link.
- English only; the channel is not localised.

## Why

The product page shows this trust block:

```
Report date            2026-08-11
Readiness              ready
Validation passed
Latest completed day   2026-08-10
Freshness              current
Coverage through       2026-08-10
```

The channel posted `Bitcoin Risk Brief — 10 August 2026`. Both statements are true and they disagree on sight: the page headlines the **report date**, the post headlines the **covered day**, and the formats differ. A reader comparing the two has to work out that nothing is wrong.

Three defects follow from that, and one is a correctness bug in published text.

---

### Task 1: Do not publish an observation that has fallen behind

**Files:**
- Modify: `collector/collector/publisher.py`
- Test: `collector/tests/test_publisher.py`

**Interfaces:**
- Consumes: `last_completed_utc_day` from `collector.csv_refresh`.
- Produces: no signature change. `publish_daily_post(pool, *, now=None)` gains one gate.

**The defect.** The publisher's only freshness gate is `readiness['status'] != 'ready'`. Readiness tolerates data up to `DATA_FRESHNESS_MAX_AGE_DAYS` old, which defaults to **two days**. So a two-day-old observation can be announced as if it were the news of the day, and the report date derived in Task 2 would then land on yesterday rather than today.

The page can afford that tolerance because it shows its own freshness state beside the number and the reader sees both at once. A channel post is read on its own, hours later, with no such context.

- [ ] **Step 1: Write the failing test**

Append to `collector/tests/test_publisher.py`, using the existing `enabled()` and `repository()` helpers:

```python
    async def test_does_not_publish_an_observation_that_is_two_days_old(self) -> None:
        send = AsyncMock(return_value=4242)
        patches = repository()
        # LATEST covers 2026-08-09; "now" is 2026-08-11, so the last completed
        # UTC day is 2026-08-10 and the observation has fallen a day behind.
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for p in patches:
                p.start()
            try:
                published = await publisher.publish_daily_post(
                    object(), now=datetime(2026, 8, 11, 3, 0, tzinfo=timezone.utc)
                )
            finally:
                for p in patches:
                    p.stop()

        self.assertFalse(published)
        send.assert_not_awaited()

    async def test_publishes_when_the_observation_is_the_last_completed_day(self) -> None:
        send = AsyncMock(return_value=4242)
        patches = repository()
        with enabled(), patch.object(publisher, 'send_channel_post', send):
            for p in patches:
                p.start()
            try:
                published = await publisher.publish_daily_post(
                    object(), now=datetime(2026, 8, 10, 3, 0, tzinfo=timezone.utc)
                )
            finally:
                for p in patches:
                    p.stop()

        self.assertTrue(published)
        self.assertEqual(1, send.await_count)
```

`LATEST` in that file covers `2026-08-09`. The first test passes `now` on the 11th, so the last completed UTC day is the 10th and the observation is behind. The second passes `now` on the 10th, so the observation *is* the last completed day.

**Every existing publisher test must gain an explicit `now`.** None of them passes one today, so they read the real
wall clock through `build_readiness_payload`. The `LATEST` fixture covers `2026-08-09`; on 2026-08-11 that is exactly
two days old, which `DATA_FRESHNESS_MAX_AGE_DAYS=2` still accepts. One day later the age becomes three, readiness stops
being ready, and the three tests asserting `assertTrue(published)` fail on their own — with no code change and no
obvious cause.

They are time bombs with about a day left. Task 1's gate forces the fix, which is the right outcome: pass
`now=datetime(2026, 8, 10, 3, 0, tzinfo=timezone.utc)` to every test that expects publication, so the suite stops
depending on the date it is run.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_publisher -v`
Expected: FAIL — the stale observation publishes.

- [ ] **Step 3: Add the gate**

In `collector/collector/publisher.py`, import the helper the collector already owns:

```python
from collector.csv_refresh import last_completed_utc_day
```

After `as_of` is derived and **before** `claim_telegram_post`, add:

```python
    if as_of != last_completed_utc_day(now):
        logger.info(
            'telegram_publish_skipped reason=observation_behind as_of=%s expected=%s',
            as_of.isoformat(),
            last_completed_utc_day(now).isoformat(),
        )
        return False
```

Placing it before the claim matters: a behind observation must not consume the date, or a later run that catches up would find it already claimed and stay silent.

- [ ] **Step 4: Run the checks**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_publisher -v`
Expected: PASS.

Run: `./scripts/manage.sh test-python`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add collector/collector/publisher.py collector/tests/test_publisher.py
git commit -m "fix: skip channel posts for observations that fell behind"
```

---

### Task 2: Match the page's date vocabulary, and name the right band

**Files:**
- Modify: `collector/collector/daily_post.py`
- Test: `collector/tests/test_daily_post.py`

**Interfaces:**
- Produces: `compose_daily_post` keeps its signature. `band_boundary` keeps its signature. A new helper names the band entered at a boundary.

**Two defects.**

*Dates.* The post writes `10 August 2026` where the page writes `2026-08-10`, and it headlines the covered day where the page headlines the report date. The page derives the report date as the covered day plus one, which is exactly what Task 1's gate now guarantees to be today.

*The band name is hardcoded.* The boundary line reads `Neutral band begins at risk {boundary}` whatever the boundary is. In the `neutral` state with risk near `0.70`, `band_boundary` returns `0.70` and the post says *"Neutral band begins at risk 0.70"* — but at `0.66` the reader is already in neutral, and `0.70` is where **high** begins. The published sentence is wrong.

- [ ] **Step 1: Write the failing test**

Append to `collector/tests/test_daily_post.py`:

```python
class ReportDateTests(unittest.TestCase):
    def test_the_headline_carries_the_report_date_one_day_after_coverage(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=risk_row("2026-08-09", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertTrue(text.startswith("Bitcoin Risk Brief — report date 2026-08-11"))

    def test_every_date_is_iso(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=risk_row("2026-08-09", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Change: +0.03 from 2026-08-09", text)
        self.assertIn("Coverage through 2026-08-10", text)
        for month in ("January", "August", "December"):
            self.assertNotIn(month, text)

    def test_a_band_change_headline_also_carries_the_report_date(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.31, "neutral"),
            previous=risk_row("2026-08-09", 0.29, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertTrue(
            text.startswith("Bitcoin risk moved from low to neutral — report date 2026-08-11")
        )

    def test_a_report_date_crossing_a_month_end_is_correct(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-31", 0.24, "low"),
            previous=risk_row("2026-08-30", 0.21, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("report date 2026-09-01", text)


class BandNameTests(unittest.TestCase):
    def test_from_low_the_next_band_is_neutral(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.24, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Neutral band at risk 0.30", text)

    def test_from_neutral_near_the_upper_edge_the_next_band_is_high(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.66, "neutral"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("High band at risk 0.70", text)
        self.assertNotIn("Neutral band at risk 0.70", text)

    def test_from_neutral_near_the_lower_edge_the_next_band_is_low(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.34, "neutral"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Low band at risk 0.30", text)

    def test_from_high_the_next_band_is_neutral(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-10", 0.82, "high"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Neutral band at risk 0.70", text)
```

Existing tests in this file assert `"9 August 2026"`, `"Bitcoin Risk Brief — 1 August 2026"`, `"Neutral band begins at"` and similar. Update them to the new format rather than deleting them; the assertion that no boundary line appears when the level snapshot is missing must keep working.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Expected: FAIL — the headline still reads `Bitcoin Risk Brief — 10 August 2026`.

- [ ] **Step 3: Change the formatting and the band name**

In `collector/collector/daily_post.py`:

- delete `_MONTH_NAMES` and rewrite `_format_day` to return `parsed.strftime("%Y-%m-%d")`, keeping its existing handling of `datetime`, `date`, and ISO strings;
- add a helper that returns the report date as the covered day plus one, using `datetime.timedelta(days=1)` on the parsed date;
- add a helper that names the band entered at a boundary, given the current state and that boundary:

  | State | Boundary | Band entered |
  | --- | --- | --- |
  | `low` | `0.30` | `Neutral` |
  | `neutral` | `0.30` | `Low` |
  | `neutral` | `0.70` | `High` |
  | `high` | `0.70` | `Neutral` |

- use it in the boundary line, which becomes `f"{band} band at risk {boundary:.2f} — model price ${price:,.0f}"`.

The resulting post:

```text
Bitcoin Risk Brief — report date 2026-08-11

Risk 0.24 — low
Change: +0.03 from 2026-08-09
Neutral band at risk 0.30 — model price $74,098
Coverage through 2026-08-10 · crypto-scout-canonical-v1.1

bitcoinriskbrief.minihub.app

Analytics and research context, not financial advice.
```

`Data: fresh through …` becomes `Coverage through …`, matching the page's own label. The freshness claim is dropped from the text because Task 1 now guarantees it structurally — the post only exists when the observation is the last completed day.

On a band-change day the first line becomes
`Bitcoin risk moved from low to neutral — report date 2026-08-11`.

- [ ] **Step 4: Run the checks**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Expected: PASS.

Run: `./scripts/manage.sh test-python`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add collector/collector/daily_post.py collector/tests/test_daily_post.py
git commit -m "fix: use the page's date vocabulary and name the right band"
```

---

## Verification Summary

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
./scripts/manage.sh validate
mkdocs build --strict
```

The frontend is untouched, but run its checks anyway to prove that.

## Update The Design

`docs/superpowers/specs/2026-08-07-telegram-channel-honest-cta-design.md` shows the old post shape in its **Post Content** section and describes the boundary line as always naming the neutral band. Update both to match what ships, in the same branch.

## Out Of Scope

- Localising the channel; posts stay English.
- Any change to the readiness rule, `DATA_FRESHNESS_MAX_AGE_DAYS`, or the page.
- Back-filling or editing posts already published to the channel.
