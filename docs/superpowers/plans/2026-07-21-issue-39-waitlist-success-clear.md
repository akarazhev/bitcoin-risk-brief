# Waitlist Success Clear Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear the waitlist contact input after a successful submission while preserving inline success and error behavior.

**Architecture:** The waitlist form is controlled by React state in `frontend/src/App.tsx`. Keep the existing inline `role="status"` success confirmation and `role="alert"` error path, and only clear the `lead` state after `joinWaitlist(...)` resolves successfully. Cover the success and failure paths with focused Vitest/Testing Library assertions in `frontend/src/App.test.tsx`.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, `@testing-library/jest-dom`.

## Global Constraints

- Successful waitlist submission clears the `email or @telegram` input.
- Successful waitlist submission still shows the localized success message.
- Failed waitlist submission does not clear the input.
- Existing no-browser-storage behavior remains unchanged.
- The behavior is covered by focused frontend tests in `frontend/src/App.test.tsx`.
- `npm test --prefix frontend` passes.
- `npm run build --prefix frontend` passes.
- Do not introduce a modal or popup for this flow; the success message should stay in context and remain accessible.
- Keep the existing loading behavior: disabled button and `aria-busy` while submitting.
- On failed submission, keep the current input value so the visitor can correct it and retry.

---

## File Structure

- Modify `frontend/src/App.tsx`: update `submitWaitlist` so the controlled `lead` input state is cleared only after `joinWaitlist({ contact: value, locale, source: 'landing' })` succeeds.
- Modify `frontend/src/App.test.tsx`: extend existing waitlist tests to prove the input clears on success, the localized inline success message remains visible, and failed submission preserves the entered contact.
- Do not modify backend, collector, migrations, or API client files for this issue.

### Task 1: Cover Waitlist Success And Failure Input State

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: existing mocked `joinWaitlist` API function from `vi.mock('./api', ...)`.
- Consumes: existing controlled waitlist input found by `screen.findByPlaceholderText('email or @telegram')`.
- Produces: failing assertions that require successful submissions to clear the input and failed submissions to preserve it.

- [ ] **Step 1: Update the success-path API submission test**

In `frontend/src/App.test.tsx`, replace the existing `submits waitlist contacts to the backend API` test with this version:

```tsx
test('submits waitlist contacts to the backend API and clears the input on success', async () => {
  render(<App />)

  const input = await screen.findByPlaceholderText('email or @telegram')
  fireEvent.change(input, { target: { value: 'USER@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  await waitFor(() => {
    expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({ contact: 'USER@example.com', locale: 'en', source: 'landing' })
  })
  await waitFor(() => {
    expect(input).toHaveValue('')
  })
  expect(screen.getByRole('status')).toHaveTextContent('Saved. You are on the Bitcoin Risk Brief waitlist.')
})
```

- [ ] **Step 2: Update the error-path test**

In `frontend/src/App.test.tsx`, replace the existing `announces waitlist errors assertively and links them to the input` test with this version:

```tsx
test('announces waitlist errors assertively, links them to the input, and preserves the contact', async () => {
  apiMocks.joinWaitlist.mockRejectedValueOnce(new Error('invalid contact'))
  render(<App />)

  const input = await screen.findByPlaceholderText('email or @telegram')
  fireEvent.change(input, { target: { value: 'not-a-contact' } })
  fireEvent.click(screen.getByRole('button', { name: /join waitlist/i }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Enter a valid email or Telegram handle.')
  expect(input).toHaveAttribute('aria-invalid', 'true')
  expect(input).toHaveAccessibleDescription('Enter a valid email or Telegram handle.')
  expect(input).toHaveValue('not-a-contact')
})
```

- [ ] **Step 3: Run the focused frontend tests and verify the new success assertion fails**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected before implementation: the success-path test fails because the input still has `USER@example.com` after `joinWaitlist(...)` resolves. The error-path test should pass because current behavior already preserves the input on failure.

- [ ] **Step 4: Commit the failing tests**

Only commit if the repository workflow allows committing failing tests before implementation. Otherwise, leave this step unchecked and continue to Task 2.

```bash
git add frontend/src/App.test.tsx
git commit -m "test: cover waitlist input reset behavior"
```

### Task 2: Clear The Controlled Input After Successful Join

**Files:**
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: existing `submitWaitlist(event: FormEvent<HTMLFormElement>)` function.
- Consumes: existing `lead` state from `const [lead, setLead] = useState('')`.
- Produces: success-only call to `setLead('')` after `joinWaitlist(...)` resolves.

- [ ] **Step 1: Update `submitWaitlist` success path**

In `frontend/src/App.tsx`, change the `try` block inside `submitWaitlist` from:

```tsx
try {
  await joinWaitlist({ contact: value, locale, source: 'landing' })
  setJoined(true)
} catch {
  setJoined(false)
  setJoinError(t.joinError)
} finally {
  setJoining(false)
}
```

to:

```tsx
try {
  await joinWaitlist({ contact: value, locale, source: 'landing' })
  setLead('')
  setJoined(true)
} catch {
  setJoined(false)
  setJoinError(t.joinError)
} finally {
  setJoining(false)
}
```

- [ ] **Step 2: Confirm no failure-path clearing was introduced**

Read the updated `submitWaitlist` function and verify `setLead('')` appears only inside the `try` block after the awaited `joinWaitlist(...)` call. It must not appear before the API call, in `catch`, or in `finally`.

- [ ] **Step 3: Run the focused frontend tests**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected after implementation: all tests in `frontend/src/App.test.tsx` pass.

- [ ] **Step 4: Commit the implementation**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "fix: clear waitlist input after successful join"
```

### Task 3: Run Required Frontend Verification

**Files:**
- Verify: `frontend/src/App.tsx`
- Verify: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: completed Task 1 and Task 2 changes.
- Produces: verification evidence for issue #39 acceptance criteria.

- [ ] **Step 1: Run the full frontend test suite**

Run:

```bash
npm test --prefix frontend
```

Expected: Vitest exits with code 0 and reports all frontend tests passing.

- [ ] **Step 2: Run the frontend production build**

Run:

```bash
npm run build --prefix frontend
```

Expected: TypeScript build and Vite production build exit with code 0.

- [ ] **Step 3: Inspect the final diff**

Run:

```bash
git diff -- frontend/src/App.tsx frontend/src/App.test.tsx
```

Expected diff characteristics:

```diff
+  setLead('')
```

appears in `frontend/src/App.tsx` only after the awaited `joinWaitlist(...)` success call, and `frontend/src/App.test.tsx` includes assertions equivalent to:

```tsx
expect(input).toHaveValue('')
expect(screen.getByRole('status')).toHaveTextContent('Saved. You are on the Bitcoin Risk Brief waitlist.')
expect(input).toHaveValue('not-a-contact')
```

- [ ] **Step 4: Prepare final implementation note**

Report these points to the orchestrator or user:

```markdown
Implemented issue #39.

Changed:
- `frontend/src/App.tsx`: clears the controlled waitlist input after successful `joinWaitlist(...)`.
- `frontend/src/App.test.tsx`: covers success clearing, success status visibility, and failure preserving the typed contact.

Verified:
- `npm test --prefix frontend`
- `npm run build --prefix frontend`
```

## Self-Review

- Spec coverage: Task 1 covers success clearing, success message visibility, failed submission preservation, and focused tests. Task 2 implements success-only clearing without changing modal, popup, loading, or error behavior. Task 3 covers the required frontend test and build commands.
- Placeholder scan: no placeholders remain.
- Type consistency: all referenced functions and state names match the existing `frontend/src/App.tsx` and `frontend/src/App.test.tsx` code.
