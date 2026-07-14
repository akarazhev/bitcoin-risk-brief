# Report Date Readiness Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a clear public report date in the readiness metric while keeping latest completed data coverage visible and accurate.

**Architecture:** Keep the backend readiness API unchanged. Compute a display-only report date in the React UI as one UTC day after `readiness.data.latest_date` when the data is fresh, then continue showing `latest_date` and `covered_end` as provenance details. This preserves the daily-candle contract while avoiding a primary "yesterday" date for ready data.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/App.test.tsx`
  - Responsibility: lock the desired public copy and date behavior with focused UI tests.
- Modify `frontend/src/App.tsx`
  - Responsibility: derive the display-only report date from readiness metadata and render the primary metric label/value.
- Modify `frontend/src/locales.ts`
  - Responsibility: add localized `reportDate` copy for every supported locale.
- Do not modify `backend/app/readiness.py`, `backend/app/main.py`, `frontend/src/types.ts`, collector code, migrations, or API documentation. The readiness payload still reports actual validated coverage as `latest_date` and `covered_end`.

## Product Rules

- For ready/fresh daily data, the primary date metric must read as a report date, not as data coverage.
- The report date is `readiness.data.latest_date + 1 UTC day`.
  - Example: `latest_date: 2026-07-12` renders primary `Report date` value `2026-07-13`.
  - Example: `latest_date: 2026-12-31` renders primary `Report date` value `2027-01-01`.
- Provenance details must remain unchanged:
  - `Latest completed day: <readiness.data.latest_date>`
  - `Coverage through: <readiness.data.covered_end>`
  - `Freshness: current` when `checks.data_fresh` is true.
- Stale data must not get a forward-looking report date. If `checks.data_fresh` is false, keep the existing `Updated` label and stale age copy.
- Do not use the browser clock or the user's local timezone for the report date. The report date comes from the data boundary, not wall-clock time.

---

### Task 1: Write Failing Frontend Tests

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Replace the ready readiness test**

In `frontend/src/App.test.tsx`, replace the existing test named `renders ready daily data as current through the latest completed day` with:

```tsx
test('renders ready daily data with a report date after the latest completed day', async () => {
  render(<App />)

  expect(apiMocks.fetchReadiness).toHaveBeenCalled()
  expect(await screen.findByText('Report date')).toBeInTheDocument()
  expect(screen.getByText('2026-06-27')).toBeInTheDocument()
  expect(screen.getByText('Readiness ready')).toBeInTheDocument()
  expect(screen.getByText('Validation passed')).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Latest completed day: 2026-06-26'))).toBeInTheDocument()
  expect(screen.getByText('Freshness: current')).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Coverage through: 2026-06-26'))).toBeInTheDocument()
  expect(screen.queryByText('Current through')).not.toBeInTheDocument()
  expect(screen.queryByText('Fresh: 1 day old')).not.toBeInTheDocument()
  expect(screen.queryByText('Data is 1 day old')).not.toBeInTheDocument()
})
```

- [ ] **Step 2: Add a UTC rollover regression test**

Add this test immediately after the ready readiness test:

```tsx
test('rolls the report date across UTC year boundaries', async () => {
  apiMocks.fetchLatestRisk.mockResolvedValueOnce({
    data: latestRisk({ timestamp: '2026-12-31T00:00:00Z' }),
  })
  apiMocks.fetchBrief.mockResolvedValueOnce({
    data: {
      snapshot_version: 'v1',
      as_of: '2026-12-31T00:00:00Z',
      risk: 0.7,
      risk_state: 'high',
      price_usd: 100000,
      delta_risk: 0.1,
      sections: {
        en: {
          summary: 'Risk elevated',
          what_changed: 'Changed',
          avoid_now: 'Avoid',
          confirm_next: 'Confirm',
        },
      },
    },
  })
  apiMocks.fetchReadiness.mockResolvedValueOnce({
    status: 'ready',
    checks: {
      risk_data_available: true,
      validation_available: true,
      risk_range_ok: true,
      validation_has_rows: true,
      latest_matches_validation_end: true,
      source_is_canonical: true,
      data_fresh: true,
    },
    data: {
      latest_date: '2026-12-31',
      covered_end: '2026-12-31',
      data_age_days: 1,
      max_age_days: 2,
      source: 'coinmarketcap_csv',
      row_count: 5827,
      methodology_version: 'crypto-scout-canonical-v1',
    },
  })

  render(<App />)

  expect(await screen.findByText('Report date')).toBeInTheDocument()
  expect(screen.getByText('2027-01-01')).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Latest completed day: 2026-12-31'))).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Coverage through: 2026-12-31'))).toBeInTheDocument()
})
```

- [ ] **Step 3: Strengthen the degraded readiness test**

In the existing test named `renders degraded readiness copy without hiding the latest risk`, keep the current degraded payload and final assertions, then add this assertion near the other readiness copy assertions:

```tsx
  expect(screen.queryByText('Report date')).not.toBeInTheDocument()
```

The final assertion block should include:

```tsx
  expect(screen.getByText('Readiness degraded')).toBeInTheDocument()
  expect(screen.getByText('Validation needs attention')).toBeInTheDocument()
  expect(screen.queryByText('Report date')).not.toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Latest completed day: 2026-06-20'))).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Stale: 6 days behind'))).toBeInTheDocument()
  expect(screen.getByText(textContentMatcher('Coverage through: 2026-06-19'))).toBeInTheDocument()
  expect(screen.queryByText('Data is 6 days old')).not.toBeInTheDocument()
```

- [ ] **Step 4: Run the targeted frontend test and confirm it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result before implementation:

```text
FAIL  src/App.test.tsx
```

Expected reason: the UI still renders `Current through` with `2026-06-26`, and `Report date` is not present.

---

### Task 2: Add Localized Report Date Copy

**Files:**
- Modify: `frontend/src/locales.ts`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add `reportDate` to the copy type**

In `frontend/src/locales.ts`, update the `Copy` type near `updated: string`:

```ts
  updated: string
  reportDate: string
  currentRisk: string
```

- [ ] **Step 2: Add locale values**

In each locale object in `frontend/src/locales.ts`, add `reportDate` immediately after `updated`.

English:

```ts
    updated: 'Updated',
    reportDate: 'Report date',
    currentRisk: 'Current risk',
```

Russian:

```ts
    updated: 'Обновлено',
    reportDate: 'Дата выпуска',
    currentRisk: 'Текущий риск',
```

Chinese:

```ts
    updated: '已更新',
    reportDate: '报告日期',
    currentRisk: '当前风险',
```

German:

```ts
    updated: 'Aktualisiert',
    reportDate: 'Berichtsdatum',
    currentRisk: 'Aktuelles Risiko',
```

French:

```ts
    updated: 'Mis à jour',
    reportDate: 'Date du rapport',
    currentRisk: 'Risque actuel',
```

Spanish:

```ts
    updated: 'Actualizado',
    reportDate: 'Fecha del informe',
    currentRisk: 'Riesgo actual',
```

Arabic:

```ts
    updated: 'آخر تحديث',
    reportDate: 'تاريخ التقرير',
    currentRisk: 'المخاطر الحالية',
```

- [ ] **Step 3: Run TypeScript through the frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected result at this point:

```text
✓ built
```

If TypeScript fails with a missing `reportDate` property, one locale object was missed. Add the missing `reportDate` entry before continuing.

---

### Task 3: Implement Report Date Derivation And Rendering

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add a UTC-safe date helper**

In `frontend/src/App.tsx`, add this helper after `formatDateLabel`:

```tsx
function addUtcDays(isoDate: string, days: number) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate)
  if (!match) return null

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const parsed = new Date(Date.UTC(year, month - 1, day))

  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== isoDate) {
    return null
  }

  parsed.setUTCDate(parsed.getUTCDate() + days)
  return parsed.toISOString().slice(0, 10)
}
```

- [ ] **Step 2: Derive the primary date metric values**

In `frontend/src/App.tsx`, find this block:

```tsx
  const modelDrivers = buildModelDrivers(latest, t)
```

Replace it with:

```tsx
  const modelDrivers = buildModelDrivers(latest, t)
  const reportDate = readiness.checks.data_fresh && readiness.data.latest_date
    ? addUtcDays(readiness.data.latest_date, 1)
    : null
  const primaryDateLabel = reportDate ? t.reportDate : t.updated
  const primaryDateValue = reportDate ?? latest.timestamp.slice(0, 10)
```

- [ ] **Step 3: Render the primary date metric**

In `frontend/src/App.tsx`, find the readiness metric date markup:

```tsx
        <div className="freshness-metric">
          <span>{ready && readiness.checks.data_fresh ? t.currentThrough : t.updated}</span>
          <strong><NumericValue>{latest.timestamp.slice(0, 10)}</NumericValue></strong>
```

Replace it with:

```tsx
        <div className="freshness-metric">
          <span>{primaryDateLabel}</span>
          <strong><NumericValue>{primaryDateValue}</NumericValue></strong>
```

- [ ] **Step 4: Run the targeted frontend test and confirm it passes**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result:

```text
PASS  src/App.test.tsx
```

- [ ] **Step 5: Commit the frontend behavior change**

Run:

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/locales.ts
git commit -m "feat: show report date in readiness summary"
```

---

### Task 4: Final Verification

**Files:**
- Read: `frontend/src/App.tsx`
- Read: `frontend/src/App.test.tsx`
- Read: `frontend/src/locales.ts`

- [ ] **Step 1: Run frontend unit tests**

Run:

```bash
npm test --prefix frontend
```

Expected result:

```text
PASS
```

- [ ] **Step 2: Run frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected result:

```text
✓ built
```

- [ ] **Step 3: Review the focused diff**

Run:

```bash
git diff -- frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/locales.ts
```

Expected diff characteristics:

```text
frontend/src/App.tsx       | adds UTC report-date helper and uses Report date primary metric
frontend/src/App.test.tsx  | expects Report date, latest completed day, coverage through, stale fallback
frontend/src/locales.ts    | adds reportDate copy for every supported locale
```

- [ ] **Step 4: Confirm no backend or data files changed**

Run:

```bash
git status --short
```

Expected result: no modified backend, collector, migration, CSV, or environment files from this task. The only task-related changes should be the three frontend files, unless the implementation agent already committed them.
