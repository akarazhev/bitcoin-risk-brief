# Channel Post Price Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the daily post carry the price the risk value describes, and stop the change line from implying a gap that is not there.

**Architecture:** One file, `collector/collector/daily_post.py`, plus its tests. No other module changes. No schema, configuration, or dependency change.

**Tech Stack:** Python 3.13, `unittest`.

## Global Constraints

- **Never make a real outbound Telegram request.** The channel is public and live. Tests use `AsyncMock` or `httpx.MockTransport`.
- No new dependency, no migration, no configuration.
- No change to the publisher's gates, to the readiness rule, or to band thresholds.
- **No status emoji.** The existing test enforcing this stays.
- Only `<b>` and `<i>` tags. The existing tag-count test stays; update its expected counts only if the count genuinely changes.
- English only.
- Every post keeps the `bitcoinriskbrief.minihub.app` link and the analytics-not-advice line.

## Why

The post gives a boundary price with nothing to measure it against. Today it reads `Neutral band at risk 0.30 — model price $74,560` while the actual model price is `$63,724` — a seventeen per cent distance the reader cannot see.

And the change line reads `Change: −0.01 from 2026-08-10` beside `Coverage through 2026-08-11`. Both are correct, and together they look like a one-day gap that does not exist: the previous observation simply *is* the day before.

Live values used throughout this plan, from `/api/risk/latest` on 2026-08-12:

```
risk 0.2307 low · model_price 63723.6756287 · low 63185.473624 · high 64433.6799244 · timestamp 2026-08-11
```

## Target Output

```text
<b>Bitcoin Risk Brief</b> — report date 2026-08-12

<b>Risk 0.23 — low</b>
Change: −0.01
Model price $63,724 · HLC3, not a spot quote
Low $63,185 · High $64,434
Neutral band at risk 0.30 · $74,560
Coverage through 2026-08-11 · crypto-scout-canonical-v1.1

bitcoinriskbrief.minihub.app

<i>Analytics and research context, not financial advice.</i>
```

`Low` and `High` use the labels the product page already uses, as `report date` does.

The boundary line drops the words `model price` so the phrase means one thing in the post.

---

### Task 1: Show the comparison date only when it is not yesterday

**Files:**
- Modify: `collector/collector/daily_post.py`
- Test: `collector/tests/test_daily_post.py`

**Interfaces:**
- Produces: a private helper deciding whether two observations are consecutive days. `compose_daily_post` keeps its signature.

**Why conditional rather than simply removed.** For a daily series the delta is unambiguously day-over-day, so the date only invites arithmetic. But the publisher now refuses to post an observation that has fallen behind, which means a skipped day is possible and does not self-heal. After a skip the previous observation is two or more days back, and a bare `Change: −0.01` would silently compare across that gap.

Silent when normal, explicit when not — the same rule the readiness gate follows.

- [ ] **Step 1: Write the failing test**

Append to `collector/tests/test_daily_post.py`:

```python
class ChangeLineTests(unittest.TestCase):
    def test_consecutive_days_omit_the_comparison_date(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-11", 0.23, "low"),
            previous=risk_row("2026-08-10", 0.24, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Change: −0.01\n", text)
        self.assertNotIn("from 2026-08-10", text)

    def test_a_gap_names_the_day_being_compared(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-11", 0.23, "low"),
            previous=risk_row("2026-08-09", 0.24, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertIn("Change: −0.01 from 2026-08-09", text)

    def test_a_month_boundary_still_counts_as_consecutive(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-09-01", 0.23, "low"),
            previous=risk_row("2026-08-31", 0.24, "low"),
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("from 2026-08-31", text)

    def test_no_previous_observation_still_omits_the_change_line(self) -> None:
        text = compose_daily_post(
            latest=risk_row("2026-08-11", 0.23, "low"),
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )
        self.assertNotIn("Change:", text)
```

Existing tests assert `Change: +0.03 from 2026-08-09` and similar. Their fixtures use consecutive days, so update them to the bare form rather than deleting them.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Expected: FAIL — the date is always present.

- [ ] **Step 3: Add the condition**

Add a helper beside `_format_day` that returns whether the previous observation is exactly one day before the latest, comparing dates rather than timestamps so a time component cannot affect the answer. Use `datetime.timedelta(days=1)`; do not subtract day numbers, which breaks across month and year boundaries.

Then in `compose_daily_post`:

```python
    if previous is not None:
        delta = latest_risk - float(previous["risk"])
        line = f"Change: {_signed_delta(delta)}"
        if not _is_previous_day(previous["timestamp"], latest["timestamp"]):
            line += f" from {_format_day(previous['timestamp'])}"
        lines.append(line)
```

- [ ] **Step 4: Run the checks**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Run: `./scripts/manage.sh test-python`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add collector/collector/daily_post.py collector/tests/test_daily_post.py
git commit -m "fix: name the comparison day only when it is not yesterday"
```

---

### Task 2: Add the model price and the day's range

**Files:**
- Modify: `collector/collector/daily_post.py`
- Test: `collector/tests/test_daily_post.py`

**Interfaces:**
- `compose_daily_post` keeps its signature and starts reading `model_price_usd`, `low_usd` and `high_usd` from `latest`.

**Where the values come from.** `fetch_latest_risk` already returns all three, and the publisher already passes that row as `latest`. Nothing new is fetched.

**Both new lines disappear when their data is missing.** `low_usd` and `high_usd` are nullable by contract — `docs/engineering/api-reference.md` states that when the matching OHLCV row is absent they are `null` and clients must hide them rather than show zeroes. `model_price_usd` gets the same treatment. This is the third place in the post where absent data means silence rather than a substitute, alongside the boundary line and the change line.

**The spot-price qualification is not optional.** A dollar figure beside the word Bitcoin reads as the price of Bitcoin. The model price is HLC3 of the completed daily candle, and the post is read on its own with no page around it to explain that. `· HLC3, not a spot quote` stays on the line.

- [ ] **Step 1: Write the failing test**

Extend the `risk_row` helper with optional price fields, so existing three-argument calls keep working:

```python
def risk_row(
    day: str,
    risk: float,
    state: str,
    *,
    model_price: float | None = None,
    low: float | None = None,
    high: float | None = None,
) -> dict:
    return {
        "timestamp": datetime.fromisoformat(day).replace(tzinfo=timezone.utc),
        "risk": risk,
        "risk_state": state,
        "model_price_usd": model_price,
        "low_usd": low,
        "high_usd": high,
    }
```

Then append:

```python
class PriceContextTests(unittest.TestCase):
    def _post(self, **overrides) -> str:
        row = risk_row(
            "2026-08-11", 0.23, "low",
            model_price=63723.6756287, low=63185.473624, high=64433.6799244,
        )
        row.update(overrides)
        return compose_daily_post(
            latest=row,
            previous=None,
            levels=LEVELS,
            methodology_version="crypto-scout-canonical-v1.1",
        )

    def test_the_model_price_is_shown_and_qualified(self) -> None:
        text = self._post()
        self.assertIn("Model price $63,724 · HLC3, not a spot quote", text)

    def test_the_day_range_uses_the_page_labels(self) -> None:
        self.assertIn("Low $63,185 · High $64,434", self._post())

    def test_a_missing_model_price_omits_its_line(self) -> None:
        text = self._post(model_price_usd=None)
        self.assertNotIn("Model price", text)
        self.assertIn("Low $63,185", text)

    def test_a_missing_low_omits_the_whole_range_line(self) -> None:
        text = self._post(low_usd=None)
        self.assertNotIn("Low ", text)
        self.assertNotIn("High ", text)
        self.assertIn("Model price", text)

    def test_a_missing_high_omits_the_whole_range_line(self) -> None:
        text = self._post(high_usd=None)
        self.assertNotIn("High ", text)
        self.assertNotIn("Low ", text)

    def test_the_boundary_line_no_longer_says_model_price(self) -> None:
        text = self._post()
        self.assertIn("Neutral band at risk 0.30 · $74,560", text)
        # Case-insensitive on purpose: the old boundary line said "model price"
        # in lower case, so a case-sensitive count would pass either way.
        self.assertEqual(1, text.lower().count("model price"))

    def test_prices_carry_no_decimals_and_use_separators(self) -> None:
        text = self._post()
        for fragment in ("$63,724", "$63,185", "$64,434"):
            self.assertIn(fragment, text)
        self.assertNotIn(".67", text)
```

The last two matter: the first guards against `model price` meaning two different things in one post, the second against a raw float reaching a reader.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Expected: FAIL — no price lines exist.

- [ ] **Step 3: Add the lines**

After the change line and before the boundary line, append the model price when `model_price_usd` is present, then the range when **both** `low_usd` and `high_usd` are present. Format every price with thousands separators and no decimals, as the boundary line already does.

Change the boundary line to `f"{band} band at risk {boundary:.2f} · ${price:,.0f}"`.

- [ ] **Step 4: Run the checks**

Run: `PYTHONPATH=backend:collector python -m unittest collector.tests.test_daily_post -v`
Run: `./scripts/manage.sh test-python`
Expected: PASS.

Then print one post for each shape and put them in the report: full data; missing model price; missing range; and a gap in the change line.

- [ ] **Step 5: Commit**

```bash
git add collector/collector/daily_post.py collector/tests/test_daily_post.py
git commit -m "feat: show the model price and the day's range in the post"
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

Only the collector changes — run the rest to prove it.

## Update The Design

`docs/superpowers/specs/2026-08-07-telegram-channel-honest-cta-design.md` shows the post shape in its **Post Content** section and describes the boundary line as carrying a model price. Update both to match what ships, in the same branch.

## Out Of Scope

- Any change to the publisher, its gates, or the readiness rule.
- Localising the post.
- Editing posts already published to the channel.
- Adding the closing price, which the API does not return.
