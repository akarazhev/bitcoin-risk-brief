# CoinMarketCap Public Source Link Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove implementation-heavy `CSV import` wording from the public UI and show CoinMarketCap as a clean, visible data-source link in the Methodology panel.

**Architecture:** Keep all backend, collector, readiness, and API payload behavior unchanged. Treat this as a frontend presentation change: localized public copy says "validated daily Bitcoin market data", while the Methodology metadata grid adds a `Data source` row linking to CoinMarketCap historical data. Tests lock the user-facing copy, link attributes, and absence of public CSV wording.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, lucide-react.

---

## File Structure

- Modify `frontend/src/App.test.tsx`
  - Responsibility: assert the public Methodology panel uses user-facing data wording, exposes a CoinMarketCap source link, and does not expose `CSV` or `import` copy.
- Modify `frontend/src/locales.ts`
  - Responsibility: add a localized `dataSource` label and replace each locale's `methodologyBody` with non-pipeline public copy.
- Modify `frontend/src/App.tsx`
  - Responsibility: render the CoinMarketCap historical-data link as a fourth metadata item in the Methodology panel.
- Modify `frontend/src/App.css`
  - Responsibility: make the source link fit the existing trust-panel visual language and update the desktop metadata grid from three to four columns.
- Do not modify backend, collector, migrations, API docs, readiness payload types, or source-ingestion code. The underlying source value may remain `coinmarketcap_csv`; only public UI copy changes.

## Product Rules

- Public UI must not say `CoinMarketCap CSV`, `CSV import`, or expose the local file/import mechanism in the Methodology panel.
- Public UI should still name CoinMarketCap as the market-data provider.
- The CoinMarketCap link must point to `https://coinmarketcap.com/currencies/bitcoin/historical-data/`.
- The link must open in a new tab with a safe `rel` attribute.
- The existing Methodology metadata stays visible:
  - `Methodology version`
  - `Latest completed day`
  - `Coverage through`
- The new metadata item is:
  - `Data source`
  - `CoinMarketCap` external link
- Existing localization coverage must stay complete for all supported locales: `en`, `ru`, `zh`, `de`, `fr`, `es`, `ar`.

---

### Task 1: Write Failing UI Tests

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Replace the Methodology test expectations**

In `frontend/src/App.test.tsx`, replace the existing test named `renders methodology reference and no-advice disclaimer` with:

```tsx
test('renders methodology reference, public data-source copy, and no-advice disclaimer', async () => {
  render(<App />)

  expect(await screen.findByText('Methodology')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /methodology/i })).toHaveAttribute('href', '#methodology')

  const methodology = within(screen.getByRole('region', { name: 'Methodology' }))
  expect(methodology.getByText('The public signal uses the canonical BTC risk model and validated daily Bitcoin market data.')).toBeInTheDocument()
  expect(methodology.getByText('crypto-scout-canonical-v1')).toBeInTheDocument()
  expect(methodology.getByText('Data source')).toBeInTheDocument()

  const sourceLink = methodology.getByRole('link', { name: 'CoinMarketCap' })
  expect(sourceLink).toHaveAttribute('href', 'https://coinmarketcap.com/currencies/bitcoin/historical-data/')
  expect(sourceLink).toHaveAttribute('target', '_blank')
  expect(sourceLink).toHaveAttribute('rel', 'noreferrer')

  expect(methodology.queryByText(/CSV/i)).not.toBeInTheDocument()
  expect(methodology.queryByText(/import/i)).not.toBeInTheDocument()
  expect(screen.getByText('Risk levels are scenario outputs for research. They are not financial advice or trading instructions.')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run the targeted test and confirm it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result before implementation:

```text
FAIL  src/App.test.tsx
```

Expected reasons:

```text
Unable to find an element with the text: The public signal uses the canonical BTC risk model and validated daily Bitcoin market data.
Unable to find an accessible element with the role "link" and name "CoinMarketCap"
```

---

### Task 2: Update Localized Public Copy

**Files:**
- Modify: `frontend/src/locales.ts`
- Test: `frontend/src/locales.test.ts`

- [ ] **Step 1: Add the `dataSource` key to the copy type**

In `frontend/src/locales.ts`, update the `Copy` type near the methodology keys:

```ts
  methodology: string
  methodologyLink: string
  methodologyVersion: string
  dataSource: string
  methodologyBody: string
  disclaimer: string
```

- [ ] **Step 2: Update the English methodology copy**

In the English locale object, replace the Methodology block with:

```ts
    methodology: 'Methodology',
    methodologyLink: 'View methodology',
    methodologyVersion: 'Methodology version',
    dataSource: 'Data source',
    methodologyBody: 'The public signal uses the canonical BTC risk model and validated daily Bitcoin market data.',
    disclaimer: 'Risk levels are scenario outputs for research. They are not financial advice or trading instructions.',
```

- [ ] **Step 3: Update the Russian methodology copy**

In the Russian locale object, replace the Methodology block with:

```ts
    methodology: 'Методология',
    methodologyLink: 'Методология',
    methodologyVersion: 'Версия методологии',
    dataSource: 'Источник данных',
    methodologyBody: 'Публичный сигнал использует каноническую BTC risk-модель и валидированные ежедневные рыночные данные Bitcoin.',
    disclaimer: 'Уровни риска — исследовательские сценарии. Это не финансовая рекомендация и не торговая инструкция.',
```

- [ ] **Step 4: Update the Chinese methodology copy**

In the Chinese locale object, replace the Methodology block with:

```ts
    methodology: '方法论',
    methodologyLink: '查看方法论',
    methodologyVersion: '方法论版本',
    dataSource: '数据来源',
    methodologyBody: '公开信号使用标准 BTC 风险模型和经过验证的每日 Bitcoin 市场数据。',
    disclaimer: '风险等级是研究场景输出，不是财务建议或交易指令。',
```

- [ ] **Step 5: Update the German methodology copy**

In the German locale object, replace the Methodology block with:

```ts
    methodology: 'Methodik',
    methodologyLink: 'Methodik ansehen',
    methodologyVersion: 'Methodikversion',
    dataSource: 'Datenquelle',
    methodologyBody: 'Das öffentliche Signal nutzt das kanonische BTC-Risikomodell und validierte tägliche Bitcoin-Marktdaten.',
    disclaimer: 'Risikostufen sind Szenarioausgaben für Research. Sie sind keine Finanzberatung oder Handelsanweisung.',
```

- [ ] **Step 6: Update the French methodology copy**

In the French locale object, replace the Methodology block with:

```ts
    methodology: 'Méthodologie',
    methodologyLink: 'Voir la méthodologie',
    methodologyVersion: 'Version de la méthodologie',
    dataSource: 'Source de données',
    methodologyBody: 'Le signal public utilise le modèle de risque BTC canonique et des données quotidiennes validées du marché Bitcoin.',
    disclaimer: 'Les niveaux de risque sont des sorties de scénarios pour la recherche. Ils ne sont pas des conseils financiers ni des instructions de trading.',
```

- [ ] **Step 7: Update the Spanish methodology copy**

In the Spanish locale object, replace the Methodology block with:

```ts
    methodology: 'Metodología',
    methodologyLink: 'Ver metodología',
    methodologyVersion: 'Versión de metodología',
    dataSource: 'Fuente de datos',
    methodologyBody: 'La señal pública usa el modelo canónico de riesgo BTC y datos diarios validados del mercado de Bitcoin.',
    disclaimer: 'Los niveles de riesgo son salidas de escenarios para investigación. No son asesoramiento financiero ni instrucciones de trading.',
```

- [ ] **Step 8: Update the Arabic methodology copy**

In the Arabic locale object, replace the Methodology block with:

```ts
    methodology: 'المنهجية',
    methodologyLink: 'عرض المنهجية',
    methodologyVersion: 'إصدار المنهجية',
    dataSource: 'مصدر البيانات',
    methodologyBody: 'تستخدم الإشارة العامة نموذج مخاطر BTC المعتمد وبيانات سوق Bitcoin اليومية التي تم التحقق منها.',
    disclaimer: 'مستويات المخاطر هي مخرجات سيناريوهات للبحث وليست نصيحة مالية أو تعليمات تداول.',
```

- [ ] **Step 9: Run locale tests**

Run:

```bash
npm test --prefix frontend -- locales.test.ts
```

Expected result:

```text
PASS  src/locales.test.ts
```

If this fails with missing keys, re-check that every locale has exactly one `dataSource` key.

---

### Task 3: Render the CoinMarketCap Source Link

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add a module-level source URL constant**

In `frontend/src/App.tsx`, add this constant near the other top-level constants, before `const riskColors`:

```tsx
const COINMARKETCAP_HISTORICAL_DATA_URL = 'https://coinmarketcap.com/currencies/bitcoin/historical-data/'
```

- [ ] **Step 2: Add the source metadata row**

In the Methodology panel `<dl>` in `frontend/src/App.tsx`, change:

```tsx
          <dl>
            <div><dt>{t.methodologyVersion}</dt><dd>{methodologyVersion}</dd></div>
            <div><dt>{t.latestCompletedDay}</dt><dd>{readiness.data.latest_date ? <NumericValue>{readiness.data.latest_date}</NumericValue> : t.unavailable}</dd></div>
            <div><dt>{t.coverageThrough}</dt><dd>{readiness.data.covered_end ? <NumericValue>{readiness.data.covered_end}</NumericValue> : t.unavailable}</dd></div>
          </dl>
```

to:

```tsx
          <dl>
            <div><dt>{t.methodologyVersion}</dt><dd>{methodologyVersion}</dd></div>
            <div><dt>{t.dataSource}</dt><dd><a className="source-link" href={COINMARKETCAP_HISTORICAL_DATA_URL} target="_blank" rel="noreferrer">CoinMarketCap <ExternalLink size={14} aria-hidden="true" /></a></dd></div>
            <div><dt>{t.latestCompletedDay}</dt><dd>{readiness.data.latest_date ? <NumericValue>{readiness.data.latest_date}</NumericValue> : t.unavailable}</dd></div>
            <div><dt>{t.coverageThrough}</dt><dd>{readiness.data.covered_end ? <NumericValue>{readiness.data.covered_end}</NumericValue> : t.unavailable}</dd></div>
          </dl>
```

- [ ] **Step 3: Run the App test**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected result after Tasks 2 and 3:

```text
PASS  src/App.test.tsx
```

---

### Task 4: Polish Trust Panel Layout and Link Styling

**Files:**
- Modify: `frontend/src/App.css`
- Test: visual inspection via built CSS and frontend tests

- [ ] **Step 1: Update the desktop metadata grid to four columns**

In `frontend/src/App.css`, replace:

```css
.trust-panel dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 0; }
```

with:

```css
.trust-panel dl { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 0; }
```

- [ ] **Step 2: Add source-link styling**

In `frontend/src/App.css`, add these rules immediately after the existing `.trust-panel dd` rule:

```css
.source-link { display: inline-flex; width: fit-content; align-items: center; gap: 6px; color: #f4f0e8; text-decoration: none; }
.source-link:hover { color: #5bd6c6; }
.source-link:focus-visible { outline: 2px solid #f2b84b; outline-offset: 3px; border-radius: 4px; }
[dir="rtl"] .source-link { flex-direction: row-reverse; }
```

- [ ] **Step 3: Confirm mobile behavior remains stacked**

Verify this existing media rule is still present and unchanged:

```css
@media (max-width: 900px) {
  .trust-panel dl { grid-template-columns: 1fr; }
}
```

Expected result: desktop shows four compact metadata tiles; mobile remains one metadata tile per row.

---

### Task 5: Final Verification

**Files:**
- Verify: `frontend/src/App.test.tsx`
- Verify: `frontend/src/locales.test.ts`
- Verify: `frontend/src/App.tsx`
- Verify: `frontend/src/App.css`

- [ ] **Step 1: Run focused frontend tests**

Run:

```bash
npm test --prefix frontend -- App.test.tsx locales.test.ts
```

Expected result:

```text
PASS  src/App.test.tsx
PASS  src/locales.test.ts
```

- [ ] **Step 2: Run the frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected result:

```text
✓ built in
```

The exact build duration may differ.

- [ ] **Step 3: Inspect the final diff**

Run:

```bash
git diff -- frontend/src/App.test.tsx frontend/src/locales.ts frontend/src/App.tsx frontend/src/App.css
```

Expected diff characteristics:

```text
frontend/src/App.test.tsx: Methodology test expects public data copy and CoinMarketCap link.
frontend/src/locales.ts: dataSource key added for all locales; methodologyBody no longer mentions CSV/import.
frontend/src/App.tsx: Methodology metadata grid renders CoinMarketCap source link.
frontend/src/App.css: Trust metadata grid uses four desktop columns; source-link styling added.
```

- [ ] **Step 4: Commit the implementation**

Run:

```bash
git add frontend/src/App.test.tsx frontend/src/locales.ts frontend/src/App.tsx frontend/src/App.css
git commit -m "fix: clean up public data source copy"
```

Expected result:

```text
[branch-name commit-sha] fix: clean up public data source copy
```

---

## Self-Review

- Spec coverage: The plan removes public CSV/import wording, adds a visible CoinMarketCap source link, preserves existing trust metadata, localizes the new label and body copy, and verifies with frontend tests plus build.
- Placeholder scan: Placeholder wording, copied-task shortcuts, and vague follow-up markers are absent.
- Type consistency: The new locale key is consistently named `dataSource`, referenced as `t.dataSource`, and covered by the existing locale key-completeness test.
