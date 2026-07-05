# Price Model Input OHLC Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the latest completed daily candle's HLC3 model price together with that candle's low and high in the first viewport, while keeping `price_usd` as the backwards-compatible HLC3 alias.

**Architecture:** Keep the risk methodology and stored schema unchanged. Build `/api/risk/latest` from the latest `btc_risk_daily` row plus a same-timestamp `btc_ohlcv_daily` row, then render a compact three-value price input group in the existing metrics strip when low/high are available. If the OHLCV row is missing, keep the latest risk payload usable and hide Low/High in the UI instead of showing stale or zero values.

**Tech Stack:** FastAPI, asyncpg, Python 3.13 `unittest`, React, TypeScript, Vite, Vitest, Testing Library, Playwright smoke tests, Markdown API docs.

---

## Context

- Production deploy is unavailable for this work.
- Local cache warmup and USB kit v2 work are complete.
- This is a local API/UI polish implementation plan only. Do not implement it while creating this plan.
- Do not commit or push during this work unless the operator gives a separate explicit command.
- `docs/superpowers/specs/2026-07-01-price-model-input-ohlc-display-design.md` says `price_usd` currently serializes `btc_risk_daily.price_hlc3`; this must remain true.
- `migrations/001_initial_schema.sql` already has the required columns: `btc_risk_daily.timestamp`, `btc_risk_daily.price_hlc3`, `btc_ohlcv_daily.timestamp`, `btc_ohlcv_daily.low_usd`, and `btc_ohlcv_daily.high_usd`. No migration is needed.

## Exact Files Likely To Change

- Modify: `backend/app/repository.py`
  - Add a latest-risk serializer that keeps `price_usd` as the HLC3 alias, adds `model_price_usd`, and attaches `low_usd`/`high_usd` from a same-timestamp OHLCV row.
  - Change only `fetch_latest_risk()` to use the OHLCV pairing; leave historical risk queries unchanged.
- Modify: `backend/tests/test_repository.py`
  - Add repository tests proving same-timestamp OHLCV pairing and missing-OHLCV fallback behavior.
- Modify: `backend/tests/test_public_cache_warmup.py`
  - Add a latest-payload producer regression test proving the public `/api/risk/latest` envelope keeps the additive fields.
- Modify: `docs/api-reference.md`
  - Document `model_price_usd`, nullable `low_usd`, nullable `high_usd`, and the unchanged meaning of `price_usd`.
- Modify: `frontend/src/types.ts`
  - Add nullable optional `model_price_usd`, `low_usd`, and `high_usd` fields to `RiskPoint`.
- Modify: `frontend/src/App.tsx`
  - Add EN/RU labels and render the grouped model price, low, and high values in the first metric cell.
- Modify: `frontend/src/App.css`
  - Add stable nested grid styles for the price metric and mobile wrapping with no horizontal overflow.
- Modify: `frontend/src/App.test.tsx`
  - Add focused render tests for present and missing OHLC fields, EN/RU labels, and CSS/mobile layout hooks.
- Modify: `frontend/e2e/frontend-quality.spec.ts`
  - Add OHLC fields to mocked latest risk data and assert the first-viewport price group still has no horizontal overflow.

Read-only references during implementation:

- `backend/app/main.py`
- `backend/app/risk.py`
- `frontend/src/api.ts`
- `docs/risk-methodology.md`

## Non-Goals

- No methodology change; `crypto-scout-canonical-v1` and HLC3 calculation stay unchanged.
- No live intraday values.
- No `Close` value in the first metric group.
- No `/api/risk/history` shape change for this polish pass.
- No database migration.
- No API breaking change; `price_usd` remains an HLC3 alias.
- No commit or push unless the operator gives a separate explicit command.

## Task 1: Pair Latest Risk With Matching OHLCV Row

**Files:**

- Modify: `backend/tests/test_repository.py`
- Modify: `backend/app/repository.py`

- [ ] **Step 1: Add failing repository tests**

Add `fetch_latest_risk` to the import in `backend/tests/test_repository.py`:

```python
from app.repository import fetch_latest_risk, fetch_ohlcv_history, fetch_public_data_version
```

Add this fake pool and test class below `FakeVersionPool`:

```python
class FakeLatestRiskPool:
    def __init__(self, row) -> None:
        self.row = row
        self.query = ""
        self.params = ()

    async def fetchrow(self, query: str, *params):
        self.query = query
        self.params = params
        return self.row


def latest_risk_row(**overrides):
    row = {
        "timestamp": datetime(2026, 6, 26, tzinfo=timezone.utc),
        "price_hlc3": 100_000.0,
        "risk": 0.7,
        "score": 1.0,
        "risk_state": "high",
        "trend_dev": 0.2,
        "vol_regime": 0.1,
        "turnover": None,
        "z_trend_dev": 1.1,
        "z_vol_regime": 0.8,
        "z_turnover": None,
        "turnover_enabled": False,
        "low_usd": 96_500.0,
        "high_usd": 104_250.0,
    }
    row.update(overrides)
    return row


class LatestRiskRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_latest_risk_pairs_matching_ohlcv_by_timestamp(self) -> None:
        pool = FakeLatestRiskPool(latest_risk_row())

        latest = await fetch_latest_risk(pool)

        self.assertIsNotNone(latest)
        self.assertEqual(latest["price_usd"], 100_000.0)
        self.assertEqual(latest["model_price_usd"], 100_000.0)
        self.assertEqual(latest["low_usd"], 96_500.0)
        self.assertEqual(latest["high_usd"], 104_250.0)
        self.assertIn("LEFT JOIN btc_ohlcv_daily", pool.query)
        self.assertIn("o.timestamp = r.timestamp", pool.query)
        self.assertEqual(pool.params, ())

    async def test_fetch_latest_risk_returns_null_ohlcv_values_when_match_is_missing(self) -> None:
        pool = FakeLatestRiskPool(latest_risk_row(low_usd=None, high_usd=None))

        latest = await fetch_latest_risk(pool)

        self.assertIsNotNone(latest)
        self.assertEqual(latest["price_usd"], 100_000.0)
        self.assertEqual(latest["model_price_usd"], 100_000.0)
        self.assertIsNone(latest["low_usd"])
        self.assertIsNone(latest["high_usd"])
```

- [ ] **Step 2: Run the focused repository tests and confirm they fail**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_repository.py' -v
```

Expected: FAIL because `fetch_latest_risk()` does not join `btc_ohlcv_daily` and does not return `model_price_usd`, `low_usd`, or `high_usd`.

- [ ] **Step 3: Implement latest-risk serialization without changing history rows**

In `backend/app/repository.py`, add these helpers below `_serialize_row`:

```python
def _optional_float(row: asyncpg.Record, key: str) -> float | None:
    try:
        value = row[key]
    except (KeyError, IndexError):
        return None
    return float(value) if value is not None else None


def _serialize_latest_risk_row(row: asyncpg.Record) -> dict[str, Any]:
    payload = _serialize_row(row)
    payload["model_price_usd"] = payload["price_usd"]
    payload["low_usd"] = _optional_float(row, "low_usd")
    payload["high_usd"] = _optional_float(row, "high_usd")
    return payload
```

Change `fetch_latest_risk()` to use a left join from latest risk to same-timestamp OHLCV:

```python
async def fetch_latest_risk(pool: asyncpg.Pool) -> dict[str, Any] | None:
    row = await pool.fetchrow(
        """
        SELECT
          r.*,
          o.low_usd,
          o.high_usd
        FROM btc_risk_daily r
        LEFT JOIN btc_ohlcv_daily o ON o.timestamp = r.timestamp
        ORDER BY r.timestamp DESC
        LIMIT 1
        """
    )
    return _serialize_latest_risk_row(row) if row else None
```

This keeps `fetch_previous_risk()` and `fetch_risk_history()` on `_serialize_row()`, so the polish pass does not broaden `/api/risk/history`.

- [ ] **Step 4: Run the repository tests and confirm they pass**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_repository.py' -v
```

Expected: PASS, including the new latest-risk pairing and fallback tests.

## Task 2: Preserve Latest API Envelope And Update API Reference

**Files:**

- Modify: `backend/tests/test_public_cache_warmup.py`
- Modify: `docs/api-reference.md`

- [ ] **Step 1: Add a failing latest payload regression test**

Add this test to `PublicPayloadSchemaRegressionTest` in `backend/tests/test_public_cache_warmup.py`:

```python
    async def test_risk_latest_payload_includes_model_price_and_daily_range(self) -> None:
        latest = {
            "timestamp": "2026-06-26T00:00:00+00:00",
            "price_usd": 100000.0,
            "model_price_usd": 100000.0,
            "low_usd": 96500.0,
            "high_usd": 104250.0,
            "risk": 0.7,
            "score": 1.0,
            "risk_state": "high",
            "trend_dev": 0.2,
            "vol_regime": 0.1,
            "turnover": None,
            "z_trend_dev": 1.1,
            "z_vol_regime": 0.8,
            "z_turnover": None,
            "turnover_enabled": False,
        }

        async def fake_latest(_pool):
            return latest

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_latest_risk", fake_latest)

        payload, status = await main._produce_risk_latest_payload()

        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["price_usd"], payload["data"]["model_price_usd"])
        self.assertEqual(payload["data"]["low_usd"], 96500.0)
        self.assertEqual(payload["data"]["high_usd"], 104250.0)
```

- [ ] **Step 2: Run the focused public payload tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache_warmup.py' -v
```

Expected after Task 1: PASS. If this fails, the latest producer is stripping or reshaping the repository payload and must be fixed before frontend work.

- [ ] **Step 3: Update `docs/api-reference.md`**

In the `GET /api/risk/latest` section, replace the planned-field note with direct documentation:

```markdown
`price_usd` is the HLC3 model price from the latest completed daily candle, not a spot price or close-only value.
`model_price_usd` is the explicit name for the same value. `low_usd` and `high_usd` come from the `btc_ohlcv_daily`
row whose `timestamp` matches the latest risk row. If that OHLCV row is missing, `low_usd` and `high_usd` are `null`;
clients should hide those sub-values rather than showing zeroes or stale values.
```

Update the response example:

```json
{
  "data": {
    "timestamp": "2026-06-25T00:00:00+00:00",
    "price_usd": 60100.0,
    "model_price_usd": 60100.0,
    "low_usd": 58800.0,
    "high_usd": 61584.0,
    "risk": 0.3025,
    "score": -0.82,
    "risk_state": "low",
    "trend_dev": 0.0,
    "vol_regime": 0.0,
    "turnover": -10.2,
    "z_trend_dev": 0.0,
    "z_vol_regime": 0.0,
    "z_turnover": 0.0,
    "turnover_enabled": true
  }
}
```

- [ ] **Step 4: Re-run backend focused tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_repository.py' -v
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache_warmup.py' -v
```

Expected: PASS.

## Task 3: Render Model Price, Low, And High In The Frontend

**Files:**

- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css`
- Modify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add failing frontend render tests**

In the default `apiMocks.fetchLatestRisk.mockResolvedValue` payload in `frontend/src/App.test.tsx`, add:

```typescript
model_price_usd: 100000,
low_usd: 96500,
high_usd: 104250,
```

Add these tests near the existing metric tests:

```typescript
test('renders model price, low, and high when latest risk includes OHLC fields', async () => {
  render(<App />)

  expect(await screen.findByText('BTC price model input')).toBeInTheDocument()
  expect(screen.getByText('Model price')).toBeInTheDocument()
  expect(screen.getByText('Low')).toBeInTheDocument()
  expect(screen.getByText('High')).toBeInTheDocument()
  expect(screen.getByText('$100,000')).toBeInTheDocument()
  expect(screen.getByText('$96,500')).toBeInTheDocument()
  expect(screen.getByText('$104,250')).toBeInTheDocument()
})

test('hides low and high labels when the matching OHLCV values are missing', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: {
      timestamp: '2026-06-26T00:00:00Z',
      price_usd: 100000,
      model_price_usd: 100000,
      low_usd: null,
      high_usd: null,
      risk: 0.7,
      score: 1,
      risk_state: 'high',
      trend_dev: 1,
      vol_regime: 0.1,
      turnover: null,
      z_trend_dev: 1,
      z_vol_regime: 1,
      z_turnover: null,
      turnover_enabled: false,
    },
  })

  render(<App />)

  expect(await screen.findByText('Model price')).toBeInTheDocument()
  expect(screen.getByText('$100,000')).toBeInTheDocument()
  expect(screen.queryByText('Low')).not.toBeInTheDocument()
  expect(screen.queryByText('High')).not.toBeInTheDocument()
})

test('preserves English and Russian labels for the price input group', async () => {
  render(<App />)

  expect(await screen.findByText('Model price')).toBeInTheDocument()
  expect(screen.getByText('Low')).toBeInTheDocument()
  expect(screen.getByText('High')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: /ru/i }))

  expect(await screen.findByText('Цена модели')).toBeInTheDocument()
  expect(screen.getByText('Мин.')).toBeInTheDocument()
  expect(screen.getByText('Макс.')).toBeInTheDocument()
})

test('defines a stable responsive grid for the price input group', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.price-input-grid')
  expect(css).toContain('grid-template-columns: repeat(3, minmax(0, 1fr))')
  expect(css).toContain('@media (max-width: 560px)')
  expect(css).toContain('.price-input-grid')
})
```

- [ ] **Step 2: Run the focused frontend tests and confirm they fail**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected: FAIL because the UI still renders only `latest.price_usd` under the price metric.

- [ ] **Step 3: Update the RiskPoint type**

In `frontend/src/types.ts`, add nullable optional fields to `RiskPoint`:

```typescript
  model_price_usd?: number | null
  low_usd?: number | null
  high_usd?: number | null
```

- [ ] **Step 4: Add localized labels and derived values**

In `frontend/src/App.tsx`, add labels to both `copy.en` and `copy.ru`:

```typescript
    modelPrice: 'Model price',
    low: 'Low',
    high: 'High',
```

```typescript
    modelPrice: 'Цена модели',
    low: 'Мин.',
    high: 'Макс.',
```

Below `const methodologyVersion = readiness.data.methodology_version ?? 'unknown'`, derive safe display values:

```typescript
  const modelPriceUsd = latest.model_price_usd ?? latest.price_usd
  const hasDailyRange = typeof latest.low_usd === 'number' && typeof latest.high_usd === 'number'
```

- [ ] **Step 5: Replace the first metric cell with the grouped display**

Replace:

```tsx
        <div><span>{t.price}</span><strong>{formatUsd(latest.price_usd)}</strong></div>
```

with:

```tsx
        <div className="price-metric">
          <span>{t.price}</span>
          <div className={`price-input-grid ${hasDailyRange ? 'with-range' : 'model-only'}`}>
            <div className="price-input-value">
              <em>{t.modelPrice}</em>
              <strong>{formatUsd(modelPriceUsd)}</strong>
            </div>
            {hasDailyRange && (
              <>
                <div className="price-input-value">
                  <em>{t.low}</em>
                  <strong>{formatUsd(latest.low_usd as number)}</strong>
                </div>
                <div className="price-input-value">
                  <em>{t.high}</em>
                  <strong>{formatUsd(latest.high_usd as number)}</strong>
                </div>
              </>
            )}
          </div>
        </div>
```

- [ ] **Step 6: Add responsive CSS without changing the outer metrics strip contract**

In `frontend/src/App.css`, add near the `.metrics-strip` rules:

```css
.price-metric { min-width: 0; }
.price-input-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  align-items: start;
}
.price-input-grid.model-only { grid-template-columns: minmax(0, 1fr); }
.price-input-value { min-width: 0; display: grid; gap: 4px; }
.price-input-value strong { overflow-wrap: anywhere; }
```

Inside the existing `@media (max-width: 560px)` block, add:

```css
  .price-input-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .price-input-grid.with-range .price-input-value:first-child {
    grid-column: 1 / -1;
  }
```

The outer `.metrics-strip` continues to collapse to one column at `max-width: 900px`, so the nested price grid must not increase page width on mobile.

- [ ] **Step 7: Run the focused frontend tests and confirm they pass**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected: PASS.

## Task 4: Extend Browser Smoke Coverage For First-Viewport Layout

**Files:**

- Modify: `frontend/e2e/frontend-quality.spec.ts`

- [ ] **Step 1: Add OHLC fields to the mocked latest risk payload**

In `frontend/e2e/frontend-quality.spec.ts`, update `latestRisk.data`:

```typescript
    model_price_usd: 100000,
    low_usd: 96500,
    high_usd: 104250,
```

Because `riskLevels.meta.base` reuses `latestRisk.data`, the new additive fields will also appear in that mock base without changing assertions outside the first viewport.

- [ ] **Step 2: Assert the grouped values render in the smoke test**

In `renders desktop and mobile layouts with non-empty chart canvases`, add after the readiness assertion:

```typescript
  await expect(page.getByText('Model price')).toBeVisible()
  await expect(page.getByText('Low')).toBeVisible()
  await expect(page.getByText('High')).toBeVisible()
  await expect(page.getByText('$96,500')).toBeVisible()
  await expect(page.getByText('$104,250')).toBeVisible()
```

The existing `expectNoHorizontalOverflow(page)` assertion is the mobile and desktop no-overflow gate for this layout change.

- [ ] **Step 3: Run the smoke command when the UI layout is ready**

Run:

```bash
npm run smoke --prefix frontend
```

Expected: PASS across desktop Chromium/Firefox/WebKit and mobile Chrome/Safari projects with no horizontal overflow.

## Task 5: Full Verification

Run these checks before finalizing implementation work:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_repository.py' -v
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_public_cache_warmup.py' -v
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
npm run smoke --prefix frontend
git diff --check
```

Expected:

- Backend targeted tests pass and prove same-timestamp OHLCV pairing plus missing-match fallback.
- `./scripts/manage.sh test-python` passes all backend and collector unit tests.
- `npm test --prefix frontend` passes all Vitest tests.
- `npm run build --prefix frontend` passes TypeScript and Vite production build.
- `npm run smoke --prefix frontend` passes because the UI layout changed.
- `git diff --check` reports no whitespace errors.

## Implementation Handoff Notes

- Keep API behavior additive. Existing clients reading `price_usd` must continue to work without interpreting it differently.
- Use a `LEFT JOIN`, not an inner join, so a missing OHLCV row cannot hide the latest risk observation.
- Do not source Low/High from live spot or intraday data.
- Treat `low_usd: null` and `high_usd: null` as a display-suppression signal in the frontend.
- Avoid adding explanatory copy to the first viewport; the methodology section already explains HLC3.
- Keep the first metrics strip compact: no `Close`, no wick/shadow wording, and no card nested inside a card.
