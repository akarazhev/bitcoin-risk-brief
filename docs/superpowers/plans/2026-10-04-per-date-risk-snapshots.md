# Per-Date Risk Snapshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve `/risk/YYYY-MM-DD` and its six localised variants from the backend as server-rendered HTML, so one
historical observation can be cited by URL.

**Architecture:** A pure function builds the page from two risk rows and a shared label file; a thin FastAPI route
serves it with the existing data-versioned cache headers. nginx proxies `/risk/`, `/<locale>/risk/` and
`/sitemap-risk.xml` to the backend. The labels both sides render move into one JSON file that the backend image
copies in, which requires moving the backend's build context to the repository root.

**Tech Stack:** Python 3.14, FastAPI, asyncpg, `unittest`; React 19 + Vite + Vitest; nginx.

**Spec:** [`docs/superpowers/specs/2026-09-21-per-date-risk-snapshots-design.md`](../specs/2026-09-21-per-date-risk-snapshots-design.md)

## Global Constraints

- **No change to the risk computation, the methodology, the bands, or the data pipeline.** Nothing under
  `collector/collector/` changes, and no migration is added. The one change the pipeline carries is wording: Task 5
  removes the time adverb from the seven neutral summaries in `backend/app/brief.py`, which the collector imports
  when it writes the brief snapshot.
- **These pages are a deliberate exception to the `/api/*` rule in `AGENTS.md`.** That rule keeps backend *API* routes
  under `/api/`. `/risk/YYYY-MM-DD` is an HTML page and a citation target, so its URL cannot carry an `/api/` prefix.
  Every other new backend route this plan adds stays under `/api/` or is `/sitemap-risk.xml`. Do not move the page
  routes under `/api/` to satisfy the rule; that would defeat the sub-project.
- **No page may present itself as the current reading.** The date and its pastness come first, above the value.
- **No live value is added to S4a's prerender.** Per-date pages never pass through `frontend/scripts/prerender.mjs`.
- **Each localised label exists in exactly one file:** `frontend/src/localeStrings.json`.
- **`frontend/public/sitemap.xml` keeps exactly its current contents.** The rolling window lives in
  `/sitemap-risk.xml`, served by the backend.
- **Never assert 404s or redirects in Playwright.** The smoke suite runs against `vite preview`, which answers HTTP 200
  with the root document for unknown paths — measured during S4a. Those contracts are asserted against
  `frontend/nginx.conf` only.
- **Two CSP headers reach every proxied response, and the page must satisfy both.** nginx's server-level
  `add_header Content-Security-Policy` is inherited by any `location` that sets no `add_header` of its own, which
  includes the new proxied locations, and the backend sends its own. Browsers enforce the intersection. The page uses
  inline CSS and no JavaScript, so both policies must allow `style-src 'unsafe-inline'`. nginx's already does.

### Running The Tests

```bash
node -v                                     # must print v22.x; a stale nvm default breaks the build
./scripts/manage.sh test-python             # backend + collector; guards its own interpreter and Node
npm test --prefix frontend                  # Vitest
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
npm run smoke --prefix frontend             # also needs the Turnstile key exported
```

Focused backend run:

```bash
PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k risk_page -v
```

`-k` filters after discovery, so an import error anywhere under `backend/tests` still surfaces.

## Review Focus

The inputs and wiring the spec implies but no happy-path test would exercise, most likely to bite first. Each has a
test in the task that owns the code. Items 6 and 7 were found by rendering pages against the bundled CSV during this
plan's dry run; the unit fixtures missed both.

1. **A well-formed string that is not a date** — `2026-02-30`, `2026-13-01`, `2026-9-1` — must return 404, never a
   500 from `date.fromisoformat`. Owned by Task 5.
2. **The first row of the series** — 2010-07-13 in the bundled CSV — has no previous observation. The page must render
   without a change line rather than crash or invent a zero. A date after a gap is different: Task 4 returns the
   nearest earlier row, so it does get a change line. Owned by Tasks 4 and 5.
3. **A row with `turnover` null or `turnover_enabled` false** must show the activity driver as unavailable, not as
   neutral. Neutral is a claim about the market; unavailable is a claim about the data. Owned by Task 5.
4. **A row without a matching OHLCV row** has null `low_usd` and `high_usd`. The range line is omitted, never shown as
   `$0`. Owned by Task 5.
5. **Text that needs escaping** — a label containing `"` or `<`, the Arabic page in `dir="rtl"`, and the date inside
   attribute values — must not break the markup. Owned by Task 5.
6. **The brief speaks in the present.** Every neutral summary said "right now" in its own language, and with no
   previous row `what_changed` invents "broadly unchanged from the previous observation". Only `summary` is rendered,
   and the neutral summaries lose the adverb. Owned by Task 5.
7. **Prices below $1** — every day from 2010-07-13 to February 2011 — must keep their digits, not print `$0`. Owned
   by Task 5.
8. **Route order and the locale prefix.** Registered before the API, `/{locale}/risk/{day}` captures
   `/api/risk/latest`, `/history` and `/levels`. The handler must 404 `api`, `en`, and anything outside the six
   prefixed locales. Owned by Task 6.
9. **A missing or incomplete label file** must stop the app from starting, not answer 500 on the first page request.
   Owned by Tasks 6 and 7.
10. **nginx: no `add_header` in the proxied locations.** One `add_header` drops every inherited security header for
    that location. Owned by Task 8. Its routing check also pins relative `Location` headers, which `main` already sends
    — see Task 8.

---
### Task 1: One file for the labels both sides render

**Files:**
- Create: `frontend/src/localeStrings.json`, `frontend/scripts/extract-locale-strings.mjs`, `frontend/src/localeStrings.test.ts`
- Modify: `frontend/src/locales.ts`, `frontend/src/App.tsx:44`

**Interfaces:**
- Produces `frontend/src/localeStrings.json` with exactly this shape, which Tasks 2 and 5 read from Python:

```json
{
  "driverNeutralBand": 0.25,
  "labels": { "en": { "<key>": "<string or array>" }, "ru": {}, "zh": {}, "de": {}, "fr": {}, "es": {}, "ar": {} },
  "riskStates": { "en": { "low": "Low", "neutral": "Neutral", "high": "High" } },
  "localeMeta": { "en": { "lang": "en", "dir": "ltr" }, "zh": { "lang": "zh-CN", "dir": "ltr" }, "ar": { "lang": "ar", "dir": "rtl" } }
}
```

**The shared keys, and only these.** Twenty-four already exist in `copy` and move unchanged:

`title`, `reportDate`, `modelPrice`, `low`, `high`, `riskChange`, `riskChangeContext`, `modelDrivers`, `driverTrend`,
`driverTrendDetail`, `driverVolatility`, `driverVolatilityDetail`, `driverActivity`, `driverActivityDetail`,
`driverActivityUnavailableDetail`, `driverRaises`, `driverNeutral`, `driverLowers`, `driverUnavailable`,
`methodology`, `methodologyLink`, `methodologyVersion`, `disclaimer`, `riskZones`.

**`currentRisk` is deliberately absent.** It reads "Current risk", and a historical page that says so is the one
failure this sub-project must not ship. Task 5 tests that it never appears.

Three are new, with `{date}` as a placeholder the backend fills:

| key | en | ru | zh | de | fr | es | ar |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pageTitle` | Bitcoin risk on {date} | Риск биткоина на {date} | {date} 的比特币风险 | Bitcoin-Risiko am {date} | Risque Bitcoin au {date} | Riesgo de Bitcoin el {date} | مخاطر البيتكوين في {date} |
| `historicalNotice` | This is the observation for {date}. It is not the current reading. | Это наблюдение за {date}. Это не текущее значение. | 这是 {date} 的观测值，并非当前读数。 | Dies ist die Beobachtung vom {date}. Sie ist nicht der aktuelle Wert. | Ceci est l’observation du {date}. Ce n’est pas la valeur actuelle. | Esta es la observación del {date}. No es el valor actual. | هذه هي الملاحظة بتاريخ {date}. وهي ليست القراءة الحالية. |
| `todayLink` | See today's reading | Посмотреть сегодняшнее значение | 查看今日读数 | Heutigen Wert ansehen | Voir la valeur du jour | Ver el valor de hoy | عرض قراءة اليوم |

**`localeMeta` moves too.** The page needs `lang` and `dir` on its document element — `zh-CN` for Chinese, `rtl` for
Arabic — and today those live only in `localeOptions` in `locales.ts`. The display labels in `localeOptions`
(`Русский`, `RU - Русский`) stay in TypeScript, since only the frontend renders a language menu.

**`driverNeutralBand` moves too.** `App.tsx:44` holds `const DRIVER_NEUTRAL_BAND = 0.25`, and the backend must
classify drivers with the same number. It is not a label, but it decides which label is shown, and two copies of it
would drift exactly as two copies of a string would.

- [ ] **Step 1: Generate the file from the current values, never by retyping**

Transcribing 24 keys across seven languages by hand would introduce errors nobody can see in Chinese or Arabic.
Generate it instead. Node 22 imports `locales.ts` directly with type stripping — verified, no new dependency:

Create `frontend/scripts/extract-locale-strings.mjs`:

```javascript
import { writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const { copy, getLocaleOption, riskStateLabels, supportedLocales } = await import(resolve(here, '../src/locales.ts'))

const SHARED = [
  'title', 'reportDate', 'modelPrice', 'low', 'high', 'riskChange', 'riskChangeContext', 'modelDrivers',
  'driverTrend', 'driverTrendDetail', 'driverVolatility', 'driverVolatilityDetail', 'driverActivity',
  'driverActivityDetail', 'driverActivityUnavailableDetail', 'driverRaises', 'driverNeutral', 'driverLowers',
  'driverUnavailable', 'methodology', 'methodologyLink', 'methodologyVersion', 'disclaimer', 'riskZones',
]

const ADDED = {
  en: { pageTitle: 'Bitcoin risk on {date}', historicalNotice: 'This is the observation for {date}. It is not the current reading.', todayLink: "See today's reading" },
  ru: { pageTitle: 'Риск биткоина на {date}', historicalNotice: 'Это наблюдение за {date}. Это не текущее значение.', todayLink: 'Посмотреть сегодняшнее значение' },
  zh: { pageTitle: '{date} 的比特币风险', historicalNotice: '这是 {date} 的观测值，并非当前读数。', todayLink: '查看今日读数' },
  de: { pageTitle: 'Bitcoin-Risiko am {date}', historicalNotice: 'Dies ist die Beobachtung vom {date}. Sie ist nicht der aktuelle Wert.', todayLink: 'Heutigen Wert ansehen' },
  fr: { pageTitle: 'Risque Bitcoin au {date}', historicalNotice: 'Ceci est l’observation du {date}. Ce n’est pas la valeur actuelle.', todayLink: 'Voir la valeur du jour' },
  es: { pageTitle: 'Riesgo de Bitcoin el {date}', historicalNotice: 'Esta es la observación del {date}. No es el valor actual.', todayLink: 'Ver el valor de hoy' },
  ar: { pageTitle: 'مخاطر البيتكوين في {date}', historicalNotice: 'هذه هي الملاحظة بتاريخ {date}. وهي ليست القراءة الحالية.', todayLink: 'عرض قراءة اليوم' },
}

const labels = {}
for (const locale of supportedLocales) {
  labels[locale] = {}
  for (const key of SHARED) labels[locale][key] = copy[locale][key]
  Object.assign(labels[locale], ADDED[locale])
}

const localeMeta = {}
for (const locale of supportedLocales) {
  const { lang, dir } = getLocaleOption(locale)
  localeMeta[locale] = { lang, dir }
}

const shared = { driverNeutralBand: 0.25, labels, riskStates: riskStateLabels, localeMeta }
writeFileSync(resolve(here, '../src/localeStrings.json'), `${JSON.stringify(shared, null, 2)}\n`, 'utf-8')
console.log(`wrote ${supportedLocales.length} locales x ${SHARED.length + 3} keys`)
```

Run it once:

```bash
node --experimental-strip-types --no-warnings frontend/scripts/extract-locale-strings.mjs
```

Expected: `wrote 7 locales x 27 keys`. Commit the script with the JSON: it documents how the file was derived, and
it is the tool for regenerating it if `locales.ts` is ever restructured again.

- [ ] **Step 2: Prove the move changed nothing, before switching anything over**

Create `frontend/src/localeStrings.test.ts`:

```typescript
import { describe, expect, it } from 'vitest'
import { copy, getLocaleOption, riskStateLabels, supportedLocales } from './locales'
import shared from './localeStrings.json'

const MOVED = [
  'title', 'reportDate', 'modelPrice', 'low', 'high', 'riskChange', 'riskChangeContext', 'modelDrivers',
  'driverTrend', 'driverTrendDetail', 'driverVolatility', 'driverVolatilityDetail', 'driverActivity',
  'driverActivityDetail', 'driverActivityUnavailableDetail', 'driverRaises', 'driverNeutral', 'driverLowers',
  'driverUnavailable', 'methodology', 'methodologyLink', 'methodologyVersion', 'disclaimer', 'riskZones',
] as const

describe('shared locale strings', () => {
  it('carries every moved key with the exact value locales.ts renders', () => {
    for (const locale of supportedLocales) {
      for (const key of MOVED) {
        expect(shared.labels[locale][key], `${locale}.${key}`).toEqual(copy[locale][key])
      }
    }
  })

  it('carries the three page keys in every locale, each with its date placeholder where needed', () => {
    for (const locale of supportedLocales) {
      expect(shared.labels[locale].pageTitle).toContain('{date}')
      expect(shared.labels[locale].historicalNotice).toContain('{date}')
      expect(shared.labels[locale].todayLink.length).toBeGreaterThan(0)
    }
  })

  it('never carries the label that would make a past page read as current', () => {
    for (const locale of supportedLocales) {
      expect(Object.keys(shared.labels[locale])).not.toContain('currentRisk')
    }
  })

  it('holds the risk state names, the driver band, and each locale\'s lang and dir', () => {
    expect(shared.riskStates).toEqual(riskStateLabels)
    expect(shared.driverNeutralBand).toBe(0.25)
    for (const locale of supportedLocales) {
      const { lang, dir } = getLocaleOption(locale)
      expect(shared.localeMeta[locale]).toEqual({ lang, dir })
    }
    expect(shared.localeMeta.ar.dir).toBe('rtl')
    expect(shared.localeMeta.zh.lang).toBe('zh-CN')
  })
})
```

Run: `npm test --prefix frontend -- src/localeStrings.test.ts`
Expected: PASS, 4 tests. **This must pass before Step 3.** It proves the generated file equals what the interface
renders today; after Step 3 the first assertion compares a value with itself and stops proving anything, which is why
the order matters.

- [ ] **Step 3: Make `locales.ts` read the shared file**

In `frontend/src/locales.ts`, import the file and build each locale's entry from it, deleting the 24 moved literals
from all seven locale blocks:

```typescript
import shared from './localeStrings.json'
```

Each entry in `copy` becomes `{ ...shared.labels.<locale>, <the keys that did not move> }`. Add `pageTitle`,
`historicalNotice` and `todayLink` to the `Copy` type as `string`, since the spread now carries them.

Replace the literal `riskStateLabels` object with:

```typescript
export const riskStateLabels: Record<Locale, RiskStateLabels> = shared.riskStates
```

Make `localeOptions` take `lang` and `dir` from the file through a typed helper, so no cast is needed — the JSON
import types `dir` as `string`, and `LocaleOption.dir` is `'ltr' | 'rtl'`:

```typescript
function meta(code: Locale): Pick<LocaleOption, 'lang' | 'dir'> {
  const entry = shared.localeMeta[code]
  return { lang: entry.lang, dir: entry.dir === 'rtl' ? 'rtl' : 'ltr' }
}

export const localeOptions: readonly LocaleOption[] = [
  { code: 'en', label: 'English', shortLabel: 'EN - English', ...meta('en') },
  { code: 'ru', label: 'Русский', shortLabel: 'RU - Русский', ...meta('ru') },
  { code: 'zh', label: '简体中文', shortLabel: 'ZH - 简体中文', ...meta('zh') },
  { code: 'de', label: 'Deutsch', shortLabel: 'DE - Deutsch', ...meta('de') },
  { code: 'fr', label: 'Français', shortLabel: 'FR - Français', ...meta('fr') },
  { code: 'es', label: 'Español', shortLabel: 'ES - Español', ...meta('es') },
  { code: 'ar', label: 'العربية', shortLabel: 'AR - العربية', ...meta('ar') },
]
```

In `frontend/src/App.tsx:44`, replace `const DRIVER_NEUTRAL_BAND = 0.25` with:

```typescript
const DRIVER_NEUTRAL_BAND = shared.driverNeutralBand
```

and add `import shared from './localeStrings.json'` beside the other imports.

- [ ] **Step 4: Run everything**

```bash
npm test --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
```

Expected: PASS, and the build still prerenders 14 documents. `locales.test.ts` checks that every locale carries every
key in `Copy`; it now also checks the three added ones.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/localeStrings.json frontend/scripts/extract-locale-strings.mjs \
        frontend/src/localeStrings.test.ts frontend/src/locales.ts frontend/src/App.tsx
git commit -m "refactor: move the labels both sides render into one file"
```

---

### Task 2: The backend reads the shared file

**Files:**
- Create: `backend/app/locale_strings.py`, `backend/tests/test_locale_strings.py`

**Interfaces:**
- Consumes: `frontend/src/localeStrings.json` from Task 1.
- Produces:
  - `SUPPORTED_LOCALES: tuple[str, ...] = ("en", "ru", "zh", "de", "fr", "es", "ar")`
  - `@dataclass(frozen=True) class LocaleStrings` with fields `driver_neutral_band: float`,
    `labels: dict[str, dict[str, Any]]`, `risk_states: dict[str, dict[str, str]]`,
    `locale_meta: dict[str, dict[str, str]]` — each value `{"lang": ..., "dir": "ltr" | "rtl"}`
  - `def locale_strings_path() -> Path`
  - `def load_locale_strings(path: Path | None = None) -> LocaleStrings` — cached after the first call with no
    argument

**Where the file is, in each environment.** In a checkout it sits at `<repo>/frontend/src/localeStrings.json`, which
is `Path(__file__).resolve().parents[2] / "frontend" / "src" / "localeStrings.json"`. Inside the backend image the
code lives at `/app/app/`, a different depth, so Task 7's Dockerfile copies the file to `/app/localeStrings.json` and
sets `LOCALE_STRINGS_PATH` to it. The environment variable wins when set; otherwise the checkout path is used. Two
explicit cases, no searching.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_locale_strings.py`:

```python
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.locale_strings import SUPPORTED_LOCALES, load_locale_strings, locale_strings_path


class LocaleStringsTests(unittest.TestCase):
    def test_the_checkout_path_points_at_the_frontend_file(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LOCALE_STRINGS_PATH", None)
            path = locale_strings_path()
        self.assertEqual(path.name, "localeStrings.json")
        self.assertTrue(path.is_file(), f"{path} must exist in a checkout")

    def test_the_environment_variable_wins(self) -> None:
        with mock.patch.dict(os.environ, {"LOCALE_STRINGS_PATH": "/somewhere/else.json"}):
            self.assertEqual(locale_strings_path(), Path("/somewhere/else.json"))

    def test_every_locale_carries_the_page_keys(self) -> None:
        strings = load_locale_strings(locale_strings_path())
        self.assertEqual(tuple(strings.labels), SUPPORTED_LOCALES)
        for locale in SUPPORTED_LOCALES:
            for key in ("pageTitle", "historicalNotice", "todayLink", "driverRaises", "disclaimer"):
                self.assertIn(key, strings.labels[locale], f"{locale}.{key}")

    def test_it_reads_the_driver_band_the_frontend_uses(self) -> None:
        self.assertEqual(load_locale_strings(locale_strings_path()).driver_neutral_band, 0.25)

    def test_a_missing_locale_fails_loudly_rather_than_rendering_english(self) -> None:
        broken = {"driverNeutralBand": 0.25, "labels": {"en": {}}, "riskStates": {"en": {}}, "localeMeta": {"en": {}}}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(broken, handle)
        try:
            with self.assertRaises(ValueError):
                load_locale_strings(Path(handle.name))
        finally:
            Path(handle.name).unlink()
```

- [ ] **Step 2: Run it and watch it fail**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k locale_strings -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.locale_strings'`.

- [ ] **Step 3: Write the module**

Create `backend/app/locale_strings.py`:

```python
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

SUPPORTED_LOCALES: tuple[str, ...] = ("en", "ru", "zh", "de", "fr", "es", "ar")


@dataclass(frozen=True)
class LocaleStrings:
    driver_neutral_band: float
    labels: dict[str, dict[str, Any]]
    risk_states: dict[str, dict[str, str]]
    locale_meta: dict[str, dict[str, str]]


def locale_strings_path() -> Path:
    override = os.environ.get("LOCALE_STRINGS_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "frontend" / "src" / "localeStrings.json"


def _parse(raw: dict[str, Any]) -> LocaleStrings:
    labels = raw["labels"]
    states = raw["riskStates"]
    meta = raw["localeMeta"]
    missing = [
        locale for locale in SUPPORTED_LOCALES if locale not in labels or locale not in states or locale not in meta
    ]
    if missing:
        # A missing locale must fail at startup. Silently rendering English for it would serve a page
        # in the wrong language under a URL that promises the right one.
        raise ValueError(f"localeStrings.json is missing locales: {', '.join(missing)}")
    return LocaleStrings(
        driver_neutral_band=float(raw["driverNeutralBand"]),
        labels={locale: labels[locale] for locale in SUPPORTED_LOCALES},
        risk_states={locale: states[locale] for locale in SUPPORTED_LOCALES},
        locale_meta={locale: meta[locale] for locale in SUPPORTED_LOCALES},
    )


@lru_cache(maxsize=1)
def _load_default() -> LocaleStrings:
    return _parse(json.loads(locale_strings_path().read_text(encoding="utf-8")))


def load_locale_strings(path: Path | None = None) -> LocaleStrings:
    if path is None:
        return _load_default()
    return _parse(json.loads(path.read_text(encoding="utf-8")))
```

- [ ] **Step 4: Run it and watch it pass**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k locale_strings -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/locale_strings.py backend/tests/test_locale_strings.py
git commit -m "feat: read the shared locale strings from the backend"
```

---

### Task 3: Security headers for an HTML response

**Files:**
- Modify: `backend/app/security.py`
- Create: `backend/tests/test_html_security_headers.py`

**Interfaces:**
- Produces: `def build_html_security_headers(*, app_env: str) -> dict[str, str]`

`build_security_headers` sets `Content-Security-Policy: default-src 'none'`, right for JSON and fatal for a page that
must apply its own styles. `security_headers_middleware` in `backend/app/main.py` applies headers with `setdefault`,
so a route that sets its own `Content-Security-Policy` keeps it. This function is that route's header set.

**It serves S5b too.** The S5b spec points here for its confirmation and unsubscribe pages, and the unsubscribe page
submits a form. So `form-action` is `'self'`, not `'none'` — `'none'` would be tighter for this sub-project and would
break the next one.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_html_security_headers.py`:

```python
import unittest

from app.security import build_html_security_headers, build_security_headers


def _directives(policy: str) -> dict[str, str]:
    parts = [part.strip() for part in policy.split(";") if part.strip()]
    return {part.split()[0]: " ".join(part.split()[1:]) for part in parts}


class HtmlSecurityHeadersTests(unittest.TestCase):
    def test_the_page_may_apply_its_own_inline_styles(self) -> None:
        csp = _directives(build_html_security_headers(app_env="production")["Content-Security-Policy"])
        self.assertIn("'unsafe-inline'", csp["style-src"])

    def test_it_is_not_the_json_policy(self) -> None:
        html = build_html_security_headers(app_env="production")["Content-Security-Policy"]
        json_policy = build_security_headers(app_env="production")["Content-Security-Policy"]
        self.assertNotEqual(html, json_policy)
        self.assertNotIn("default-src 'none'", html)

    def test_it_runs_no_script(self) -> None:
        csp = _directives(build_html_security_headers(app_env="production")["Content-Security-Policy"])
        self.assertEqual(csp["script-src"], "'none'")

    def test_it_allows_a_same_origin_form_post_for_the_s5b_pages(self) -> None:
        csp = _directives(build_html_security_headers(app_env="production")["Content-Security-Policy"])
        self.assertEqual(csp["form-action"], "'self'")

    def test_it_keeps_the_framing_and_transport_protections(self) -> None:
        headers = build_html_security_headers(app_env="production")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("Strict-Transport-Security", headers)
        self.assertNotIn("Strict-Transport-Security", build_html_security_headers(app_env="development"))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k html_security -v`
Expected: FAIL — `ImportError: cannot import name 'build_html_security_headers'`.

- [ ] **Step 3: Add the function**

Append to `backend/app/security.py`:

```python
def build_html_security_headers(*, app_env: str) -> dict[str, str]:
    # For server-rendered pages. Inline CSS, no JavaScript, and same-origin form posts so the S5b
    # unsubscribe page can use the same set. nginx adds its own CSP in front of this one; browsers
    # enforce both, and nginx's already allows style-src 'unsafe-inline'.
    headers = build_security_headers(app_env=app_env)
    headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'none'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "base-uri 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    return headers
```

- [ ] **Step 4: Run it and watch it pass**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k html_security -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/security.py backend/tests/test_html_security_headers.py
git commit -m "feat: add the security header set for server-rendered pages"
```

---
### Task 4: Reading one observation and the recent dates

**Files:**
- Modify: `backend/app/repository.py:4` and append two functions
- Create: `backend/tests/test_risk_for_date.py`

**Interfaces:**
- Produces:
  - `async def fetch_risk_for_date(pool, day: date) -> tuple[dict[str, Any] | None, dict[str, Any] | None]` —
    `(observation, previous)`. The observation carries `model_price_usd`, `low_usd` and `high_usd`, exactly as
    `fetch_latest_risk` returns them. `previous` is the nearest earlier row, not necessarily the day before, so a gap
    in the series still yields a change line; it is `None` for the first row of the series.
  - `async def fetch_recent_risk_dates(pool, *, limit: int) -> list[date]` — most recent first.

Timestamps are stored at midnight UTC. Matching the day as a half-open range `[day 00:00, next day 00:00)` rather
than by equality keeps the query correct if a row is ever written at another instant of the same day.

This repository tests queries with a fake pool, as `backend/tests/test_repository.py` does, and stubs `asyncpg` so
the test runs without a database. Follow that pattern.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_risk_for_date.py`:

```python
from __future__ import annotations

import asyncio
import sys
import types
import unittest
from datetime import date, datetime, timezone

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Record=dict, Pool=object))

from app.repository import fetch_recent_risk_dates, fetch_risk_for_date


def _row(day: int, risk: float, *, low: float | None = 58800.0, high: float | None = 61584.0) -> dict:
    return {
        "timestamp": datetime(2026, 9, day, tzinfo=timezone.utc),
        "price_hlc3": 60100.0,
        "risk": risk,
        "score": -0.8,
        "risk_state": "neutral",
        "trend_dev": 0.1,
        "vol_regime": 0.2,
        "turnover": 0.3,
        "z_trend_dev": 0.4,
        "z_vol_regime": -0.5,
        "z_turnover": 0.0,
        "turnover_enabled": True,
        "low_usd": low,
        "high_usd": high,
    }


class OrderedFakePool:
    """Answers fetchrow calls in the order they are made, and records every query."""

    def __init__(self, *responses: dict | None) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, tuple]] = []

    async def fetchrow(self, query: str, *params):
        self.calls.append((query, params))
        return self.responses.pop(0)

    async def fetch(self, query: str, *params):
        self.calls.append((query, params))
        return self.responses.pop(0)


class FetchRiskForDateTests(unittest.TestCase):
    def test_returns_the_observation_and_the_one_before_it(self) -> None:
        pool = OrderedFakePool(_row(20, 0.31), _row(19, 0.29))
        observation, previous = asyncio.run(fetch_risk_for_date(pool, date(2026, 9, 20)))
        self.assertEqual(observation["risk"], 0.31)
        self.assertEqual(observation["model_price_usd"], 60100.0)
        self.assertEqual(observation["low_usd"], 58800.0)
        self.assertEqual(previous["risk"], 0.29)

    def test_matches_the_whole_day_as_a_half_open_range(self) -> None:
        pool = OrderedFakePool(_row(20, 0.31), None)
        asyncio.run(fetch_risk_for_date(pool, date(2026, 9, 20)))
        _, params = pool.calls[0]
        self.assertEqual(params[0], datetime(2026, 9, 20, tzinfo=timezone.utc))
        self.assertEqual(params[1], datetime(2026, 9, 21, tzinfo=timezone.utc))

    def test_a_date_outside_the_series_returns_nothing_and_asks_no_second_question(self) -> None:
        pool = OrderedFakePool(None)
        self.assertEqual(asyncio.run(fetch_risk_for_date(pool, date(2001, 1, 1))), (None, None))
        self.assertEqual(len(pool.calls), 1)

    def test_the_first_row_of_the_series_has_no_previous(self) -> None:
        pool = OrderedFakePool(_row(1, 0.4), None)
        observation, previous = asyncio.run(fetch_risk_for_date(pool, date(2026, 9, 1)))
        self.assertIsNotNone(observation)
        self.assertIsNone(previous)

    def test_a_day_without_ohlcv_keeps_low_and_high_null(self) -> None:
        pool = OrderedFakePool(_row(20, 0.31, low=None, high=None), _row(19, 0.29))
        observation, _ = asyncio.run(fetch_risk_for_date(pool, date(2026, 9, 20)))
        self.assertIsNone(observation["low_usd"])
        self.assertIsNone(observation["high_usd"])


class FetchRecentRiskDatesTests(unittest.TestCase):
    def test_returns_dates_most_recent_first(self) -> None:
        pool = OrderedFakePool([{"timestamp": datetime(2026, 9, 20, tzinfo=timezone.utc)},
                                {"timestamp": datetime(2026, 9, 19, tzinfo=timezone.utc)}])
        dates = asyncio.run(fetch_recent_risk_dates(pool, limit=90))
        self.assertEqual(dates, [date(2026, 9, 20), date(2026, 9, 19)])
        self.assertEqual(pool.calls[0][1], (90,))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k risk_for_date -v`
Expected: FAIL — `ImportError: cannot import name 'fetch_recent_risk_dates'`.

- [ ] **Step 3: Write the two functions**

`backend/app/repository.py:4` imports `date, datetime, time, timezone` and **not** `timedelta`. Change it to:

```python
from datetime import date, datetime, time, timedelta, timezone
```

Append:

```python
async def fetch_risk_for_date(
    pool: asyncpg.Pool, day: date
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    row = await pool.fetchrow(
        """
        SELECT
          r.*,
          o.low_usd,
          o.high_usd
        FROM btc_risk_daily r
        LEFT JOIN btc_ohlcv_daily o ON o.timestamp = r.timestamp
        WHERE r.timestamp >= $1 AND r.timestamp < $2
        ORDER BY r.timestamp ASC
        LIMIT 1
        """,
        start,
        end,
    )
    if row is None:
        return None, None
    previous = await pool.fetchrow(
        """
        SELECT r.*
        FROM btc_risk_daily r
        WHERE r.timestamp < $1
        ORDER BY r.timestamp DESC
        LIMIT 1
        """,
        start,
    )
    return _serialize_latest_risk_row(row), (_serialize_row(previous) if previous else None)


async def fetch_recent_risk_dates(pool: asyncpg.Pool, *, limit: int) -> list[date]:
    rows = await pool.fetch(
        """
        SELECT timestamp
        FROM btc_risk_daily
        ORDER BY timestamp DESC
        LIMIT $1
        """,
        limit,
    )
    return [row["timestamp"].date() for row in rows]
```

- [ ] **Step 4: Run it and watch it pass**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k risk_for_date -v`
Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repository.py backend/tests/test_risk_for_date.py
git commit -m "feat: read one observation and the dates behind the sitemap"
```

---
### Task 5: Building the page

**Files:**
- Create: `backend/app/risk_page.py`, `backend/tests/test_risk_page.py`
- Modify: `backend/app/brief.py` (the seven `"neutral"` summaries in `RISK_COPY`, nothing else)

**Interfaces:**
- Consumes: `LocaleStrings`, `SUPPORTED_LOCALES`, `load_locale_strings` from Task 2; `build_brief` and `RISK_COPY`
  from `backend/app/brief.py`; `LOW_RISK_THRESHOLD`, `HIGH_RISK_THRESHOLD`, `METHODOLOGY_VERSION` from
  `backend/app/risk.py`.
- Produces:
  - `SITE_ORIGIN = "https://bitcoinriskbrief.minihub.app"`
  - `def parse_risk_date(text: str) -> date | None`
  - `def risk_page_path(day: date, locale: str) -> str` — `/risk/2026-09-20` for English, `/ru/risk/2026-09-20` otherwise
  - `def driver_status(z: float | None, band: float) -> str` — `"raises" | "neutral" | "lowers" | "unavailable"`
  - `def build_risk_page(*, observation: dict, previous: dict | None, strings: LocaleStrings, locale: str) -> str`

**This is a pure function, and the repository's style is to test pure functions directly.** No backend test in this
repository drives a route through an HTTP client; `build_readiness_payload` is the model. Every behaviour of the page
is asserted here, and Task 6's route only wires it to HTTP and the cache headers.

**What the page says, in order:** the date as the heading; the historical notice, *above* the value; the value, its
band and the change from the previous observation; the model price and the day's range; the three drivers; the
brief's one-sentence summary for that state; the band boundaries and methodology version; links to today's reading and to the guide; the
disclaimer.

`driver_status` mirrors `driverStatusFromZScore` in `frontend/src/App.tsx` exactly, with the band read from the
shared file. The activity driver is `unavailable` — not `neutral` — when `turnover_enabled` is false or `turnover` or
`z_turnover` is missing, as the frontend does. Neutral is a statement about the market; unavailable is a statement
about the data.

**The page shows only the brief's `summary`, never its other three parts.** The spec asks for "the localised brief
prose for that state", and `summary` is the sentence about the state. The other three are written for a reader of the
*current* reading: `what_changed` duplicates the change row and, with no previous observation, `build_brief` fills it
with "broadly unchanged from the previous observation" — a comparison with a row that does not exist; `avoid_now` and
`confirm_next` are instructions in the present tense, which on a 2013 page read as guidance about today's market.

**The seven neutral summaries lose their time adverb.** Each says the equivalent of "right now" — *right now*,
*Сейчас*, *当前*, *derzeit*, *pour le moment*, *ahora*, *الآن* — so every neutral per-date page would assert the present,
which is the one thing the spec forbids. Found by rendering a page against the bundled CSV during the plan's dry run.
The fix is in `brief.py` rather than a second copy of the sentences, because two copies of one string have drifted in
this repository before. The live brief keeps saying the same thing minus one word; the live page already states the
date and freshness of the reading it shows.

**Prices keep their significant digits.** BTC traded below $1 from the series' first row, 2010-07-13, until February
2011. Whole-dollar rounding printed those days as `$0` for the model price, the low and the high — found the same way.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_risk_page.py`:

```python
from __future__ import annotations

import dataclasses
import re
import unittest
from datetime import date
from html import escape

from app.brief import RISK_COPY, build_brief
from app.locale_strings import SUPPORTED_LOCALES, load_locale_strings
from app.risk_page import build_risk_page, driver_status, parse_risk_date, risk_page_path

STRINGS = load_locale_strings()

# Words that place a sentence in the reader's present. None may appear in a state summary, because the per-date
# page renders those summaries under a past date.
PRESENT_TIME_WORDS = {
    "en": ("right now", "currently", "at the moment", "today"),
    "ru": ("сейчас", "в данный момент", "сегодня"),
    "zh": ("当前", "目前", "现在", "今天"),
    "de": ("derzeit", "jetzt", "aktuell", "heute"),
    "fr": ("pour le moment", "actuellement", "maintenant", "aujourd"),
    "es": ("ahora", "actualmente", "hoy"),
    "ar": ("الآن", "حاليا", "حالياً", "اليوم"),
}


def _observation(**overrides) -> dict:
    row = {
        "timestamp": "2026-09-20T00:00:00+00:00",
        "price_usd": 60100.0,
        "model_price_usd": 60100.0,
        "low_usd": 58800.0,
        "high_usd": 61584.0,
        "risk": 0.31,
        "score": -0.8,
        "risk_state": "neutral",
        "trend_dev": 0.1,
        "vol_regime": 0.2,
        "turnover": 0.3,
        "z_trend_dev": 0.9,
        "z_vol_regime": -0.9,
        "z_turnover": 0.1,
        "turnover_enabled": True,
    }
    row.update(overrides)
    return row


PREVIOUS = _observation(timestamp="2026-09-19T00:00:00+00:00", risk=0.29, risk_state="low")


def _driver_row(page: str, locale: str, name_key: str) -> str:
    """The <dd> that follows a driver's <dt>, so a status can be asserted for one driver alone."""
    name = escape(STRINGS.labels[locale][name_key], quote=True)
    match = re.search(rf"<dt>{re.escape(name)}</dt><dd>(.*?)</dd>", page)
    assert match is not None, f"no row for {name_key}"
    return match.group(1)


class ParseRiskDateTests(unittest.TestCase):
    def test_accepts_a_real_date(self) -> None:
        self.assertEqual(parse_risk_date("2026-09-20"), date(2026, 9, 20))

    def test_rejects_well_formed_strings_that_are_not_dates(self) -> None:
        for text in ("2026-02-30", "2026-13-01", "2026-00-10", "0000-01-01"):
            with self.subTest(text=text):
                self.assertIsNone(parse_risk_date(text))

    def test_rejects_anything_not_shaped_like_yyyy_mm_dd(self) -> None:
        for text in ("2026-9-1", "20260920", "yesterday", "", "2026-09-20x", " 2026-09-20"):
            with self.subTest(text=text):
                self.assertIsNone(parse_risk_date(text))


class PathTests(unittest.TestCase):
    def test_english_is_unprefixed_and_the_rest_carry_their_code(self) -> None:
        self.assertEqual(risk_page_path(date(2026, 9, 20), "en"), "/risk/2026-09-20")
        self.assertEqual(risk_page_path(date(2026, 9, 20), "ru"), "/ru/risk/2026-09-20")


class DriverStatusTests(unittest.TestCase):
    def test_uses_the_shared_band_on_both_sides_of_zero(self) -> None:
        band = STRINGS.driver_neutral_band
        self.assertEqual(driver_status(band + 0.01, band), "raises")
        self.assertEqual(driver_status(band - 0.01, band), "neutral")
        self.assertEqual(driver_status(-band - 0.01, band), "lowers")

    def test_missing_or_non_finite_is_unavailable(self) -> None:
        for value in (None, float("nan"), float("inf")):
            with self.subTest(value=value):
                self.assertEqual(driver_status(value, 0.25), "unavailable")


class BuildRiskPageTests(unittest.TestCase):
    def render(self, locale: str = "en", **overrides) -> str:
        return build_risk_page(
            observation=_observation(**overrides), previous=PREVIOUS, strings=STRINGS, locale=locale
        )

    def test_the_date_and_its_pastness_come_before_the_value(self) -> None:
        page = self.render()
        notice = STRINGS.labels["en"]["historicalNotice"].replace("{date}", "2026-09-20")
        self.assertLess(page.index("2026-09-20"), page.index("0.31"))
        self.assertIn(notice, page)
        self.assertLess(page.index(notice), page.index("0.31"))

    def test_states_its_pastness_in_every_locale(self) -> None:
        # The structural guarantee is in Task 1: currentRisk is not in the shared file, so this module
        # cannot render it. This checks the positive side — each locale says the page is historical.
        for locale in SUPPORTED_LOCALES:
            with self.subTest(locale=locale):
                notice = escape(STRINGS.labels[locale]["historicalNotice"].replace("{date}", "2026-09-20"), quote=True)
                self.assertIn(notice, self.render(locale))

    def test_renders_the_value_band_change_price_and_range(self) -> None:
        page = self.render()
        self.assertIn("0.31", page)
        self.assertIn(STRINGS.risk_states["en"]["neutral"], page)
        self.assertIn("+0.02", page)
        self.assertIn("$60,100", page)
        self.assertIn("$58,800", page)
        self.assertIn("$61,584", page)

    def test_renders_the_state_summary_and_none_of_the_present_tense_brief(self) -> None:
        for locale in SUPPORTED_LOCALES:
            for state in ("low", "neutral", "high"):
                with self.subTest(locale=locale, state=state):
                    page = self.render(locale, risk_state=state)
                    sections = build_brief(_observation(risk_state=state), PREVIOUS)["sections"][locale]
                    self.assertIn(escape(sections["summary"], quote=True), page)
                    for part in ("what_changed", "avoid_now", "confirm_next"):
                        self.assertNotIn(escape(sections[part], quote=True), page)
                    self.assertIn(STRINGS.labels[locale]["modelDrivers"], page)
                    self.assertIn(STRINGS.labels[locale]["disclaimer"], page)

    def test_no_state_summary_places_itself_in_the_present(self) -> None:
        for locale, states in RISK_COPY.items():
            for state, (summary, _avoid, _confirm) in states.items():
                with self.subTest(locale=locale, state=state):
                    for word in PRESENT_TIME_WORDS[locale]:
                        self.assertNotIn(word, summary.lower())

    def test_the_first_row_invents_no_comparison(self) -> None:
        page = build_risk_page(observation=_observation(), previous=None, strings=STRINGS, locale="en")
        invented = build_brief(_observation(), None)["sections"]["en"]["what_changed"]
        self.assertNotIn(invented, page)

    def test_early_sub_dollar_prices_keep_their_digits(self) -> None:
        page = self.render(model_price_usd=0.05816341, low_usd=0.05261677, high_usd=0.06634905)
        self.assertIn("$0.0582", page)
        self.assertIn("$0.0526", page)
        self.assertIn("$0.0663", page)
        self.assertNotIn("<dd>$0</dd>", page)

    def test_prices_between_one_and_a_thousand_dollars_show_cents(self) -> None:
        self.assertIn("$12.35", self.render(model_price_usd=12.3456))
        self.assertIn("$1,126", self.render(model_price_usd=1126.2))

    def test_states_the_band_boundaries_and_the_methodology_version(self) -> None:
        page = self.render()
        self.assertIn("0.30", page)
        self.assertIn("0.70", page)
        self.assertIn("crypto-scout-canonical-v1.1", page)

    def test_carries_canonical_hreflang_lang_and_dir(self) -> None:
        page = self.render("ru")
        self.assertIn('<link rel="canonical" href="https://bitcoinriskbrief.minihub.app/ru/risk/2026-09-20"', page)
        self.assertEqual(len(re.findall(r'rel="alternate"', page)), len(SUPPORTED_LOCALES) + 1)
        self.assertIn('hreflang="zh-CN"', page)
        self.assertIn('hreflang="x-default" href="https://bitcoinriskbrief.minihub.app/risk/2026-09-20"', page)
        self.assertIn('lang="ru" dir="ltr"', page)
        self.assertIn('lang="ar" dir="rtl"', self.render("ar"))

    def test_links_today_and_the_guide_in_the_same_language(self) -> None:
        page = self.render("de")
        self.assertIn('href="/de"', page)
        self.assertIn('href="/de/methodology"', page)
        english = self.render("en")
        self.assertIn('href="/"', english)
        self.assertIn('href="/methodology"', english)

    def test_inline_styles_only_and_no_script(self) -> None:
        page = self.render()
        self.assertIn("<style>", page)
        self.assertNotIn("<script", page)

    # ---- Review Focus -------------------------------------------------------------------

    def test_the_first_row_of_the_series_renders_without_a_change_line(self) -> None:
        page = build_risk_page(observation=_observation(), previous=None, strings=STRINGS, locale="en")
        self.assertIn("0.31", page)
        self.assertNotIn(STRINGS.labels["en"]["riskChange"], page)

    def test_missing_turnover_makes_activity_unavailable_not_neutral(self) -> None:
        # Assert the status itself, not only the explanatory detail: a page that printed "Neutral"
        # beside an "unavailable" explanation would pass a detail-only check, and is exactly the
        # claim about the market this must not make when the data is missing.
        for overrides in ({"turnover_enabled": False}, {"turnover": None}, {"z_turnover": None}):
            with self.subTest(**{k: str(v) for k, v in overrides.items()}):
                row = _driver_row(self.render(**overrides), "en", "driverActivity")
                self.assertIn(STRINGS.labels["en"]["driverUnavailable"], row)
                self.assertNotIn(STRINGS.labels["en"]["driverNeutral"], row)
                self.assertIn(STRINGS.labels["en"]["driverActivityUnavailableDetail"], row)

    def test_a_present_turnover_is_classified_by_its_z_score(self) -> None:
        row = _driver_row(self.render(z_turnover=0.9), "en", "driverActivity")
        self.assertIn(STRINGS.labels["en"]["driverRaises"], row)

    def test_a_day_without_ohlcv_omits_the_range_rather_than_showing_zero(self) -> None:
        page = self.render(low_usd=None, high_usd=None)
        self.assertNotIn("$0", page)
        self.assertNotIn(f'{STRINGS.labels["en"]["low"]} ', page.split("<body", 1)[1].split(STRINGS.labels["en"]["modelDrivers"])[0])

    def test_escapes_text_that_would_break_the_markup(self) -> None:
        hostile = dataclasses.replace(
            STRINGS,
            labels={**STRINGS.labels, "en": {**STRINGS.labels["en"], "disclaimer": 'a "quoted" <b>bold</b> line'}},
        )
        page = build_risk_page(observation=_observation(), previous=PREVIOUS, strings=hostile, locale="en")
        self.assertNotIn("<b>bold</b>", page)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", page)
        self.assertIn("&quot;quoted&quot;", page)
```

- [ ] **Step 2: Run it and watch it fail**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k risk_page -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.risk_page'`.

- [ ] **Step 3: Write the module**

Create `backend/app/risk_page.py`:

```python
from __future__ import annotations

import math
import re
from datetime import date
from html import escape
from typing import Any

from app.brief import build_brief
from app.locale_strings import SUPPORTED_LOCALES, LocaleStrings
from app.risk import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD, METHODOLOGY_VERSION

SITE_ORIGIN = "https://bitcoinriskbrief.minihub.app"
_DATE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}")

_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; background: #0c0d0f; color: #f4f0e8;
       font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       line-height: 1.55; }
main { max-width: 44rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
h1 { font-size: 1.6rem; margin: 0 0 .5rem; }
.notice { border-inline-start: 3px solid #f2b84b; padding: .6rem .9rem; background: #16181c; margin: 0 0 1.75rem; }
.value { font-size: 3rem; font-weight: 700; margin: 0; }
.muted { color: #b8b2a7; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: .35rem 1.25rem; }
dt { color: #b8b2a7; }
dd { margin: 0; }
section { margin-top: 2rem; }
a { color: #f2b84b; }
footer { margin-top: 3rem; font-size: .9rem; color: #b8b2a7; }
"""


def parse_risk_date(text: str) -> date | None:
    if not _DATE_SHAPE.fullmatch(text):
        return None
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return None
    return parsed


def risk_page_path(day: date, locale: str) -> str:
    prefix = "" if locale == "en" else f"/{locale}"
    return f"{prefix}/risk/{day.isoformat()}"


def _home_path(locale: str) -> str:
    return "/" if locale == "en" else f"/{locale}"


def _guide_path(locale: str) -> str:
    return "/methodology" if locale == "en" else f"/{locale}/methodology"


def driver_status(z: float | None, band: float) -> str:
    if z is None or not math.isfinite(z):
        return "unavailable"
    if z > band:
        return "raises"
    if z < -band:
        return "lowers"
    return "neutral"


def _usd(value: float) -> str:
    # Whole dollars would print every day before February 2011 as "$0".
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:.4f}"


def build_risk_page(
    *, observation: dict[str, Any], previous: dict[str, Any] | None, strings: LocaleStrings, locale: str
) -> str:
    labels = strings.labels[locale]
    states = strings.risk_states[locale]
    meta = strings.locale_meta[locale]
    day = date.fromisoformat(str(observation["timestamp"])[:10])
    day_text = day.isoformat()
    band = strings.driver_neutral_band

    def t(key: str) -> str:
        return escape(str(labels[key]), quote=True)

    def status_label(status: str) -> str:
        return t({"raises": "driverRaises", "lowers": "driverLowers",
                  "unavailable": "driverUnavailable"}.get(status, "driverNeutral"))

    activity_ok = (
        bool(observation.get("turnover_enabled"))
        and observation.get("turnover") is not None
        and observation.get("z_turnover") is not None
    )
    activity_status = driver_status(observation.get("z_turnover"), band) if activity_ok else "unavailable"
    activity_detail = "driverActivityDetail" if activity_ok else "driverActivityUnavailableDetail"
    drivers = [
        ("driverTrend", "driverTrendDetail", driver_status(observation.get("z_trend_dev"), band)),
        ("driverVolatility", "driverVolatilityDetail", driver_status(observation.get("z_vol_regime"), band)),
        ("driverActivity", activity_detail, activity_status),
    ]

    risk = float(observation["risk"])
    state = str(observation.get("risk_state") or "neutral")
    # Only the state summary: the brief's other parts address a reader of the current reading.
    summary = build_brief(observation)["sections"][locale]["summary"]

    rows = [f"<dt>{t('modelPrice')}</dt><dd>{_usd(float(observation['model_price_usd']))}</dd>"]
    if observation.get("low_usd") is not None and observation.get("high_usd") is not None:
        rows.append(f"<dt>{t('low')}</dt><dd>{_usd(float(observation['low_usd']))}</dd>")
        rows.append(f"<dt>{t('high')}</dt><dd>{_usd(float(observation['high_usd']))}</dd>")
    if previous is not None:
        delta = risk - float(previous["risk"])
        rows.append(f"<dt>{t('riskChange')}</dt><dd>{delta:+.2f} <span class=\"muted\">{t('riskChangeContext')}</span></dd>")

    driver_rows = "".join(
        f"<dt>{t(name)}</dt><dd>{status_label(status)} <span class=\"muted\">{t(detail)}</span></dd>"
        for name, detail, status in drivers
    )
    zones = labels["riskZones"]
    canonical = f"{SITE_ORIGIN}{risk_page_path(day, locale)}"
    alternates = "".join(
        f'<link rel="alternate" hreflang="{escape(strings.locale_meta[other]["lang"], quote=True)}" '
        f'href="{SITE_ORIGIN}{risk_page_path(day, other)}" />'
        for other in SUPPORTED_LOCALES
    )
    alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE_ORIGIN}{risk_page_path(day, "en")}" />'
    title = escape(labels["pageTitle"].replace("{date}", day_text), quote=True)
    notice = escape(labels["historicalNotice"].replace("{date}", day_text), quote=True)
    prose = f"<p>{escape(summary, quote=True)}</p>"

    return f"""<!doctype html>
<html lang="{escape(meta["lang"], quote=True)}" dir="{escape(meta["dir"], quote=True)}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<link rel="canonical" href="{canonical}" />
{alternates}
<style>{_STYLE}</style>
</head>
<body>
<main>
<h1>{title}</h1>
<p class="notice">{notice}</p>
<p class="value">{risk:.2f} <span class="muted">{escape(states.get(state, state), quote=True)}</span></p>
<dl>{"".join(rows)}</dl>
<section>
<h2>{t('modelDrivers')}</h2>
<dl>{driver_rows}</dl>
</section>
<section>{prose}</section>
<section>
<p class="muted">{LOW_RISK_THRESHOLD:.2f} {escape(str(zones[0]), quote=True)} · {HIGH_RISK_THRESHOLD:.2f} {escape(str(zones[1]), quote=True)}</p>
<p class="muted">{t('methodologyVersion')}: {escape(METHODOLOGY_VERSION, quote=True)}</p>
<p><a href="{_home_path(locale)}">{t('todayLink')}</a> · <a href="{_guide_path(locale)}">{t('methodologyLink')}</a></p>
</section>
<footer>{t('disclaimer')}</footer>
</main>
</body>
</html>
"""
```

- [ ] **Step 4: Take the time adverb out of the neutral summaries**

In `backend/app/brief.py`, `RISK_COPY`, replace exactly these seven strings — the first element of each locale's
`"neutral"` tuple — and change nothing else in the file:

| Locale | Before | After |
| --- | --- | --- |
| `en` | `Risk is neutral. BTC is not showing an extreme risk reading right now.` | `Risk is neutral. BTC is not showing an extreme risk reading.` |
| `ru` | `Риск нейтральный. Сейчас нет экстремального риск-сигнала по BTC.` | `Риск нейтральный. Экстремального риск-сигнала по BTC нет.` |
| `zh` | `风险中性。BTC 当前没有显示极端风险读数。` | `风险中性。BTC 没有显示极端风险读数。` |
| `de` | `Das Risiko ist neutral. BTC zeigt derzeit keinen extremen Risikowert.` | `Das Risiko ist neutral. BTC zeigt keinen extremen Risikowert.` |
| `fr` | `Le risque est neutre. BTC ne montre pas de lecture de risque extrême pour le moment.` | `Le risque est neutre. BTC ne montre pas de lecture de risque extrême.` |
| `es` | `El riesgo es neutral. BTC no muestra ahora una lectura de riesgo extrema.` | `El riesgo es neutral. BTC no muestra una lectura de riesgo extrema.` |
| `ar` | `المخاطر محايدة. لا يظهر BTC قراءة مخاطر متطرفة الآن.` | `المخاطر محايدة. لا يظهر BTC قراءة مخاطر متطرفة.` |

- [ ] **Step 5: Run it and watch it pass**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k risk_page -v`
Expected: PASS — the 23 tests in `test_risk_page.py`.

Run: `./scripts/manage.sh test-python`
Expected: PASS. No other test pins the neutral wording; if one does, it is asserting the sentence this task removes.

- [ ] **Step 6: Commit**

```bash
git add backend/app/risk_page.py backend/app/brief.py backend/tests/test_risk_page.py
git commit -m "feat: build a server-rendered page for one historical observation"
```

---
### Task 6: Routes, versioned headers and the dynamic sitemap

**Files:**
- Create: `backend/app/risk_sitemap.py`, `backend/tests/test_risk_sitemap.py`, `backend/tests/test_risk_routes.py`
- Modify: `backend/app/public_cache.py` (one public alias), `backend/app/main.py` (append at the end)

**Interfaces:**
- Consumes: Task 2's `load_locale_strings`, `SUPPORTED_LOCALES`; Task 3's `build_html_security_headers`; Task 4's
  `fetch_risk_for_date`, `fetch_recent_risk_dates`; Task 5's `build_risk_page`, `parse_risk_date`,
  `risk_page_path`, `SITE_ORIGIN`.
- Produces:
  - `def build_risk_sitemap(dates: list[date]) -> str` in `backend/app/risk_sitemap.py`
  - `def content_etag(key: str, data_version: str, content: Any) -> str` in `backend/app/public_cache.py`
  - Routes `GET /risk/{day}`, `GET /{locale}/risk/{day}`, `GET /sitemap-risk.xml`, all `include_in_schema=False`

**These pages do not go through `public_read_cache`, and that is a decision, not an omission.** The spec requires
them to use `build_cache_headers` with the same `data_version`, and they do. They do not need the in-process cache:
`PublicEndpointCache` has a 300-second TTL and prunes on write but has no size cap, and per-date pages are a long tail
of 41,398 addresses where an in-memory entry is almost never hit twice and is pure memory cost. Each request renders
the page: the data-version query, two indexed queries, and string building.

**Cloudflare does not cache these pages, and this plan does not change that.** `scripts/cloudflare_edge_rules.py`
enables edge caching only for the four `PUBLIC_READ_PATHS` under `/api/`, and Cloudflare does not cache HTML by
default. What the headers buy is browser caching for `max-age` and a body-less 304 on revalidation. That is enough at
the current traffic; an edge rule for `/risk/` is listed under Out of Scope, because applying one is operator work.

**The ETag is computed from the rendered page.** `_build_etag` already hashes content alongside the data version, so
the tag changes when the data changes *and* when a deploy changes the template or a label. A tag derived from the
data version alone would answer 304 to a client holding a page whose wording a deploy has since corrected.

`X-Cache` is always `MISS` on these responses. That is accurate — they bypass the in-process cache.

**Register the routes at the end of `main.py`.** Starlette matches in registration order, and
`/api/risk/latest`, `/api/risk/history` and `/api/risk/levels` have exactly the shape `/{locale}/risk/{day}`. Registered
first, the localised route would capture all three with `locale="api"` and answer 404 — the API would vanish without
a single failing route test of its own. Registered last, the API routes win; `/api/risk/2026-09-20` still matches no
API route and reaches the localised handler with `locale="api"`. So the handler must 404 any locale outside the six
prefixed ones — including `en`, which nginx redirects before it ever reaches the backend.

**The labels load when `main.py` is imported, not on the first page request.** Task 2's loader raises on a missing
file or a missing locale, and its comment promises that this fails at startup. Called lazily, it would not: the app
would start, pass its healthcheck, and answer 500 on the first per-date page hours later. Loading at import makes
uvicorn exit instead, and it gives CI's existing `import app.main` step in the image build a second job — proving the
image carries the file.

**They stay out of the OpenAPI schema.** That document is the API contract; an HTML page and a sitemap are not part
of it. `test_openapi_contract.py` checks `paths & PUBLIC_PATHS`, so it neither requires nor forbids extra paths.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_risk_sitemap.py`:

```python
import unittest
import xml.etree.ElementTree as ET
from datetime import date

from app.locale_strings import SUPPORTED_LOCALES
from app.risk_sitemap import build_risk_sitemap

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class RiskSitemapTests(unittest.TestCase):
    def test_lists_every_date_in_every_locale(self) -> None:
        xml = build_risk_sitemap([date(2026, 9, 20), date(2026, 9, 19)])
        self.assertNotIn("<!DOCTYPE", xml)
        locations = [node.text for node in ET.fromstring(xml).iter(f"{NS}loc")]
        self.assertEqual(len(locations), 2 * len(SUPPORTED_LOCALES))
        self.assertIn("https://bitcoinriskbrief.minihub.app/risk/2026-09-20", locations)
        self.assertIn("https://bitcoinriskbrief.minihub.app/ar/risk/2026-09-19", locations)
        self.assertEqual(len(locations), len(set(locations)))

    def test_states_the_advice_boundary_like_the_committed_sitemap(self) -> None:
        self.assertIn("not financial advice", build_risk_sitemap([date(2026, 9, 20)]).lower())

    def test_an_empty_series_is_still_a_valid_sitemap(self) -> None:
        root = ET.fromstring(build_risk_sitemap([]))
        self.assertEqual(root.tag, f"{NS}urlset")
        self.assertEqual(list(root), [])
```

Create `backend/tests/test_risk_routes.py`:

```python
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from fastapi import HTTPException
from starlette.requests import Request

import app.main as main

ROOT = Path(__file__).resolve().parents[2]


def _request(path: str, if_none_match: str | None = None) -> Request:
    headers = [(b"if-none-match", if_none_match.encode())] if if_none_match else []
    return Request({"type": "http", "method": "GET", "path": path, "query_string": b"", "headers": headers})


OBSERVATION = {
    "timestamp": "2026-09-20T00:00:00+00:00", "price_usd": 60100.0, "model_price_usd": 60100.0,
    "low_usd": 58800.0, "high_usd": 61584.0, "risk": 0.31, "score": -0.8, "risk_state": "neutral",
    "trend_dev": 0.1, "vol_regime": 0.2, "turnover": 0.3, "z_trend_dev": 0.9, "z_vol_regime": -0.9,
    "z_turnover": 0.1, "turnover_enabled": True,
}


class RiskRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patches = [
            mock.patch.object(main, "get_pool", return_value=object()),
            mock.patch.object(main, "fetch_public_data_version", mock.AsyncMock(return_value="v1")),
            mock.patch.object(main, "fetch_risk_for_date", mock.AsyncMock(return_value=(OBSERVATION, None))),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self) -> None:
        for patch in self.patches:
            patch.stop()

    def _status(self, call) -> int:
        try:
            return asyncio.run(call).status_code
        except HTTPException as error:
            return error.status_code

    def test_a_known_date_renders_html_with_page_headers(self) -> None:
        response = asyncio.run(main.risk_page_en(_request("/risk/2026-09-20"), "2026-09-20"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.media_type.startswith("text/html"))
        self.assertIn("style-src 'self' 'unsafe-inline'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["X-Cache-Version"], "v1")
        self.assertEqual(response.headers["X-Cache"], "MISS")
        self.assertIn(b"2026-09-20", response.body)

    def test_a_malformed_or_impossible_date_is_a_404_not_a_500(self) -> None:
        for text in ("2026-02-30", "2026-13-01", "yesterday", "2026-9-1"):
            with self.subTest(text=text):
                self.assertEqual(self._status(main.risk_page_en(_request(f"/risk/{text}"), text)), 404)

    def test_a_date_outside_the_series_is_a_404(self) -> None:
        with mock.patch.object(main, "fetch_risk_for_date", mock.AsyncMock(return_value=(None, None))):
            self.assertEqual(self._status(main.risk_page_en(_request("/risk/2001-01-01"), "2001-01-01")), 404)

    def test_the_localised_route_accepts_only_the_six_prefixed_locales(self) -> None:
        self.assertEqual(
            self._status(main.risk_page_localised(_request("/ru/risk/2026-09-20"), "ru", "2026-09-20")), 200
        )
        for locale in ("en", "api", "xx", "methodology"):
            with self.subTest(locale=locale):
                status = self._status(
                    main.risk_page_localised(_request(f"/{locale}/risk/2026-09-20"), locale, "2026-09-20")
                )
                self.assertEqual(status, 404)

    def test_a_matching_etag_answers_304_without_a_body(self) -> None:
        first = asyncio.run(main.risk_page_en(_request("/risk/2026-09-20"), "2026-09-20"))
        again = asyncio.run(
            main.risk_page_en(_request("/risk/2026-09-20", first.headers["ETag"]), "2026-09-20")
        )
        self.assertEqual(again.status_code, 304)
        self.assertEqual(again.body, b"")

    def test_a_changed_page_changes_the_etag_even_with_the_same_data_version(self) -> None:
        first = asyncio.run(main.risk_page_en(_request("/risk/2026-09-20"), "2026-09-20"))
        altered = dict(OBSERVATION, risk=0.42)
        with mock.patch.object(main, "fetch_risk_for_date", mock.AsyncMock(return_value=(altered, None))):
            second = asyncio.run(main.risk_page_en(_request("/risk/2026-09-20"), "2026-09-20"))
        self.assertNotEqual(first.headers["ETag"], second.headers["ETag"])

    def test_a_new_data_version_changes_the_etag_of_an_unchanged_page(self) -> None:
        first = asyncio.run(main.risk_page_en(_request("/risk/2026-09-20"), "2026-09-20"))
        with mock.patch.object(main, "fetch_public_data_version", mock.AsyncMock(return_value="v2")):
            second = asyncio.run(main.risk_page_en(_request("/risk/2026-09-20"), "2026-09-20"))
        self.assertEqual(first.body, second.body)
        self.assertNotEqual(first.headers["ETag"], second.headers["ETag"])
        self.assertEqual(second.headers["X-Cache-Version"], "v2")

    def test_the_sitemap_is_xml_without_the_page_csp(self) -> None:
        with mock.patch.object(main, "fetch_recent_risk_dates", mock.AsyncMock(return_value=[])):
            response = asyncio.run(main.risk_sitemap(_request("/sitemap-risk.xml")))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.media_type.startswith("application/xml"))
        self.assertNotIn("Content-Security-Policy", response.headers)

    def test_the_app_refuses_to_start_without_the_label_file(self) -> None:
        env = dict(os.environ, LOCALE_STRINGS_PATH=str(ROOT / "no-such-dir" / "localeStrings.json"))
        result = subprocess.run(
            [sys.executable, "-c", "import app.main"], cwd=ROOT, env=env, capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("localeStrings.json", result.stderr)

    def test_the_routes_are_registered_after_every_api_route(self) -> None:
        paths = [getattr(route, "path", "") for route in main.app.routes]
        last_api = max(index for index, path in enumerate(paths) if path.startswith("/api/"))
        self.assertGreater(paths.index("/{locale}/risk/{day}"), last_api)
```

`test_the_sitemap_is_xml_without_the_page_csp` checks the *route's* headers. The default JSON policy is added later by
`security_headers_middleware`, which these direct calls bypass, so the assertion confirms only that the HTML set is
not attached to the sitemap — which is the point.

- [ ] **Step 2: Run them and watch them fail**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k risk_ -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.risk_sitemap'` for the sitemap module, and every route
test erroring in `setUp` with `AttributeError: <module 'app.main' ...> does not have the attribute
'fetch_risk_for_date'`, because the patch target does not exist yet.

- [ ] **Step 3: Write the sitemap builder**

Create `backend/app/risk_sitemap.py`:

```python
from __future__ import annotations

from datetime import date
from xml.sax.saxutils import escape

from app.locale_strings import SUPPORTED_LOCALES
from app.risk_page import SITE_ORIGIN, risk_page_path


def build_risk_sitemap(dates: list[date]) -> str:
    entries = "".join(
        f"  <url>\n    <loc>{escape(SITE_ORIGIN + risk_page_path(day, locale))}</loc>\n"
        f"    <changefreq>monthly</changefreq>\n  </url>\n"
        for day in dates
        for locale in SUPPORTED_LOCALES
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!-- Analytics and research context only; not financial advice. -->\n"
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}"
        "</urlset>\n"
    )
```

`changefreq` is `monthly` because a settled day changes only when a re-import corrects history.

- [ ] **Step 4: Expose the ETag function**

Append to `backend/app/public_cache.py`:

```python
def content_etag(key: str, data_version: str, content: Any) -> str:
    """The same tag the public cache assigns, for responses that do not go through it."""
    return _build_etag(key, data_version, content)
```

- [ ] **Step 5: Wire the routes**

Add to the imports at the top of `backend/app/main.py`:

```python
from app.locale_strings import SUPPORTED_LOCALES, load_locale_strings
from app.public_cache import content_etag
from app.repository import fetch_recent_risk_dates, fetch_risk_for_date
from app.risk_page import build_risk_page, parse_risk_date
from app.risk_sitemap import build_risk_sitemap
from app.security import build_html_security_headers
```

`content_etag` belongs in the existing `from app.public_cache import (...)` block, and the two repository functions in
the existing `from app.repository import (...)` block — add them there rather than as second import lines.

Append **at the very end** of `backend/app/main.py`:

```python
RISK_PAGE_LOCALES = frozenset(locale for locale in SUPPORTED_LOCALES if locale != "en")
RISK_SITEMAP_DAYS = 90
# Loaded at import so a missing or incomplete file stops the app from starting.
LOCALE_STRINGS = load_locale_strings()


async def _versioned_response(request: Request, body: str, *, media_type: str, html: bool) -> Response:
    data_version = await fetch_public_data_version(get_pool())
    etag = content_etag(_public_cache_key(request), data_version, body)
    headers = build_cache_headers(
        etag=etag,
        data_version=data_version,
        cache_hit=False,
        max_age_seconds=settings.public_cache_max_age_seconds,
        stale_while_revalidate_seconds=settings.public_cache_stale_while_revalidate_seconds,
    )
    if html:
        # security_headers_middleware uses setdefault, so these survive it.
        headers.update(build_html_security_headers(app_env=settings.app_env))
    if etag_matches(etag, request.headers.get("if-none-match")):
        return Response(status_code=304, headers=headers)
    return Response(content=body, media_type=media_type, headers=headers)


async def _risk_page_response(request: Request, locale: str, day_text: str) -> Response:
    day = parse_risk_date(day_text)
    if day is None:
        raise HTTPException(status_code=404, detail="Not Found")
    observation, previous = await fetch_risk_for_date(get_pool(), day)
    if observation is None:
        raise HTTPException(status_code=404, detail="Not Found")
    page = build_risk_page(observation=observation, previous=previous, strings=LOCALE_STRINGS, locale=locale)
    return await _versioned_response(request, page, media_type="text/html; charset=utf-8", html=True)


@app.get("/risk/{day}", include_in_schema=False)
async def risk_page_en(request: Request, day: str) -> Response:
    return await _risk_page_response(request, "en", day)


@app.get("/{locale}/risk/{day}", include_in_schema=False)
async def risk_page_localised(request: Request, locale: str, day: str) -> Response:
    if locale not in RISK_PAGE_LOCALES:
        raise HTTPException(status_code=404, detail="Not Found")
    return await _risk_page_response(request, locale, day)


@app.get("/sitemap-risk.xml", include_in_schema=False)
async def risk_sitemap(request: Request) -> Response:
    dates = await fetch_recent_risk_dates(get_pool(), limit=RISK_SITEMAP_DAYS)
    return await _versioned_response(
        request, build_risk_sitemap(dates), media_type="application/xml", html=False
    )
```

- [ ] **Step 6: Run them and watch them pass**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k risk_ -v`
Expected: PASS — the 3 `RiskSitemapTests` and 10 `RiskRouteTests` among them, alongside Tasks 4 and 5 and the
existing tests whose names contain `risk_`.

Run: `./scripts/manage.sh test-python`
Expected: PASS. `test_openapi_contract.py` must still pass; the new routes are excluded from the schema.

- [ ] **Step 7: Commit**

```bash
git add backend/app/risk_sitemap.py backend/app/public_cache.py backend/app/main.py \
        backend/tests/test_risk_sitemap.py backend/tests/test_risk_routes.py
git commit -m "feat: serve per-date risk pages and their sitemap from the backend"
```

---
### Task 7: The backend image carries the label file

**Files:**
- Create: `backend/tests/test_backend_build.py`
- Modify: `backend/Dockerfile`, `podman-compose.yml` (the `backend` service's `build`), `.github/workflows/ci.yml`
  (the `image-build` job's backend build line)

**Interfaces:**
- Consumes: Task 2's `LOCALE_STRINGS_PATH` override; Task 6's import-time `LOCALE_STRINGS = load_locale_strings()`.
- Produces: a backend image in which `import app.main` succeeds only because `/app/localeStrings.json` is present.

The backend build context moves from `./backend` to the repository root, the way the collector's already did. Nothing
else in the image changes: the Dockerfile still copies only `requirements.txt` and `app/`, now addressed from the root,
plus the one JSON file.

**The root context contains the operator's `.env`.** The root `.dockerignore` already excludes `.env` and `.env.*` —
the collector has depended on that since it moved — and the Dockerfile copies named paths only, so no secret reaches
the image either way. The test below pins the exclusion, because this change makes a second image depend on it.

**CI's existing `import app.main` step becomes the proof the spec asks for.** After Task 6, importing `app.main` loads
the labels; an image missing the file fails that step. No new CI step is needed, and adding one that loads the labels
again would only test the same thing twice.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_backend_build.py`:

```python
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


def _compose_service(name: str) -> str:
    text = (ROOT / "podman-compose.yml").read_text(encoding="utf-8")
    match = re.search(rf"^  {name}:\n(?P<body>.*?)(?=^  [\w-]+:\n|\Z)", text, re.MULTILINE | re.DOTALL)
    if match is None:
        raise AssertionError(f"compose service {name} not found")
    return match.group("body")


class BackendBuildTests(unittest.TestCase):
    def test_the_dockerfile_copies_the_shared_labels_and_points_at_them(self) -> None:
        dockerfile = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY backend/requirements.txt .", dockerfile)
        self.assertIn("COPY backend/app ./app", dockerfile)
        self.assertIn("COPY frontend/src/localeStrings.json ./localeStrings.json", dockerfile)
        self.assertIn("LOCALE_STRINGS_PATH=/app/localeStrings.json", dockerfile)

    def test_compose_builds_the_backend_from_the_repository_root(self) -> None:
        backend = _compose_service("backend")
        self.assertRegex(backend, r"\n      context: \.\n")
        self.assertIn("dockerfile: ./backend/Dockerfile", backend)

    def test_ci_builds_the_backend_from_the_repository_root_and_imports_it(self) -> None:
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("docker build -t brb-backend:ci -f ./backend/Dockerfile .", ci)
        self.assertIn('docker run --rm brb-backend:ci python -c "import app.main"', ci)

    def test_the_root_build_context_never_sends_env_files(self) -> None:
        ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".env", ignored)
        self.assertIn(".env.*", ignored)
```

- [ ] **Step 2: Run them and watch them fail**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest backend/tests/test_backend_build.py -v`
Expected: FAIL — three failures (Dockerfile, compose, CI); `test_the_root_build_context_never_sends_env_files`
already passes, because it pins an existing property.

- [ ] **Step 3: Rewrite the Dockerfile for the root context**

Replace the whole of `backend/Dockerfile` with:

```dockerfile
FROM docker.io/library/python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     LOCALE_STRINGS_PATH=/app/localeStrings.json

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY frontend/src/localeStrings.json ./localeStrings.json

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The `FROM` line is unchanged; keep whatever tag `main` has when you start, because Dependabot bumps it.

- [ ] **Step 4: Point compose and CI at the root**

In `podman-compose.yml`, the `backend` service's build block becomes:

```yaml
    build:
      context: .
      dockerfile: ./backend/Dockerfile
```

In `.github/workflows/ci.yml`, job `image-build`, replace the backend build step and comment the import step:

```yaml
      - name: Build backend image
        run: docker build -t brb-backend:ci -f ./backend/Dockerfile .
      # Importing app.main loads frontend/src/localeStrings.json, so this also proves the image carries it.
      - name: Backend imports
        run: docker run --rm brb-backend:ci python -c "import app.main"
```

- [ ] **Step 5: Run the tests and build the image**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest backend/tests/test_backend_build.py -v`
Expected: PASS — 4 tests.

Run: `./scripts/manage.sh validate`
Expected: `compose config ok`.

If `podman` or `docker` is available locally, build and import exactly as CI does (substitute `docker` for `podman`
if that is what you have):

```bash
podman build -t brb-backend:local -f ./backend/Dockerfile .
podman run --rm brb-backend:local python -c "import app.main"
podman run --rm -e LOCALE_STRINGS_PATH=/nowhere.json brb-backend:local python -c "import app.main"
```

Expected: the first `run` exits 0 silently; the second exits non-zero with a `FileNotFoundError` naming
`/nowhere.json`. The second command is the negative control — it shows the first passes because of the file, not in
spite of it. If neither engine is available, say so in the task report; CI runs the first two commands.

- [ ] **Step 6: Commit**

```bash
git add backend/Dockerfile podman-compose.yml .github/workflows/ci.yml backend/tests/test_backend_build.py
git commit -m "build: build the backend from the repository root so it can read the shared labels"
```

---

### Task 8: nginx sends per-date pages to the backend

**Files:**
- Create: `scripts/check-nginx-routes.sh`
- Modify: `frontend/nginx.conf`, `frontend/public/robots.txt`, `.github/workflows/ci.yml` (job `image-build`),
  `backend/tests/test_agent_surface.py`, `backend/tests/test_frontend_security_headers.py`, `README.md`,
  `docs/engineering/architecture.md`, `docs/engineering/security-and-privacy.md`

**Interfaces:**
- Consumes: Task 2's `SUPPORTED_LOCALES`; Task 6's routes `/risk/{day}`, `/{locale}/risk/{day}`, `/sitemap-risk.xml`.
- Produces: `scripts/check-nginx-routes.sh <frontend-image>` — exits non-zero if any path lands on the wrong side of the
  nginx/backend boundary.

Three locations proxy to the backend: `/risk/`, the six prefixed locales' `/<locale>/risk/`, and `/sitemap-risk.xml`.
`/en/risk/<date>` redirects to `/risk/<date>`, as S4a's `/en/methodology` does. Everything else is untouched and still
404s from `try_files $uri $uri.html =404`.

**The new locations carry no `add_header`, on purpose — copy `/api/`, not `/`.** nginx inherits server-level
`add_header` only into locations that declare none of their own. Without any, the proxied pages keep the server's
security headers and the backend's `Cache-Control` and `ETag` pass through untouched. One `add_header` line would
silently drop every inherited header for that location. The browser receives two CSPs — nginx's and the backend's —
and enforces both, which the Global Constraints already cover. `test_all_frontend_csp_headers_use_four_identical_exact_policies`
counts CSP lines and must still count four.

**`proxy_pass http://backend:8000;` has no URI part,** unlike `/api/`'s `http://backend:8000/api/`. nginx forbids a URI
part in a regex location, and without one it passes the request path through unchanged — which is what all three need.

**Redirects are already relative; keep them so.** `frontend/nginx.conf` on `main` sets `absolute_redirect off;`,
added by a hotfix after this plan's dry run found that nginx's default built `Location` from its own port — `/en`
answered `Location: http://bitcoinriskbrief.minihub.app:3000/` behind the tunnel. `NginxRouteTests` already guards
the directive. The new `/en/risk/` redirect inherits it; do not add the directive again, and do not move it into a
location.

**Checking the routing with the real nginx.** Text assertions on `nginx.conf` cannot tell whether a location actually
wins. `scripts/check-nginx-routes.sh` runs the built frontend image *without a backend*, with `backend` pointed at the
loopback: a proxied path answers 502, because nothing listens upstream, and a path nginx owns answers 200, 301 or 404.
The status code therefore says which side of the boundary each path lands on. It runs in CI after the existing
`nginx -t` step. It does not belong in Playwright, whose `vite preview` server knows nothing of `nginx.conf`.

- [ ] **Step 1: Write the failing tests**

In `backend/tests/test_agent_surface.py`, add `from app.locale_strings import SUPPORTED_LOCALES` to the imports, and
replace `test_robots_allows_crawling_and_points_at_the_sitemap` with:

```python
    def test_robots_allows_crawling_and_points_at_both_sitemaps(self) -> None:
        text = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", text)
        self.assertIn("Allow: /", text)
        self.assertIn(f"Sitemap: {PRODUCT_URL}sitemap.xml", text)
        self.assertIn(f"Sitemap: {PRODUCT_URL}sitemap-risk.xml", text)
        self.assertIn("not financial advice", text.lower())
```

Append to class `NginxRouteTests` in the same file:

```python
    def test_per_date_pages_are_proxied_for_exactly_the_six_prefixed_locales(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("location /risk/ {", text)
        self.assertIn("location = /sitemap-risk.xml {", text)
        match = re.search(r"location ~ \^/\(([a-z|]+)\)/risk/ \{", text)
        self.assertIsNotNone(match, "the localised per-date location is missing")
        self.assertEqual(set(match.group(1).split("|")), set(SUPPORTED_LOCALES) - {"en"})

    def test_english_prefixed_risk_pages_redirect_to_the_canonical_ones(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("location ~ ^/en/risk/(.*)$ {", text)
        self.assertIn("return 301 /risk/$1;", text)

    def test_ci_checks_the_routing_with_the_real_nginx(self) -> None:
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("./scripts/check-nginx-routes.sh brb-frontend:ci", ci)
```

In `backend/tests/test_frontend_security_headers.py`, append to class `FrontendSecurityHeaderTests`:

```python
    def test_backend_rendered_pages_inherit_headers_and_keep_backend_caching(self) -> None:
        config = _read_nginx_conf()
        for location in ("/risk/", "~ ^/(ru|zh|de|fr|es|ar)/risk/", "= /sitemap-risk.xml"):
            block = _location_block(config, location)
            self.assertIn("proxy_pass http://backend:8000;", block, location)
            self.assertNotIn("add_header", block, location)
```

- [ ] **Step 2: Run them and watch them fail**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest backend/tests/test_agent_surface.py backend/tests/test_frontend_security_headers.py -v`
(`node -v` must print v22.x first: `test_frontend_security_headers.py` runs `npm run prebuild`, and under an older
Node three unrelated sitekey tests fail too.)
Expected: FAIL — the robots test, the three new `NginxRouteTests`, and the new header test (`AssertionError: location
/risk/ block not found`); five failures.

- [ ] **Step 3: Add the locations**

In `frontend/nginx.conf`, insert this directly after the closing `}` of `location /api/`:

```nginx

  # Per-date risk pages and their sitemap are rendered by the backend. No add_header here: as with
  # /api/, the server-level security headers are inherited and the backend's caching headers pass through.
  location /risk/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location ~ ^/(ru|zh|de|fr|es|ar)/risk/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location = /sitemap-risk.xml {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location ~ ^/en/risk/(.*)$ {
    return 301 /risk/$1;
  }
```

- [ ] **Step 4: Add the second sitemap to robots.txt**

In `frontend/public/robots.txt`, directly after the existing `Sitemap:` line, add:

```text
Sitemap: https://bitcoinriskbrief.minihub.app/sitemap-risk.xml
```

- [ ] **Step 5: Write the routing check**

Create `scripts/check-nginx-routes.sh` and make it executable (`chmod +x scripts/check-nginx-routes.sh`):

```bash
#!/usr/bin/env bash
# Checks frontend/nginx.conf's routing with the real nginx in a built frontend image, and no backend.
# A path proxied to the backend answers 502, because nothing listens upstream; a path nginx owns answers
# 200, 301 or 404. The status therefore shows which side of the boundary each path lands on.
set -euo pipefail

IMAGE="${1:?usage: $0 <frontend-image>}"
ENGINE="${CONTAINER_ENGINE:-docker}"
PORT="${NGINX_CHECK_PORT:-3999}"
NAME="brb-nginx-route-check-$$"
BASE="http://127.0.0.1:${PORT}"

"${ENGINE}" run -d --rm --name "${NAME}" --add-host backend:127.0.0.1 -p "127.0.0.1:${PORT}:3000" "${IMAGE}" >/dev/null
trap '"${ENGINE}" rm -f "${NAME}" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 40); do
  if curl -fs -o /dev/null "${BASE}/"; then break; fi
  sleep 0.25
done

failures=0
expect() {
  local path="$1" want="$2" got
  got="$(curl -s -o /dev/null -w '%{http_code}' "${BASE}${path}")"
  if [[ "${got}" == "${want}" ]]; then
    echo "ok   ${want} ${path}"
  else
    echo "FAIL ${path}: expected ${want}, got ${got}" >&2
    failures=$((failures + 1))
  fi
}
expect_location() {
  local path="$1" want="$2" got
  got="$(curl -s -o /dev/null -D - "${BASE}${path}" | tr -d '\r' | sed -n 's/^[Ll]ocation: //p')"
  if [[ "${got}" == "${want}" ]]; then
    echo "ok   ${path} -> ${want}"
  else
    echo "FAIL ${path}: expected Location ${want}, got '${got}'" >&2
    failures=$((failures + 1))
  fi
}

# Proxied to the backend.
expect /risk/2026-09-20 502
for locale in ru zh de fr es ar; do expect "/${locale}/risk/2026-09-20" 502; done
expect /sitemap-risk.xml 502
expect /api/readiness 502

# Owned by nginx.
expect / 200
expect /sitemap.xml 200
expect /robots.txt 200
expect /en/risk/2026-09-20 301
expect_location /en/risk/2026-09-20 /risk/2026-09-20
expect_location /en /
expect_location /risk /risk/
expect /xx/risk/2026-09-20 404
expect /en-gb/risk/2026-09-20 404
expect /riskless 404

if (( failures > 0 )); then
  echo "${failures} route check(s) failed" >&2
  exit 1
fi
echo "nginx routes ok"
```

`/risk` without a trailing slash is not a 404 from nginx. A prefix location ending in `/` with `proxy_pass` makes
nginx answer `/risk` with a 301 to `/risk/`, which it then proxies; the backend 404s it, because `{day}` cannot be
empty. The visitor still ends on a 404, one hop later. The check pins the redirect so the behaviour is known rather
than discovered.

In `.github/workflows/ci.yml`, job `image-build`, add a step directly after `Frontend nginx config is valid`:

```yaml
      - name: Frontend nginx routes per-date pages to the backend
        run: ./scripts/check-nginx-routes.sh brb-frontend:ci
```

- [ ] **Step 6: Update the current-state docs**

In `README.md`, the services table:

```markdown
| `backend` | FastAPI, asyncpg | API, readiness, waitlist storage, risk and brief reads, per-date risk pages |
| `frontend` | React, Vite, ECharts, nginx | Public seven-locale interface; proxies the API and per-date pages |
```

In `docs/engineering/architecture.md`, the `backend` and `frontend` rows of the service table:

```markdown
| `backend` | FastAPI, asyncpg | Serves health/readiness, risk, risk levels, brief, and waitlist endpoints, plus server-rendered per-date risk pages (`/risk/YYYY-MM-DD`, `/<locale>/risk/YYYY-MM-DD`) and `/sitemap-risk.xml`. |
| `frontend` | React, Vite, ECharts, nginx | Renders the product UI and proxies `/api/*`, the per-date risk pages, and `/sitemap-risk.xml` to the backend. |
```

and replace the first paragraph of `## Public Entry Point` with:

```markdown
The frontend nginx container is the public local entry point on `127.0.0.1:3001` by default. It serves static assets and proxies `/api/*`, `/risk/*`, `/<locale>/risk/*` and `/sitemap-risk.xml` to the backend service; any other unknown path is a 404 from nginx. `scripts/check-nginx-routes.sh` verifies that boundary against the built image.

The backend image is built from the repository root, like the collector's, so it can copy `frontend/src/localeStrings.json` — the one file of localised labels both the frontend and the per-date pages render.
```

In `docs/engineering/security-and-privacy.md`, replace the paragraph that begins `Backend API responses also include` with:

```markdown
Backend API responses also include API-safe security headers, with `Content-Security-Policy: default-src 'none'`. Backend-rendered HTML pages — the per-date risk pages — use `build_html_security_headers` instead: `default-src 'self'`, no scripts, inline styles allowed, same-origin form posts. Behind nginx those pages carry both nginx's policy and the backend's, and the browser enforces both. In production mode, backend responses include HSTS.
```

- [ ] **Step 7: Run everything this task touches**

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest backend/tests/test_agent_surface.py backend/tests/test_frontend_security_headers.py -v`
Expected: PASS.

Run the routing check against a freshly built image (substitute `docker` for `podman` if that is what you have):

```bash
podman build -t brb-frontend:local --build-arg VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA ./frontend
CONTAINER_ENGINE=podman ./scripts/check-nginx-routes.sh brb-frontend:local
```

Expected: every line `ok`, ending `nginx routes ok`. If neither engine is available, say so in the task report; CI runs
the check.

Run the three commands from Global Constraints:

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/nginx.conf frontend/public/robots.txt scripts/check-nginx-routes.sh .github/workflows/ci.yml \
        backend/tests/test_agent_surface.py backend/tests/test_frontend_security_headers.py \
        README.md docs/engineering/architecture.md docs/engineering/security-and-privacy.md
git commit -m "feat: route per-date risk pages through nginx and advertise their sitemap"
```

---
## Final Verification

Run after Task 8, on the integrated branch.

```bash
node -v                                     # v22.x
./scripts/manage.sh test-python
npm test --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run smoke --prefix frontend
./scripts/manage.sh validate
.venv/bin/mkdocs build --strict -d "$(mktemp -d)"
```

### End to end against the bundled CSV

Unit fixtures missed two of this plan's defects; rendering real rows found them. If `podman` or `docker` is available,
run the stack by hand as below. **Do not use `./scripts/manage.sh start` or `backfill` for this.** Compose reads the
repository's `.env`, which on an operator's machine can hold a real `TELEGRAM_BOT_TOKEN`, and `--backfill` ends by
calling `publish_daily_post`. These commands pass only a database URL, on a private network, with no volume that
outlives the run.

```bash
E=podman   # or docker
NET=brb-s4b-check; DB=postgresql://postgres:check@timescaledb:5432/bitcoin_risk_brief
$E network create $NET
$E run -d --name brb-check-db --network $NET --network-alias timescaledb \
  -e POSTGRES_DB=bitcoin_risk_brief -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=check \
  -v "$PWD/migrations:/docker-entrypoint-initdb.d:ro" docker.io/timescale/timescaledb:2.30.1-pg16
until $E exec brb-check-db pg_isready -U postgres -d bitcoin_risk_brief; do sleep 1; done; sleep 3
$E build -t brb-collector:check -f ./collector/Dockerfile .
$E build -t brb-backend:check -f ./backend/Dockerfile .
$E build -t brb-frontend:check --build-arg VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA ./frontend
$E run --rm --network $NET -e DATABASE_URL=$DB brb-collector:check python -m collector.main --backfill
$E run -d --name brb-check-backend --network $NET --network-alias backend -e DATABASE_URL=$DB brb-backend:check
$E run -d --name brb-check-frontend --network $NET -p 127.0.0.1:3997:3000 brb-frontend:check
```

Use the `timescaledb` tag from `podman-compose.yml` on `main` if Dependabot has moved it. Start the frontend last:
nginx resolves `backend` once, at start, so a backend container recreated afterwards answers 502 until the frontend
restarts.

Then, against `http://127.0.0.1:3997`:

| Request | Expected |
| --- | --- |
| `/risk/2024-01-01`, `/ru/risk/2024-01-01`, `/ar/risk/2024-01-01` | 200 `text/html`; the Arabic page has `dir="rtl"` |
| `/risk/2009-01-03`, `/risk/2030-01-01`, `/risk/2024-02-30`, `/risk/yesterday` | 404 |
| `/api/risk/2024-01-01` | 404; `/api/risk/latest` still 200 |
| `/en/risk/2024-01-01` | 301, `Location: /risk/2024-01-01` |
| `/sitemap-risk.xml` | 200 `application/xml`, 630 `<loc>` entries |
| `/risk/2010-07-13` | the first row: no change row, no "previous observation" prose, prices with four decimals |
| headers of `/risk/2024-01-01` | two `Content-Security-Policy` headers (nginx's and the backend's); `X-Cache-Version` equal to `/api/risk/latest`'s |
| the same request with `If-None-Match: <its ETag>` | 304 with an empty body |

Tear down: `$E rm -f -v brb-check-frontend brb-check-backend brb-check-db && $E network rm $NET`.

If no container engine is available, say so in the final report; CI covers the image builds, the import and the nginx
routing, but not the rendered pages against real rows.

## Out Of Scope

- **Edge caching and edge rate limiting for the new paths.** `scripts/cloudflare_edge_rules.py` caches only the four
  `/api/` public reads and rate-limits only `/api/`. Adding `/risk/`, `/<locale>/risk/` and `/sitemap-risk.xml` is a
  change to that script plus an operator run of `scripts/apply-cloudflare-cache-rules.sh`; worth doing if crawler
  traffic grows.
- **An uptime monitor for a per-date page.** `docs/operations/uptime-monitoring.md` leaves `/sitemap.xml` unmonitored
  because it cannot fail apart from the homepage. `/risk/<date>` and `/sitemap-risk.xml` can — they need the backend
  and the database. A HetrixTools keyword monitor on a fixed historical date is operator work, recorded in
  `uptime-monitors.csv` once it exists.
- **Linking to per-date pages** from the history chart, the MCP tools, or `llms.txt`.
- **Submitting `/sitemap-risk.xml` to search consoles.** `robots.txt` advertises it; submission is operator work.
- **Historical ladders and prerendering**, per the spec's non-goals.
