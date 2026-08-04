# Turnstile Waitlist Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require a valid Cloudflare Turnstile token before `POST /api/waitlist` can persist a Bitcoin Risk Brief lead.

**Architecture:** A repository-owned React component renders the official Turnstile script explicitly and sends a single-use token in the existing JSON waitlist request. A focused async FastAPI verifier calls Siteverify, validates `success`, `action=waitlist`, and a deployment-specific hostname allowlist, then gates the unchanged persistence path.

**Tech Stack:** React, TypeScript, Vite, Vitest/Testing Library, Playwright, FastAPI, Pydantic, Python 3.13, httpx, nginx CSP, Podman Compose, Cloudflare Turnstile Spin.

## Global Constraints

- Use the `turnstile-spin` creation flow and its helper scripts; do not create a replacement Worker, proxy, or sidecar.
- Widget mode is Managed; widget name is `bitcoin-risk-brief-waitlist`; action is exactly `waitlist`.
- Widget domains are exactly `bitcoinriskbrief.minihub.app`, `localhost`, and `127.0.0.1`.
- Production `TURNSTILE_HOSTNAMES` is exactly `bitcoinriskbrief.minihub.app`; it must not include local hostnames.
- Siteverify is mandatory and fail-closed. Invalid verification returns 403; upstream/unusable verification returns 503.
- The optional visitor IP is omitted from Siteverify to minimize transmitted data.
- Token length is 1-2048 characters; tokens and secrets are never logged.
- The production secret is `TURNSTILE_SECRET`; the public build input is `VITE_TURNSTILE_SITE_KEY`.
- No third-party React Turnstile wrapper is added.
- Every same-page submission attempt resets the widget because tokens are single-use.
- Existing persistence, validation, rate limiting, no-store headers, and waitlist privacy rules remain intact.
- Production deployment remains an operator-run, backup-gated USB update; the agent does not mutate the production server.

---

### Task 1: Create and safely store the Turnstile widget credentials

**Files:**
- Read: `/Users/andrey.karazhev/.agents/skills/turnstile-spin/SKILL.md`
- Read: `.gitignore`
- Modify outside Git: `.env`

**Interfaces:**
- Consumes: Cloudflare account authentication with `Account.Turnstile:Edit` and the existing ignored `.env` secret store.
- Produces: a Managed widget sitekey in `VITE_TURNSTILE_SITE_KEY`, secret in `TURNSTILE_SECRET`, and `TURNSTILE_HOSTNAMES=localhost,127.0.0.1` for local execution.

- [ ] **Step 1: Run the Spin authentication probe**

From the Turnstile skill directory, set the project root and run the helper without printing credentials:

```bash
export PROJECT_ROOT=/Users/andrey.karazhev/Developer/minihub/bitcoin-risk-brief
bash /Users/andrey.karazhev/.agents/skills/turnstile-spin/scripts/auth-probe.sh
```

Expected: JSON with `status: "ok"` and one selected account. For `missing_token`, `missing_scope`, `network_failure`, `multiple_accounts`, or `account_mismatch`, follow the exact branch in `turnstile-spin/SKILL.md`; never ask the user to paste a token into chat.

- [ ] **Step 2: Confirm the exact domain and insertion mapping**

Present this exact mapping and wait for confirmation immediately before widget creation:

```text
Widget: bitcoin-risk-brief-waitlist
Mode: managed
Domains: bitcoinriskbrief.minihub.app, localhost, 127.0.0.1
Surface: React waitlist form
Action: waitlist
Handler: POST /api/waitlist
```

Expected: explicit confirmation.

- [ ] **Step 3: Create the widget with Spin**

Use the approved Wrangler executable only if it meets the Spin requirements; otherwise use the bundled helper:

```bash
bash /Users/andrey.karazhev/.agents/skills/turnstile-spin/scripts/widget-create.sh \
  --account-id "$CLOUDFLARE_ACCOUNT_ID" \
  --name bitcoin-risk-brief-waitlist \
  --domains bitcoinriskbrief.minihub.app,localhost,127.0.0.1 \
  --mode managed
```

Run it inside the skill's required `set +x` capture flow. Parse the sitekey and non-empty secret without printing the full response. Report only the sitekey.

Expected: one widget, Managed mode, all three approved domains.

- [ ] **Step 4: Confirm the secret write manifest**

Run:

```bash
cd /Users/andrey.karazhev/Developer/minihub/bitcoin-risk-brief
git check-ignore -q .env
```

Expected: exit 0. Present this manifest and wait for a new explicit confirmation:

```text
Destination: ignored project .env
Public key: VITE_TURNSTILE_SITE_KEY
Secret key: TURNSTILE_SECRET
Local hostname allowlist: TURNSTILE_HOSTNAMES=localhost,127.0.0.1
No value will be printed or committed.
```

- [ ] **Step 5: Validate and store the secret without exposing it**

Use the Turnstile Spin guarded flow: pass the captured secret through standard input to `validate.sh`, require the expected domain array below, then write the sitekey/secret/hostnames to the already ignored `.env` without command arguments, logs, or temporary files.

```json
["bitcoinriskbrief.minihub.app", "localhost", "127.0.0.1"]
```

Expected: the dummy-token probe reports an invalid response token but not an invalid secret; `.env` remains ignored and no secret appears in terminal output, Git diff, or process arguments.

### Task 2: Implement the isolated backend Siteverify client with TDD

**Files:**
- Create: `backend/app/turnstile.py`
- Create: `backend/tests/test_turnstile.py`
- Modify: `backend/requirements.txt:1-5`

**Interfaces:**
- Consumes: `token: str`, `secret: str`, `expected_hostnames: frozenset[str]`, and optional injected `httpx.AsyncClient`.
- Produces: `verify_turnstile_token(...) -> None`, `TurnstileRejected`, `TurnstileUnavailable`, and `TURNSTILE_ACTION = "waitlist"`.

- [ ] **Step 1: Write failing verifier tests**

Create `backend/tests/test_turnstile.py` with an injected fake client and these exact behaviors:

```python
from __future__ import annotations

import unittest

import httpx

from app.turnstile import TurnstileRejected, TurnstileUnavailable, verify_turnstile_token


class FakeClient:
    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def post(self, url: str, *, data: dict[str, str]) -> httpx.Response:
        self.calls.append((url, data))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def response(status: int, payload: dict[str, object] | None = None, raw: bytes | None = None) -> httpx.Response:
    request = httpx.Request("POST", "https://challenges.cloudflare.com/turnstile/v0/siteverify")
    if raw is not None:
        return httpx.Response(status, content=raw, request=request)
    return httpx.Response(status, json=payload, request=request)


class TurnstileVerifierTest(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_success_for_expected_action_and_hostname(self) -> None:
        client = FakeClient(response(200, {
            "success": True,
            "action": "waitlist",
            "hostname": "bitcoinriskbrief.minihub.app",
        }))
        await verify_turnstile_token(
            "fresh-token",
            secret="test-secret",
            expected_hostnames=frozenset({"bitcoinriskbrief.minihub.app"}),
            client=client,
        )
        self.assertEqual(client.calls[0][1], {"secret": "test-secret", "response": "fresh-token"})

    async def test_rejects_failed_wrong_action_and_wrong_hostname_results(self) -> None:
        payloads = (
            {"success": False, "action": "waitlist", "hostname": "bitcoinriskbrief.minihub.app"},
            {"success": True, "action": "login", "hostname": "bitcoinriskbrief.minihub.app"},
            {"success": True, "action": "waitlist", "hostname": "localhost"},
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(TurnstileRejected):
                    await verify_turnstile_token(
                        "token",
                        secret="secret",
                        expected_hostnames=frozenset({"bitcoinriskbrief.minihub.app"}),
                        client=FakeClient(response(200, payload)),
                    )

    async def test_rejects_empty_and_oversized_tokens(self) -> None:
        for token in ("", "x" * 2049):
            with self.subTest(length=len(token)):
                with self.assertRaises(TurnstileRejected):
                    await verify_turnstile_token(
                        token,
                        secret="secret",
                        expected_hostnames=frozenset({"localhost"}),
                        client=FakeClient(),
                    )

    async def test_treats_missing_server_configuration_as_unavailable(self) -> None:
        for secret, hostnames in (("", frozenset({"localhost"})), ("secret", frozenset())):
            with self.subTest(secret=bool(secret), hostnames=hostnames):
                with self.assertRaises(TurnstileUnavailable):
                    await verify_turnstile_token(
                        "token", secret=secret, expected_hostnames=hostnames, client=FakeClient()
                    )

    async def test_treats_network_http_and_json_failures_as_unavailable(self) -> None:
        clients = (
            FakeClient(error=httpx.ConnectError("offline")),
            FakeClient(response(502, {"success": False})),
            FakeClient(response(200, raw=b"not-json")),
        )
        for client in clients:
            with self.subTest(client=client):
                with self.assertRaises(TurnstileUnavailable):
                    await verify_turnstile_token(
                        "token",
                        secret="secret",
                        expected_hostnames=frozenset({"localhost"}),
                        client=client,
                    )
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONPATH=backend python3 -m unittest backend.tests.test_turnstile -v
```

Expected: FAIL because `app.turnstile` does not exist.

- [ ] **Step 3: Add httpx and implement the minimal verifier**

Add `httpx==0.28.1` to `backend/requirements.txt`, then create `backend/app/turnstile.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx


SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_ACTION = "waitlist"
TURNSTILE_TIMEOUT_SECONDS = 10.0
TURNSTILE_TOKEN_MAX_LENGTH = 2048


class TurnstileRejected(Exception):
    pass


class TurnstileUnavailable(Exception):
    pass


async def verify_turnstile_token(
    token: str,
    *,
    secret: str,
    expected_hostnames: frozenset[str],
    client: httpx.AsyncClient | None = None,
) -> None:
    if not token or len(token) > TURNSTILE_TOKEN_MAX_LENGTH:
        raise TurnstileRejected("invalid token")
    if not secret or not expected_hostnames:
        raise TurnstileUnavailable("missing server configuration")

    active_client = client
    owns_client = active_client is None
    if active_client is None:
        active_client = httpx.AsyncClient(timeout=TURNSTILE_TIMEOUT_SECONDS)

    try:
        result = await active_client.post(
            SITEVERIFY_URL,
            data={"secret": secret, "response": token},
        )
        result.raise_for_status()
        payload: Any = result.json()
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        raise TurnstileUnavailable("siteverify unavailable") from exc
    finally:
        if owns_client:
            await active_client.aclose()

    if not isinstance(payload, Mapping):
        raise TurnstileUnavailable("siteverify returned a malformed payload")
    if (
        payload.get("success") is not True
        or payload.get("action") != TURNSTILE_ACTION
        or payload.get("hostname") not in expected_hostnames
    ):
        raise TurnstileRejected("siteverify rejected the token")
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the Step 2 command again.

Expected: all five verifier tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/turnstile.py backend/tests/test_turnstile.py backend/requirements.txt
git commit -m "feat: add Turnstile verifier"
```

### Task 3: Gate the FastAPI waitlist handler with TDD

**Files:**
- Modify: `backend/app/config.py:7-25`
- Modify: `backend/app/main.py:14-65,337-358`
- Modify: `backend/tests/test_waitlist.py:60-75`
- Modify: `backend/tests/test_public_cache_warmup.py:155-168`
- Create: `backend/tests/test_waitlist_turnstile.py`

**Interfaces:**
- Consumes: `verify_turnstile_token`, `TurnstileRejected`, `TurnstileUnavailable`, `TURNSTILE_SECRET`, and `TURNSTILE_HOSTNAMES`.
- Produces: required `WaitlistRequest.turnstile_token`, HTTP 403/503 mapping, and persistence only after verification.

- [ ] **Step 1: Write failing handler tests**

Create focused tests that patch `main.verify_turnstile_token` and `main.upsert_waitlist_lead`. The core assertions are:

```python
async def test_verifies_before_persisting(self) -> None:
    calls: list[str] = []

    async def fake_verify(token: str, *, secret: str, expected_hostnames: frozenset[str]) -> None:
        self.assertEqual(token, "fresh-token")
        calls.append("verify")

    async def fake_upsert(_pool, *, contact: str, locale: str, source: str):
        calls.append("persist")
        return {"contact_type": "email", "locale": locale, "created": True}

    self.patch_main("verify_turnstile_token", fake_verify)
    self.patch_main("upsert_waitlist_lead", fake_upsert)
    self.patch_main("get_pool", lambda: object())
    response = await main.waitlist_join(main.WaitlistRequest(
        contact="user@example.com",
        locale="en",
        source="landing",
        turnstile_token="fresh-token",
    ))
    self.assertEqual(response.status_code, 201)
    self.assertEqual(calls, ["verify", "persist"])

async def test_rejected_token_does_not_persist(self) -> None:
    async def reject(*_args, **_kwargs) -> None:
        raise main.TurnstileRejected("rejected")

    async def forbidden_upsert(*_args, **_kwargs):
        raise AssertionError("persistence must not run")

    self.patch_main("verify_turnstile_token", reject)
    self.patch_main("upsert_waitlist_lead", forbidden_upsert)
    with self.assertRaises(HTTPException) as raised:
        await main.waitlist_join(main.WaitlistRequest(
            contact="user@example.com", locale="en", source="landing", turnstile_token="bad-token"
        ))
    self.assertEqual(raised.exception.status_code, 403)

async def test_unavailable_siteverify_does_not_persist(self) -> None:
    async def unavailable(*_args, **_kwargs) -> None:
        raise main.TurnstileUnavailable("offline")

    self.patch_main("verify_turnstile_token", unavailable)
    with self.assertRaises(HTTPException) as raised:
        await main.waitlist_join(main.WaitlistRequest(
            contact="user@example.com", locale="en", source="landing", turnstile_token="token"
        ))
    self.assertEqual(raised.exception.status_code, 503)
```

Also update the request-model test to assert a missing token fails Pydantic validation and a 2048-character token passes.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
PYTHONPATH=backend python3 -m unittest backend.tests.test_waitlist backend.tests.test_waitlist_turnstile backend.tests.test_public_cache_warmup -v
```

Expected: FAIL because `turnstile_token` and handler verification are absent.

- [ ] **Step 3: Implement configuration and handler gate**

Add to `Settings`:

```python
turnstile_secret: str = os.getenv("TURNSTILE_SECRET", "").strip()
turnstile_hostnames: frozenset[str] = frozenset(
    hostname.strip()
    for hostname in os.getenv("TURNSTILE_HOSTNAMES", "").split(",")
    if hostname.strip()
)
```

Add imports from `app.turnstile`, add the request field, and gate the handler:

```python
class WaitlistRequest(BaseModel):
    contact: str = Field(min_length=3, max_length=254)
    locale: str = Field(default="en")
    source: str = Field(default="landing", max_length=64)
    turnstile_token: str = Field(min_length=1, max_length=2048)


@app.post("/api/waitlist", status_code=201)
async def waitlist_join(payload: WaitlistRequest) -> JSONResponse:
    try:
        await verify_turnstile_token(
            payload.turnstile_token,
            secret=settings.turnstile_secret,
            expected_hostnames=settings.turnstile_hostnames,
        )
    except TurnstileRejected as exc:
        raise HTTPException(status_code=403, detail="Turnstile verification failed") from exc
    except TurnstileUnavailable as exc:
        raise HTTPException(status_code=503, detail="Turnstile verification unavailable") from exc

    try:
        lead = await upsert_waitlist_lead(
            get_pool(), contact=payload.contact, locale=payload.locale, source=payload.source
        )
    except InvalidWaitlistContact as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse(
        status_code=201,
        content={"data": {
            "contact_type": lead["contact_type"],
            "locale": lead["locale"],
            "created": lead["created"],
        }},
        headers=no_store_headers(),
    )
```

Update every direct `WaitlistRequest(...)` construction in existing tests with `turnstile_token="test-token"` and patch the verifier in success-path unit tests.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command again.

Expected: all focused tests pass and no success-path test reaches the network.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/main.py backend/tests/test_waitlist.py backend/tests/test_waitlist_turnstile.py backend/tests/test_public_cache_warmup.py
git commit -m "feat: require Turnstile for waitlist"
```

### Task 4: Build the explicit React Turnstile component with TDD

**Files:**
- Create: `frontend/src/Turnstile.tsx`
- Create: `frontend/src/Turnstile.test.tsx`

**Interfaces:**
- Consumes: `sitekey`, `action`, `language`, `onVerify(token | null)`, and `onError()`.
- Produces: `TurnstileHandle.reset()` and an explicitly rendered widget whose ID is removed on cleanup.

- [ ] **Step 1: Write failing component tests**

The test file must cover these exact calls using a typed `window.turnstile` stub:

```tsx
const renderWidget = vi.fn((_container: HTMLElement, options: TurnstileRenderOptions) => {
  options.callback('fresh-token')
  return 'widget-1'
})
const resetWidget = vi.fn()
const removeWidget = vi.fn()

Object.assign(window, {
  turnstile: { render: renderWidget, reset: resetWidget, remove: removeWidget },
})

const handle = createRef<TurnstileHandle>()
const onVerify = vi.fn()
render(<Turnstile
  ref={handle}
  sitekey="1x00000000000000000000AA"
  action="waitlist"
  language="en"
  onVerify={onVerify}
  onError={vi.fn()}
/>)

await waitFor(() => expect(renderWidget).toHaveBeenCalledTimes(1))
expect(renderWidget.mock.calls[0][1]).toMatchObject({
  sitekey: '1x00000000000000000000AA',
  action: 'waitlist',
  language: 'en',
})
expect(onVerify).toHaveBeenCalledWith('fresh-token')
act(() => handle.current?.reset())
expect(resetWidget).toHaveBeenCalledWith('widget-1')
```

Add separate assertions that `expired-callback` calls `onVerify(null)`, `error-callback` calls both `onVerify(null)` and `onError()`, changing language removes/re-renders the widget, unmount removes it, and absence of `window.turnstile` injects exactly one script with:

```text
https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit
```

- [ ] **Step 2: Run the component test and verify RED**

```bash
npm test --prefix frontend -- --run src/Turnstile.test.tsx
```

Expected: FAIL because `Turnstile.tsx` does not exist.

- [ ] **Step 3: Implement the component**

Use these exact public interfaces and render options:

```tsx
export type TurnstileHandle = { reset: () => void }

export type TurnstileRenderOptions = {
  sitekey: string
  action: string
  language: string
  theme: 'auto'
  size: 'flexible'
  callback: (token: string) => void
  'expired-callback': () => void
  'error-callback': () => void
}

type TurnstileApi = {
  render: (container: HTMLElement, options: TurnstileRenderOptions) => string
  reset: (widgetId: string) => void
  remove: (widgetId: string) => void
}

declare global {
  interface Window { turnstile?: TurnstileApi }
}
```

Implement a singleton script loader for `api.js?render=explicit`, `forwardRef`, `useImperativeHandle`, callback refs, and an effect keyed only by `sitekey`, `action`, and `language`. Render into `<div className="turnstile-container" />`; use `theme: 'auto'` and `size: 'flexible'`. Cleanup must call `remove(widgetId)` and clear the stored ID.

- [ ] **Step 4: Run the component test and verify GREEN**

Run the Step 2 command again.

Expected: component tests pass with no live Cloudflare requests.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/Turnstile.tsx frontend/src/Turnstile.test.tsx
git commit -m "feat: add Turnstile widget component"
```

### Task 5: Integrate Turnstile into the waitlist UX with TDD

**Files:**
- Modify: `frontend/src/types.ts:88-92`
- Modify: `frontend/src/api.ts:1-20`
- Modify: `frontend/src/api.test.ts`
- Modify: `frontend/src/App.tsx:1-8,284-299,460-476,632-676`
- Modify: `frontend/src/App.test.tsx:48-84,179-230,502-620,1270-1310`
- Modify: `frontend/src/App.css:247-262,269-281`
- Modify: `frontend/src/locales.ts:85-105` and every locale block
- Modify: `frontend/src/locales.test.ts`
- Modify: `frontend/e2e/frontend-quality.spec.ts:118-129,234-279`

**Interfaces:**
- Consumes: `Turnstile`, `TurnstileHandle`, `VITE_TURNSTILE_SITE_KEY`, and backend JSON field `turnstile_token`.
- Produces: disabled-before-token form, typed 403/503 messages, reset-after-every-attempt, and localized privacy disclosure.

- [ ] **Step 1: Write failing API and App tests**

Add `turnstile_token: string` to the expected request type. Export a typed error:

```ts
export class ApiError extends Error {
  constructor(readonly status: number) {
    super(`Request failed: ${status}`)
    this.name = 'ApiError'
  }
}
```

Tests must assert:

```tsx
expect(screen.getByRole('button', { name: /join waitlist/i })).toBeDisabled()
turnstileCallbacks.onVerify('fresh-token')
expect(screen.getByRole('button', { name: /join waitlist/i })).toBeEnabled()
```

and after submit:

```tsx
expect(apiMocks.joinWaitlist).toHaveBeenCalledWith({
  contact: 'USER@example.com',
  locale: 'en',
  source: 'landing',
  turnstile_token: 'fresh-token',
})
expect(turnstileMocks.reset).toHaveBeenCalled()
```

Add cases for `new ApiError(403)` using the localized verification message, `new ApiError(503)` using the temporary-unavailability message, preserved contact on both failures, reset after contact validation failure, locale passed to the widget, and the privacy disclosure mentioning Cloudflare Turnstile.

- [ ] **Step 2: Run focused frontend tests and verify RED**

```bash
npm test --prefix frontend -- --run src/api.test.ts src/App.test.tsx src/locales.test.ts
```

Expected: FAIL because the request, state, messages, and widget are not integrated.

- [ ] **Step 3: Implement typed API errors and request shape**

Change `postJson` to throw `new ApiError(response.status)`. Extend `WaitlistRequest`:

```ts
export interface WaitlistRequest {
  contact: string
  locale: Locale
  source: string
  turnstile_token: string
}
```

- [ ] **Step 4: Integrate the component and reset contract**

Add state/ref:

```tsx
const [turnstileToken, setTurnstileToken] = useState<string | null>(null)
const turnstileRef = useRef<TurnstileHandle>(null)
const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY
```

Submit only when a token exists, send `turnstile_token: turnstileToken`, map 403/503 through `ApiError`, preserve the contact on failure, and always run:

```tsx
setTurnstileToken(null)
turnstileRef.current?.reset()
setJoining(false)
```

in `finally`. Render the widget between the input and button with `action="waitlist"`, selected locale language, `onVerify={setTurnstileToken}`, and a localized widget-error callback. Disable submit with `disabled={joining || !turnstileToken}`.

Change `.lead-form` to a one-column grid so the flexible widget fits the existing 420px panel; keep the button and input focus outlines and mobile width behavior.

- [ ] **Step 5: Add exact localized copy**

Add keys `turnstileError`, `turnstileUnavailable`, and `privacyNoteTurnstile` to every locale. Use these exact values:

| Locale | `turnstileError` | `turnstileUnavailable` | `privacyNoteTurnstile` |
| --- | --- | --- | --- |
| en | Complete the bot check and try again. | Bot verification is temporarily unavailable. Try again shortly. | Cloudflare Turnstile checks waitlist submissions for automated abuse. |
| ru | Пройдите проверку на бота и повторите попытку. | Проверка на бота временно недоступна. Повторите попытку чуть позже. | Cloudflare Turnstile проверяет отправку формы листа ожидания на автоматические злоупотребления. |
| zh | 请完成人机验证后重试。 | 人机验证暂时不可用，请稍后重试。 | Cloudflare Turnstile 会检查候补名单提交，以防止自动化滥用。 |
| de | Schließen Sie die Bot-Prüfung ab und versuchen Sie es erneut. | Die Bot-Prüfung ist vorübergehend nicht verfügbar. Versuchen Sie es gleich noch einmal. | Cloudflare Turnstile prüft Wartelistenanmeldungen auf automatisierten Missbrauch. |
| fr | Effectuez la vérification anti-robot puis réessayez. | La vérification anti-robot est temporairement indisponible. Réessayez dans un instant. | Cloudflare Turnstile vérifie les inscriptions à la liste d’attente contre les abus automatisés. |
| es | Completa la verificación anti-bot y vuelve a intentarlo. | La verificación anti-bot no está disponible temporalmente. Inténtalo de nuevo en breve. | Cloudflare Turnstile comprueba los envíos a la lista de espera para evitar abusos automatizados. |
| ar | أكمل التحقق من الروبوت ثم حاول مرة أخرى. | التحقق من الروبوت غير متاح مؤقتا. حاول مرة أخرى بعد قليل. | يتحقق Cloudflare Turnstile من طلبات قائمة الانتظار لمنع إساءة الاستخدام الآلي. |

Render `privacyNoteTurnstile` inside the existing privacy note.

- [ ] **Step 6: Update Playwright's deterministic Turnstile stub**

Before `page.goto`, install a `window.turnstile` stub via `page.addInitScript`. Its `render` method calls the supplied callback with `e2e-turnstile-token`, returns `e2e-widget`, and has no-op `reset`/`remove`. Update the captured waitlist payload expectation to:

```json
{
  "contact": "keyboard@example.invalid",
  "locale": "en",
  "source": "landing",
  "turnstile_token": "e2e-turnstile-token"
}
```

No Playwright test may contact the live Turnstile service or submit to production.

- [ ] **Step 7: Run focused tests and verify GREEN**

Run the Step 2 command.

Expected: API, App, and locale tests pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts frontend/src/api.test.ts frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/App.css frontend/src/locales.ts frontend/src/locales.test.ts frontend/e2e/frontend-quality.spec.ts
git commit -m "feat: protect waitlist with Turnstile"
```

### Task 6: Wire build/runtime configuration and strict CSP with TDD

**Files:**
- Create: `frontend/scripts/require-turnstile-sitekey.mjs`
- Modify: `frontend/package.json`
- Modify: `frontend/src/vite-env.d.ts`
- Modify: `frontend/Dockerfile:1-8`
- Modify: `podman-compose.yml:24-60`
- Modify: `.env.example`
- Modify: `.env.production.example`
- Modify: `frontend/nginx.conf:7-37`
- Modify: `backend/tests/test_frontend_security_headers.py`
- Modify: `.github/workflows/ci.yml:74-102`

**Interfaces:**
- Consumes: public build sitekey plus backend runtime secret/hostname allowlist.
- Produces: reproducible frontend builds, backend env wiring, and CSP limited to `challenges.cloudflare.com`.

- [ ] **Step 1: Write failing CSP/config tests**

Update `_assert_strict_csp` to require:

```python
self.assertEqual(["'self'", "https://challenges.cloudflare.com"], directives["script-src"])
self.assertEqual(["https://challenges.cloudflare.com"], directives["frame-src"])
self.assertEqual(["'self'", "https://challenges.cloudflare.com"], directives["connect-src"])
self.assertEqual(["'none'"], directives["frame-ancestors"])
self.assertNotIn("static.cloudflareinsights.com", csp)
```

Add repository-text assertions that Compose passes `TURNSTILE_SECRET`, `TURNSTILE_HOSTNAMES`, and the frontend build arg but never places `TURNSTILE_SECRET` under frontend build arguments.

- [ ] **Step 2: Run security/config tests and verify RED**

```bash
PYTHONPATH=backend python3 -m unittest backend.tests.test_frontend_security_headers -v
```

Expected: FAIL because Turnstile is absent from CSP and Compose.

- [ ] **Step 3: Add build guard and Vite typing**

Create `frontend/scripts/require-turnstile-sitekey.mjs`:

```js
const sitekey = process.env.VITE_TURNSTILE_SITE_KEY?.trim()
if (!sitekey) {
  throw new Error('VITE_TURNSTILE_SITE_KEY is required for frontend builds')
}
```

Add `"prebuild": "node scripts/require-turnstile-sitekey.mjs"` to `frontend/package.json`. Add:

```ts
interface ImportMetaEnv { readonly VITE_TURNSTILE_SITE_KEY: string }
interface ImportMeta { readonly env: ImportMetaEnv }
```

to `frontend/src/vite-env.d.ts`.

- [ ] **Step 4: Wire Docker and Compose**

Before `RUN npm run build` in `frontend/Dockerfile`, add:

```dockerfile
ARG VITE_TURNSTILE_SITE_KEY
ENV VITE_TURNSTILE_SITE_KEY=${VITE_TURNSTILE_SITE_KEY}
```

Under `frontend.build` add:

```yaml
args:
  VITE_TURNSTILE_SITE_KEY: ${VITE_TURNSTILE_SITE_KEY:?VITE_TURNSTILE_SITE_KEY is required}
```

Under backend environment add:

```yaml
TURNSTILE_SECRET: ${TURNSTILE_SECRET:-}
TURNSTILE_HOSTNAMES: ${TURNSTILE_HOSTNAMES:-}
```

Do not pass `TURNSTILE_SECRET` to frontend.

- [ ] **Step 5: Update environment examples and CI**

Add to `.env.example`:

```env
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA
TURNSTILE_SECRET=1x0000000000000000000000000000000AA
TURNSTILE_HOSTNAMES=localhost,127.0.0.1
```

Add to `.env.production.example`:

```env
VITE_TURNSTILE_SITE_KEY=replace-with-public-turnstile-sitekey
TURNSTILE_SECRET=replace-with-private-turnstile-secret
TURNSTILE_HOSTNAMES=bitcoinriskbrief.minihub.app
```

Set `VITE_TURNSTILE_SITE_KEY: 1x00000000000000000000AA` in CI jobs that run `npm run build`, Playwright's build-backed smoke, or Compose validation.

- [ ] **Step 6: Update CSP in all three nginx header locations**

Use this exact policy:

```text
default-src 'self'; script-src 'self' https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
```

Retain existing `Cache-Control` values and `no-transform`.

- [ ] **Step 7: Run focused and build validation**

```bash
PYTHONPATH=backend python3 -m unittest backend.tests.test_frontend_security_headers -v
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA ./scripts/manage.sh validate
```

Expected: tests pass, frontend build succeeds, and output ends with `compose config ok`.

- [ ] **Step 8: Commit**

```bash
git add frontend/scripts/require-turnstile-sitekey.mjs frontend/package.json frontend/src/vite-env.d.ts frontend/Dockerfile podman-compose.yml .env.example .env.production.example frontend/nginx.conf backend/tests/test_frontend_security_headers.py .github/workflows/ci.yml
git commit -m "build: wire Turnstile configuration"
```

### Task 7: Update API, privacy, security, and USB handoff documentation

**Files:**
- Modify: `docs/api-reference.md:235-278`
- Modify: `docs/waitlist.md`
- Modify: `docs/security-and-privacy.md`
- Modify: `docs/deploy-ubuntu-cloudflare.md`
- Modify: `docs/operations.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: implemented environment names, API status behavior, and USB deployment boundary.
- Produces: exact operator instructions without secret values or a false production-deployed claim.

- [ ] **Step 1: Update the API contract**

Document this request:

```json
{
  "contact": "user@example.com",
  "locale": "en",
  "source": "landing",
  "turnstile_token": "single-use-client-token"
}
```

Add status rows:

```markdown
| `403` | Turnstile rejected a missing, invalid, expired, replayed, wrong-action, or wrong-hostname token. |
| `503` | Turnstile verification is temporarily unavailable or server configuration is incomplete. |
```

State that every outcome is no-store and no failed verification writes a lead.

- [ ] **Step 2: Update security/privacy and waitlist docs**

Record that the browser contacts `challenges.cloudflare.com`, Siteverify is server-side, tokens are single-use and not logged, visitor IP is omitted from the application Siteverify request, and existing rate limits remain layered protection. Preserve the no-product-analytics statement; do not describe Turnstile as product analytics.

- [ ] **Step 3: Update deployment and operations docs**

Document the production `.env` contract without recording credentials: `VITE_TURNSTILE_SITE_KEY` receives the public
sitekey returned in Task 1, `TURNSTILE_SECRET` receives its matching private secret from operator-controlled storage,
and `TURNSTILE_HOSTNAMES` is set exactly to `bitcoinriskbrief.minihub.app`.

State that `.env` is preserved on the server and excluded from USB. Require the operator to edit `.env` before the update build/restart and use:

```bash
bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app
```

Do not claim deployment or production validation before the operator completes it.

- [ ] **Step 4: Verify docs**

```bash
git diff --check
rg -n "Turnstile|turnstile_token|TURNSTILE_SECRET|TURNSTILE_HOSTNAMES|VITE_TURNSTILE_SITE_KEY|403|503" README.md docs
```

Expected: API, privacy, security, deployment, and operations references agree.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/api-reference.md docs/waitlist.md docs/security-and-privacy.md docs/deploy-ubuntu-cloudflare.md docs/operations.md
git commit -m "docs: document Turnstile waitlist protection"
```

### Task 8: Run whole-repository verification and prepare USB handoff

**Files:**
- Verify: all files changed in Tasks 2-7
- Optional on user approval: `.claude/skills/turnstile-spin/SKILL.md`

**Interfaces:**
- Consumes: completed local implementation and ignored local Turnstile credentials.
- Produces: verified commit, sanitized USB instructions, and explicit production validation pending state.

- [ ] **Step 1: Run complete local checks**

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA ./scripts/manage.sh validate
python3 -m compileall backend collector
```

Expected: Python tests pass, frontend tests pass, frontend build succeeds, Compose validation prints `compose config ok`, and compileall exits 0.

- [ ] **Step 2: Run browser smoke with deterministic local Turnstile**

```bash
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run smoke --prefix frontend
```

Expected: all configured Playwright projects pass without any production waitlist POST.

- [ ] **Step 3: Check secret and USB boundaries**

```bash
git status --short
git grep -n "TURNSTILE_SECRET=" -- ':!*.example' ':!docs/**' || true
python3 -m unittest server-kit.tests.test_prepare_usb_kit -v
```

Expected: only intentional tracked changes, no secret assignment in tracked non-example files, and USB packaging tests pass.

- [ ] **Step 4: Request code review and address confirmed findings**

Use `superpowers:requesting-code-review`. Review the complete diff against the approved spec, especially fail-closed behavior, hostname/action checks, CSP, token reset, logging, and USB secret exclusion. Apply only verified fixes and rerun affected checks.

- [ ] **Step 5: Ask whether to persist the Spin skill**

As required by `turnstile-spin`, ask whether to save the skill under `.claude/skills/turnstile-spin/SKILL.md`. If approved, use the skill's `persist-skill.sh` flow, inspect the diff, and commit it separately:

```bash
git add .claude/skills/turnstile-spin/SKILL.md
git commit -m "chore: persist Turnstile setup skill"
```

- [ ] **Step 6: Provide the operator handoff**

Report the implementation commit, exact checks run, public sitekey, and these production-only steps without printing the secret:

```text
1. sudoedit /srv/projects/bitcoin-risk-brief/.env
2. Set VITE_TURNSTILE_SITE_KEY to the widget sitekey.
3. Set TURNSTILE_SECRET to the widget secret from operator-controlled storage.
4. Set TURNSTILE_HOSTNAMES=bitcoinriskbrief.minihub.app.
5. Prepare the USB kit from the verified commit.
6. Run deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app.
```

State clearly that destination validation remains pending until the USB deployment.

- [ ] **Step 7: Validate the deployed destination after the operator returns**

With an operator-approved test contact and a fresh real token, verify one successful waitlist request and then replay the same token.

Expected:

- fresh token: HTTP 201 and exactly one approved lead write;
- replay: HTTP 403 and no second write;
- missing token: HTTP 422 and no write;
- `/api/health` and `/api/readiness`: HTTP 200;
- application logs contain neither token, secret, nor raw contact.

Do not claim end-to-end Turnstile completion until this destination validation passes.
