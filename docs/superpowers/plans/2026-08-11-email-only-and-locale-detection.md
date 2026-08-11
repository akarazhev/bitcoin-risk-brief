# Email-Only Contact And Locale Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop collecting a contact type nothing can deliver to, and let the seven translations the product already ships actually reach the people they were written for.

**Architecture:** Two unrelated changes that happen to touch the same file. Task 1 narrows waitlist validation to email and updates the copy that offered a Telegram handle. Task 2 picks the initial locale from the browser instead of hardcoding English. No schema change, no backend behaviour change beyond validation.

**Tech Stack:** FastAPI, React/Vite, Vitest, `unittest`.

## Global Constraints

- No new dependency, no migration, no schema change.
- **The `waitlist_leads_contact_type_check` constraint keeps `'telegram'`.** Two rows already carry that type. Removing the value from the constraint would make existing data invalid; this plan stops accepting *new* Telegram handles, it does not rewrite history.
- All seven locales stay complete: `en`, `ru`, `zh`, `de`, `fr`, `es`, `ar`. Arabic is RTL.
- Never weaken the Content-Security-Policy.
- No copy may describe the product as a pilot, a trial, or a limited preview.
- **No browser storage.** See Task 2 for why persistence is deliberately out of scope.

---

### Task 1: Accept email only

**Files:**
- Modify: `backend/app/waitlist.py`
- Modify: `frontend/src/locales.ts`
- Modify: `docs/engineering/api-reference.md`, `README.md`
- Test: `backend/tests/test_waitlist.py`, `frontend/src/locales.test.ts`

**Interfaces:**
- `normalize_waitlist_contact` keeps its signature and stops returning `contact_type="telegram"`.

**Why.** A Telegram bot cannot message a handle. It can only reply to someone who has pressed `/start`, which yields a `chat_id`; the handle itself is never usable. Direct Telegram delivery, when it arrives in #52, works through a deep link where the user initiates — so **the handle is not merely undelivered today, it is unused by the design that would deliver it**.

The form therefore collects personal data that no current or planned mechanism consumes. Telegram users already have the channel, which is free and needs no contact at all.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_waitlist.py`:

```python
class EmailOnlyContactTests(unittest.TestCase):
    def test_a_telegram_handle_is_rejected(self) -> None:
        with self.assertRaises(InvalidWaitlistContact):
            normalize_waitlist_contact("@someholder")

    def test_an_email_is_still_accepted_and_normalised(self) -> None:
        result = normalize_waitlist_contact("USER@Example.COM")
        self.assertEqual("email", result.contact_type)
        self.assertEqual("user@example.com", result.normalized_contact)
        self.assertEqual("USER@Example.COM", result.contact)

    def test_no_input_can_produce_the_telegram_contact_type(self) -> None:
        for candidate in ("@bitcoinriskbrief", "@a_user_name", "@12345678"):
            with self.subTest(candidate=candidate):
                with self.assertRaises(InvalidWaitlistContact):
                    normalize_waitlist_contact(candidate)
```

Existing tests in that file assert a Telegram handle is accepted. Change them to assert rejection; do not delete them — they are the regression guard for this decision.

Append to `frontend/src/locales.test.ts`:

```typescript
it('offers only email in every locale', () => {
  for (const [code, value] of Object.entries(copy)) {
    expect(value.placeholder, `${code} placeholder still mentions Telegram`).not.toMatch(/telegram/i)
    expect(value.waitlistBody, `${code} body still offers a Telegram handle`).not.toMatch(/telegram/i)
    expect(value.joinError, `${code} error still mentions Telegram`).not.toMatch(/telegram/i)
  }
})
```

Note the channel copy — `channelBody` and `channelCta` — must still mention Telegram. Only the three contact-form strings change.

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=backend:collector python -m unittest discover -s backend/tests -k waitlist -v`
Run: `npm test --prefix frontend -- locales`
Expected: FAIL — the handle is accepted, the copy still offers it.

- [ ] **Step 3: Narrow the validator and the copy**

In `backend/app/waitlist.py`, delete `TELEGRAM_RE` and the branch that returns `contact_type="telegram"`. Update the two `InvalidWaitlistContact` messages to name only an email address.

Leave `migrations/001_initial_schema.sql` untouched. The `CHECK (contact_type IN ('email', 'telegram'))` constraint stays: two stored rows still carry `telegram`, and the column must keep accepting the value it already holds.

In `frontend/src/locales.ts`, replace three keys per locale with exactly these:

| Locale | `placeholder` | `joinError` |
| --- | --- | --- |
| `en` | `your email` | `Enter a valid email address.` |
| `ru` | `ваш email` | `Введите корректный email.` |
| `zh` | `您的邮箱` | `请输入有效的邮箱地址。` |
| `de` | `Ihre E-Mail` | `Bitte geben Sie eine gültige E-Mail-Adresse ein.` |
| `fr` | `votre e-mail` | `Saisissez une adresse e-mail valide.` |
| `es` | `tu correo` | `Introduce un correo electrónico válido.` |
| `ar` | `بريدك الإلكتروني` | `أدخل بريدا إلكترونيا صالحا.` |

`waitlistBody` keeps its current sentence and drops the handle:

- `en`: `Band changes are rare. Leave an email to hear about one. This is a manual follow-up — automated delivery does not exist yet.`
- `ru`: `Диапазон меняется редко. Оставьте email, чтобы узнать о смене. Это ручная связь — автоматической рассылки пока нет.`
- `zh`: `风险区间变化很少见。留下邮箱以便获知变化。这是人工联系，目前没有自动推送。`
- `de`: `Bandwechsel sind selten. Hinterlassen Sie eine E-Mail, um davon zu erfahren. Das ist eine manuelle Rückmeldung — einen automatischen Versand gibt es noch nicht.`
- `fr`: `Les changements de bande sont rares. Laissez un e-mail pour en être informé. Il s’agit d’un suivi manuel — l’envoi automatique n’existe pas encore.`
- `es`: `Los cambios de banda son poco frecuentes. Deja un correo para enterarte. Es un seguimiento manual: todavía no existe el envío automático.`
- `ar`: `تغيّر النطاق نادر. اترك بريدا إلكترونيا لتعرف بذلك. هذه متابعة يدوية — لا يوجد إرسال تلقائي بعد.`

> `zh`, `de`, `fr`, `es` and `ar` were written without native review. Flag anything that reads wrong rather than silently rewording.

Update the two places that document the old behaviour:

- `docs/engineering/api-reference.md`, the **Accepted contacts** list — remove the Telegram line.
- `README.md` line describing the waitlist — it currently says "accepts email or Telegram waitlist contacts server-side". Drop the Telegram half; keep the server-side and no-sensitive-information statements.

Search for any other prose describing the accepted contact types and update it too. Existing rows of type `telegram` remain valid and should not be described as impossible.

- [ ] **Step 4: Run the checks**

Run: `./scripts/manage.sh test-python`
Run: `npm test --prefix frontend`
Run: `npm run build --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/waitlist.py frontend/src/locales.ts docs/engineering/api-reference.md README.md backend/tests/test_waitlist.py frontend/src/locales.test.ts
git commit -m "fix: accept only email on the interest form"
```

---

### Task 2: Choose the initial locale from the browser

**Files:**
- Modify: `frontend/src/locales.ts` (add the resolver)
- Modify: `frontend/src/App.tsx:274`
- Test: `frontend/src/locales.test.ts`, `frontend/src/App.test.tsx`

**Interfaces:**
- Produces: `export function resolveInitialLocale(languages: readonly string[] | undefined): Locale` in `locales.ts`, pure and independently testable.

**Why.** `App.tsx` opens with `useState<Locale>('en')`. There is no detection anywhere — `navigator.language` appears nowhere in `frontend/src`. A German speaker arriving from the channel reads English until they find the language selector, and their choice is gone on the next visit.

Seven translations exist, were paid for in work, and are effectively invisible. This is the cheapest way to make them reach anyone.

**Why no persistence.** Storing the choice would mean disclosing browser storage in the privacy note across seven locales, for a preference that S4 is about to put in the URL anyway — at which point the URL *is* the persistence and the storage becomes dead code. Detection alone solves the stated problem: a German browser gets German. Manual overrides lasting only the session is an acceptable cost for not building something the next sub-project deletes.

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/locales.test.ts`:

```typescript
describe('resolveInitialLocale', () => {
  it('matches an exact supported tag', () => {
    expect(resolveInitialLocale(['de'])).toBe('de')
  })

  it('matches on the primary subtag', () => {
    expect(resolveInitialLocale(['de-AT'])).toBe('de')
    expect(resolveInitialLocale(['zh-Hans-CN'])).toBe('zh')
    expect(resolveInitialLocale(['pt-BR', 'es-ES'])).toBe('es')
  })

  it('honours preference order', () => {
    expect(resolveInitialLocale(['fr-CA', 'de'])).toBe('fr')
  })

  it('falls back to English for anything unsupported', () => {
    expect(resolveInitialLocale(['pt', 'sv'])).toBe('en')
  })

  it('falls back to English when the browser tells us nothing', () => {
    expect(resolveInitialLocale(undefined)).toBe('en')
    expect(resolveInitialLocale([])).toBe('en')
  })

  it('is case-insensitive', () => {
    expect(resolveInitialLocale(['DE-de'])).toBe('de')
  })

  it('only ever returns a supported locale', () => {
    for (const tag of ['de', 'xx', 'zh-Hant', '', 'ru-RU']) {
      expect(supportedLocales).toContain(resolveInitialLocale([tag]))
    }
  })
})
```

Append to `frontend/src/App.test.tsx`:

```tsx
test('opens in the language the browser asks for', async () => {
  const original = Object.getOwnPropertyDescriptor(window.navigator, 'languages')
  Object.defineProperty(window.navigator, 'languages', { value: ['de-DE', 'en'], configurable: true })
  try {
    render(<App />)
    expect(await screen.findByRole('button', { name: /interesse hinterlegen/i })).toBeInTheDocument()
  } finally {
    if (original) Object.defineProperty(window.navigator, 'languages', original)
  }
})

test('writes nothing to browser storage', async () => {
  render(<App />)
  await screen.findByRole('link', { name: /telegram channel/i })

  expect(window.localStorage.length).toBe(0)
  expect(window.sessionStorage.length).toBe(0)
})
```

The second test is the guard for the no-storage decision. Keep it.

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test --prefix frontend`
Expected: FAIL — `resolveInitialLocale` does not exist.

- [ ] **Step 3: Add the resolver and use it**

In `frontend/src/locales.ts`, beside the existing `supportedLocales` export:

```typescript
export function resolveInitialLocale(languages: readonly string[] | undefined): Locale {
  for (const tag of languages ?? []) {
    const primary = tag.toLowerCase().split('-')[0]
    const match = supportedLocales.find((locale) => locale === primary)
    if (match) return match
  }
  return 'en'
}
```

In `frontend/src/App.tsx`, replace the hardcoded initial state with a lazy initialiser so the lookup runs once rather than on every render:

```tsx
const [locale, setLocale] = useState<Locale>(() =>
  resolveInitialLocale(typeof navigator === 'undefined' ? undefined : navigator.languages),
)
```

The `typeof navigator` guard costs nothing and keeps the component safe if it is ever rendered outside a browser.

Nothing else changes. The language selector keeps working exactly as before, and the choice still lasts for the session.

- [ ] **Step 4: Run the checks**

Run: `npm test --prefix frontend`
Expected: PASS. Existing tests assume English; jsdom reports `en-US`, so they are unaffected. If any test sets a different browser language, pin `navigator.languages` in that test rather than changing the resolver.

Run: `npm run build --prefix frontend`
Run: `npm run smoke --prefix frontend`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/locales.ts frontend/src/App.tsx frontend/src/locales.test.ts frontend/src/App.test.tsx
git commit -m "feat: open in the language the browser asks for"
```

---

## Verification Summary

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
npm run smoke --prefix frontend
./scripts/manage.sh validate
mkdocs build --strict
```

## Out Of Scope

- Persisting the language choice, and putting the language in the URL — both belong to S4 (#42).
- Deleting or rewriting the two stored `telegram` waitlist rows.
- Direct Telegram delivery through a bot deep link — that is #52.
- Additional channel languages; the channel stays English.
