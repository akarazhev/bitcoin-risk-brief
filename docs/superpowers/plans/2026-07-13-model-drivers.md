# Model Drivers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a localized, compact Model drivers block that explains the directional inputs behind the latest BTC risk without revealing `crypto-scout-canonical-v1` internals in the UI.

**Architecture:** Keep the change frontend-only. Derive plain-language driver statuses from `/api/risk/latest` component z-score fields already present in `RiskPoint`, render them below the brief and above the methodology/trust area, and avoid displaying raw component values, weights, windows, or formulas.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, CSS.

---

## File Structure

- Modify `frontend/src/App.tsx`
  - Add localized EN/RU copy for Model drivers.
  - Add small helper types/functions for driver status derivation.
  - Render the Model drivers section after the daily brief grid and before the methodology trust section.
- Modify `frontend/src/App.css`
  - Style the section as a compact, scannable block with three repeated driver items.
  - Keep responsive behavior stable on mobile.
- Modify `frontend/src/App.test.tsx`
  - Add focused tests for normal turnover-enabled data, turnover-disabled data, localization, and CSS layout.
- Do not modify backend, collector, database, risk formula, or API shape.
- Do not update `docs/api-reference.md` for this issue because the frontend already has the required fields: `trend_dev`, `vol_regime`, `turnover`, `z_trend_dev`, `z_vol_regime`, `z_turnover`, and `turnover_enabled`.

## Product Rules

- UI labels must be plain-language and novice-first.
- UI must not show raw `z_*` values, raw turnover, formula details, exact model weights, rolling windows, or thresholds.
- Trading activity must use turnover semantics, not raw USD volume.
- If turnover is missing or disabled, show `Unavailable` for Activity instead of `0`, `0%`, or any fake neutral value.
- The existing BTC price model input must remain limited to `Model price`, `Low`, and `High`.

## Driver Semantics

Use a display-only neutral band to prevent tiny normalized moves from becoming over-explained:

- `z > 0.25` -> `Raises risk`
- `z < -0.25` -> `Lowers risk`
- otherwise -> `Neutral`
- missing, non-finite, disabled turnover -> `Unavailable`

This neutral band is UI interpretation only. Do not expose it in copy.

---

### Task 1: Add Failing Frontend Tests

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Import the `RiskPoint` type**

At the top of `frontend/src/App.test.tsx`, add this import after the existing `App` import:

```tsx
import type { RiskPoint } from './types'
```

- [ ] **Step 2: Add test helpers**

After the existing `findPriceMetric()` helper, add:

```tsx
async function findModelDrivers(title = 'Model drivers') {
  const titleElement = await screen.findByRole('heading', { name: title })
  const section = titleElement.closest('.model-drivers')
  expect(section).not.toBeNull()
  return within(section as HTMLElement)
}
```

After the existing `deferred<T>()` helper, add:

```tsx
function latestRisk(overrides: Partial<RiskPoint> = {}): RiskPoint {
  return {
    timestamp: '2026-06-26T00:00:00Z',
    price_usd: 100000,
    model_price_usd: 100000,
    low_usd: 96500,
    high_usd: 104250,
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
    ...overrides,
  }
}
```

- [ ] **Step 3: Use the helper in the default latest-risk mock**

In `beforeEach()`, replace the current `apiMocks.fetchLatestRisk.mockResolvedValue(...)` call with:

```tsx
  apiMocks.fetchLatestRisk.mockResolvedValue({ data: latestRisk() })
```

- [ ] **Step 4: Add the normal and localized driver test**

Add this test near the existing price input tests:

```tsx
test('renders localized model drivers from latest risk component directions', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: latestRisk({
      turnover: -10.1,
      z_trend_dev: 0.8,
      z_vol_regime: -0.7,
      z_turnover: 0.05,
      turnover_enabled: true,
    }),
  })

  render(<App />)

  const drivers = await findModelDrivers()

  expect(drivers.getByText("Plain-language directions behind today's risk, based on the latest validated daily data.")).toBeInTheDocument()
  expect(drivers.getByText('Trend')).toBeInTheDocument()
  expect(drivers.getByText('Price vs long-term baseline')).toBeInTheDocument()
  expect(drivers.getByText('Raises risk')).toBeInTheDocument()
  expect(drivers.getByText('Volatility')).toBeInTheDocument()
  expect(drivers.getByText('Recent price swings')).toBeInTheDocument()
  expect(drivers.getByText('Lowers risk')).toBeInTheDocument()
  expect(drivers.getByText('Activity')).toBeInTheDocument()
  expect(drivers.getByText('Trading activity adjusted for market size')).toBeInTheDocument()
  expect(drivers.getByText('Neutral')).toBeInTheDocument()
  expect(drivers.queryByText('-10.1')).not.toBeInTheDocument()
  expect(drivers.queryByText('0.05')).not.toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: /ru/i }))

  const ruDrivers = await findModelDrivers('Драйверы модели')

  expect(ruDrivers.getByText('Понятные направления за сегодняшним риском по последним валидированным дневным данным.')).toBeInTheDocument()
  expect(ruDrivers.getByText('Тренд')).toBeInTheDocument()
  expect(ruDrivers.getByText('Цена относительно долгосрочной базы')).toBeInTheDocument()
  expect(ruDrivers.getByText('Повышает риск')).toBeInTheDocument()
  expect(ruDrivers.getByText('Волатильность')).toBeInTheDocument()
  expect(ruDrivers.getByText('Недавние колебания цены')).toBeInTheDocument()
  expect(ruDrivers.getByText('Снижает риск')).toBeInTheDocument()
  expect(ruDrivers.getByText('Активность')).toBeInTheDocument()
  expect(ruDrivers.getByText('Торговая активность с учетом размера рынка')).toBeInTheDocument()
  expect(ruDrivers.getByText('Нейтрально')).toBeInTheDocument()
})
```

- [ ] **Step 5: Add the turnover-disabled test**

Add this test near the normal driver test:

```tsx
test('marks trading activity unavailable when turnover is disabled', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: latestRisk({
      turnover: null,
      z_trend_dev: 0.1,
      z_vol_regime: 0.1,
      z_turnover: null,
      turnover_enabled: false,
    }),
  })

  render(<App />)

  const drivers = await findModelDrivers()

  expect(drivers.getByText('Activity')).toBeInTheDocument()
  expect(drivers.getByText('Unavailable')).toBeInTheDocument()
  expect(drivers.getByText('Market-adjusted activity unavailable')).toBeInTheDocument()
  expect(drivers.queryByText('0')).not.toBeInTheDocument()
  expect(drivers.queryByText('0%')).not.toBeInTheDocument()
})
```

- [ ] **Step 6: Add the CSS structure test**

Add this test near the existing CSS layout test:

```tsx
test('defines a stable responsive layout for model drivers', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.model-drivers')
  expect(css).toContain('grid-template-columns: minmax(220px, 0.65fr) minmax(0, 1fr)')
  expect(css).toContain('.driver-list')
  expect(css).toContain('grid-template-columns: repeat(3, minmax(0, 1fr))')
  expect(css).toContain('.driver-card.unavailable strong')
  expect(css).toContain('@media (max-width: 900px)')
})
```

- [ ] **Step 7: Run the targeted test and verify it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected: FAIL. The first useful failure should be unable to find the `Model drivers` heading or missing `.model-drivers` CSS.

---

### Task 2: Implement Driver Copy, Semantics, and Rendering

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add driver types**

In `frontend/src/App.tsx`, after `type ThresholdCallout = ...`, add:

```tsx
type DriverStatus = 'raises' | 'neutral' | 'lowers' | 'unavailable'
type ModelDriver = {
  id: 'trend' | 'volatility' | 'activity'
  label: string
  description: string
  status: DriverStatus
  statusLabel: string
}
```

- [ ] **Step 2: Add the display neutral band constant**

After `const ACCESSIBLE_HISTORY_POINTS = 6`, add:

```tsx
const DRIVER_NEUTRAL_BAND = 0.25
```

- [ ] **Step 3: Add English driver copy**

In the `copy.en` object, insert these keys after `riskChangeContext`:

```tsx
    modelDrivers: 'Model drivers',
    modelDriversBody: "Plain-language directions behind today's risk, based on the latest validated daily data.",
    driverTrend: 'Trend',
    driverTrendDetail: 'Price vs long-term baseline',
    driverVolatility: 'Volatility',
    driverVolatilityDetail: 'Recent price swings',
    driverActivity: 'Activity',
    driverActivityDetail: 'Trading activity adjusted for market size',
    driverActivityUnavailableDetail: 'Market-adjusted activity unavailable',
    driverRaises: 'Raises risk',
    driverNeutral: 'Neutral',
    driverLowers: 'Lowers risk',
    driverUnavailable: 'Unavailable',
```

- [ ] **Step 4: Add Russian driver copy**

In the `copy.ru` object, insert these keys after `riskChangeContext`:

```tsx
    modelDrivers: 'Драйверы модели',
    modelDriversBody: 'Понятные направления за сегодняшним риском по последним валидированным дневным данным.',
    driverTrend: 'Тренд',
    driverTrendDetail: 'Цена относительно долгосрочной базы',
    driverVolatility: 'Волатильность',
    driverVolatilityDetail: 'Недавние колебания цены',
    driverActivity: 'Активность',
    driverActivityDetail: 'Торговая активность с учетом размера рынка',
    driverActivityUnavailableDetail: 'Активность с учетом размера рынка недоступна',
    driverRaises: 'Повышает риск',
    driverNeutral: 'Нейтрально',
    driverLowers: 'Снижает риск',
    driverUnavailable: 'Недоступно',
```

- [ ] **Step 5: Add status helper functions**

After `function stateLabel(...)`, add:

```tsx
function driverStatusFromZScore(value: number | null | undefined): DriverStatus {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'unavailable'
  if (value > DRIVER_NEUTRAL_BAND) return 'raises'
  if (value < -DRIVER_NEUTRAL_BAND) return 'lowers'
  return 'neutral'
}

function driverStatusLabel(status: DriverStatus, labels: typeof copy[Locale]) {
  if (status === 'raises') return labels.driverRaises
  if (status === 'lowers') return labels.driverLowers
  if (status === 'unavailable') return labels.driverUnavailable
  return labels.driverNeutral
}

function buildModelDrivers(latest: RiskPoint, labels: typeof copy[Locale]): ModelDriver[] {
  const activityAvailable = latest.turnover_enabled
    && typeof latest.turnover === 'number'
    && Number.isFinite(latest.turnover)
    && typeof latest.z_turnover === 'number'
    && Number.isFinite(latest.z_turnover)
  const activityStatus = activityAvailable ? driverStatusFromZScore(latest.z_turnover) : 'unavailable'

  const drivers: Array<Omit<ModelDriver, 'statusLabel'>> = [
    {
      id: 'trend',
      label: labels.driverTrend,
      description: labels.driverTrendDetail,
      status: driverStatusFromZScore(latest.z_trend_dev),
    },
    {
      id: 'volatility',
      label: labels.driverVolatility,
      description: labels.driverVolatilityDetail,
      status: driverStatusFromZScore(latest.z_vol_regime),
    },
    {
      id: 'activity',
      label: labels.driverActivity,
      description: activityAvailable ? labels.driverActivityDetail : labels.driverActivityUnavailableDetail,
      status: activityStatus,
    },
  ]

  return drivers.map((driver) => ({
    ...driver,
    statusLabel: driverStatusLabel(driver.status, labels),
  }))
}
```

- [ ] **Step 6: Build the drivers in the component**

In `App()`, after `const chartCurrentSummary = ...`, add:

```tsx
  const modelDrivers = buildModelDrivers(latest, t)
```

- [ ] **Step 7: Render the Model drivers section**

In the returned JSX, insert this section immediately after the closing `</section>` for `brief-grid` and before the `methodology` section:

```tsx
      <section className="model-drivers" aria-labelledby="model-drivers-heading">
        <div className="model-drivers-copy">
          <h2 id="model-drivers-heading">{t.modelDrivers}</h2>
          <p>{t.modelDriversBody}</p>
        </div>
        <div className="driver-list">
          {modelDrivers.map((driver) => (
            <article className={`driver-card ${driver.status}`} key={driver.id}>
              <span>{driver.label}</span>
              <strong>{driver.statusLabel}</strong>
              <p>{driver.description}</p>
            </article>
          ))}
        </div>
      </section>
```

- [ ] **Step 8: Run the targeted test and verify remaining failures**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected: The content tests should pass. The CSS structure test should still fail until Task 3 is complete.

---

### Task 3: Add Compact Responsive Styling

**Files:**
- Modify: `frontend/src/App.css`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add base Model drivers styles**

In `frontend/src/App.css`, add this block after the `.lead-panel` rule and before `.trust-layer`:

```css
.model-drivers {
  max-width: 1180px;
  margin: 0 auto 28px;
  display: grid;
  grid-template-columns: minmax(220px, 0.65fr) minmax(0, 1fr);
  gap: 14px;
  align-items: stretch;
}
.model-drivers-copy { display: grid; align-content: center; gap: 8px; min-width: 0; }
.model-drivers-copy h2 { margin: 0; font-size: 1.2rem; }
.model-drivers-copy p { margin: 0; color: #b2ada5; line-height: 1.45; }
.driver-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; min-width: 0; }
.driver-card { border: 1px solid #30343b; border-radius: 8px; background: #111316; padding: 14px; display: grid; gap: 6px; min-width: 0; }
.driver-card span { color: #8d948f; font-size: 0.78rem; }
.driver-card strong { font-size: 0.95rem; overflow-wrap: anywhere; }
.driver-card p { margin: 0; color: #b2ada5; font-size: 0.85rem; line-height: 1.4; }
.driver-card.raises strong { color: #ffb15f; }
.driver-card.lowers strong { color: #5bd687; }
.driver-card.neutral strong { color: #f4f0e8; }
.driver-card.unavailable strong { color: #8d948f; }
```

- [ ] **Step 2: Add mobile layout rules**

In the existing `@media (max-width: 900px)` block, after the `.hero, .brief-grid, .charts, .waitlist { grid-template-columns: 1fr; }` rule, add:

```css
  .model-drivers, .driver-list { grid-template-columns: 1fr; }
```

- [ ] **Step 3: Add small-screen padding consistency**

In the existing `@media (max-width: 560px)` block, update:

```css
  .brief-panel, .chart-panel, .waitlist, .empty-state, .trust-panel { padding: 18px; }
```

to:

```css
  .brief-panel, .chart-panel, .waitlist, .empty-state, .trust-panel, .driver-card { padding: 18px; }
```

- [ ] **Step 4: Run the targeted frontend test**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected: PASS.

---

### Task 4: Final Verification and Scope Check

**Files:**
- Read: `frontend/src/App.tsx`
- Read: `frontend/src/App.css`
- Read: `frontend/src/App.test.tsx`
- No product docs changes expected. Ignore `docs/superpowers/plans/2026-07-13-model-drivers.md` if it remains uncommitted as the orchestration artifact.

- [ ] **Step 1: Run all frontend tests**

Run:

```bash
npm test --prefix frontend
```

Expected: PASS.

- [ ] **Step 2: Run the frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected: PASS.

- [ ] **Step 3: Confirm price input did not gain extra metrics**

Run:

```bash
rg -n "price-input-grid|modelDrivers|driverActivity|turnover|z_turnover|Model price|Low|High" frontend/src/App.tsx frontend/src/App.test.tsx
```

Expected:
- `price-input-grid` still renders only model price and optional low/high.
- `turnover` and `z_turnover` are used only for model-driver activity availability/status.
- No raw driver values are rendered in the Model drivers section.

- [ ] **Step 4: Check the git diff for accidental scope expansion**

Run:

```bash
git diff -- frontend/src/App.tsx frontend/src/App.css frontend/src/App.test.tsx
```

Expected:
- Only frontend UI, style, and test changes.
- No backend, collector, database, risk formula, or API-shape changes.
- No product docs changes unless the implementer found an actual field-definition issue.

- [ ] **Step 5: Commit the implementation**

Run:

```bash
git add frontend/src/App.tsx frontend/src/App.css frontend/src/App.test.tsx
git commit -m "feat: show latest risk model drivers"
```

Expected: commit succeeds.

---

## Acceptance Mapping

- Frontend renders a localized Model drivers block when latest risk data is available: Task 2, Steps 3-7; Task 1, Step 4.
- The block includes trend, volatility, and trading activity when turnover is available: Task 2, Step 5; Task 1, Step 4.
- Trading activity uses turnover/z_turnover semantics, not raw USD volume: Task 2, Step 5.
- Missing or disabled turnover is handled clearly without misleading zeroes: Task 2, Step 5; Task 1, Step 5.
- Existing BTC price model input remains Model price / Low / High only: Task 4, Step 3.
- Focused frontend tests cover normal and turnover-disabled states: Task 1, Steps 4-5.
- API docs are not updated because no field definitions or backend API behavior change.

## Suggested `/goal` Prompt

```text
/goal Implement GitHub issue #15 for bitcoin-risk-brief using docs/superpowers/plans/2026-07-13-model-drivers.md as the execution plan. Add the localized Model drivers frontend block, keep the risk methodology and API/backend unchanged, add the focused frontend tests from the plan, run npm test --prefix frontend and npm run build --prefix frontend, and report the final commit plus verification results.
```
