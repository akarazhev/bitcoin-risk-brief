# Issue 38 Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the two code review findings on the custom language listbox before merging issue #38.

**Architecture:** Keep the existing `LanguageSelect` component and add narrowly scoped behavior: Tab closes the open listbox without trapping focus, and every visible language option label is isolated as LTR text. Add focused Vitest coverage in `App.test.tsx`; no new component split, dependency, or styling system is needed.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, existing CSS in `frontend/src/App.css`.

## Global Constraints

- Do not add a new UI dependency.
- Keep the compact trigger behavior from issue #38.
- Preserve all existing locale, `document.lang`, `document.dir`, Arabic RTL, and numeric/date/currency isolation behavior.
- Do not change `localeOptions` labels or ordering.
- Do not trap keyboard focus in the language menu.
- `Tab` from the open listbox must close the menu and allow the browser to continue normal focus navigation.
- Mixed-direction option text such as `AR - العربية` must render in stable left-to-right order in RTL page context.
- Run `npm test --prefix frontend`, `npm run build --prefix frontend`, `npm run smoke --prefix frontend`, and `git diff --check` before final handoff.

---

## File Structure

- Modify `frontend/src/LanguageSelect.tsx`: add Tab close handling and wrap option text in `<bdi dir="ltr">`.
- Modify `frontend/src/App.test.tsx`: add focused regression tests for Tab close behavior and LTR isolation of mixed-direction option labels.
- Do not modify `frontend/src/locales.ts`, `frontend/src/App.tsx`, or `frontend/src/App.css` unless a test proves they are required for these two findings.

---

### Task 1: Close Listbox On Tab Without Trapping Focus

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/LanguageSelect.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: existing `LanguageSelect` keyboard handling in `handleListboxKeyDown(event: ReactKeyboardEvent<HTMLUListElement>)`.
- Produces: `Tab` key handling that calls `setOpen(false)` and does not call `event.preventDefault()` or `buttonRef.current?.focus()`.

- [ ] **Step 1: Add the failing Tab regression test**

In `frontend/src/App.test.tsx`, add this test immediately after `test('opens and closes the custom language listbox from keyboard and outside pointer interaction', async () => { ... })`:

```tsx
test('closes the custom language listbox on Tab without returning focus to the trigger', async () => {
  render(<App />)

  const trigger = await screen.findByRole('button', { name: /select language: english/i })
  fireEvent.keyDown(trigger, { key: 'Enter' })

  const listbox = await screen.findByRole('listbox', { name: /select language/i })
  expect(listbox).toHaveFocus()
  expect(trigger).toHaveAttribute('aria-expanded', 'true')

  fireEvent.keyDown(listbox, { key: 'Tab' })

  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(trigger).toHaveAttribute('aria-expanded', 'false')
  expect(trigger).not.toHaveFocus()
})
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "closes the custom language listbox on Tab"
```

Expected: FAIL because the current `handleListboxKeyDown` does not close the listbox on `Tab`.

- [ ] **Step 3: Implement Tab close behavior**

In `frontend/src/LanguageSelect.tsx`, update `handleListboxKeyDown` so the first branch handles `Tab`:

```tsx
  const handleListboxKeyDown = (event: ReactKeyboardEvent<HTMLUListElement>) => {
    if (event.key === 'Tab') {
      setOpen(false)
      return
    }

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
```

Do not call `event.preventDefault()` for `Tab`. Do not focus `buttonRef` for `Tab`.

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "closes the custom language listbox on Tab"
```

Expected: PASS.

- [ ] **Step 5: Check related keyboard tests**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "custom language listbox"
```

Expected: PASS.

- [ ] **Step 6: Commit or report Task 1**

If issue #38 implementation is already committed in your working branch, commit this review fix:

```bash
git add frontend/src/LanguageSelect.tsx frontend/src/App.test.tsx
git commit -m "fix: close language listbox on tab"
```

If issue #38 implementation is still uncommitted, do not create a misleading partial commit. Leave the files unstaged and report that Task 1 changed `frontend/src/LanguageSelect.tsx` and `frontend/src/App.test.tsx`.

---

### Task 2: Isolate Mixed-Direction Option Labels As LTR

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/LanguageSelect.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `option.shortLabel` strings from `localeOptions`.
- Produces: option text rendered as `<bdi dir="ltr">{option.shortLabel}</bdi>` inside each `role="option"` list item.

- [ ] **Step 1: Add the failing LTR isolation regression test**

In `frontend/src/App.test.tsx`, add this test immediately after `test('supports arrow navigation and keyboard selection in the custom language listbox', async () => { ... })`:

```tsx
test('isolates mixed-direction language option labels as LTR while Arabic is active', async () => {
  render(<App />)

  await selectLanguage(/^AR -/)
  fireEvent.click(getLanguageTrigger())

  const listbox = await screen.findByRole('listbox')
  const arabicOption = within(listbox).getByRole('option', { name: /^AR - العربية$/ })
  const isolatedLabel = arabicOption.querySelector('bdi')

  expect(isolatedLabel).not.toBeNull()
  expect(isolatedLabel as HTMLElement).toHaveAttribute('dir', 'ltr')
  expect(isolatedLabel as HTMLElement).toHaveTextContent('AR - العربية')
})
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "isolates mixed-direction language option labels"
```

Expected: FAIL because the current option label is plain text and no `<bdi dir="ltr">` exists.

- [ ] **Step 3: Wrap option text in an LTR isolation element**

In `frontend/src/LanguageSelect.tsx`, replace this option body:

```tsx
              {option.shortLabel}
```

with:

```tsx
              <bdi dir="ltr">{option.shortLabel}</bdi>
```

The containing `<li>` must keep its existing `role="option"`, `aria-selected`, `onClick`, and `onMouseMove` behavior.

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "isolates mixed-direction language option labels"
```

Expected: PASS.

- [ ] **Step 5: Verify all language selector tests together**

Run:

```bash
npm test --prefix frontend -- App.test.tsx -t "language|locale|Arabic|localized|custom language|mixed-direction|Tab"
```

Expected: PASS.

- [ ] **Step 6: Commit or report Task 2**

If issue #38 implementation is already committed in your working branch, commit this review fix:

```bash
git add frontend/src/LanguageSelect.tsx frontend/src/App.test.tsx
git commit -m "fix: isolate language option labels"
```

If issue #38 implementation is still uncommitted, do not create a misleading partial commit. Leave the files unstaged and report that Task 2 changed `frontend/src/LanguageSelect.tsx` and `frontend/src/App.test.tsx`.

---

### Task 3: Final Verification

**Files:**
- Read: `frontend/src/LanguageSelect.tsx`
- Read: `frontend/src/App.test.tsx`
- Test: frontend verification commands

**Interfaces:**
- Consumes: completed Task 1 and Task 2 changes.
- Produces: final evidence that review findings are fixed and existing frontend behavior still passes.

- [ ] **Step 1: Confirm both review fixes are present**

Run:

```bash
rg -n "event.key === 'Tab'|<bdi dir=\"ltr\">\\{option.shortLabel\\}</bdi>|mixed-direction language option labels|listbox on Tab" frontend/src/LanguageSelect.tsx frontend/src/App.test.tsx
```

Expected output includes all four concepts:

```text
frontend/src/LanguageSelect.tsx:...event.key === 'Tab'
frontend/src/LanguageSelect.tsx:...<bdi dir="ltr">{option.shortLabel}</bdi>
frontend/src/App.test.tsx:...closes the custom language listbox on Tab without returning focus to the trigger
frontend/src/App.test.tsx:...isolates mixed-direction language option labels as LTR while Arabic is active
```

- [ ] **Step 2: Check for stale native selector assumptions**

Run:

```bash
rg -n "language-select select|<select|</select|<option|</option|combobox" frontend/src frontend/e2e
```

Expected: no output.

- [ ] **Step 3: Run full frontend unit tests**

Run:

```bash
npm test --prefix frontend
```

Expected: PASS with 57 or more tests passing.

- [ ] **Step 4: Run frontend production build**

Run:

```bash
npm run build --prefix frontend
```

Expected: PASS.

- [ ] **Step 5: Run frontend smoke tests**

Run:

```bash
npm run smoke --prefix frontend
```

Expected: PASS with 30 or more browser tests passing.

If this fails only because the sandbox blocks the local preview server with `listen EPERM: operation not permitted 127.0.0.1:4173`, rerun the same command with the required sandbox escalation and record both the initial sandbox failure and the successful rerun.

- [ ] **Step 6: Check whitespace**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 7: Final report**

Report:

```text
Fixed review findings:
- Tab closes the open language listbox without trapping focus.
- Mixed-direction language option labels are isolated with <bdi dir="ltr">.

Verification:
- npm test --prefix frontend: PASS
- npm run build --prefix frontend: PASS
- npm run smoke --prefix frontend: PASS
- git diff --check: clean
```

If a verification command fails, report the exact failing command and stop before claiming the review fixes are complete.

## Suggested `/goal` Objective

Implement the review fixes for GitHub issue #38 by following `docs/superpowers/plans/2026-07-16-issue-38-review-fixes.md`: make Tab close the custom language listbox without trapping focus, isolate mixed-direction language option labels as LTR, add focused Vitest regression tests, and verify with `npm test --prefix frontend`, `npm run build --prefix frontend`, `npm run smoke --prefix frontend`, and `git diff --check`.
