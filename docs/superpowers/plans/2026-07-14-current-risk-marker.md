# Current Risk Marker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a visible current-risk marker to the frontend Risk levels chart, using `/api/risk/levels` metadata when available and falling back to `/api/risk/latest` risk when that metadata is absent.

**Architecture:** Keep this as a frontend-only change. Type the existing risk-level payload metadata, store it with the level rows in `App.tsx`, derive a single chart marker model, and render it as an ECharts `markLine` on the existing turquoise bar series. Keep the existing category x-axis and align the vertical marker to the nearest rendered risk bucket while labeling it with the actual current risk value.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, ECharts.

---

## Scope And File Map

Do not change backend code. `backend/app/risk_levels.py` already returns `meta.current_risk` and `meta.current_price` in `build_risk_levels_public_payload()`.

Modify:

- `frontend/src/types.ts`: add `RiskLevelsMeta` and `RiskLevelsPayload`.
- `frontend/src/api.ts`: make `fetchRiskLevels()` return `RiskLevelsPayload`.
- `frontend/src/App.tsx`: store level metadata, derive the current-risk marker, add `markLine`, and update the screen-reader alternative.
- `frontend/src/App.test.tsx`: add focused tests for metadata priority, fallback behavior, and accessible text.

Do not modify:

- backend API fields;
- collector logic;
- docs, unless implementation uncovers a mismatch with `docs/api-reference.md`.

Execution notes:

- Follow TDD: add or update a focused failing test before each behavior change.
- Commit after each task if commits are allowed in the session. If the user explicitly asks for uncommitted changes, skip commit steps and report the intended commit messages instead.
- Preserve loading, empty, and error states.
- Preserve no-advice copy. Do not add buy/sell language.

---

### Task 1: Add A Failing Test For Metadata-Driven Marker

**Files:**

- Modify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Update the default risk-level mock metadata**

In `beforeEach()`, replace the existing `apiMocks.fetchRiskLevels.mockResolvedValue(...)` block with this shape so default frontend tests receive the documented metadata:

```tsx
  apiMocks.fetchRiskLevels.mockResolvedValue({ data: [
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.65, price_usd: 118000 },
  ], meta: {
    base: latestRisk(),
    methodology_version: 'crypto-scout-canonical-v1',
    evaluation_date: '2026-06-26',
    current_price: 100000,
    current_risk: 0.7,
    turnover_enabled: false,
    risk_step: 0.025,
    source_row_count: 5827,
  } })
```

- [ ] **Step 2: Add the focused failing test**

Add this test near the existing chart-option tests, after `uses accessible risk threshold labels outside the chart canvas`:

```tsx
test('marks the current risk on levels chart using levels snapshot metadata', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({ data: latestRisk({ risk: 0.2 }) })
  apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.65, price_usd: 118000 },
  ], meta: {
    base: latestRisk({ risk: 0.7 }),
    methodology_version: 'crypto-scout-canonical-v1',
    evaluation_date: '2026-06-26',
    current_price: 100000,
    current_risk: 0.7,
    turnover_enabled: false,
    risk_step: 0.025,
    source_row_count: 5827,
  } })

  render(<App />)

  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(priceOption.series[0].markLine).toMatchObject({
    symbol: 'none',
    silent: true,
    data: [{ xAxis: '65%' }],
    lineStyle: { color: '#f2b84b', width: 2 },
  })
  expect(priceOption.series[0].markLine.label).toMatchObject({
    show: true,
    formatter: 'Current risk: 70%',
  })
})
```

- [ ] **Step 3: Run the focused test and verify it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "marks the current risk"
```

Expected: FAIL because `priceOption.series[0].markLine` is currently `undefined`.

- [ ] **Step 4: Commit the failing test if your workflow commits red tests**

If committing red tests is acceptable:

```bash
git add frontend/src/App.test.tsx
git commit -m "test: cover current risk marker metadata"
```

If not, leave it uncommitted until Task 2 passes.

---

### Task 2: Type Levels Metadata And Render The Metadata Marker

**Files:**

- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add risk-level payload types**

In `frontend/src/types.ts`, after `RiskLevel`, add:

```ts
export interface RiskLevelsMeta {
  base?: Partial<RiskPoint> | null
  methodology_version?: string | null
  evaluation_date?: string | null
  current_price?: number | null
  current_risk?: number | null
  turnover_enabled?: boolean | null
  risk_step?: number | null
  source_row_count?: number | null
}

export interface RiskLevelsPayload {
  data: RiskLevel[]
  meta?: RiskLevelsMeta | null
}
```

- [ ] **Step 2: Update the API client type**

In `frontend/src/api.ts`, change the import:

```ts
import type { BriefPayload, ReadinessPayload, RiskLevelsPayload, RiskPoint, WaitlistRequest, WaitlistResponse } from './types'
```

Then replace `fetchRiskLevels()` with:

```ts
export async function fetchRiskLevels() {
  return getJson<RiskLevelsPayload>('/api/risk/levels')
}
```

- [ ] **Step 3: Add App-level marker types and helpers**

In `frontend/src/App.tsx`, change the type import:

```ts
import type { BriefPayload, Locale, ReadinessPayload, RiskLevel, RiskLevelsMeta, RiskPoint } from './types'
```

After `type ThresholdCallout = ...`, add:

```ts
type RiskLevelsChartData = {
  levels: RiskLevel[]
  meta: RiskLevelsMeta | null
}
type CurrentRiskMarker = {
  risk: number
  xAxisLabel: string
}
```

After `function formatTooltipPercent(...)`, add:

```ts
function riskLevelAxisLabel(risk: number) {
  return `${Math.round(risk * 100)}%`
}
```

After `function nearestRiskLevel(...)`, add:

```ts
function emptyRiskLevelsChartData(): RiskLevelsChartData {
  return { levels: [], meta: null }
}

function isRiskValue(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
}

function buildCurrentRiskMarker(levels: RiskLevel[], levelsMeta: RiskLevelsMeta | null): CurrentRiskMarker | null {
  const currentRisk = levelsMeta?.current_risk
  if (!isRiskValue(currentRisk)) return null

  const nearestLevel = nearestRiskLevel(levels, currentRisk)
  if (!nearestLevel) return null

  return {
    risk: currentRisk,
    xAxisLabel: riskLevelAxisLabel(nearestLevel.risk),
  }
}
```

- [ ] **Step 4: Store levels metadata with chart data**

Replace the levels state initialization:

```tsx
  const [levelsState, setLevelsState] = useState<ChartLoadState<RiskLevelsChartData>>({
    status: 'idle',
    data: emptyRiskLevelsChartData(),
    error: null,
  })
```

Replace the derived `levels` constant:

```tsx
  const levels = levelsState.data.levels
  const levelsMeta = levelsState.data.meta
```

Replace the loading state update:

```tsx
    setLevelsState({ status: 'loading', data: emptyRiskLevelsChartData(), error: null })
```

Replace the successful levels load update:

```tsx
        setLevelsState({
          status: 'loaded',
          data: { levels: levelsResponse.data, meta: levelsResponse.meta ?? null },
          error: null,
        })
```

Replace the error state update:

```tsx
        setLevelsState({ status: 'error', data: emptyRiskLevelsChartData(), error: err.message })
```

- [ ] **Step 5: Derive the current-risk marker and render it as a markLine**

Before `levelsOption`, add:

```tsx
  const currentRiskMarker = useMemo(
    () => buildCurrentRiskMarker(levels, levelsMeta),
    [levels, levelsMeta],
  )
```

Replace `levelsOption` with:

```tsx
  const levelsOption = useMemo<EChartsOption>(() => ({
    backgroundColor: 'transparent',
    animation: false,
    grid: {
      left: compactCharts ? 46 : 62,
      right: compactCharts ? 8 : 22,
      top: currentRiskMarker ? (compactCharts ? 38 : 34) : (compactCharts ? 14 : 18),
      bottom: compactCharts ? 30 : 36,
    },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: levels.map((row) => riskLevelAxisLabel(row.risk)), axisLabel: { color: '#7e8794', hideOverlap: compactCharts }, axisLine: { lineStyle: { color: '#2a3441' } } },
    yAxis: { type: 'value', axisLabel: { color: '#7e8794', formatter: (value: number) => `$${Math.round(value / 1000)}k` }, splitLine: { lineStyle: { color: '#26303b' } } },
    series: [{
      name: 'Price',
      type: 'bar',
      barMaxWidth: compactCharts ? 5 : 9,
      data: levels.map((row) => row.price_usd),
      itemStyle: { color: '#5bd6c6', borderRadius: [4, 4, 0, 0] },
      markLine: currentRiskMarker ? {
        symbol: 'none',
        silent: true,
        label: {
          show: true,
          formatter: `${t.currentRisk}: ${formatPercent(currentRiskMarker.risk)}`,
          position: 'end',
          color: '#f8fafc',
          backgroundColor: 'rgba(8, 13, 22, 0.88)',
          borderRadius: 4,
          padding: [3, 6],
          fontSize: compactCharts ? 10 : 11,
        },
        data: [{ xAxis: currentRiskMarker.xAxisLabel }],
        lineStyle: { color: '#f2b84b', width: 2, type: 'solid' },
      } : undefined,
    }],
  }), [compactCharts, currentRiskMarker, levels, t.currentRisk])
```

- [ ] **Step 6: Run the focused test and verify it passes**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "marks the current risk"
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "feat: mark current risk on levels chart"
```

---

### Task 3: Add And Implement Fallback To Latest Risk

**Files:**

- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add the failing fallback test**

Add this test after the metadata marker test:

```tsx
test('falls back to latest risk for levels marker when levels metadata omits current risk', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({ data: latestRisk({ risk: 0.35 }) })
  apiMocks.fetchRiskLevels.mockResolvedValueOnce({ data: [
    { risk: 0.35, price_usd: 82000 },
    { risk: 0.65, price_usd: 118000 },
  ], meta: { base: latestRisk({ risk: 0.35 }) } })

  render(<App />)

  const priceChart = await screen.findByTestId('chart-price')
  const priceOption = JSON.parse(priceChart.dataset.option ?? '{}')

  expect(priceOption.series[0].markLine.data).toEqual([{ xAxis: '35%' }])
  expect(priceOption.series[0].markLine.label.formatter).toBe('Current risk: 35%')
})
```

- [ ] **Step 2: Run the fallback test and verify it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "falls back to latest risk"
```

Expected: FAIL because `buildCurrentRiskMarker()` ignores `latest.risk`.

- [ ] **Step 3: Update marker helper to accept a fallback risk**

In `frontend/src/App.tsx`, replace `buildCurrentRiskMarker(...)` with:

```ts
function buildCurrentRiskMarker(
  levels: RiskLevel[],
  levelsMeta: RiskLevelsMeta | null,
  fallbackRisk: number | null | undefined,
): CurrentRiskMarker | null {
  const metadataRisk = levelsMeta?.current_risk
  const currentRisk = isRiskValue(metadataRisk) ? metadataRisk : fallbackRisk
  if (!isRiskValue(currentRisk)) return null

  const nearestLevel = nearestRiskLevel(levels, currentRisk)
  if (!nearestLevel) return null

  return {
    risk: currentRisk,
    xAxisLabel: riskLevelAxisLabel(nearestLevel.risk),
  }
}
```

Replace the marker memo:

```tsx
  const currentRiskMarker = useMemo(
    () => buildCurrentRiskMarker(levels, levelsMeta, latest?.risk),
    [levels, levelsMeta, latest?.risk],
  )
```

- [ ] **Step 4: Run the metadata and fallback tests**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "current risk|falls back"
```

Expected: both marker tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "feat: fall back to latest risk for levels marker"
```

---

### Task 4: Add Screen-Reader Text For The Marker

**Files:**

- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update the accessibility test expectation**

In `renders screen-reader chart data alternatives for current risk, recent history, and thresholds`, replace the exact levels chart description assertion:

```tsx
  expect(levelsChart).toHaveAccessibleDescription('The table lists the key risk threshold prices used with the risk levels chart.')
```

with:

```tsx
  expect(levelsChart).toHaveAccessibleDescription(/The table lists the key risk threshold prices used with the risk levels chart\./)
  expect(levelsChart).toHaveAccessibleDescription(/Current risk: 70%/)
```

- [ ] **Step 2: Run the accessibility test and verify it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "screen-reader chart data alternatives"
```

Expected: FAIL because the levels chart accessible description does not mention the current marker.

- [ ] **Step 3: Build a levels chart summary string**

In `frontend/src/App.tsx`, after `chartCurrentSummary`, add:

```tsx
  const riskLevelsSummary = currentRiskMarker
    ? `${t.riskLevelsAlternativeNote} ${t.currentRisk}: ${formatPercent(currentRiskMarker.risk)}.`
    : t.riskLevelsAlternativeNote
```

- [ ] **Step 4: Keep `aria-describedby` valid even without threshold callouts**

In the Risk levels article JSX, replace the current conditional screen-reader section:

```tsx
          {thresholdCallouts.length > 0 && (
            <section className="sr-only" aria-labelledby="risk-levels-alternative-heading">
              <h3 id="risk-levels-alternative-heading">{t.riskLevelsAlternative}</h3>
              <p id="risk-levels-chart-summary">{t.riskLevelsAlternativeNote}</p>
              <table aria-describedby="risk-levels-chart-summary">
                <caption>{t.riskThresholdPriceTable}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t.thresholdColumn}</th>
                    <th scope="col">{t.bandColumn}</th>
                    <th scope="col">{t.nearestModelPriceColumn}</th>
                  </tr>
                </thead>
                <tbody>
                  {thresholdCallouts.map((callout) => (
                    <tr key={callout.risk}>
                      <td>{formatPercent(callout.risk)}</td>
                      <td>{callout.label}</td>
                      <td>{callout.price}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
```

with:

```tsx
          {levels.length > 0 && (
            <section className="sr-only" aria-labelledby="risk-levels-alternative-heading">
              <h3 id="risk-levels-alternative-heading">{t.riskLevelsAlternative}</h3>
              <p id="risk-levels-chart-summary">{riskLevelsSummary}</p>
              {thresholdCallouts.length > 0 && (
                <table aria-describedby="risk-levels-chart-summary">
                  <caption>{t.riskThresholdPriceTable}</caption>
                  <thead>
                    <tr>
                      <th scope="col">{t.thresholdColumn}</th>
                      <th scope="col">{t.bandColumn}</th>
                      <th scope="col">{t.nearestModelPriceColumn}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {thresholdCallouts.map((callout) => (
                      <tr key={callout.risk}>
                        <td>{formatPercent(callout.risk)}</td>
                        <td>{callout.label}</td>
                        <td>{callout.price}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          )}
```

- [ ] **Step 5: Run the accessibility test and verify it passes**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "screen-reader chart data alternatives"
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "test: describe levels current risk marker accessibly"
```

---

### Task 5: Regression Checks And Final Verification

**Files:**

- Verify: `frontend/src/App.tsx`
- Verify: `frontend/src/App.test.tsx`
- Verify: `frontend/src/types.ts`
- Verify: `frontend/src/api.ts`

- [ ] **Step 1: Run the full frontend test suite**

Run:

```bash
npm test --prefix frontend
```

Expected: all frontend tests PASS.

- [ ] **Step 2: Run the frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected: TypeScript build and Vite production build PASS.

- [ ] **Step 3: Inspect the final diff**

Run:

```bash
git diff -- frontend/src/types.ts frontend/src/api.ts frontend/src/App.tsx frontend/src/App.test.tsx
```

Check:

- `fetchRiskLevels()` returns the typed full payload.
- `levelsState` keeps both rows and metadata.
- `meta.current_risk` is preferred over `latest.risk`.
- missing `meta.current_risk` falls back to `latest.risk`.
- `series[0].markLine` is only present when levels data and a bounded risk value exist.
- `aria-describedby="risk-levels-chart-summary"` points to an existing element whenever the chart renders.
- loading, empty, and error branches remain structurally intact.
- copy remains informational and contains no buy/sell language.

- [ ] **Step 4: Final commit if previous commits were skipped**

If the prior task commits were skipped, make one scoped commit:

```bash
git add frontend/src/types.ts frontend/src/api.ts frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "feat: mark current risk on levels chart"
```

- [ ] **Step 5: Report completion**

Report:

- files changed;
- tests run;
- build status;
- whether commits were made;
- any residual risk, especially around exact ECharts label placement on very narrow screens.
