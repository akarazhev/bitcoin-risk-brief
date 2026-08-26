# Methodology Guide And Addressable URLs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every page a locale-bearing URL whose content is in the server response, and publish an in-product
guide explaining what the risk number means.

**Architecture:** A route × locale matrix drives a build-time `renderToString` pass that writes fourteen flat HTML
files. The prerender never calls the API, so no live value can be frozen into a crawlable document. nginx serves the
files with `try_files $uri $uri.html =404`, which keeps genuine 404s for everything else.

**Tech Stack:** React 19 + Vite + TypeScript, Vitest for unit tests, Playwright for smoke, `react-dom/server` for the
prerender, nginx for serving, Python `unittest` for the cross-cutting assertions.

**Spec:** [`docs/superpowers/specs/2026-08-25-methodology-guide-and-addressable-urls-design.md`](../specs/2026-08-25-methodology-guide-and-addressable-urls-design.md)

## Global Constraints

- **No change to product behaviour outside the frontend.** Nothing under `backend/app/`, `collector/collector/`, the
  database, or the methodology. Two exceptions, both in scope and both named in their tasks: `backend/tests/` gains
  assertions, and `frontend/nginx.conf` changes.
- **The prerender must never perform a network request.** Enforced by a test, not by intention.
- **No live risk value in any generated document.** Follows from the constraint above.
- **All seven locales ship.** `en`, `ru`, `zh`, `de`, `fr`, `es`, `ar`. The six non-English guides carry a visible
  notice that they are translations and that the English text is authoritative.
- **Canonical URLs carry no trailing slash:** `/`, `/ru`, `/methodology`, `/ru/methodology`.
- **The in-product guide publishes only `0.30`, `0.70`, and the methodology version.** Weights, the 1460-day z-score
  window, the 365-day minimum, the clip at 6.0, the 365-day EMA and the 30-day volatility window stay in the
  documentation-site reference and are reached by link.
- **Unknown paths must still return 404.** `backend/tests/test_agent_surface.py::NginxRouteTests` guards this.
- **Never assert 404s or redirects in Playwright.** The smoke suite runs against `vite preview`, which answers HTTP 200
  with the root document for unknown paths and for directory paths without a trailing slash. Measured, not assumed.
  Playwright navigates only to the four canonical shapes.

### Running The Tests

Node must be 22. A stale `nvm` default has silently produced `SyntaxError: Unexpected token .` from optional chaining
in this repository before; that is the interpreter, not the code.

```bash
node -v                                   # must print v22.x
npm test --prefix frontend                # Vitest
npm run build --prefix frontend           # needs VITE_TURNSTILE_SITE_KEY
npm run smoke --prefix frontend           # Playwright, builds and previews first
./scripts/manage.sh test-python           # backend + collector, guards its own interpreter
```

`npm run build` fails by design without a Turnstile site key. Use the documented test key:

```bash
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
```

---

### Task 1: The route matrix

**Files:**
- Create: `frontend/src/routes.ts`, `frontend/src/routes.test.ts`

**Interfaces:**
- Consumes: `Locale` and `supportedLocales` from `frontend/src/locales.ts`.
- Produces:
  - `type RouteName = 'home' | 'methodology'`
  - `interface SiteDocument { route: RouteName; locale: Locale; urlPath: string; filePath: string }`
  - `const siteDocuments: readonly SiteDocument[]` — fourteen entries
  - `function urlPathFor(route: RouteName, locale: Locale): string`
  - `function documentForPath(pathname: string): SiteDocument | undefined`
  - `const SITE_ORIGIN = 'https://bitcoinriskbrief.minihub.app'`

This module is the single source of truth. The app, the prerender, the head builder and the sitemap test all read it,
so a route exists in exactly one place.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/routes.test.ts`:

```typescript
import { describe, expect, it } from 'vitest'
import { supportedLocales } from './locales'
import { documentForPath, siteDocuments, urlPathFor, SITE_ORIGIN } from './routes'

describe('site documents', () => {
  it('covers both routes in every locale and nothing else', () => {
    expect(siteDocuments).toHaveLength(supportedLocales.length * 2)
    for (const locale of supportedLocales) {
      expect(siteDocuments.some((d) => d.locale === locale && d.route === 'home')).toBe(true)
      expect(siteDocuments.some((d) => d.locale === locale && d.route === 'methodology')).toBe(true)
    }
  })

  it('gives English the unprefixed paths and every other locale a prefix', () => {
    expect(urlPathFor('home', 'en')).toBe('/')
    expect(urlPathFor('methodology', 'en')).toBe('/methodology')
    expect(urlPathFor('home', 'ru')).toBe('/ru')
    expect(urlPathFor('methodology', 'ru')).toBe('/ru/methodology')
    expect(urlPathFor('methodology', 'ar')).toBe('/ar/methodology')
  })

  it('never emits a trailing slash except at the root', () => {
    for (const document of siteDocuments) {
      if (document.urlPath === '/') continue
      expect(document.urlPath.endsWith('/')).toBe(false)
    }
  })

  it('maps each url path to a flat file, so nginx resolves it with $uri.html', () => {
    const byPath = Object.fromEntries(siteDocuments.map((d) => [d.urlPath, d.filePath]))
    expect(byPath['/']).toBe('index.html')
    expect(byPath['/ru']).toBe('ru.html')
    expect(byPath['/methodology']).toBe('methodology.html')
    expect(byPath['/ru/methodology']).toBe('ru/methodology.html')
  })

  it('resolves a pathname back to its document, and unknown paths to undefined', () => {
    expect(documentForPath('/ru/methodology')).toMatchObject({ route: 'methodology', locale: 'ru' })
    expect(documentForPath('/')).toMatchObject({ route: 'home', locale: 'en' })
    expect(documentForPath('/nonsense')).toBeUndefined()
    expect(documentForPath('/ru/')).toBeUndefined()
  })

  it('states the production origin without a trailing slash', () => {
    expect(SITE_ORIGIN).toBe('https://bitcoinriskbrief.minihub.app')
  })
})
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `npm test --prefix frontend -- src/routes.test.ts`
Expected: FAIL — `Failed to resolve import "./routes"`.

- [ ] **Step 3: Write the module**

Create `frontend/src/routes.ts`:

```typescript
import { supportedLocales, type Locale } from './locales'

export const SITE_ORIGIN = 'https://bitcoinriskbrief.minihub.app'

export type RouteName = 'home' | 'methodology'

export interface SiteDocument {
  route: RouteName
  locale: Locale
  /** Canonical path, no trailing slash except at the root. */
  urlPath: string
  /** Path inside dist/. Flat, so nginx resolves it with try_files $uri $uri.html. */
  filePath: string
}

export function urlPathFor(route: RouteName, locale: Locale): string {
  const prefix = locale === 'en' ? '' : `/${locale}`
  if (route === 'home') return prefix === '' ? '/' : prefix
  return `${prefix}/methodology`
}

function filePathFor(route: RouteName, locale: Locale): string {
  if (route === 'home') return locale === 'en' ? 'index.html' : `${locale}.html`
  return locale === 'en' ? 'methodology.html' : `${locale}/methodology.html`
}

export const siteDocuments: readonly SiteDocument[] = supportedLocales.flatMap((locale) =>
  (['home', 'methodology'] as const).map((route) => ({
    route,
    locale,
    urlPath: urlPathFor(route, locale),
    filePath: filePathFor(route, locale),
  })),
)

export function documentForPath(pathname: string): SiteDocument | undefined {
  return siteDocuments.find((document) => document.urlPath === pathname)
}
```

- [ ] **Step 4: Run the test and watch it pass**

Run: `npm test --prefix frontend -- src/routes.test.ts`
Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes.ts frontend/src/routes.test.ts
git commit -m "feat: define the route and locale matrix"
```

---

---

### Task 2: The head builder

**Files:**
- Create: `frontend/src/head.ts`, `frontend/src/head.test.ts`

**Interfaces:**
- Consumes: `RouteName`, `SiteDocument`, `siteDocuments`, `urlPathFor`, `SITE_ORIGIN` from Task 1; `localeOptions` and
  `copy` from `frontend/src/locales.ts`.
- Produces:
  - `interface Alternate { hreflang: string; href: string }`
  - `interface HeadFields { title: string; description: string; canonical: string; lang: string; dir: 'ltr' | 'rtl'; alternates: Alternate[]; jsonLd: string }`
  - `function buildHead(route: RouteName, locale: Locale): HeadFields`
  - `function renderHead(fields: HeadFields): string` — the `<head>` fragment the prerender injects

`localeOptions` already carries `lang` (`zh-CN` for Chinese) and `dir` (`rtl` for Arabic). Read them; do not restate
them.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/head.test.ts`:

```typescript
import { describe, expect, it } from 'vitest'
import { supportedLocales } from './locales'
import { buildHead, renderHead } from './head'

describe('buildHead', () => {
  it('points canonical at its own document', () => {
    expect(buildHead('methodology', 'ru').canonical).toBe(
      'https://bitcoinriskbrief.minihub.app/ru/methodology',
    )
    expect(buildHead('home', 'en').canonical).toBe('https://bitcoinriskbrief.minihub.app/')
  })

  it('lists every locale plus x-default, which points at English', () => {
    const { alternates } = buildHead('methodology', 'de')
    expect(alternates).toHaveLength(supportedLocales.length + 1)
    const xDefault = alternates.find((a) => a.hreflang === 'x-default')
    expect(xDefault?.href).toBe('https://bitcoinriskbrief.minihub.app/methodology')
  })

  it('uses the full BCP-47 tag in hreflang, not the path segment', () => {
    const { alternates } = buildHead('home', 'en')
    expect(alternates.map((a) => a.hreflang)).toContain('zh-CN')
    expect(alternates.map((a) => a.hreflang)).not.toContain('zh')
  })

  it('carries the document language and direction', () => {
    expect(buildHead('home', 'ar')).toMatchObject({ lang: 'ar', dir: 'rtl' })
    expect(buildHead('home', 'de')).toMatchObject({ lang: 'de', dir: 'ltr' })
  })

  it('titles the guide differently from the home page in every locale', () => {
    for (const locale of supportedLocales) {
      expect(buildHead('methodology', locale).title).not.toBe(buildHead('home', locale).title)
      expect(buildHead('methodology', locale).title.length).toBeGreaterThan(0)
    }
  })
})

describe('renderHead', () => {
  it('emits every per-document social tag, and no static one', () => {
    const html = renderHead(buildHead('home', 'en'))
    for (const perDocument of ['og:title', 'og:description', 'og:url', 'twitter:title', 'twitter:description']) {
      expect(html).toContain(perDocument)
    }
    // These are identical on all fourteen documents and stay in index.html, outside the marker block.
    for (const static_ of ['og:image', 'og:site_name', 'og:type', 'twitter:card']) {
      expect(html).not.toContain(static_)
    }
  })

  it('emits one canonical link and one alternate per entry', () => {
    const html = renderHead(buildHead('methodology', 'ru'))
    expect(html.match(/rel="canonical"/g)).toHaveLength(1)
    expect(html.match(/rel="alternate"/g)).toHaveLength(supportedLocales.length + 1)
  })

  it('escapes quotes so an apostrophe in copy cannot break an attribute', () => {
    const html = renderHead({
      title: 'a "quoted" title',
      description: 'a "quoted" description',
      canonical: 'https://example.test/',
      lang: 'en',
      dir: 'ltr',
      alternates: [],
      jsonLd: '{}',
    })
    expect(html).not.toContain('content="a "quoted" description"')
    expect(html).toContain('&quot;')
  })
})
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `npm test --prefix frontend -- src/head.test.ts`
Expected: FAIL — `Failed to resolve import "./head"`.

- [ ] **Step 3: Write the module**

Create `frontend/src/head.ts`. As part of this step add exactly four keys to the `Copy` type in
`frontend/src/locales.ts` and to all seven locale entries: `headTitle`, `headDescription`, `headTitleMethodology`,
`headDescriptionMethodology`. All four are plain strings. The test above requires the guide's title to differ from the
home page's in every locale, and `locales.test.ts` requires every locale to carry every key.

```typescript
import { copy, getLocaleOption, supportedLocales, type Locale } from './locales'
import { SITE_ORIGIN, urlPathFor, type RouteName } from './routes'

export interface Alternate {
  hreflang: string
  href: string
}

export interface HeadFields {
  title: string
  description: string
  canonical: string
  lang: string
  dir: 'ltr' | 'rtl'
  alternates: Alternate[]
  jsonLd: string
}

function absolute(route: RouteName, locale: Locale): string {
  const path = urlPathFor(route, locale)
  return path === '/' ? `${SITE_ORIGIN}/` : `${SITE_ORIGIN}${path}`
}

function escapeAttribute(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
}

export function buildHead(route: RouteName, locale: Locale): HeadFields {
  const option = getLocaleOption(locale)
  const t = copy[locale]
  const alternates: Alternate[] = supportedLocales.map((other) => ({
    hreflang: getLocaleOption(other).lang,
    href: absolute(route, other),
  }))
  alternates.push({ hreflang: 'x-default', href: absolute(route, 'en') })

  return {
    title: route === 'home' ? t.headTitle : t.headTitleMethodology,
    description: route === 'home' ? t.headDescription : t.headDescriptionMethodology,
    canonical: absolute(route, locale),
    lang: option.lang,
    dir: option.dir,
    alternates,
    jsonLd: JSON.stringify(
      route === 'home'
        ? {
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            name: 'Bitcoin Risk Brief',
            url: `${SITE_ORIGIN}/`,
            inLanguage: option.lang,
          }
        : {
            '@context': 'https://schema.org',
            '@type': 'TechArticle',
            headline: t.headTitleMethodology,
            url: absolute('methodology', locale),
            inLanguage: option.lang,
            isAccessibleForFree: true,
          },
    ),
  }
}

export function renderHead(fields: HeadFields): string {
  const lines = [
    `<title>${escapeAttribute(fields.title)}</title>`,
    `<meta name="description" content="${escapeAttribute(fields.description)}" />`,
    `<link rel="canonical" href="${escapeAttribute(fields.canonical)}" />`,
    `<meta property="og:title" content="${escapeAttribute(fields.title)}" />`,
    `<meta property="og:description" content="${escapeAttribute(fields.description)}" />`,
    `<meta property="og:url" content="${escapeAttribute(fields.canonical)}" />`,
    `<meta name="twitter:title" content="${escapeAttribute(fields.title)}" />`,
    `<meta name="twitter:description" content="${escapeAttribute(fields.description)}" />`,
  ]
  for (const alternate of fields.alternates) {
    lines.push(
      `<link rel="alternate" hreflang="${escapeAttribute(alternate.hreflang)}" href="${escapeAttribute(alternate.href)}" />`,
    )
  }
  lines.push(`<script type="application/ld+json">${fields.jsonLd}</script>`)
  return lines.join('\n    ')
}
```

- [ ] **Step 4: Run the test and watch it pass**

Run: `npm test --prefix frontend -- src/head.test.ts`
Expected: PASS, 8 tests.

- [ ] **Step 5: Run the whole frontend suite**

Run: `npm test --prefix frontend`
Expected: PASS. The `copy` additions must not break `locales.test.ts`, which checks every locale carries every key.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/head.ts frontend/src/head.test.ts frontend/src/locales.ts
git commit -m "feat: build per-document head metadata"
```

---

---

### Task 3: The locale preference and the language selector

**Files:**
- Create: `frontend/src/localePreference.ts`, `frontend/src/localePreference.test.ts`
- Modify: `frontend/src/LanguageSelect.tsx`

**Interfaces:**
- Consumes: `urlPathFor` and `RouteName` from Task 1, `Locale` from `locales.ts`.
- Produces:
  - `const LOCALE_STORAGE_KEY = 'brb.locale'`
  - `function readStoredLocale(): Locale | null`
  - `function storeLocale(locale: Locale): void`
  - `LanguageSelect` gains a required `route: RouteName` prop and navigates instead of calling a setter.

**Why this is its own task.** The stored preference is read by two unrelated things: the selector writes it, and the
home page's automatic hop reads it. Putting it in either one makes the other depend on it, and an earlier draft of
this plan did exactly that — it declared `LOCALE_STORAGE_KEY` in `Root.tsx` while `LanguageSelect` also needed it,
which made Task 3 and Task 4 depend on each other. A shared leaf module removes the cycle instead of ordering around
it.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/localePreference.test.ts`:

```typescript
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LOCALE_STORAGE_KEY, readStoredLocale, storeLocale } from './localePreference'

beforeEach(() => localStorage.clear())
afterEach(() => vi.unstubAllGlobals())

describe('locale preference', () => {
  it('round-trips a supported locale', () => {
    storeLocale('ru')
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('ru')
    expect(readStoredLocale()).toBe('ru')
  })

  it('reports no preference when nothing was stored', () => {
    expect(readStoredLocale()).toBeNull()
  })

  it('ignores a stored value that is not a supported locale', () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, 'klingon')
    expect(readStoredLocale()).toBeNull()
  })

  it('survives storage that throws, as private modes do', () => {
    vi.stubGlobal('localStorage', {
      getItem() { throw new Error('denied') },
      setItem() { throw new Error('denied') },
    } as unknown as Storage)
    expect(readStoredLocale()).toBeNull()
    expect(() => storeLocale('de')).not.toThrow()
  })
})
```

- [ ] **Step 2: Run it and watch it fail**

Run: `npm test --prefix frontend -- src/localePreference.test.ts`
Expected: FAIL — `Failed to resolve import "./localePreference"`.

- [ ] **Step 3: Write the module**

Create `frontend/src/localePreference.ts`:

```typescript
import { supportedLocales, type Locale } from './locales'

export const LOCALE_STORAGE_KEY = 'brb.locale'

function isLocale(value: string | null): value is Locale {
  return value !== null && (supportedLocales as readonly string[]).includes(value)
}

export function readStoredLocale(): Locale | null {
  try {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
    return isLocale(stored) ? stored : null
  } catch {
    // Private browsing can throw on access. No preference is the safe answer.
    return null
  }
}

export function storeLocale(locale: Locale): void {
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // A failed write only means the automatic hop may run again. Navigation still happens.
  }
}
```

- [ ] **Step 4: Run it and watch it pass**

Run: `npm test --prefix frontend -- src/localePreference.test.ts`
Expected: PASS, 4 tests.

- [ ] **Step 5: Make the selector navigate**

`frontend/src/LanguageSelect.tsx` currently calls a setter passed from `App`. Give it a required `route: RouteName`
prop and replace the setter call with:

```typescript
function chooseLocale(next: Locale) {
  storeLocale(next)
  location.assign(urlPathFor(route, next))
}
```

Keep the existing markup, ARIA attributes and keyboard behaviour exactly as they are; only the effect of choosing
changes. `App` passes `route="home"` for now — Task 5 is where `App` stops owning locale entirely.

- [ ] **Step 6: Run the whole suite**

Run: `npm test --prefix frontend`
Expected: PASS. Any existing test that renders `LanguageSelect` must now pass `route`; TypeScript names each one.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/localePreference.ts frontend/src/localePreference.test.ts \
        frontend/src/LanguageSelect.tsx frontend/src/App.tsx
git commit -m "feat: remember the chosen language and navigate on change"
```

---

### Task 4: The methodology guide

**Files:**
- Create: `frontend/src/methodologyCopy.ts`, `frontend/src/Methodology.tsx`, `frontend/src/Methodology.test.tsx`
- Test: `backend/tests/test_methodology_guide.py`

**Interfaces:**
- Consumes: `Locale` from `locales.ts`, `urlPathFor` from Task 1, and the `route`-aware `LanguageSelect` from
  Task 3. This task must not import `Root`; `Root` imports it.
- Produces:
  - `interface MethodologySection { heading: string; body: string[] }`
  - `interface MethodologyCopy { title: string; intro: string; translationNotice: string | null; sections: MethodologySection[]; referenceLinkLabel: string }`
  - `const methodologyCopy: Record<Locale, MethodologyCopy>`
  - `function Methodology(props: { locale: Locale }): JSX.Element`
  - `export const BAND_LOW = 0.3` and `export const BAND_HIGH = 0.7` and
    `export const METHODOLOGY_VERSION = 'crypto-scout-canonical-v1.1'` from `methodologyCopy.ts`

The prose lives in its own module. `locales.ts` is already 859 lines of interface labels; a thousand words of guide
text in seven languages would bury it.

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/Methodology.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { supportedLocales } from './locales'
import Methodology from './Methodology'
import { methodologyCopy, BAND_LOW, BAND_HIGH, METHODOLOGY_VERSION } from './methodologyCopy'

describe('methodology copy', () => {
  it('exists in every locale with the same section count', () => {
    const expected = methodologyCopy.en.sections.length
    expect(expected).toBeGreaterThanOrEqual(8)
    for (const locale of supportedLocales) {
      expect(methodologyCopy[locale].sections).toHaveLength(expected)
      for (const section of methodologyCopy[locale].sections) {
        expect(section.heading.trim().length).toBeGreaterThan(0)
        expect(section.body.length).toBeGreaterThan(0)
      }
    }
  })

  it('marks the six translations and leaves English unmarked', () => {
    expect(methodologyCopy.en.translationNotice).toBeNull()
    for (const locale of supportedLocales.filter((l) => l !== 'en')) {
      expect(methodologyCopy[locale].translationNotice).toBeTruthy()
    }
  })

  it('states the boundaries and version the backend uses', () => {
    expect(BAND_LOW).toBe(0.3)
    expect(BAND_HIGH).toBe(0.7)
    expect(METHODOLOGY_VERSION).toBe('crypto-scout-canonical-v1.1')
  })
})

describe('Methodology', () => {
  it('renders one h1 and one h2 per section', () => {
    render(<Methodology locale="en" />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(
      methodologyCopy.en.sections.length,
    )
  })

  it('shows the translation notice on a translated locale only', () => {
    const { unmount } = render(<Methodology locale="ru" />)
    expect(screen.getByText(methodologyCopy.ru.translationNotice!)).toBeTruthy()
    unmount()
    render(<Methodology locale="en" />)
    expect(screen.queryByText(/authoritative/i)).toBeNull()
  })

  it('links to the technical reference on the documentation site', () => {
    render(<Methodology locale="en" />)
    const link = screen.getByRole('link', { name: methodologyCopy.en.referenceLinkLabel })
    expect(link.getAttribute('href')).toBe(
      'https://docs.bitcoinriskbrief.minihub.app/product/risk-methodology/',
    )
  })

  it('renders no live risk value, because the guide explains rather than reports', () => {
    const { container } = render(<Methodology locale="en" />)
    expect(container.textContent).not.toMatch(/\brisk 0\.\d\d\b/i)
  })
})
```

Create `backend/tests/test_methodology_guide.py`:

```python
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COPY = ROOT / "frontend" / "src" / "methodologyCopy.ts"


def _constant(name: str) -> str:
    match = re.search(rf"export const {name} = ([^\n]+)", COPY.read_text(encoding="utf-8"))
    assert match is not None, f"{name} must be exported from methodologyCopy.ts"
    return match.group(1).strip().rstrip(";").strip("'\"")


class MethodologyGuideTests(unittest.TestCase):
    def test_the_guide_states_the_boundaries_the_backend_uses(self) -> None:
        from app.risk import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD, METHODOLOGY_VERSION

        self.assertEqual(float(_constant("BAND_LOW")), LOW_RISK_THRESHOLD)
        self.assertEqual(float(_constant("BAND_HIGH")), HIGH_RISK_THRESHOLD)
        self.assertEqual(_constant("METHODOLOGY_VERSION"), METHODOLOGY_VERSION)

    def test_the_english_guide_shows_the_boundaries_it_declares(self) -> None:
        # The constants can be right while the prose says something else. Assert the reader sees them.
        text = COPY.read_text(encoding="utf-8")
        self.assertIn("0.30", text)
        self.assertIn("0.70", text)
        self.assertIn("crypto-scout-canonical-v1.1", text)

    def test_the_guide_does_not_overstate_the_freshness_contract(self) -> None:
        # frontend/public/llms.txt was corrected for this exact misconception and is guarded by
        # test_agent_surface.py. The guide must not reintroduce it. These phrases are English, so
        # scanning the whole file is both sufficient and safe: a translation cannot contain them.
        english = " ".join(COPY.read_text(encoding="utf-8").split()).lower()
        for overstatement in (
            "503 rather than a stale figure",
            "stamped on every response",
            "travels with every response",
            "version on every response",
        ):
            self.assertNotIn(
                overstatement,
                english,
                "only /api/readiness answers 503 for stale data; the data endpoints keep serving "
                "stored rows, and the methodology version is not on every response",
            )
        self.assertIn("readiness", english)

    def test_the_guide_does_not_republish_the_model_weights(self) -> None:
        text = COPY.read_text(encoding="utf-8")
        # Only the three weights are safe to forbid as substrings. 0.30 and 0.70 are also the band
        # boundaries the guide must state, and 0.25 appears in the worked example, so a broader
        # substring ban would fail against correct copy.
        for weight in ("0.60", "0.15"):
            self.assertNotIn(
                weight,
                text,
                "model weights belong to the documentation-site reference, not the guide",
            )
```

- [ ] **Step 2: Run both and watch them fail**

Run: `npm test --prefix frontend -- src/Methodology.test.tsx`
Expected: FAIL — `Failed to resolve import "./methodologyCopy"`.

Run: `PYTHONPATH=backend:collector .venv/bin/python -m unittest discover -s backend/tests -k methodology_guide -v`
Expected: FAIL — the file does not exist.

- [ ] **Step 3: Write the English copy**

Create `frontend/src/methodologyCopy.ts` with the types, the three constants, and the English entry below. The
English text is authoritative and is transcribed as written.

```typescript
export const BAND_LOW = 0.3
export const BAND_HIGH = 0.7
export const METHODOLOGY_VERSION = 'crypto-scout-canonical-v1.1'
```

English sections, in order:

1. **What this number is.** A single value from 0.0 to 1.0 describing how stretched the Bitcoin market looks against
   its own history, recomputed once a day from completed daily data. It is not a probability that the price will fall,
   not a target, and not an instruction to buy or sell anything. It compresses three observations into one number, and
   like every compression it discards more than it keeps.
2. **Why today reads low, neutral, or high.** Below 0.30 is low. From 0.30 up to but not including 0.70 is neutral.
   0.70 and above is high. The boundaries are fixed, so the state changes only when the value crosses one. A reading of
   0.25 is low because it sits below 0.30, and it becomes neutral at 0.30 — not at the moment the market feels
   different.
3. **What goes into it.** Three inputs: how far the price sits from its long-run trend, how violently it has moved
   recently, and how much trading activity there is relative to the size of the market. Each is compared against its
   own history rather than an absolute level, which is why a price that would have been extreme in 2015 need not be
   extreme now. The exact formulas, weights and windows are published in the technical reference.
4. **The price shown here is not a quote.** It is the HLC3 average of the last completed daily candle — high, low and
   close divided by three. It is a model input, not the current market price, and it will differ from what an exchange
   shows right now. Nothing on this page updates intraday.
5. **The level ladder is not a forecast.** It answers a backwards question: holding everything except price fixed, at
   what price would the model report each risk level? That is a description of the model's shape, not a prediction, a
   target, a support line, or a trade. If the other inputs move, the ladder moves with them.
6. **When not to trust today's number.** The data has to be current and it has to have passed validation. A separate
   readiness check reports both, and it answers with HTTP 503 instead of a green light when either fails. The data
   endpoints behave differently on purpose: they keep returning the last rows they hold, so a value means nothing
   without the covered date beside it and a readiness state that agrees. This page shows both, and says plainly when
   the data has fallen behind.
7. **What the model cannot see.** It has no on-chain data, no news, no order-book depth, and no knowledge of anything
   that happened after the last completed day. It works on daily bars, so a fall and recovery inside one day is
   invisible to it. It assumes the future resembles the past well enough for a historical comparison to mean something,
   and that assumption fails exactly when it would be most useful.
8. **What happens when the methodology changes.** The methodology carries a version, currently
   `crypto-scout-canonical-v1.1`, reported by the readiness check and alongside the level ladder. A change that alters
   the numbers gets a new version string, so a value recorded earlier can always be traced back to the rules that
   produced it.

Close with a link labelled by `referenceLinkLabel` pointing at
`https://docs.bitcoinriskbrief.minihub.app/product/risk-methodology/`.

- [ ] **Step 4: Translate into the other six locales**

Same structure, same eight sections, same order. Each non-English entry sets `translationNotice` to a sentence in that
language meaning: *this page is a translation; the English version is authoritative.* The English entry sets it to
`null`.

Do not localise `crypto-scout-canonical-v1.1`, and do not restate weights or windows in any language — the Python test
in Step 1 fails if those numbers appear.

- [ ] **Step 5: Write the component**

Create `frontend/src/Methodology.tsx`, exporting the component as the **default** export so `Root.tsx` and
`Methodology.test.tsx` can `import Methodology from './Methodology'`.

It renders the title as the single `<h1>`, the intro, the translation notice when present, each section as an `<h2>`
with its paragraphs, the language selector with `route="methodology"`, a link home, and the reference link. It takes
only `locale` and performs no data fetching — the guide explains, it does not report.

- [ ] **Step 6: Run both suites**

Run: `npm test --prefix frontend`
Run: `./scripts/manage.sh test-python`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/methodologyCopy.ts frontend/src/Methodology.tsx \
        frontend/src/Methodology.test.tsx backend/tests/test_methodology_guide.py
git commit -m "feat: publish the interpretation guide in seven locales"
```

---

---

### Task 5: Locale becomes an input, not a guess

**Files:**
- Create: `frontend/src/Root.tsx`, `frontend/src/Root.test.tsx`
- Modify: `frontend/src/App.tsx:273-276`, `frontend/src/main.tsx`

**Interfaces:**
- Consumes: `documentForPath`, `urlPathFor`, `RouteName` from Task 1; `LOCALE_STORAGE_KEY` and `readStoredLocale`
  from Task 3; `Methodology` from Task 4.
- Produces:
  - `function Root(props: { route: RouteName; locale: Locale }): JSX.Element`
  - `App` changes from `App()` to `App({ locale }: { locale: Locale })`
  - `Root` is exported both by name and as the default

**Locale stops being state.** Each document is one language, so the language cannot change without navigating. This
deletes a `useState` rather than adding one, and it is what makes a link carry its language.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/Root.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LOCALE_STORAGE_KEY } from './localePreference'
import { Root } from './Root'

const replace = vi.fn()

beforeEach(() => {
  localStorage.clear()
  replace.mockClear()
  vi.stubGlobal('location', { pathname: '/', replace } as unknown as Location)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Root', () => {
  it('renders the guide when the route says so', () => {
    render(<Root route="methodology" locale="en" />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('sends a first-time visitor from the English root to their own language', () => {
    vi.stubGlobal('navigator', { languages: ['ru-RU', 'ru'] } as unknown as Navigator)
    render(<Root route="home" locale="en" />)
    expect(replace).toHaveBeenCalledWith('/ru')
  })

  it('never redirects away from a locale that is already in the URL', () => {
    vi.stubGlobal('navigator', { languages: ['ru-RU'] } as unknown as Navigator)
    render(<Root route="home" locale="de" />)
    expect(replace).not.toHaveBeenCalled()
  })

  it('never redirects once a language was chosen by hand', () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, 'en')
    vi.stubGlobal('navigator', { languages: ['ru-RU'] } as unknown as Navigator)
    render(<Root route="home" locale="en" />)
    expect(replace).not.toHaveBeenCalled()
  })

  it('does not redirect a visitor whose language is already English', () => {
    vi.stubGlobal('navigator', { languages: ['en-GB'] } as unknown as Navigator)
    render(<Root route="home" locale="en" />)
    expect(replace).not.toHaveBeenCalled()
  })

  it('never redirects away from the guide, only from the home page', () => {
    vi.stubGlobal('navigator', { languages: ['ru-RU'] } as unknown as Navigator)
    render(<Root route="methodology" locale="en" />)
    expect(replace).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run the test and watch it fail**

Run: `npm test --prefix frontend -- src/Root.test.tsx`
Expected: FAIL — `Failed to resolve import "./Root"`.

- [ ] **Step 3: Write `Root.tsx`**

```typescript
import { useEffect } from 'react'
import App from './App'
import Methodology from './Methodology'
import { readStoredLocale } from './localePreference'
import { resolveInitialLocale, type Locale } from './locales'
import { urlPathFor, type RouteName } from './routes'

export function Root({ route, locale }: { route: RouteName; locale: Locale }) {
  useEffect(() => {
    // Only the unprefixed English home guesses. Every other document states its language in the URL,
    // and a visitor who chose by hand is never moved again.
    if (route !== 'home' || locale !== 'en') return
    if (readStoredLocale() !== null) return
    const detected = resolveInitialLocale(navigator?.languages)
    if (detected === 'en') return
    location.replace(urlPathFor('home', detected))
  }, [route, locale])

  return route === 'methodology' ? <Methodology locale={locale} /> : <App locale={locale} />
}

export default Root
```

Both a named and a default export: `Root.test.tsx` imports `{ Root }` by name, while `main.tsx` and
`entry-server.tsx` import the default. `LOCALE_STORAGE_KEY` comes from `./localePreference`, not from here — that
separation is what keeps this task and Task 4 from depending on each other.

- [ ] **Step 4: Make `App` take its locale**

In `frontend/src/App.tsx`, replace the locale state at line 273-276:

```typescript
export default function App() {
  const [locale, setLocale] = useState<Locale>(() =>
    resolveInitialLocale(typeof navigator === 'undefined' ? undefined : navigator.languages),
  )
```

with:

```typescript
export default function App({ locale }: { locale: Locale }) {
```

Then remove the now-unused `setLocale` from wherever `LanguageSelect` receives it, and drop the
`resolveInitialLocale` import if nothing else in the file uses it. TypeScript will name every site.

- [ ] **Step 5: Hydrate instead of mounting**

Replace `frontend/src/main.tsx` entirely:

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import Root from './Root'
import { documentForPath } from './routes'
import './App.css'

const current = documentForPath(location.pathname)
const route = current?.route ?? 'home'
const locale = current?.locale ?? 'en'

const container = document.getElementById('root')!
const tree = (
  <React.StrictMode>
    <Root route={route} locale={locale} />
  </React.StrictMode>
)

// Production always serves a prerendered document, so the container has children and we hydrate.
// vite dev serves index.html with an empty #root for any path; hydrating that logs a misleading
// mismatch before React recovers, so mount there instead.
if (container.firstChild) {
  ReactDOM.hydrateRoot(container, tree)
} else {
  ReactDOM.createRoot(container).render(tree)
}
```

The `documentForPath` fallbacks exist for the same dev-only reason: in production the pathname always resolves to one
of the fourteen documents.

- [ ] **Step 6: Run the tests**

Run: `npm test --prefix frontend`
Expected: PASS. `App.test.tsx` renders `<App />` and now needs `<App locale="en" />`; update every call site it names.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/Root.tsx frontend/src/Root.test.tsx frontend/src/App.tsx \
        frontend/src/App.test.tsx frontend/src/main.tsx
git commit -m "feat: take locale from the URL instead of the browser"
```

---

---

### Task 6: The prerender

**Files:**
- Create: `frontend/src/entry-server.tsx`, `frontend/scripts/prerender.mjs`, `frontend/src/entry-server.test.tsx`
- Modify: `frontend/index.html`, `frontend/package.json`, `frontend/.gitignore` (create if absent)
- Modify: `frontend/src/documentHead.test.ts`, `frontend/src/structuredData.test.ts`

**Interfaces:**
- Consumes: `Root` from Task 5, `buildHead`/`renderHead` from Task 2, `siteDocuments` from Task 1.
- Produces: `function renderDocument(route: RouteName, locale: Locale): { html: string; head: string; lang: string; dir: string }`
  exported from `entry-server.tsx`.

**A plain `.mjs` script cannot import `.tsx`.** The prerender therefore consumes a server bundle that Vite builds
first — `vite build --ssr` — which needs no new dependency. Attempting to import the TypeScript sources directly from
Node is the obvious wrong turn here.

- [ ] **Step 1: Add explicit head markers to the template**

**The criterion, which decides every case: the marker block holds what differs between the fourteen documents.
Anything identical on all of them stays outside, in a single copy.** Do not sort the tags by prefix — `og:title`
varies and `og:image` does not, and they sit next to each other.

Move exactly these eight inside `<!--per-document-head-->` … `<!--/per-document-head-->`:

| Tag | Why it varies |
| --- | --- |
| `<title>` | localised, and different for the guide |
| `<meta name="description">` | same |
| `<link rel="canonical">` | one per document |
| `<meta property="og:title">` | localised |
| `<meta property="og:description">` | localised |
| `<meta property="og:url">` | one per document |
| `<meta name="twitter:title">` | localised |
| `<meta name="twitter:description">` | localised |
| the `WebSite` JSON-LD block | carries `inLanguage` and `url` |

Leave everything else where it is: charset, viewport, the icon links, `og:type`, `og:site_name`, `og:image`,
`og:image:width`, `og:image:height`, `og:image:alt`, `twitter:card`, and **the `Dataset` JSON-LD block**. The
`Dataset` describes the data rather than the page, so it is the same on all fourteen; `structuredData.test.ts`
requires both a `Dataset` and a `WebSite` type to be present, and it is satisfied by the static block plus the one
`renderHead` emits.

The template holds two `<script type="application/ld+json">` blocks. The first is the `Dataset` and stays put; the
second is the `WebSite` and moves inside the markers.

Replacing a marked block is deterministic; regex-matching a `<head>` is not.

- [ ] **Step 2: Write the failing test**

Create `frontend/src/entry-server.test.tsx`:

```typescript
import net from 'node:net'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { renderDocument } from './entry-server'
import { siteDocuments } from './routes'

const originalConnect = net.Socket.prototype.connect
const originalFetch = globalThis.fetch

beforeEach(() => {
  net.Socket.prototype.connect = function () {
    throw new Error('OUTBOUND NETWORK ATTEMPTED')
  } as never
  globalThis.fetch = (() => {
    throw new Error('OUTBOUND NETWORK ATTEMPTED')
  }) as unknown as typeof fetch
})

afterEach(() => {
  net.Socket.prototype.connect = originalConnect
  globalThis.fetch = originalFetch
})

describe('renderDocument', () => {
  it('renders every document without touching the network', () => {
    for (const document of siteDocuments) {
      const rendered = renderDocument(document.route, document.locale)
      expect(rendered.html.length).toBeGreaterThan(0)
      expect(rendered.head).toContain('rel="canonical"')
    }
  })

  it('carries the document language and direction', () => {
    expect(renderDocument('home', 'ar')).toMatchObject({ lang: 'ar', dir: 'rtl' })
    expect(renderDocument('methodology', 'de')).toMatchObject({ lang: 'de', dir: 'ltr' })
  })

  it('renders the guide text into the markup rather than leaving it to the client', () => {
    const { html } = renderDocument('methodology', 'ru')
    expect(html).toContain('<h1')
    expect(html.length).toBeGreaterThan(2000)
  })
})
```

- [ ] **Step 3: Run it and watch it fail**

Run: `npm test --prefix frontend -- src/entry-server.test.tsx`
Expected: FAIL — `Failed to resolve import "./entry-server"`.

- [ ] **Step 4: Write the server entry**

Create `frontend/src/entry-server.tsx`:

```typescript
import { renderToString } from 'react-dom/server'
import Root from './Root'
import { buildHead, renderHead } from './head'
import type { Locale } from './locales'
import type { RouteName } from './routes'

export function renderDocument(route: RouteName, locale: Locale) {
  const fields = buildHead(route, locale)
  return {
    html: renderToString(<Root route={route} locale={locale} />),
    head: renderHead(fields),
    lang: fields.lang,
    dir: fields.dir,
  }
}
```

`renderToString` does not run effects, so the automatic language hop in `Root` cannot fire during the build. Data
fetching lives in effects too, which is why the rendered markup carries the waiting state and no live value.

**The seven home documents will have almost no body, and that is correct.** Measured on the current code,
`renderToString(<App />)` produces exactly 79 bytes:

```html
<main class="shell centered"><p class="loading">Loading risk data...</p></main>
```

`App.tsx:512` returns early when `latest`, `brief` or `readiness` is missing, and the prerender has none of them. Do
not try to fix this, and do not treat a small `dist/ru.html` as a broken build. The home documents exist for their
localised head — title, description, `hreflang`, `lang`, `dir` — which is what distinguishes seven language versions
to a search engine. Opening up the home body is follow-up work, deliberately out of scope.

The guide documents are the opposite: their content is prose, so they render in full. That is why Step 2's length
assertion applies to `methodology` and not to `home`.

- [ ] **Step 5: Run it and watch it pass**

Run: `npm test --prefix frontend -- src/entry-server.test.tsx`
Expected: PASS, 3 tests.

- [ ] **Step 6: Write the prerender script**

Create `frontend/scripts/prerender.mjs`:

```javascript
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const dist = resolve(root, 'dist')

const serverBundle = resolve(root, 'dist-ssr/entry-server.js')
const { renderDocument, siteDocuments } = await import(pathToFileURL(serverBundle).href).catch(() => {
  throw new Error(`missing ${serverBundle}; run the --ssr build before this script`)
})

const template = readFileSync(resolve(dist, 'index.html'), 'utf-8')
const HEAD_START = '<!--per-document-head-->'
const HEAD_END = '<!--/per-document-head-->'

const headStart = template.indexOf(HEAD_START)
const headEnd = template.indexOf(HEAD_END)
if (headStart === -1 || headEnd === -1) {
  throw new Error('index.html lost its per-document-head markers')
}

for (const document of siteDocuments) {
  const rendered = renderDocument(document.route, document.locale)
  let html = template.slice(0, headStart) + rendered.head + template.slice(headEnd + HEAD_END.length)
  html = html.replace('<html lang="en">', `<html lang="${rendered.lang}" dir="${rendered.dir}">`)
  html = html.replace('<div id="root"></div>', `<div id="root">${rendered.html}</div>`)
  if (html.includes('<div id="root"></div>')) {
    throw new Error(`root placeholder not replaced for ${document.urlPath}`)
  }
  const target = resolve(dist, document.filePath)
  mkdirSync(dirname(target), { recursive: true })
  writeFileSync(target, html, 'utf-8')
  console.log(`prerendered ${document.urlPath} -> dist/${document.filePath}`)
}
```

`siteDocuments` must therefore be re-exported from `entry-server.tsx`: add
`export { siteDocuments } from './routes'`.

- [ ] **Step 7: Wire the build**

In `frontend/package.json`, change `build` and add the SSR step:

```json
"build": "tsc -b && vite build && vite build --ssr src/entry-server.tsx --outDir dist-ssr && node scripts/prerender.mjs",
```

Add `dist-ssr` to `frontend/.gitignore`.

- [ ] **Step 8: Build and inspect the output**

Run: `VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend`

Expected: fourteen `prerendered …` lines. Then confirm the content is really in the file:

```bash
grep -c '<h1' frontend/dist/ru/methodology.html      # at least 1
grep -o 'lang="ar" dir="rtl"' frontend/dist/ar/methodology.html
grep -o 'hreflang="zh-CN"' frontend/dist/methodology.html
ls frontend/dist/*.html frontend/dist/*/methodology.html | wc -l   # 14
```

- [ ] **Step 9: Move the head tests onto the generated documents**

`frontend/src/documentHead.test.ts` and `frontend/src/structuredData.test.ts` currently read the source
`frontend/index.html`, which is now only a template and no longer carries the real title or canonical. Point both at
`dist/index.html` and `dist/methodology.html`, and skip with a clear message when `dist` is absent:

```typescript
const distIndex = resolve(__dirname, '../dist/index.html')
const built = existsSync(distIndex)
describe.skipIf(!built)('document head', () => {
  // ...assert against readFileSync(distIndex, 'utf-8')
})
```

The assertion gets stronger: it now checks what is served rather than what is authored.

One detail `structuredData.test.ts` must respect: `dist/index.html` carries `Dataset` and `WebSite`, while
`dist/methodology.html` carries `Dataset` and `TechArticle`, because `buildHead` emits `TechArticle` for the guide.
Assert `WebSite` against the home document only, and add a matching `TechArticle` assertion for the guide.

- [ ] **Step 10: Make CI run the tests that need a build**

`frontend-tests` runs the suite without building and `frontend-build` builds without testing, so the two tests moved
in Step 9 would skip on every CI run and assert nothing. Add a step to the `frontend-build` job in
`.github/workflows/ci.yml`, after `Build frontend`:

```yaml
      - name: Verify the generated documents
        run: npm test --prefix frontend -- src/documentHead.test.ts src/structuredData.test.ts
```

That job already exports `VITE_TURNSTILE_SITE_KEY`, so the build it runs produces the `dist` these tests read.

- [ ] **Step 11: Run everything**

Run: `npm test --prefix frontend`
Expected: PASS.

- [ ] **Step 12: Commit**

```bash
git add frontend/src/entry-server.tsx frontend/src/entry-server.test.tsx \
        frontend/scripts/prerender.mjs frontend/index.html frontend/package.json \
        frontend/.gitignore frontend/src/documentHead.test.ts frontend/src/structuredData.test.ts \
        .github/workflows/ci.yml
git commit -m "feat: prerender every document at build time"
```

---

---

### Task 7: Serving

**Files:**
- Modify: `frontend/nginx.conf`, `frontend/public/sitemap.xml`, `frontend/public/llms.txt`, `frontend/src/App.tsx`,
  `frontend/src/App.test.tsx`
- Modify: `backend/tests/test_agent_surface.py`
- Create: `frontend/src/sitemap.test.ts`
- Modify: `frontend/e2e/frontend-quality.spec.ts`

**Interfaces:**
- Consumes: `siteDocuments`, `SITE_ORIGIN` from Task 1.

- [ ] **Step 1: Write the failing sitemap test**

Create `frontend/src/sitemap.test.ts`:

```typescript
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { SITE_ORIGIN, siteDocuments } from './routes'

const xml = readFileSync(resolve(__dirname, '../public/sitemap.xml'), 'utf-8')
const listed = new Set([...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]))
const DOCS_URL = 'https://docs.bitcoinriskbrief.minihub.app/'

describe('sitemap', () => {
  it('lists every document', () => {
    for (const document of siteDocuments) {
      const expected = document.urlPath === '/' ? `${SITE_ORIGIN}/` : `${SITE_ORIGIN}${document.urlPath}`
      expect(listed).toContain(expected)
    }
  })

  it('lists nothing that is not a document, apart from the documentation site', () => {
    const allowed = new Set(
      siteDocuments.map((d) => (d.urlPath === '/' ? `${SITE_ORIGIN}/` : `${SITE_ORIGIN}${d.urlPath}`)),
    )
    allowed.add(DOCS_URL)
    for (const location of listed) {
      expect(allowed).toContain(location)
    }
  })
})
```

- [ ] **Step 2: Run it and watch it fail**

Run: `npm test --prefix frontend -- src/sitemap.test.ts`
Expected: FAIL — the sitemap lists two URLs and thirteen documents are missing.

- [ ] **Step 3: Write the sitemap**

Rewrite `frontend/public/sitemap.xml` with fifteen `<url>` entries: fourteen documents plus
`https://docs.bitcoinriskbrief.minihub.app/`. Keep the existing comment line
`<!-- Analytics and research context only; not financial advice. -->`, which
`backend/tests/test_agent_surface.py::test_sitemap_is_valid_xml_listing_both_hosts` asserts, and add no doctype or
entity declaration — the same test rejects both.

Give the home documents `<changefreq>daily</changefreq>` and the guides `<changefreq>monthly</changefreq>`.

- [ ] **Step 4: Update nginx**

In `frontend/nginx.conf`, change the fallthrough location's directive from `try_files $uri =404;` to:

```nginx
    try_files $uri $uri.html =404;
```

Leave `location = /` and `location /assets/` untouched. Then add the two redirects **above** the fallthrough
`location /` block, so the exact matches win:

```nginx
  location = /en {
    return 301 /;
  }

  location = /en/methodology {
    return 301 /methodology;
  }
```

Do not add `$uri/`. Measured against nginx, `try_files $uri $uri.html $uri/ =404` answers **403** for `/ru/` because
the directory has no index and autoindex is off; without it the same path is a clean 404.

- [ ] **Step 5: Update the nginx route tests**

In `backend/tests/test_agent_surface.py`, `test_fallthrough_location_returns_404` asserts the literal string
`try_files $uri =404;`, which Step 4 removes. Replace it with an assertion of the property rather than the spelling,
and add coverage for the new rules:

```python
    def test_fallthrough_location_returns_404(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("try_files $uri $uri.html =404;", text)
        self.assertNotIn("/index.html;", text.split("location /assets/")[0])

    def test_locale_and_guide_paths_resolve_to_flat_files(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        # $uri.html is what turns /ru into ru.html and /ru/methodology into ru/methodology.html.
        self.assertIn("$uri.html", text)
        # $uri/ would answer 403 for /ru/, because the directory carries no index.
        self.assertNotIn("$uri/", text)

    def test_english_prefixed_paths_redirect_to_the_canonical_ones(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("location = /en {", text)
        self.assertIn("return 301 /;", text)
        self.assertIn("location = /en/methodology {", text)
        self.assertIn("return 301 /methodology;", text)
```

`test_unknown_paths_are_not_rewritten_to_the_app_shell` needs no change: the new directive still contains no
`/index.html` fallback.

- [ ] **Step 6: Add the guide to the agent surface**

In `frontend/public/llms.txt`, add one line to the links section:

```
- Methodology and interpretation guide: https://bitcoinriskbrief.minihub.app/methodology
```

`docs/llms.txt` is not touched; it belongs to the documentation site.

- [ ] **Step 7: Point the home page at the guide**

Issue #42 requires the guide to be "reachable from the existing public page" and linked "prominently from the current
methodology entry point". Without this the guide lives at a URL no visitor to the site can reach, and the sub-project
is visible only to crawlers.

`frontend/src/App.tsx:544` currently links the in-page summary:

```tsx
<a className="methodology-link" href="#methodology">
```

Point it at the guide, in the reader's own language:

```tsx
<a className="methodology-link" href={urlPathFor('methodology', locale)}>
```

The compact `#methodology` section stays as a summary; its link now leads to the full explanation. Add a test to
`frontend/src/App.test.tsx`:

```typescript
it('links the methodology guide in the reader\'s own language', () => {
  render(<App locale="ru" />)
  const link = screen.getByRole('link', { name: new RegExp(copy.ru.methodologyLink, 'i') })
  expect(link.getAttribute('href')).toBe('/ru/methodology')
})
```

- [ ] **Step 8: Make a duplicated sitemap entry fail**

`sitemap.test.ts` collects locations into a `Set`, so a URL listed twice satisfies both directions. Count before
deduplicating:

```typescript
const rawLocations = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])

it('lists each location exactly once', () => {
  expect(rawLocations).toHaveLength(new Set(rawLocations).size)
})
```

- [ ] **Step 9: Add a localised route to the smoke run**

In `frontend/e2e/frontend-quality.spec.ts`, add a test that navigates to `/ru/methodology`, asserts the `<h1>` is
present and `document.documentElement.lang` is `ru`, and runs the same axe check the existing tests use.

**Navigate only to `/`, `/ru`, `/methodology` and `/ru/methodology`.** Do not assert a 404 and do not assert a
redirect: the smoke suite runs against `vite preview`, which was measured answering HTTP 200 with the root document
for unknown paths and for directory paths without a trailing slash. Those contracts belong to Step 5.

- [ ] **Step 10: Run everything**

```bash
npm test --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
npm run smoke --prefix frontend
./scripts/manage.sh test-python
./scripts/manage.sh validate
```

Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add frontend/nginx.conf frontend/public/sitemap.xml frontend/public/llms.txt \
        frontend/src/sitemap.test.ts backend/tests/test_agent_surface.py \
        frontend/e2e/frontend-quality.spec.ts frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "feat: serve the addressable routes and list them for agents"
```

---

---


## Verification Summary

```bash
node -v                                                     # v22.x
npm test --prefix frontend
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run build --prefix frontend
npm run smoke --prefix frontend
./scripts/manage.sh test-python
./scripts/manage.sh validate
mkdocs build --strict
```

The `image-build` CI job runs `nginx -t` inside the built image, so the configuration is validated on every pull
request without a local nginx.

## Out Of Scope

- Per-date snapshot URLs at `/risk/YYYY-MM-DD`. That is S4b, and it reuses everything built here.
- Server-side language redirection.
- Publishing weights, z-score windows or clipping values in the product.
- Any change to `backend/app/`, `collector/collector/`, the database, or the methodology.
- Restructuring `App.tsx` beyond taking `locale` as a prop. In particular, the early return at `App.tsx:512` stays:
  server-rendering the home page's static copy is worthwhile but is a separate change to the highest-traffic
  component.
