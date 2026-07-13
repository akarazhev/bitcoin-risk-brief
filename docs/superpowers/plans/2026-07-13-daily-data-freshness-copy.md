# Daily Data Freshness Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ready daily BTC data read as current in the public readiness UI, while stale/degraded data still shows a clear behind-age.

**Architecture:** Keep this change frontend-only. The backend readiness payload, freshness checks, status codes, and API types remain unchanged; the React UI maps the existing readiness fields to clearer daily-candle copy. Tests lock both the ready daily state and degraded stale state so `Fresh: 1 day old` cannot return for ready data.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/App.tsx`
  - Responsibility: hold localized copy, derive display-only freshness text from the existing `ReadinessPayload`, and render the readiness metric/trust labels.
- Modify `frontend/src/App.test.tsx`
  - Responsibility: cover ready daily freshness copy and degraded stale/behind copy.
- Do not modify `backend/app/readiness.py`, `backend/app/main.py`, `frontend/src/types.ts`, collector code, migrations, or readiness API semantics.
- Do not add unrelated dirty files. At the time this plan was written, `collector/btc-csv/btc_usd_daily.csv` was already modified and is unrelated to this issue.

## Product Rules

- Ready data with `status: 'ready'`, `checks.data_fresh: true`, and `data_age_days: 1` must render as current, not old.
- Ready copy must make the daily-data boundary explicit:
  - `Current through 2026-06-26` via the metric label/date.
  - `Latest completed day: 2026-06-26`.
  - `Coverage through: 2026-06-26`.
  - `Freshness: current`.
- Ready copy must not render `Fresh: 1 day old` or `Data is 1 day old`.
- Stale degraded copy must preserve age signal as behind/stale copy:
  - `Stale: 6 days behind`.
- If `checks.data_fresh` is true but another readiness check degrades status, freshness text should still say `Freshness: current`; validation/status copy already communicates the other problem.

---

### Task 1: Add Failing Frontend Tests

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Replace the ready readiness test**

In `frontend/src/App.test.tsx`, replace the existing test named `renders readiness freshness and validation near the latest data date` with:

```tsx
test('renders ready daily data as current through the latest completed day', async () => {
  render(<App />)

  expect(apiMocks.fetchReadiness).toHaveBeenCalled()
  expect(await screen.findByText('Current through')).toBeInTheDocument()
  expect(screen.getAllByText('2026-06-26').length).toBeGreaterThan(0)
  expect(screen.getByText('Readiness ready')).toBeInTheDocument()
  expect(screen.getByText('Validation passed')).toBeInTheDocument()
  expect(screen.getByText('Latest completed day: 2026-06-26')).toBeInTheDocument()
  expect(screen.getByText('Freshness: current')).toBeInTheDocument()
  expect(screen.getByText('Coverage through: 2026-06-26')).toBeInTheDocument()
  expect(screen.queryByText('Fresh: 1 day old')).not.toBeInTheDocument()
  expect(screen.queryByText('Data is 1 day old')).not.toBeInTheDocument()
})
```

- [ ] **Step 2: Replace the degraded readiness assertions**

In the existing test named `renders degraded readiness copy without hiding the latest risk`, replace the final four assertions with:

```tsx
  expect(screen.getByText('Readiness degraded')).toBeInTheDocument()
  expect(screen.getByText('Validation needs attention')).toBeInTheDocument()
  expect(screen.getByText('Latest completed day: 2026-06-20')).toBeInTheDocument()
  expect(screen.getByText('Stale: 6 days behind')).toBeInTheDocument()
  expect(screen.getByText('Coverage through: 2026-06-19')).toBeInTheDocument()
  expect(screen.queryByText('Data is 6 days old')).not.toBeInTheDocument()
```

- [ ] **Step 3: Run the targeted frontend test and confirm it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result before implementation:

```text
FAIL  src/App.test.tsx
```

At least the ready test should fail because the UI still renders `Updated`, `Latest date`, `Fresh: 1 day old`, and `Covered end`.

---

### Task 2: Implement Daily Freshness Copy

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add a small type for readiness freshness labels**

In `frontend/src/App.tsx`, add this type near the other top-level type aliases, after `type DriverStatus = ...`:

```tsx
type ReadinessLabels = {
  freshnessCurrent: string
  staleAge: (days: number | null) => string
}
```

- [ ] **Step 2: Replace English readiness copy keys**

In the English `copy.en` object in `frontend/src/App.tsx`, replace these current keys:

```tsx
    latestDate: 'Latest date',
    coveredEnd: 'Covered end',
    freshAge: (days: number | null) => (days === null ? 'Freshness unknown' : `Fresh: ${days} ${days === 1 ? 'day' : 'days'} old`),
    staleAge: (days: number | null) => (days === null ? 'Data age unavailable' : `Data is ${days} ${days === 1 ? 'day' : 'days'} old`),
```

with:

```tsx
    currentThrough: 'Current through',
    latestCompletedDay: 'Latest completed day',
    coverageThrough: 'Coverage through',
    freshnessCurrent: 'Freshness: current',
    staleAge: (days: number | null) => (days === null ? 'Staleness unavailable' : `Stale: ${days} ${days === 1 ? 'day' : 'days'} behind`),
```

- [ ] **Step 3: Replace Russian readiness copy keys**

In the Russian `copy.ru` object in `frontend/src/App.tsx`, replace these current keys:

```tsx
    latestDate: 'Последняя дата',
    coveredEnd: 'Покрыто до',
    freshAge: (days: number | null) => (days === null ? 'Свежесть неизвестна' : `Свежесть: ${days} дн.`),
    staleAge: (days: number | null) => (days === null ? 'Возраст данных неизвестен' : `Данным ${days} дн.`),
```

with:

```tsx
    currentThrough: 'Актуально по',
    latestCompletedDay: 'Последний завершенный день',
    coverageThrough: 'Покрытие по',
    freshnessCurrent: 'Свежесть: актуально',
    staleAge: (days: number | null) => (days === null ? 'Отставание данных неизвестно' : `Отставание: ${days} дн.`),
```

- [ ] **Step 4: Add the display-only freshness helper**

In `frontend/src/App.tsx`, add this helper after `formatTrustValue()` and before `validationPassed()`:

```tsx
function readinessFreshnessText(readiness: ReadinessPayload, labels: ReadinessLabels) {
  return readiness.checks.data_fresh
    ? labels.freshnessCurrent
    : labels.staleAge(readiness.data.data_age_days)
}
```

- [ ] **Step 5: Update the readiness metric rendering**

In the `freshness-metric` block in `frontend/src/App.tsx`, replace this current section:

```tsx
          <span>{t.updated}</span>
          <strong>{latest.timestamp.slice(0, 10)}</strong>
          <p className={`readiness-badge ${readiness.status}`}>
            {ready ? <CheckCircle2 size={15} /> : <TriangleAlert size={15} />}
            {ready ? t.readinessReady : t.readinessDegraded}
          </p>
          <em>{validationOk ? t.validationPassed : t.validationNeedsAttention}</em>
          <em>{formatTrustValue(t.latestDate, readiness.data.latest_date)}</em>
          <em>{ready && readiness.checks.data_fresh ? t.freshAge(readiness.data.data_age_days) : t.staleAge(readiness.data.data_age_days)}</em>
          <em>{formatTrustValue(t.coveredEnd, readiness.data.covered_end)}</em>
```

with:

```tsx
          <span>{ready && readiness.checks.data_fresh ? t.currentThrough : t.updated}</span>
          <strong>{latest.timestamp.slice(0, 10)}</strong>
          <p className={`readiness-badge ${readiness.status}`}>
            {ready ? <CheckCircle2 size={15} /> : <TriangleAlert size={15} />}
            {ready ? t.readinessReady : t.readinessDegraded}
          </p>
          <em>{validationOk ? t.validationPassed : t.validationNeedsAttention}</em>
          <em>{formatTrustValue(t.latestCompletedDay, readiness.data.latest_date)}</em>
          <em>{readinessFreshnessText(readiness, t)}</em>
          <em>{formatTrustValue(t.coverageThrough, readiness.data.covered_end)}</em>
```

- [ ] **Step 6: Update methodology trust labels**

In the methodology `dl` in `frontend/src/App.tsx`, replace:

```tsx
            <div><dt>{t.latestDate}</dt><dd>{readiness.data.latest_date ?? 'unavailable'}</dd></div>
            <div><dt>{t.coveredEnd}</dt><dd>{readiness.data.covered_end ?? 'unavailable'}</dd></div>
```

with:

```tsx
            <div><dt>{t.latestCompletedDay}</dt><dd>{readiness.data.latest_date ?? 'unavailable'}</dd></div>
            <div><dt>{t.coverageThrough}</dt><dd>{readiness.data.covered_end ?? 'unavailable'}</dd></div>
```

- [ ] **Step 7: Run the targeted frontend test and confirm it passes**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result after implementation:

```text
PASS  src/App.test.tsx
```

---

### Task 3: Verify, Review Diff, And Commit

**Files:**
- Verify: `frontend/src/App.tsx`
- Verify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Run the full frontend test suite**

Run:

```bash
npm test --prefix frontend
```

Expected result:

```text
Test Files  2 passed
```

The exact assertion count can vary as tests evolve, but there should be no failed test files.

- [ ] **Step 2: Run the frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected result:

```text
✓ built in
```

- [ ] **Step 3: Review the scoped diff**

Run:

```bash
git diff -- frontend/src/App.tsx frontend/src/App.test.tsx
```

Confirm the diff only changes:

- readiness copy keys,
- the display-only readiness freshness helper,
- readiness metric/methodology labels,
- readiness UI tests.

- [ ] **Step 4: Check worktree status**

Run:

```bash
git status --short
```

Expected result may still show the pre-existing unrelated CSV modification:

```text
 M collector/btc-csv/btc_usd_daily.csv
 M frontend/src/App.test.tsx
 M frontend/src/App.tsx
```

Only stage the frontend files for this issue.

- [ ] **Step 5: Commit the scoped frontend change**

Run:

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "fix: clarify daily readiness freshness copy"
```

Do not stage or commit `collector/btc-csv/btc_usd_daily.csv`.

---

## Acceptance Checklist

- [ ] Ready daily data with latest date equal to yesterday renders as `Freshness: current`.
- [ ] Ready state no longer renders `Fresh: 1 day old`.
- [ ] Ready labels say `Current through`, `Latest completed day`, and `Coverage through`.
- [ ] Degraded stale data renders `Stale: N days behind`.
- [ ] Backend readiness validation semantics remain unchanged.
- [ ] `npm test --prefix frontend -- App.test.tsx` passes.
- [ ] `npm test --prefix frontend` passes.
- [ ] `npm run build --prefix frontend` passes.
