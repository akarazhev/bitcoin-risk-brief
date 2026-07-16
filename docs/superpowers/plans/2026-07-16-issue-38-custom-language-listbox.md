# Issue 38 Custom Language Listbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the native language `<select>` with an app-styled accessible custom language button and listbox.

**Architecture:** Add a focused `LanguageSelect` React component that owns menu open state, active option state, outside-click close behavior, and keyboard handling. `App.tsx` continues to own the selected `locale` state and document `lang`/`dir` effects; `localeOptions` remains the single source of truth for supported languages.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, lucide-react icons, existing CSS in `frontend/src/App.css`.

## Global Constraints

- Do not add a new UI dependency.
- Closed trigger must be compact: show the locale code such as `EN`, `RU`, `ZH`, or `AR`, not the full language label.
- Open listbox must use app-controlled dark styling and show the existing full `shortLabel` values from `localeOptions`.
- Preserve current locale options, labels, selected locale state, `document.documentElement.lang`, and `document.documentElement.dir`.
- Preserve Arabic RTL behavior and existing LTR isolation for numeric, date, currency, email, and handle values.
- Trigger must expose the selected language and expanded/collapsed state to assistive technology.
- Keyboard support must include Enter/Space to open, Arrow Up/Down to navigate, Enter/Space to select, and Escape to close.
- The menu must close on outside pointer interaction and after selection.
- Focus states must remain visible and match the rest of the app.
- Run `npm test --prefix frontend` and `npm run build --prefix frontend` before final handoff.

---

## File Structure

- Create `frontend/src/LanguageSelect.tsx`: custom language selector component. It receives `locale`, `options`, localized `label`, and `onLocaleChange`.
- Modify `frontend/src/App.tsx`: remove direct native `<select>` markup and render `LanguageSelect`.
- Modify `frontend/src/App.css`: replace native select styling with trigger, menu, option, focus, RTL, and mobile styles.
- Modify `frontend/src/App.test.tsx`: replace `combobox` test queries, add listbox click and keyboard coverage, and update CSS assertions.

---

### Task 1: Add Click-Selectable Custom Language Component

**Files:**
- Create: `frontend/src/LanguageSelect.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `Locale` from `frontend/src/types.ts`; `LocaleOption` from `frontend/src/locales.ts`; `localeOptions` and `copy[locale].languageSelector` from `App.tsx`.
- Produces: `LanguageSelect({ label, locale, options, onLocaleChange })`, where `onLocaleChange` is `(locale: Locale) => void`.

- [ ] **Step 1: Add test helpers for the custom selector**

Add these helpers near the other helper functions in `frontend/src/App.test.tsx`, after `textContentMatcher`:

```tsx
function getLanguageTrigger() {
  const trigger = document.querySelector<HTMLButtonElement>('.language-trigger')
  expect(trigger).not.toBeNull()
  return trigger as HTMLButtonElement
}

async function openLanguageMenu() {
  fireEvent.click(getLanguageTrigger())
  return screen.findByRole('listbox')
}

async function selectLanguage(optionName: RegExp | string) {
  fireEvent.click(getLanguageTrigger())
  fireEvent.click(await screen.findByRole('option', { name: optionName }))
}
```

- [ ] **Step 2: Replace the core native-select locale test with a listbox test**

Replace the body of `test('offers all issue 28 languages and applies document language metadata', async () => { ... })` in `frontend/src/App.test.tsx` with:

```tsx
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  expect(trigger).toHaveTextContent('EN')
  expect(trigger).toHaveAttribute('aria-haspopup', 'listbox')
  expect(trigger).toHaveAttribute('aria-expanded', 'false')

  fireEvent.click(trigger)
  expect(trigger).toHaveAttribute('aria-expanded', 'true')
  const listbox = screen.getByRole('listbox', { name: /select language/i })
  expect(within(listbox).getAllByRole('option').map((option) => option.textContent)).toEqual([
    'EN - English',
    'RU - Русский',
    'ZH - 简体中文',
    'DE - Deutsch',
    'FR - Français',
    'ES - Español',
    'AR - العربية',
  ])

  fireEvent.click(within(listbox).getByRole('option', { name: /^DE -/ }))
  expect(await screen.findByText('Aktuelles Risiko')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'de')
  expect(document.documentElement).toHaveAttribute('dir', 'ltr')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(getLanguageTrigger()).toHaveTextContent('DE')

  await selectLanguage(/^FR -/)
  expect(await screen.findByText('Risque actuel')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'fr')
  expect(getLanguageTrigger()).toHaveTextContent('FR')

  await selectLanguage(/^ES -/)
  expect(await screen.findByText('Riesgo actual')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'es')
  expect(getLanguageTrigger()).toHaveTextContent('ES')

  await selectLanguage(/^ZH -/)
  expect(await screen.findByText('当前风险')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'zh-CN')
  expect(getLanguageTrigger()).toHaveTextContent('ZH')

  await selectLanguage(/^AR -/)
  expect(await screen.findByText('المخاطر الحالية')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ar')
  expect(document.documentElement).toHaveAttribute('dir', 'rtl')
  expect(getLanguageTrigger()).toHaveTextContent('AR')
```

- [ ] **Step 3: Run the focused test to confirm it fails against the native select**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "offers all issue 28 languages"
```

Expected: FAIL because the current control has role `combobox`, not role `button` with a `listbox`.

- [ ] **Step 4: Create `LanguageSelect.tsx` with click selection and ARIA state**

Create `frontend/src/LanguageSelect.tsx` with:

```tsx
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent as ReactKeyboardEvent } from 'react'
import { Languages } from 'lucide-react'
import type { LocaleOption } from './locales'
import type { Locale } from './types'

type LanguageSelectProps = {
  label: string
  locale: Locale
  options: readonly LocaleOption[]
  onLocaleChange: (locale: Locale) => void
}

function wrappedIndex(index: number, length: number) {
  return (index + length) % length
}

function optionId(listboxId: string, option: LocaleOption) {
  return `${listboxId}-${option.code}`
}

export function LanguageSelect({ label, locale, options, onLocaleChange }: LanguageSelectProps) {
  const listboxId = useId()
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const listboxRef = useRef<HTMLUListElement>(null)
  const selectedIndex = Math.max(options.findIndex((option) => option.code === locale), 0)
  const selectedOption = options[selectedIndex] ?? options[0]
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(selectedIndex)
  const activeOption = options[activeIndex] ?? selectedOption

  useEffect(() => {
    if (!open) setActiveIndex(selectedIndex)
  }, [open, selectedIndex])

  useEffect(() => {
    if (!open) return
    listboxRef.current?.focus()
  }, [open])

  useEffect(() => {
    if (!open) return

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target
      if (target && rootRef.current && !rootRef.current.contains(target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [open])

  const selectedLabel = useMemo(() => `${label}: ${selectedOption.label}`, [label, selectedOption.label])

  const openMenu = (nextActiveIndex = selectedIndex) => {
    setActiveIndex(nextActiveIndex)
    setOpen(true)
  }

  const selectOption = (option: LocaleOption) => {
    onLocaleChange(option.code)
    setOpen(false)
    buttonRef.current?.focus()
  }

  const handleButtonKeyDown = (event: ReactKeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openMenu(selectedIndex)
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      openMenu(wrappedIndex(selectedIndex + 1, options.length))
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      openMenu(wrappedIndex(selectedIndex - 1, options.length))
    }
  }

  const handleListboxKeyDown = (event: ReactKeyboardEvent<HTMLUListElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((index) => wrappedIndex(index + 1, options.length))
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => wrappedIndex(index - 1, options.length))
    }

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      selectOption(activeOption)
    }

    if (event.key === 'Escape') {
      event.preventDefault()
      setOpen(false)
      buttonRef.current?.focus()
    }
  }

  return (
    <div className="language-select" ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className="language-trigger"
        aria-label={selectedLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listboxId : undefined}
        onClick={() => (open ? setOpen(false) : openMenu(selectedIndex))}
        onKeyDown={handleButtonKeyDown}
      >
        <Languages size={16} aria-hidden="true" />
        <span className="language-code" aria-hidden="true">{selectedOption.code.toUpperCase()}</span>
      </button>
      {open ? (
        <ul
          ref={listboxRef}
          id={listboxId}
          className="language-menu"
          role="listbox"
          aria-label={label}
          aria-activedescendant={optionId(listboxId, activeOption)}
          tabIndex={-1}
          onKeyDown={handleListboxKeyDown}
        >
          {options.map((option, index) => (
            <li
              key={option.code}
              id={optionId(listboxId, option)}
              className={`language-option${index === activeIndex ? ' is-active' : ''}`}
              role="option"
              aria-selected={option.code === locale}
              onClick={() => selectOption(option)}
              onMouseMove={() => setActiveIndex(index)}
            >
              {option.shortLabel}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
```

- [ ] **Step 5: Replace the native selector in `App.tsx`**

In `frontend/src/App.tsx`, change the imports:

```tsx
import { Bell, CheckCircle2, ExternalLink, Radio, Send, ShieldAlert, TriangleAlert } from 'lucide-react'
import { LanguageSelect } from './LanguageSelect'
```

Replace the current `<label className="language-select">...</label>` block with:

```tsx
          <LanguageSelect
            label={t.languageSelector}
            locale={locale}
            options={localeOptions}
            onLocaleChange={setLocale}
          />
```

- [ ] **Step 6: Run the focused test again**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "offers all issue 28 languages"
```

Expected: PASS.

- [ ] **Step 7: Commit Task 1**

```bash
git add frontend/src/LanguageSelect.tsx frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "feat: replace language select with custom listbox"
```

---

### Task 2: Migrate Existing Locale Tests And Add Keyboard Coverage

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `getLanguageTrigger`, `openLanguageMenu`, and `selectLanguage` helpers from Task 1.
- Produces: frontend test coverage for click selection, keyboard opening, keyboard selection, Escape close, outside close, and existing locale-dependent workflows.

- [ ] **Step 1: Replace every remaining native `combobox` selector interaction**

Run:

```bash
rg -n "combobox|fireEvent.change\\(languageSelector|fireEvent.change\\(selector" frontend/src/App.test.tsx
```

For each remaining language selector interaction, replace the native change with `await selectLanguage(...)`. Use these exact replacements:

```tsx
await selectLanguage(/^RU -/)
await selectLanguage(/^FR -/)
await selectLanguage(/^AR -/)
await selectLanguage(/^DE -/)
```

The affected tests are:

```text
localizes accessible chart labels and unavailable methodology metadata -> await selectLanguage(/^RU -/)
localizes the privacy terms and disclaimer note -> await selectLanguage(/^RU -/)
renders localized model drivers from latest risk component directions -> await selectLanguage(/^RU -/)
preserves English and Russian labels for the price input group -> await selectLanguage(/^RU -/)
isolates visible Arabic numeric, date, and currency values as LTR -> await selectLanguage(/^AR -/)
isolates visible Arabic degraded freshness counts as LTR -> await selectLanguage(/^AR -/)
submits the selected expanded locale to the waitlist API -> await selectLanguage(/^FR -/)
keeps Arabic waitlist contact entry LTR and submits locale metadata -> await selectLanguage(/^AR -/)
falls back to the English generated brief when selected locale is absent from an old snapshot -> await selectLanguage(/^DE -/)
```

After the replacements, the command must return no matches:

```bash
rg -n "combobox|fireEvent.change\\(languageSelector|fireEvent.change\\(selector" frontend/src/App.test.tsx
```

Expected: no output.

- [ ] **Step 2: Add keyboard open, Escape close, and outside close coverage**

Add this test after `offers all issue 28 languages and applies document language metadata`:

```tsx
test('opens and closes the custom language listbox from keyboard and outside pointer interaction', async () => {
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  fireEvent.keyDown(trigger, { key: 'Enter' })

  const listbox = await screen.findByRole('listbox', { name: /select language/i })
  expect(listbox).toHaveFocus()
  expect(trigger).toHaveAttribute('aria-expanded', 'true')

  fireEvent.keyDown(listbox, { key: 'Escape' })
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(trigger).toHaveFocus()
  expect(trigger).toHaveAttribute('aria-expanded', 'false')

  fireEvent.keyDown(trigger, { key: ' ' })
  expect(await screen.findByRole('listbox')).toBeInTheDocument()
  fireEvent.pointerDown(document.body)
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(trigger).toHaveAttribute('aria-expanded', 'false')
})
```

- [ ] **Step 3: Add arrow navigation and keyboard selection coverage**

Add this test after the open/close keyboard test:

```tsx
test('supports arrow navigation and keyboard selection in the custom language listbox', async () => {
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  fireEvent.keyDown(trigger, { key: 'ArrowDown' })

  let listbox = await screen.findByRole('listbox', { name: /select language/i })
  expect(listbox.getAttribute('aria-activedescendant')).toMatch(/-ru$/)

  fireEvent.keyDown(listbox, { key: ' ' })
  expect(await screen.findByText('Текущий риск')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ru')
  expect(document.documentElement).toHaveAttribute('dir', 'ltr')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(getLanguageTrigger()).toHaveFocus()

  fireEvent.keyDown(getLanguageTrigger(), { key: 'ArrowUp' })
  listbox = await screen.findByRole('listbox')
  expect(listbox.getAttribute('aria-activedescendant')).toMatch(/-en$/)
  fireEvent.keyDown(listbox, { key: 'ArrowUp' })
  expect(listbox.getAttribute('aria-activedescendant')).toMatch(/-ar$/)
  fireEvent.keyDown(listbox, { key: 'Enter' })

  expect(await screen.findByText('المخاطر الحالية')).toBeInTheDocument()
  expect(document.documentElement).toHaveAttribute('lang', 'ar')
  expect(document.documentElement).toHaveAttribute('dir', 'rtl')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})
```

- [ ] **Step 4: Run the locale and keyboard test subset**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "language|locale|Arabic|localized|custom language"
```

Expected: PASS.

- [ ] **Step 5: Run the full frontend test suite**

Run:

```bash
npm test --prefix frontend
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

```bash
git add frontend/src/App.test.tsx
git commit -m "test: cover custom language listbox interactions"
```

---

### Task 3: Add App-Controlled Styling And Final Verification

**Files:**
- Modify: `frontend/src/App.css`
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: class names from Task 1: `.language-select`, `.language-trigger`, `.language-code`, `.language-menu`, `.language-option`, `.language-option.is-active`.
- Produces: app-controlled topbar trigger, dark listbox panel, visible focus states, RTL menu alignment, and CSS regression assertions.

- [ ] **Step 1: Update CSS focus-state test expectations**

In `test('defines visible keyboard focus states for interactive controls', () => { ... })`, replace:

```tsx
  expect(css).toContain('.language-select select:focus-visible')
```

with:

```tsx
  expect(css).toContain('.language-trigger:focus-visible')
  expect(css).toContain('.language-menu:focus-visible')
```

- [ ] **Step 2: Add a CSS regression test for custom listbox styling**

Add this test after the focus-state test:

```tsx
test('defines app-controlled language listbox styling', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.language-select { position: relative')
  expect(css).toContain('.language-trigger')
  expect(css).toContain('.language-menu')
  expect(css).toContain('.language-option.is-active')
  expect(css).toContain('[dir="rtl"] .language-menu')
})
```

- [ ] **Step 3: Replace native select styles with custom trigger and menu styles**

In `frontend/src/App.css`, replace the existing language selector rules:

```css
.brand, .language-select, .methodology-link { display: inline-flex; gap: 8px; align-items: center; color: #c8c4bd; }
.top-actions { display: inline-flex; align-items: center; gap: 10px; }
.methodology-link { border: 1px solid #30343b; background: rgba(21, 23, 27, 0.76); color: #f4f0e8; padding: 9px 12px; border-radius: 8px; text-decoration: none; }
.language-select { border: 1px solid #30343b; background: #15171b; color: #f4f0e8; padding: 0 10px; border-radius: 8px; }
.language-select svg { color: #c8c4bd; }
.language-select select { min-height: 38px; border: 0; background: transparent; color: #f4f0e8; font: inherit; font-weight: 800; cursor: pointer; }
.language-select select:focus-visible, .methodology-link:focus-visible, .lead-form input:focus-visible, .lead-form button:focus-visible, .privacy-note summary:focus-visible { outline: 2px solid #f2b84b; outline-offset: 3px; }
```

with:

```css
.brand, .language-select, .methodology-link { display: inline-flex; gap: 8px; align-items: center; color: #c8c4bd; }
.top-actions { display: inline-flex; align-items: center; gap: 10px; }
.methodology-link { border: 1px solid #30343b; background: rgba(21, 23, 27, 0.76); color: #f4f0e8; padding: 9px 12px; border-radius: 8px; text-decoration: none; }
.language-select { position: relative; border: 1px solid #30343b; background: #15171b; color: #f4f0e8; padding: 0; border-radius: 8px; }
.language-trigger {
  min-height: 38px;
  border: 0;
  background: transparent;
  color: #f4f0e8;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 10px;
}
.language-trigger svg { color: #c8c4bd; }
.language-code { min-width: 2ch; text-align: center; letter-spacing: 0; }
.language-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 20;
  min-width: 180px;
  margin: 0;
  padding: 6px;
  list-style: none;
  border: 1px solid #30343b;
  border-radius: 8px;
  background: #15171b;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.36);
}
.language-option {
  border-radius: 6px;
  color: #c8c4bd;
  cursor: pointer;
  font-weight: 700;
  padding: 9px 10px;
  white-space: nowrap;
}
.language-option:hover,
.language-option.is-active {
  background: #242830;
  color: #f4f0e8;
}
.language-option[aria-selected="true"] {
  color: #f2b84b;
}
.language-trigger:focus-visible, .language-menu:focus-visible, .methodology-link:focus-visible, .lead-form input:focus-visible, .lead-form button:focus-visible, .privacy-note summary:focus-visible { outline: 2px solid #f2b84b; outline-offset: 3px; }
```

- [ ] **Step 4: Add RTL rules for the trigger and menu**

In the existing RTL flex-direction selector, add `.language-trigger`:

```css
[dir="rtl"] .top-actions,
[dir="rtl"] .brand,
[dir="rtl"] .methodology-link,
[dir="rtl"] .language-select,
[dir="rtl"] .language-trigger,
[dir="rtl"] .readiness-badge,
[dir="rtl"] .lead-form button,
[dir="rtl"] .privacy-note summary {
  flex-direction: row-reverse;
}
```

Add this rule after that block:

```css
[dir="rtl"] .language-menu {
  right: auto;
  left: 0;
  text-align: right;
}
```

- [ ] **Step 5: Confirm no native selector references remain**

Run:

```bash
rg -n "language-select select|<select|</select|<option|</option|combobox" frontend/src
```

Expected: no output.

- [ ] **Step 6: Run full frontend verification**

Run:

```bash
npm test --prefix frontend
npm run build --prefix frontend
```

Expected: both commands PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add frontend/src/App.css frontend/src/App.test.tsx
git commit -m "style: add custom language listbox styling"
```

---

## Final Review Checklist

- [ ] `frontend/src/App.tsx` no longer renders a native `<select>` for language selection.
- [ ] The closed control shows a compact locale code.
- [ ] The open menu shows all existing `localeOptions` full `shortLabel` values.
- [ ] Trigger exposes selected language through its accessible name and exposes expanded state through `aria-expanded`.
- [ ] Click selection updates translated content and document language metadata.
- [ ] Keyboard interaction covers Enter, Space, Arrow Down, Arrow Up, and Escape.
- [ ] Outside pointer interaction closes the menu.
- [ ] Arabic sets `document.documentElement.dir` to `rtl`.
- [ ] Existing numeric/date/currency isolation tests still pass.
- [ ] `npm test --prefix frontend` passes.
- [ ] `npm run build --prefix frontend` passes.

## Suggested `/goal` Objective

Implement GitHub issue #38 by following `docs/superpowers/plans/2026-07-16-issue-38-custom-language-listbox.md`: replace the native frontend language select with a compact custom accessible listbox, preserve all locale and RTL behavior, update tests, and verify with `npm test --prefix frontend` plus `npm run build --prefix frontend`.
