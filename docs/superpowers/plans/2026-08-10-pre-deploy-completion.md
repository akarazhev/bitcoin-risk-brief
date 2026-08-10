# Pre-Deploy Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the four gaps found before the production deploy — no tab icon, no link-preview image, no path from the product to the documentation site, and a documentation `llms.txt` that the S2 design promised but never shipped.

**Architecture:** Frontend and documentation only. No backend, collector, database, nginx, or methodology change. The brand assets already exist in `frontend/public/`; this plan wires them up and adds the missing links.

**Tech Stack:** Vite/React, MkDocs Material, Vitest, Python `unittest`.

## Global Constraints

- Brand assets are already committed by PR #57 and must not be regenerated: `frontend/public/favicon.svg`, `favicon-96x96.png`, `apple-touch-icon.png`, `og-image.png`.
- **Never weaken the Content-Security-Policy.** `backend/tests/test_frontend_security_headers.py` pins it verbatim. Nothing in this plan needs a CSP change: every asset is same-origin and the new footer entries are ordinary navigation links.
- No new dependency in `backend/requirements.txt`, `collector/requirements.txt`, `frontend/package.json`, or `docs/requirements.txt`.
- No change to risk methodology, database schema, collector behaviour, or nginx.
- All seven locales stay complete and consistent: `en`, `ru`, `zh`, `de`, `fr`, `es`, `ar`. Arabic is RTL.
- Public artifacts never embed a concrete risk reading — there is no server-side rendering, so any inlined number would go stale.
- Canonical URLs: product `https://bitcoinriskbrief.minihub.app/`, documentation `https://docs.bitcoinriskbrief.minihub.app/`.

---

### Task 1: Wire the tab icon and link-preview image

**Files:**
- Modify: `frontend/index.html`
- Test: `frontend/src/documentHead.test.ts`

**Interfaces:**
- Consumes: the four asset files in `frontend/public/`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/documentHead.test.ts`:

```typescript
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const root = resolve(__dirname, '..')
const html = readFileSync(resolve(root, 'index.html'), 'utf-8')

describe('document head', () => {
  it('declares the svg icon, the png fallback and the apple touch icon', () => {
    expect(html).toContain('<link rel="icon" type="image/svg+xml" href="/favicon.svg"')
    expect(html).toContain('<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png"')
    expect(html).toContain('<link rel="apple-touch-icon" href="/apple-touch-icon.png"')
  })

  it('every declared icon file exists in public/', () => {
    for (const name of ['favicon.svg', 'favicon-96x96.png', 'apple-touch-icon.png', 'og-image.png']) {
      expect(existsSync(resolve(root, 'public', name)), `public/${name} is missing`).toBe(true)
    }
  })

  it('declares an absolute og:image on the product host', () => {
    expect(html).toContain(
      '<meta property="og:image" content="https://bitcoinriskbrief.minihub.app/og-image.png"',
    )
    expect(html).toContain('<meta property="og:image:width" content="2560"')
    expect(html).toContain('<meta property="og:image:height" content="1280"')
    expect(html).toMatch(/<meta property="og:image:alt" content="[^"]{20,}"/)
  })

  it('upgrades the twitter card now that an image exists', () => {
    expect(html).toContain('<meta name="twitter:card" content="summary_large_image"')
    expect(html).not.toContain('content="summary"')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test --prefix frontend -- documentHead`
Expected: FAIL — no `rel="icon"` declaration in `index.html`.

- [ ] **Step 3: Add the declarations**

In `frontend/index.html`, add the icon links immediately after the `viewport` meta:

```html
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png" />
    <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
```

Add the image metadata next to the existing `og:` tags:

```html
    <meta property="og:image" content="https://bitcoinriskbrief.minihub.app/og-image.png" />
    <meta property="og:image:width" content="2560" />
    <meta property="og:image:height" content="1280" />
    <meta
      property="og:image:alt"
      content="Bitcoin Risk Brief — the risk scale from 0.00 to 1.00 with its low, neutral and high bands"
    />
```

Change the existing twitter card line from `content="summary"` to:

```html
    <meta name="twitter:card" content="summary_large_image" />
```

The `og:image` URL is absolute because link-preview crawlers do not resolve relative paths. The file is served from the product host rather than hot-linked, so it stays inside `img-src 'self'`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test --prefix frontend`
Expected: PASS, including the existing `structuredData` suite.

Run: `npm run build --prefix frontend`
Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/documentHead.test.ts
git commit -m "feat: declare the tab icon and link-preview image"
```

---

### Task 2: Link the documentation and agent surface from the footer

**Files:**
- Modify: `frontend/src/App.tsx:829-840`
- Modify: `frontend/src/locales.ts`
- Test: `frontend/src/App.test.tsx`, `frontend/src/locales.test.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: a `developerLinksAriaLabel` key on the locale type, present in all seven locales.

**Why the labels are not translated.** The three entries are `Docs`, `API` and `llms.txt` — technical tokens that stay identical in every locale, exactly like the existing `minihub.app` footer token. Only the group's accessible name is localised. This deliberately avoids writing a prose block that S5a is about to rewrite; a full "for developers and agents" section belongs to S4.

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/App.test.tsx`:

The suite uses flat `test(...)` calls with `render(<App />)`, and imports `render`, `screen` and `within` from `@testing-library/react` at the top of the file. It already asserts CSS by reading `src/App.css`. Follow both patterns:

```tsx
test('links the documentation site, the API reference and llms.txt from the footer', async () => {
  render(<App />)

  const group = await screen.findByRole('navigation', { name: 'Developer and agent resources' })
  const links = within(group).getAllByRole('link')

  expect(links.map((a) => a.getAttribute('href'))).toEqual([
    'https://docs.bitcoinriskbrief.minihub.app/',
    'https://docs.bitcoinriskbrief.minihub.app/engineering/api-reference/',
    '/llms.txt',
  ])
  expect(links.map((a) => a.textContent?.trim())).toEqual(['Docs', 'API', 'llms.txt'])

  for (const link of links) {
    if (link.getAttribute('href')?.startsWith('http')) {
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noreferrer')
    } else {
      expect(link).not.toHaveAttribute('target')
    }
  }
})

test('places the developer links inside the existing bottom panel', async () => {
  render(<App />)

  const group = await screen.findByRole('navigation', { name: 'Developer and agent resources' })
  expect(group.closest('footer.bottom-panel')).not.toBeNull()
})

test('styles the footer developer links as a wrapping row', () => {
  const css = readFileSync(resolve(process.cwd(), 'src/App.css'), 'utf8')

  expect(css).toContain('.footer-dev-links')
})
```

Append to `frontend/src/locales.test.ts`:

```typescript
it('gives every locale an accessible name for the developer links', () => {
  for (const [code, value] of Object.entries(locales)) {
    expect(value.developerLinksAriaLabel, `${code} is missing developerLinksAriaLabel`).toBeTruthy()
  }
})
```

Adapt the iteration to whatever the file already uses to enumerate locales.

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test --prefix frontend`
Expected: FAIL — no navigation region named `Developer and agent resources`.

- [ ] **Step 3: Add the key and the markup**

Add `developerLinksAriaLabel: string` to the locale type in `frontend/src/locales.ts`, then add these exact values:

| Locale | Value |
| --- | --- |
| `en` | `Developer and agent resources` |
| `ru` | `Ресурсы для разработчиков и агентов` |
| `zh` | `开发者和智能体资源` |
| `de` | `Ressourcen für Entwickler und Agenten` |
| `fr` | `Ressources pour développeurs et agents` |
| `es` | `Recursos para desarrolladores y agentes` |
| `ar` | `موارد المطورين والوكلاء` |

In `frontend/src/App.tsx`, add a navigation group inside the existing `<footer className="bottom-panel">`, after the existing children, reusing the established `bottom-panel-link footer-token` classes and the `ExternalLink` icon already imported in that file:

```tsx
<nav className="footer-dev-links" aria-label={t.developerLinksAriaLabel}>
  <a
    className="bottom-panel-link footer-token"
    href="https://docs.bitcoinriskbrief.minihub.app/"
    target="_blank"
    rel="noreferrer"
    dir="ltr"
  >
    Docs
    <ExternalLink size={14} aria-hidden="true" />
  </a>
  <a
    className="bottom-panel-link footer-token"
    href="https://docs.bitcoinriskbrief.minihub.app/engineering/api-reference/"
    target="_blank"
    rel="noreferrer"
    dir="ltr"
  >
    API
    <ExternalLink size={14} aria-hidden="true" />
  </a>
  <a className="bottom-panel-link footer-token" href="/llms.txt" dir="ltr">
    llms.txt
  </a>
</nav>
```

`llms.txt` is same-origin, so it carries no `target` or external icon.

Add this rule to `frontend/src/App.css` immediately after the existing `.bottom-panel` block, which is already `display: flex` with `flex-wrap: wrap` and `gap: 12px 18px`:

```css
.footer-dev-links {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 14px;
}
```

The nav becomes a fourth child of the existing flex footer, so it wraps to its own line on narrow viewports without any media query. Each link already carries `dir="ltr"`, which keeps the tokens readable when the page direction is RTL.

- [ ] **Step 4: Run the checks**

Run: `npm test --prefix frontend`
Expected: PASS.

Run: `npm run build --prefix frontend`
Expected: build succeeds.

Run: `npm run smoke --prefix frontend`
Expected: PASS, and specifically no horizontal overflow at the 390px mobile viewport the smoke suite already asserts.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.css frontend/src/locales.ts frontend/src/App.test.tsx frontend/src/locales.test.ts
git commit -m "feat: link the documentation and agent surface from the footer"
```

---

### Task 3: Serve llms.txt from the documentation site

**Files:**
- Create: `docs/llms.txt`
- Test: `backend/tests/test_agent_surface.py` (extend)

**Interfaces:**
- Consumes: the documentation layout created by the S2 work.
- Produces: `https://docs.bitcoinriskbrief.minihub.app/llms.txt`.

The S2 design states that the documentation site "also serves its own `llms.txt`, giving agents stable canonical URLs for the technical reference." That file was never written; the URL currently returns 404. MkDocs copies non-Markdown files from `docs/` into `site/`, and `exclude_docs` lists only `superpowers/` and `README.md`, so a file at `docs/llms.txt` is published at the site root.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_agent_surface.py`:

```python
class DocsSiteAgentFileTests(unittest.TestCase):
    def test_docs_site_serves_its_own_llms_txt(self) -> None:
        path = DOCS / "llms.txt"
        self.assertTrue(path.is_file(), "docs/llms.txt must exist so the docs site publishes it")

    def test_docs_llms_txt_points_at_pages_that_exist(self) -> None:
        text = (DOCS / "llms.txt").read_text(encoding="utf-8")
        prefix = "https://docs.bitcoinriskbrief.minihub.app/"
        referenced = [line.split(prefix, 1)[1] for line in text.splitlines() if prefix in line]
        self.assertGreater(len(referenced), 3, "the map should cover more than a couple of pages")
        for ref in referenced:
            slug = ref.strip().rstrip("/)").rstrip("/")
            if not slug:
                continue
            with self.subTest(slug=slug):
                self.assertTrue(
                    (DOCS / f"{slug}.md").is_file(),
                    f"docs/{slug}.md does not exist, so the published URL would 404",
                )

    def test_docs_llms_txt_is_not_excluded_from_the_build(self) -> None:
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        exclude_block = config.split("exclude_docs:", 1)[1].split("nav:", 1)[0]
        self.assertNotIn("llms.txt", exclude_block)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
Expected: FAIL — `docs/llms.txt must exist so the docs site publishes it`.

- [ ] **Step 3: Write the file**

Create `docs/llms.txt`. Unlike the product's `llms.txt`, which maps endpoints, this one maps the technical reference:

```text
# Bitcoin Risk Brief — documentation

> Technical reference for a daily Bitcoin risk signal: methodology, API contract, freshness and validation
> semantics, and the agent access guide. The product itself is at https://bitcoinriskbrief.minihub.app/,
> and its endpoint map is at https://bitcoinriskbrief.minihub.app/llms.txt.
> Analytics and research context — not financial advice, not a price forecast, not a trade signal.

## Start here

- https://docs.bitcoinriskbrief.minihub.app/agents/agent-access-pack/: the readiness-first call sequence,
  worked endpoint examples, cache semantics, and what an agent must not present the output as.
- https://docs.bitcoinriskbrief.minihub.app/engineering/freshness-and-validation/: what readiness asserts,
  why staleness returns 503 rather than a stale figure, and how cached payloads are bound to a validation row.

## Product

- https://docs.bitcoinriskbrief.minihub.app/product/risk-methodology/: features, weights, normalisation
  windows, risk states, and the risk-level solver.
- https://docs.bitcoinriskbrief.minihub.app/product/product-spec/: what the product is and what it is not.

## Engineering

- https://docs.bitcoinriskbrief.minihub.app/engineering/api-reference/: endpoints, response shapes, cache headers.
- https://docs.bitcoinriskbrief.minihub.app/engineering/architecture/: services, runtime flow, storage.
- https://docs.bitcoinriskbrief.minihub.app/engineering/data-pipeline/: canonical source, refresh paths, validation.
- https://docs.bitcoinriskbrief.minihub.app/engineering/security-and-privacy/: headers, rate limits, PII handling.
- https://docs.bitcoinriskbrief.minihub.app/agents/openapi/: where the machine-readable schema lives.

## Operations

- https://docs.bitcoinriskbrief.minihub.app/operations/production-readiness/: current gates and accepted limits.

Operations pages are an operational log. They record what was verified and when; they are not claims about
product capability.
```

- [ ] **Step 4: Run the checks**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
Expected: PASS.

Run: `mkdocs build --strict && test -f site/llms.txt && echo "published"`
Expected: `published`.

- [ ] **Step 5: Commit**

```bash
git add docs/llms.txt backend/tests/test_agent_surface.py
git commit -m "docs: serve llms.txt from the documentation site"
```

---

## Verification Summary

All five must pass before this branch is proposed for merge:

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
./scripts/manage.sh validate
mkdocs build --strict
```

## Out Of Scope

- A full "for developers and agents" section with prose — that is S4, and S5a is about to rewrite the surrounding copy.
- Any change to the waitlist CTA — that is S5a and issue #51.
- The production deploy itself, which is operator work and happens after this branch merges.
