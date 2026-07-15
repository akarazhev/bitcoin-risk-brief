# Issue 31 Minihub Bottom Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact bottom footer strip to the public React UI with `<public-support-address>`, copyright `2026`, and `https://minihub.app`.

**Architecture:** Implement this as a quiet global footer at the end of the existing single-page dashboard, after the charts. Keep the values as constants in `App.tsx`, localize only the footer accessibility label through the existing `copy` object, and style the strip with the same constrained `1180px` layout, dark palette, 8px-or-less UI rules, focus states, and RTL support already used by the page.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, CSS.

---

## Scope Check

This plan covers one UI change for GitHub issue #31. It does not add legal pages, analytics, backend support handling, email delivery, or Minihub brand navigation beyond the requested footer content.

## File Structure

- Modify `frontend/src/App.test.tsx`: add failing tests for footer content, links, placement, and CSS focus/RTL styles.
- Modify `frontend/src/locales.ts`: add one localized accessibility label key for the footer landmark.
- Modify `frontend/src/App.tsx`: add footer constants and render the compact bottom panel after the charts.
- Modify `frontend/src/App.css`: add compact footer strip styles, keyboard focus state, mobile layout, and RTL direction support.

---

### Task 1: Write Footer Behavior Tests

**Files:**
- Modify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add a failing render test for the bottom panel**

In `frontend/src/App.test.tsx`, add this test near the existing layout/order tests, for example after `places the waitlist call to action before the charts`:

```tsx
test('renders the compact Minihub bottom panel after the charts', async () => {
  render(<App />)

  const supportLink = await screen.findByRole('link', { name: '<public-support-address>' })
  const footer = supportLink.closest('footer.bottom-panel')
  expect(footer).not.toBeNull()

  const bottomPanel = within(footer as HTMLElement)
  expect(supportLink).toHaveAttribute('href', 'mailto:<public-support-address>')
  expect(bottomPanel.getByText(textContentMatcher('© 2026 Minihub'))).toBeInTheDocument()

  const websiteLink = bottomPanel.getByRole('link', { name: /https:\/\/minihub\.app/i })
  expect(websiteLink).toHaveAttribute('href', 'https://minihub.app')
  expect(websiteLink).toHaveAttribute('target', '_blank')
  expect(websiteLink).toHaveAttribute('rel', 'noreferrer')

  const riskLevelsTitle = screen.getByRole('heading', { name: 'Risk levels' })
  expect(riskLevelsTitle.compareDocumentPosition(footer as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
})
```

- [ ] **Step 2: Extend the existing CSS focus-state test**

In the existing `defines visible keyboard focus states for interactive controls` test in `frontend/src/App.test.tsx`, add this assertion:

```tsx
expect(css).toContain('.bottom-panel-link:focus-visible')
```

- [ ] **Step 3: Add a CSS layout/RTL guard test**

In `frontend/src/App.test.tsx`, add this test near the CSS focus-state test:

```tsx
test('defines compact bottom panel layout and RTL styles', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.bottom-panel')
  expect(css).toContain('border-top: 1px solid #2c3037')
  expect(css).toContain('[dir="rtl"] .bottom-panel')
})
```

- [ ] **Step 4: Run the focused frontend test file and verify failure**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result: FAIL because `<public-support-address>` and `.bottom-panel-link:focus-visible` do not exist yet.

---

### Task 2: Add Footer Copy and Markup

**Files:**
- Modify: `frontend/src/locales.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add the footer accessibility label to the locale type**

In `frontend/src/locales.ts`, add this key to `type Copy` near the other navigation/accessibility labels:

```ts
footerAriaLabel: string
```

- [ ] **Step 2: Add the footer accessibility label to every locale**

In `frontend/src/locales.ts`, add `footerAriaLabel` to each `copy` locale object. Place it near `languageSelector` to keep accessibility labels grouped.

```ts
footerAriaLabel: 'Minihub support and copyright',
```

```ts
footerAriaLabel: 'Поддержка Minihub и авторские права',
```

```ts
footerAriaLabel: 'Minihub 支持和版权',
```

```ts
footerAriaLabel: 'Minihub Support und Copyright',
```

```ts
footerAriaLabel: 'Assistance Minihub et droits d’auteur',
```

```ts
footerAriaLabel: 'Soporte de Minihub y copyright',
```

```ts
footerAriaLabel: 'دعم Minihub وحقوق النشر',
```

- [ ] **Step 3: Add footer constants in `App.tsx`**

In `frontend/src/App.tsx`, add these constants near `COINMARKETCAP_HISTORICAL_DATA_URL`:

```ts
const SUPPORT_EMAIL = '<public-support-address>'
const SUPPORT_EMAIL_URL = `mailto:${SUPPORT_EMAIL}`
const MINIHUB_URL = 'https://minihub.app'
const COPYRIGHT_YEAR = '2026'
```

- [ ] **Step 4: Render the compact footer after the charts**

In `frontend/src/App.tsx`, add this block after the closing `</section>` for `className="charts"` and before the closing `</main>`:

```tsx
      <footer className="bottom-panel" aria-label={t.footerAriaLabel}>
        <a className="bottom-panel-link footer-token" href={SUPPORT_EMAIL_URL} dir="ltr">
          {SUPPORT_EMAIL}
        </a>
        <span className="footer-legal">
          &copy; <NumericValue>{COPYRIGHT_YEAR}</NumericValue> Minihub
        </span>
        <a className="bottom-panel-link footer-token" href={MINIHUB_URL} target="_blank" rel="noreferrer" dir="ltr">
          {MINIHUB_URL}
          <ExternalLink size={14} aria-hidden="true" />
        </a>
      </footer>
```

- [ ] **Step 5: Run locale tests and verify the locale key set is complete**

Run:

```bash
npm test --prefix frontend -- locales.test.ts
```

Expected result: PASS. If it fails in `keeps UI translation keys complete for every locale`, one locale object is missing `footerAriaLabel`.

---

### Task 3: Add Compact Footer Styles

**Files:**
- Modify: `frontend/src/App.css`

- [ ] **Step 1: Add the bottom panel base styles**

In `frontend/src/App.css`, add these styles near `.source-link` or before the media queries:

```css
.bottom-panel {
  max-width: 1180px;
  margin: 0 auto;
  padding: 18px 0 0;
  border-top: 1px solid #2c3037;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px 18px;
  flex-wrap: wrap;
  color: #b2ada5;
  font-size: 0.88rem;
}
.bottom-panel-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #f4f0e8;
  text-decoration: none;
}
.bottom-panel-link:hover { color: #5bd6c6; }
.bottom-panel-link:focus-visible { outline: 2px solid #f2b84b; outline-offset: 3px; border-radius: 4px; }
.footer-token {
  direction: ltr;
  unicode-bidi: isolate;
}
.footer-legal { color: #8d948f; }
```

- [ ] **Step 2: Add RTL support**

In the existing RTL selector list that starts with `[dir="rtl"] .topbar,`, add `.bottom-panel`:

```css
[dir="rtl"] .topbar,
[dir="rtl"] .hero,
[dir="rtl"] .metrics-strip,
[dir="rtl"] .brief-grid,
[dir="rtl"] .model-drivers,
[dir="rtl"] .trust-panel,
[dir="rtl"] .waitlist,
[dir="rtl"] .charts,
[dir="rtl"] .bottom-panel {
  direction: rtl;
}
```

- [ ] **Step 3: Add mobile layout**

Inside the existing `@media (max-width: 560px)` block, add:

```css
  .bottom-panel {
    display: grid;
    justify-items: start;
  }
```

- [ ] **Step 4: Add mobile RTL alignment**

After the `@media (max-width: 560px)` block, add:

```css
@media (max-width: 560px) {
  [dir="rtl"] .bottom-panel {
    justify-items: end;
  }
}
```

- [ ] **Step 5: Run the focused frontend test file and verify pass**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result: PASS.

---

### Task 4: Final Verification and Commit

**Files:**
- Verify: `frontend/src/App.tsx`
- Verify: `frontend/src/App.css`
- Verify: `frontend/src/locales.ts`
- Verify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Run all frontend tests**

Run:

```bash
npm test --prefix frontend
```

Expected result: PASS.

- [ ] **Step 2: Run the frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected result: PASS with TypeScript and Vite build completing successfully.

- [ ] **Step 3: Review the diff**

Run:

```bash
git diff -- frontend/src/App.tsx frontend/src/App.css frontend/src/locales.ts frontend/src/App.test.tsx
```

Expected result: The diff only adds the compact Minihub footer, footer styles, localized aria label, and focused tests.

- [ ] **Step 4: Commit the implementation**

Run:

```bash
git add frontend/src/App.tsx frontend/src/App.css frontend/src/locales.ts frontend/src/App.test.tsx
git commit -m "feat: add Minihub bottom panel"
```

Expected result: A scoped commit containing only the issue #31 implementation files.
