# Open Source And Agent Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository public under Apache-2.0, restructure documentation into a published MkDocs site, and give AI agents a discoverable, correct surface over the existing public API.

**Architecture:** Runtime services are untouched. The backend changes only its `FastAPI` constructor arguments; nginx changes only route handling; the frontend gains a static asset directory and JSON-LD. Documentation files move into a four-tier structure and are published by a CI job. No new dependency enters any production container — MkDocs runs only in CI.

**Tech Stack:** FastAPI, nginx, Vite/React, MkDocs Material, GitHub Actions, GitHub Pages.

## Global Constraints

- Licence is **Apache-2.0**. Every new file header, badge, and doc reference uses that exact name.
- **Never weaken the Content-Security-Policy.** Its current value is asserted verbatim in `backend/tests/test_frontend_security_headers.py::EXPECTED_CSP`; that constant must not change in this plan.
- No new dependency may be added to `backend/requirements.txt`, `collector/requirements.txt`, or `frontend/package.json`. MkDocs dependencies live in `docs/requirements.txt` and are installed only by CI.
- No change to risk methodology, database schema, collector behaviour, or the seven supported locales.
- Public canonical URLs: product `https://bitcoinriskbrief.minihub.app/`, documentation `https://docs.bitcoinriskbrief.minihub.app/`.
- Agent-facing files and JSON-LD describe the dataset and endpoint semantics. **They never embed a current risk value** — there is no server-side rendering, so any inlined number would go stale.
- The no-financial-advice framing appears in every new public artifact.
- Python tests are `unittest`, discovered with `PYTHONPATH=backend:collector python -m unittest discover -s backend/tests`. Frontend tests are Vitest.
- MkDocs 1.6 or newer is required for the `exclude_docs` key used in `mkdocs.yml`.
- Tasks 1-9 are branch work. Task 10 is the publication step and is performed by the operator.

---

### Task 1: Licence and repository furniture

**Files:**
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Test: `backend/tests/test_repository_furniture.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `LICENSE` at repository root containing the Apache-2.0 text; later tasks reference the licence name in README badges and `llms.txt`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_repository_furniture.py`:

```python
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RepositoryFurnitureTests(unittest.TestCase):
    def test_licence_is_apache_2_0(self) -> None:
        licence = ROOT / "LICENSE"
        self.assertTrue(licence.is_file(), "LICENSE must exist at the repository root")
        text = licence.read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)

    def test_contributing_and_security_exist(self) -> None:
        for name in ("CONTRIBUTING.md", "SECURITY.md"):
            path = ROOT / name
            self.assertTrue(path.is_file(), f"{name} must exist at the repository root")
            self.assertGreater(len(path.read_text(encoding="utf-8").strip()), 200)

    def test_security_policy_names_a_reporting_channel(self) -> None:
        text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertIn("@", text, "SECURITY.md must give a contact address for reports")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_repository_furniture -v`
Expected: FAIL — `LICENSE must exist at the repository root`.

- [ ] **Step 3: Add the three files**

Write the standard Apache-2.0 text to `LICENSE`:

```bash
curl -fsSL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE
```

Then append the copyright line to the end of `LICENSE`, replacing the bracketed placeholder block if present, and create `CONTRIBUTING.md`:

````markdown
# Contributing

Thanks for looking at Bitcoin Risk Brief. This is a small, focused product, so the most useful contributions are
narrow ones.

## Before you start

Open an issue describing what you want to change and why. For anything touching risk methodology, database schema, or
the public API contract, agree on the approach in the issue first — those areas have compatibility and evidence rules
that are easy to break by accident.

## Running the stack

```bash
cp .env.example .env
./scripts/manage.sh validate
./scripts/manage.sh start
./scripts/manage.sh migrate
./scripts/manage.sh backfill
```

The product is then at `http://localhost:3001`.

## Checks

Run the checks that match what you changed:

| Change | Command |
| --- | --- |
| Backend or collector | `./scripts/manage.sh test-python` |
| Frontend behaviour | `npm test --prefix frontend` |
| Frontend build | `npm run build --prefix frontend` |
| Compose or operations | `./scripts/manage.sh validate` |
| Documentation | `mkdocs build --strict` |

## What we will not merge

- Changes that present the risk score as financial advice, a price forecast, or a trading signal.
- Anything that weakens the Content-Security-Policy or the no-tracking posture.
- New runtime dependencies without a stated reason.
- Claims in documentation that a reader cannot open and verify.

## Licence

Contributions are accepted under the Apache-2.0 licence in `LICENSE`.
````

And `SECURITY.md`:

```markdown
# Security Policy

## Reporting a vulnerability

Email `hello@minihub.app` with the details. Please do not open a public issue for anything exploitable.

Include what you found, how to reproduce it, and what impact you think it has. A proof of concept helps but is not
required.

Expect an acknowledgement within a few days. This is a small project run by one person, so please allow reasonable
time before disclosing publicly.

## Scope

In scope: the public product at `https://bitcoinriskbrief.minihub.app`, its public API endpoints, and this repository.

Out of scope: findings that require physical access to the deployment host, denial of service through raw traffic
volume, and reports produced solely by automated scanners without a demonstrated impact.

## What this product stores

The waitlist stores contacts submitted deliberately by visitors. There is no product analytics, no tracking cookie,
and no third-party beacon. See `docs/engineering/security-and-privacy.md`.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_repository_furniture -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add LICENSE CONTRIBUTING.md SECURITY.md backend/tests/test_repository_furniture.py
git commit -m "docs: add Apache-2.0 licence and contribution policy"
```

---

### Task 2: Agent static files

**Files:**
- Create: `frontend/public/robots.txt`
- Create: `frontend/public/sitemap.xml`
- Create: `frontend/public/llms.txt`
- Create: `frontend/public/llms-full.txt`
- Test: `backend/tests/test_agent_surface.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `frontend/public/` as the static asset root that Vite copies into `dist`. Task 4 relies on those files being served by the nginx fallthrough location.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_agent_surface.py`:

```python
from __future__ import annotations

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "frontend" / "public"

PRODUCT_URL = "https://bitcoinriskbrief.minihub.app/"
DOCS_URL = "https://docs.bitcoinriskbrief.minihub.app/"


class AgentStaticFileTests(unittest.TestCase):
    def test_all_agent_files_exist(self) -> None:
        for name in ("robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt"):
            self.assertTrue((PUBLIC_DIR / name).is_file(), f"frontend/public/{name} must exist")

    def test_robots_allows_crawling_and_points_at_the_sitemap(self) -> None:
        text = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", text)
        self.assertIn("Allow: /", text)
        self.assertIn(f"Sitemap: {PRODUCT_URL}sitemap.xml", text)

    def test_sitemap_is_valid_xml_listing_both_hosts(self) -> None:
        raw = (PUBLIC_DIR / "sitemap.xml").read_text(encoding="utf-8")
        # The stdlib parser resolves external entities. This input is a file we author in this
        # repository, but assert it declares no doctype or entities before parsing, so the test
        # stays safe without pulling defusedxml into backend/requirements.txt.
        self.assertNotIn("<!DOCTYPE", raw)
        self.assertNotIn("<!ENTITY", raw)
        root = ET.fromstring(raw)
        locations = {node.text for node in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
        self.assertIn(PRODUCT_URL, locations)
        self.assertIn(DOCS_URL, locations)

    def test_llms_txt_states_the_readiness_first_rule_and_the_advice_boundary(self) -> None:
        text = (PUBLIC_DIR / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Bitcoin Risk Brief"))
        self.assertIn("/api/readiness", text)
        self.assertIn("not financial advice", text.lower())

    def test_agent_files_never_embed_a_risk_value(self) -> None:
        import re

        pattern = re.compile(r"\brisk\b[^\n]*?\b0\.\d{3,}", re.IGNORECASE)
        for name in ("llms.txt", "llms-full.txt"):
            text = (PUBLIC_DIR / name).read_text(encoding="utf-8")
            self.assertIsNone(
                pattern.search(text),
                f"{name} must not embed a concrete risk reading; it would go stale",
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
Expected: FAIL — `frontend/public/robots.txt must exist`.

- [ ] **Step 3: Create the four files**

`frontend/public/robots.txt`:

```text
User-agent: *
Allow: /
Disallow: /api/waitlist

Sitemap: https://bitcoinriskbrief.minihub.app/sitemap.xml

# Machine-readable summary for language models and agents:
# https://bitcoinriskbrief.minihub.app/llms.txt
```

`frontend/public/sitemap.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bitcoinriskbrief.minihub.app/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://docs.bitcoinriskbrief.minihub.app/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

`frontend/public/llms.txt`:

```text
# Bitcoin Risk Brief

> A daily Bitcoin risk signal computed from canonical BTC/USD daily data. One deterministic score from 0.0 to 1.0,
> its state, what changed, whether the underlying data is fresh, and the price scenarios that would move the score
> into another band. Analytics and research context — not financial advice, not a price forecast, not a trade signal.

## Read this first

Always call `/api/readiness` before reporting any value. It returns HTTP 503 when data is stale or validation failed.
A risk number without its freshness state is not usable, and this product returns 503 rather than serving a stale
figure. Never present a risk value without also stating its covered date and freshness.

## Endpoints

Base URL: https://bitcoinriskbrief.minihub.app

- `GET /api/readiness`: freshness and validation state. Never cached. Check this first.
- `GET /api/risk/latest`: the latest risk point, its state, model price, and component values.
- `GET /api/risk/history?limit=730`: historical risk rows, ascending by timestamp.
- `GET /api/risk/levels`: the solved price ladder — which BTC price corresponds to which risk level.
- `GET /api/brief/latest`: the daily brief in seven locales.
- `GET /api/openapi.json`: the full machine-readable contract.

## Interpretation

- Risk states: low below 0.30, neutral from 0.30 to below 0.70, high at 0.70 and above.
- The reported price is HLC3 from the last completed daily candle. It is not a live spot price.
- Risk-level prices are scenario outputs solved through the same model. They are not forecasts, targets, or
  support levels.
- Methodology is versioned. The version travels with every response.

## What not to do

Do not present this output as financial advice, investment advice, a price prediction, or a buy or sell
recommendation. Do not report a value without its freshness state. Do not treat a scenario price as a forecast.

## Documentation

- Full technical reference: https://docs.bitcoinriskbrief.minihub.app/
- Agent access guide: https://docs.bitcoinriskbrief.minihub.app/agents/agent-access-pack/
- Methodology: https://docs.bitcoinriskbrief.minihub.app/product/risk-methodology/
- Complete inline version of this file: https://bitcoinriskbrief.minihub.app/llms-full.txt
```

`frontend/public/llms-full.txt`: start from the `llms.txt` content above, then append the full methodology summary and the endpoint response shapes. Copy the field tables from `docs/api-reference.md` and the formula summary from `docs/risk-methodology.md` verbatim, so there is one source of truth and no paraphrase drift. Keep the same rule: no concrete risk reading anywhere in the file.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/public backend/tests/test_agent_surface.py
git commit -m "feat: publish robots, sitemap, and llms agent files"
```

---

### Task 3: Expose and enrich the OpenAPI schema

**Files:**
- Modify: `backend/app/main.py` (the `FastAPI(...)` constructor and the route decorators)
- Test: `backend/tests/test_openapi_contract.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `GET /api/openapi.json` serving the schema. Task 2's `llms.txt` already links to it; Task 8's agent pack documents it.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_openapi_contract.py`:

```python
from __future__ import annotations

import unittest

from app.main import app

PUBLIC_PATHS = {
    "/api/health",
    "/api/readiness",
    "/api/risk/latest",
    "/api/risk/history",
    "/api/risk/levels",
    "/api/brief/latest",
    "/api/waitlist",
}


class OpenApiContractTests(unittest.TestCase):
    def test_schema_is_served_under_the_api_prefix(self) -> None:
        self.assertEqual(app.openapi_url, "/api/openapi.json")

    def test_interactive_docs_are_disabled(self) -> None:
        self.assertIsNone(app.docs_url, "Swagger UI loads CDN scripts the CSP blocks")
        self.assertIsNone(app.redoc_url)

    def test_every_public_route_is_in_the_schema(self) -> None:
        paths = set(app.openapi()["paths"].keys())
        self.assertEqual(PUBLIC_PATHS, paths & PUBLIC_PATHS)

    def test_schema_declares_the_public_server(self) -> None:
        servers = app.openapi().get("servers", [])
        self.assertIn(
            "https://bitcoinriskbrief.minihub.app",
            {entry.get("url") for entry in servers},
        )

    def test_every_public_route_has_a_summary_and_description(self) -> None:
        paths = app.openapi()["paths"]
        for path in sorted(PUBLIC_PATHS):
            for method, operation in paths[path].items():
                with self.subTest(path=path, method=method):
                    self.assertTrue(operation.get("summary"), f"{method} {path} needs a summary")
                    self.assertTrue(operation.get("description"), f"{method} {path} needs a description")

    def test_description_states_the_advice_boundary(self) -> None:
        self.assertIn("not financial advice", app.openapi()["info"]["description"].lower())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_openapi_contract -v`
Expected: FAIL — `app.openapi_url` is `/openapi.json`, not `/api/openapi.json`.

- [ ] **Step 3: Change the constructor and annotate the routes**

In `backend/app/main.py`, replace the existing constructor call:

```python
app = FastAPI(
    title="Bitcoin Risk Brief API",
    version="0.1.0",
    description=(
        "A daily Bitcoin risk signal computed from canonical BTC/USD daily data. "
        "Call GET /api/readiness before reporting any value: it returns HTTP 503 when data is stale or "
        "validation failed, and a risk number without its freshness state is not usable. "
        "This is analytics and research context, not financial advice, not a price forecast, and not a trade signal."
    ),
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url=None,
    servers=[{"url": "https://bitcoinriskbrief.minihub.app", "description": "Production"}],
    lifespan=lifespan,
)
```

Then add `summary=` and `description=` to each of the seven route decorators. For example:

```python
@app.get(
    "/api/readiness",
    tags=["status"],
    summary="Freshness and validation state",
    description=(
        "Returns HTTP 200 when every check passes and HTTP 503 when the data is stale or validation failed. "
        "Never cached. Call this before reporting any risk value."
    ),
)
```

Use tags `status` for health and readiness, `risk` for the three risk routes, `brief` for the brief, and `waitlist` for the waitlist.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_openapi_contract -v`
Expected: PASS (6 tests).

Then run the full backend suite to confirm nothing regressed:

Run: `./scripts/manage.sh test-python`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_openapi_contract.py
git commit -m "feat: expose and document the OpenAPI schema"
```

---

### Task 4: Honest 404 for unknown paths

**Files:**
- Modify: `frontend/nginx.conf:31-39`
- Test: `backend/tests/test_agent_surface.py` (extend)

**Interfaces:**
- Consumes: `frontend/public/` from Task 2 — those files must still be served by the fallthrough location.
- Produces: an explicit SPA route allowlist. S4 extends it when `/methodology` and `/risk/YYYY-MM-DD` arrive.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_agent_surface.py`:

```python
NGINX_CONF = ROOT / "frontend" / "nginx.conf"


class NginxRouteTests(unittest.TestCase):
    def test_unknown_paths_are_not_rewritten_to_the_app_shell(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertNotIn(
            "try_files $uri $uri/ /index.html;",
            text,
            "the catch-all fallback answers 200 for every path, including nonexistent ones",
        )

    def test_root_serves_the_app_shell(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("location = / {", text)
        self.assertIn("try_files /index.html =404;", text)

    def test_fallthrough_location_returns_404(self) -> None:
        text = NGINX_CONF.read_text(encoding="utf-8")
        self.assertIn("try_files $uri =404;", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
Expected: FAIL — the catch-all fallback is still present.

- [ ] **Step 3: Replace the `location /` block**

In `frontend/nginx.conf`, replace the final `location / { ... }` block with two blocks. Keep every `add_header` line exactly as it appears today in both blocks — the CSP string must be byte-identical to the existing one, because `backend/tests/test_frontend_security_headers.py` asserts it verbatim.

```nginx
  location = / {
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Content-Security-Policy "<COPY THE EXISTING CSP STRING VERBATIM>" always;
    add_header Cache-Control "public, max-age=0, must-revalidate, no-transform" always;
    try_files /index.html =404;
  }

  location / {
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Content-Security-Policy "<COPY THE EXISTING CSP STRING VERBATIM>" always;
    add_header Cache-Control "public, max-age=0, must-revalidate, no-transform" always;
    try_files $uri =404;
  }
```

The second block still serves `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, and the favicon, because those files exist in the built output. Anything that does not exist now returns a real 404.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface backend.tests.test_frontend_security_headers -v`
Expected: PASS. The security-headers suite must still pass unchanged — if it fails, the CSP string was altered and must be restored.

- [ ] **Step 5: Commit**

```bash
git add frontend/nginx.conf backend/tests/test_agent_surface.py
git commit -m "fix: return 404 for unknown paths instead of the app shell"
```

---

### Task 5: Structured data in the page head

**Files:**
- Modify: `frontend/index.html`
- Test: `frontend/src/structuredData.test.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: a `<script type="application/ld+json">` block in `index.html` describing `Dataset` and `WebSite`.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/structuredData.test.ts`:

```typescript
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const html = readFileSync(resolve(__dirname, '../index.html'), 'utf-8')

function extractJsonLd(): Record<string, unknown>[] {
  const matches = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
  return matches.map((match) => JSON.parse(match[1]))
}

describe('structured data', () => {
  it('is present and parses as JSON', () => {
    expect(extractJsonLd().length).toBeGreaterThan(0)
  })

  it('declares a Dataset and a WebSite', () => {
    const types = extractJsonLd().map((entry) => entry['@type'])
    expect(types).toContain('Dataset')
    expect(types).toContain('WebSite')
  })

  it('states the advice boundary on the dataset', () => {
    const dataset = extractJsonLd().find((entry) => entry['@type'] === 'Dataset')
    expect(String(dataset?.description).toLowerCase()).toContain('not financial advice')
  })

  it('embeds no concrete risk reading', () => {
    for (const entry of extractJsonLd()) {
      expect(JSON.stringify(entry)).not.toMatch(/\brisk\b[^"]*?\b0\.\d{3,}/i)
    }
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test --prefix frontend -- structuredData`
Expected: FAIL — no JSON-LD block found.

- [ ] **Step 3: Add the JSON-LD block**

In `frontend/index.html`, immediately before `</head>`:

```html
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Bitcoin Risk Brief",
        "description": "A daily Bitcoin risk signal from 0.0 to 1.0 computed from canonical BTC/USD daily data, with its state, freshness, and the price scenarios that would move it into another band. Analytics and research context, not financial advice.",
        "url": "https://bitcoinriskbrief.minihub.app/",
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        "isAccessibleForFree": true,
        "creator": { "@type": "Person", "name": "Andrey Karazhev" },
        "temporalCoverage": "2010-07-17/..",
        "variableMeasured": [
          { "@type": "PropertyValue", "name": "risk", "description": "Modelled risk from 0.0 to 1.0" },
          { "@type": "PropertyValue", "name": "risk_state", "description": "low, neutral, or high" },
          { "@type": "PropertyValue", "name": "model_price_usd", "description": "HLC3 of the last completed daily candle" }
        ],
        "distribution": [
          {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": "https://bitcoinriskbrief.minihub.app/api/risk/latest"
          }
        ]
      }
    </script>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Bitcoin Risk Brief",
        "url": "https://bitcoinriskbrief.minihub.app/",
        "inLanguage": ["en", "ru", "zh", "de", "fr", "es", "ar"]
      }
    </script>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test --prefix frontend`
Expected: PASS, including the existing suites.

Run: `npm run build --prefix frontend`
Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/structuredData.test.ts
git commit -m "feat: describe the dataset with JSON-LD"
```

---

### Task 6: Documentation restructure

**Files:**
- Move: 24 files under `docs/` into `docs/product/`, `docs/engineering/`, `docs/operations/`
- Create: `docs/index.md`
- Modify: `docs/README.md`, `README.md`, `AGENTS.md`, and every file containing a cross-link to a moved path
- Test: `backend/tests/test_docs_structure.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the four-tier layout that Task 7's `mkdocs.yml` navigation refers to by path, and that Task 9's README links into.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_docs_structure.py`:

```python
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

EXPECTED_LAYOUT = {
    "product": {"product-spec.md", "risk-methodology.md"},
    "engineering": {
        "architecture.md",
        "data-pipeline.md",
        "api-reference.md",
        "testing-and-quality.md",
        "security-and-privacy.md",
        "frontend-qa.md",
        "waitlist.md",
    },
    "operations": {
        "operations.md",
        "production-readiness.md",
        "production-evidence-log.md",
        "production-roadmap.md",
        "deploy-ubuntu-cloudflare.md",
        "server-msi-cubi5-ubuntu-26.04.md",
        "pilot-learning-loop.md",
        "marketing-and-growth.md",
        "dependency-license-review.md",
        "backup-restore-evidence-packet-template.md",
        "import-provenance-evidence-packet-template.md",
        "launch-snapshot-evidence-packet-template.md",
        "monitoring-alert-evidence-packet-template.md",
        "operator-launch-decision-packet-template.md",
    },
}

OPERATIONAL_BANNER = "**Operational log.**"


class DocsStructureTests(unittest.TestCase):
    def test_every_document_is_in_its_tier(self) -> None:
        for tier, names in EXPECTED_LAYOUT.items():
            present = {path.name for path in (DOCS / tier).glob("*.md")}
            self.assertEqual(names, present, f"docs/{tier}/ contents differ from the planned layout")

    def test_no_stray_markdown_left_at_the_docs_root(self) -> None:
        stray = {path.name for path in DOCS.glob("*.md")} - {"README.md", "index.md"}
        self.assertEqual(set(), stray, f"unmoved documents remain at docs/: {stray}")

    def test_operations_pages_carry_the_operational_log_banner(self) -> None:
        for path in (DOCS / "operations").glob("*.md"):
            with self.subTest(path=path.name):
                self.assertIn(OPERATIONAL_BANNER, path.read_text(encoding="utf-8"))

    def test_no_markdown_link_points_at_a_moved_path(self) -> None:
        moved = {name for names in EXPECTED_LAYOUT.values() for name in names}
        broken: list[str] = []
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts or "node_modules" in path.parts:
                continue
            for target in re.findall(r"\]\(([^)#]+\.md)[^)]*\)", path.read_text(encoding="utf-8")):
                candidate = (path.parent / target).resolve()
                if candidate.name in moved and not candidate.exists():
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual([], broken, "links point at pre-restructure paths")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_docs_structure -v`
Expected: FAIL — `docs/product/` does not exist.

- [ ] **Step 3: Move the files and repair the links**

```bash
mkdir -p docs/product docs/engineering docs/operations docs/agents

git mv docs/01-bitcoin-risk-brief.md docs/product/product-spec.md
git mv docs/risk-methodology.md docs/product/

git mv docs/architecture.md docs/data-pipeline.md docs/api-reference.md \
       docs/testing-and-quality.md docs/security-and-privacy.md \
       docs/frontend-qa.md docs/waitlist.md docs/engineering/

git mv docs/operations.md docs/production-readiness.md docs/production-evidence-log.md \
       docs/production-roadmap.md docs/deploy-ubuntu-cloudflare.md \
       docs/server-msi-cubi5-ubuntu-26.04.md docs/pilot-learning-loop.md \
       docs/marketing-and-growth.md docs/dependency-license-review.md \
       docs/backup-restore-evidence-packet-template.md \
       docs/import-provenance-evidence-packet-template.md \
       docs/launch-snapshot-evidence-packet-template.md \
       docs/monitoring-alert-evidence-packet-template.md \
       docs/operator-launch-decision-packet-template.md \
       docs/operations/
```

Insert this banner as the first line after the H1 of every file now in `docs/operations/`:

```markdown
> **Operational log.** These entries record what was verified and when. They are not claims about product capability.
```

Then repair every cross-link. Find them with:

```bash
grep -rn --include=*.md -E '\]\((\.\./)*[a-z0-9-]+\.md' . | grep -v node_modules | grep -v '\.git/'
```

Rewrite `docs/README.md` as a short index pointing at the four tiers, and create `docs/index.md` as the documentation site landing page: one paragraph on what the product is, then links to the product, engineering, agents, and operations tiers.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_docs_structure -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add -A docs README.md AGENTS.md backend/tests/test_docs_structure.py
git commit -m "docs: restructure documentation into product, engineering, agents, and operations"
```

---

### Task 7: MkDocs configuration and the strict build check

**Files:**
- Create: `mkdocs.yml`
- Create: `docs/requirements.txt`
- Modify: `.github/workflows/ci.yml`
- Test: the `mkdocs build --strict` command itself, wired as a CI job

**Interfaces:**
- Consumes: the layout produced by Task 6 — every `nav:` entry is a path created there.
- Produces: a reproducible `site/` build. Task 10 adds the deploy step on top of this job.

- [ ] **Step 1: Add the configuration and pin the dependency**

Create `docs/requirements.txt`:

```text
mkdocs-material==9.7.7
```

Create `mkdocs.yml` at the repository root:

```yaml
site_name: Bitcoin Risk Brief
site_description: Technical reference for a daily Bitcoin risk signal — methodology, API contract, and operations.
site_url: https://docs.bitcoinriskbrief.minihub.app/
repo_url: https://github.com/akarazhev/bitcoin-risk-brief
edit_uri: ""

theme:
  name: material
  features:
    - navigation.sections
    - navigation.top
    - content.code.copy
    - search.suggest
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      toggle: { icon: material/brightness-7, name: Switch to dark mode }
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      toggle: { icon: material/brightness-4, name: Switch to light mode }

markdown_extensions:
  - admonition
  - tables
  - toc: { permalink: true }
  - pymdownx.superfences
  - pymdownx.highlight

exclude_docs: |
  superpowers/
  README.md

nav:
  - Home: index.md
  - Product:
      - Overview: product/product-spec.md
      - Risk methodology: product/risk-methodology.md
  - Engineering:
      - Architecture: engineering/architecture.md
      - Data pipeline: engineering/data-pipeline.md
      - Freshness and validation: engineering/freshness-and-validation.md
      - API reference: engineering/api-reference.md
      - Security and privacy: engineering/security-and-privacy.md
      - Testing and quality: engineering/testing-and-quality.md
      - Frontend QA: engineering/frontend-qa.md
      - Waitlist: engineering/waitlist.md
  - Agents:
      - Agent access pack: agents/agent-access-pack.md
      - OpenAPI: agents/openapi.md
  - Operations:
      - Operations: operations/operations.md
      - Production readiness: operations/production-readiness.md
      - Evidence log: operations/production-evidence-log.md
      - Roadmap: operations/production-roadmap.md
      - Deployment: operations/deploy-ubuntu-cloudflare.md
      - Server setup: operations/server-msi-cubi5-ubuntu-26.04.md
      - Pilot learning loop: operations/pilot-learning-loop.md
      - Marketing and growth: operations/marketing-and-growth.md
      - Dependency and licence review: operations/dependency-license-review.md
```

The `nav` entries for `engineering/freshness-and-validation.md`, `agents/agent-access-pack.md`, and `agents/openapi.md` are created in Task 8. Until then `mkdocs build --strict` fails on those three — that is expected, and Task 7's build check is only wired into CI here, then made green by Task 8.

- [ ] **Step 2: Run the build to verify it fails on the three missing pages**

Run: `pip install -r docs/requirements.txt && mkdocs build --strict`
Expected: FAIL — three `nav` entries reference files that do not exist.

- [ ] **Step 3: Add the CI job**

Append to `.github/workflows/ci.yml`:

```yaml
  docs-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: pip
          cache-dependency-path: docs/requirements.txt
      - name: Install documentation dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r docs/requirements.txt
      - name: Build documentation
        run: mkdocs build --strict
```

- [ ] **Step 4: Verify the workflow parses**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('workflow parses')"`
Expected: `workflow parses`.

- [ ] **Step 5: Commit**

```bash
git add mkdocs.yml docs/requirements.txt .github/workflows/ci.yml
git commit -m "build: add MkDocs configuration and a strict docs build check"
```

---

### Task 8: Agent access pack, OpenAPI page, and the freshness reference

**Files:**
- Create: `docs/agents/agent-access-pack.md`
- Create: `docs/agents/openapi.md`
- Create: `docs/engineering/freshness-and-validation.md`
- Test: `mkdocs build --strict`, plus `backend/tests/test_agent_surface.py` (extend)

**Interfaces:**
- Consumes: the `nav` entries declared in Task 7; the schema exposed in Task 3.
- Produces: the three pages `llms.txt` links to.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_agent_surface.py`:

```python
DOCS = ROOT / "docs"


class AgentDocumentationTests(unittest.TestCase):
    def test_the_three_agent_pages_exist(self) -> None:
        for relative in (
            "agents/agent-access-pack.md",
            "agents/openapi.md",
            "engineering/freshness-and-validation.md",
        ):
            self.assertTrue((DOCS / relative).is_file(), f"docs/{relative} must exist")

    def test_the_access_pack_states_the_readiness_first_rule(self) -> None:
        text = (DOCS / "agents" / "agent-access-pack.md").read_text(encoding="utf-8")
        self.assertIn("/api/readiness", text)
        self.assertIn("X-Cache-Version", text)
        self.assertIn("not financial advice", text.lower())

    def test_the_freshness_page_explains_every_readiness_check(self) -> None:
        text = (DOCS / "engineering" / "freshness-and-validation.md").read_text(encoding="utf-8")
        for token in (
            "data_fresh",
            "data_age_days",
            "covered_end",
            "latest_matches_validation_end",
            "btc_risk_validation",
            "X-Cache-Version",
            "503",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
Expected: FAIL — `docs/agents/agent-access-pack.md must exist`.

- [ ] **Step 3: Write the three pages**

`docs/agents/agent-access-pack.md` — implements the existing design in `docs/superpowers/specs/2026-06-30-agent-access-demand-test-design.md`. Sections, in order:

1. **Read readiness first** — the required call sequence, and why a value without its freshness state is unusable.
2. **Endpoints** — all seven, each with a real request and a real response body copied from `docs/engineering/api-reference.md`.
3. **Cache semantics** — `Cache-Control`, `ETag`, `X-Cache`, and `X-Cache-Version`; how conditional requests with `If-None-Match` return 304; that `X-Cache-Version` changes after a successful import.
4. **Rate limits** — the waitlist limit and the edge configuration.
5. **Interpretation** — band thresholds, HLC3 model price versus spot, scenario prices versus forecasts.
6. **What an agent must not do** — present the output as advice, report a value without freshness, treat a scenario as a prediction.

`docs/agents/openapi.md` — a short page: where the schema lives (`https://bitcoinriskbrief.minihub.app/api/openapi.json`), that interactive documentation is deliberately absent because the strict CSP blocks CDN-loaded Swagger assets, and a worked `curl` example generating a client.

`docs/engineering/freshness-and-validation.md` — the page carrying the most weight per line in the set. Cover: what each check in the `/api/readiness` payload asserts; how `data_age_days` is derived and compared against `DATA_FRESHNESS_MAX_AGE_DAYS`; what `latest_matches_validation_end` rules out; why staleness returns HTTP 503 rather than a stale figure; what `btc_risk_validation` records per import; how `X-Cache-Version` binds a cached payload to a validation row so a stale cache cannot outlive its data; and what an import provenance packet records. Describe implemented behaviour only.

- [ ] **Step 4: Run the tests and the strict build**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_agent_surface -v`
Expected: PASS.

Run: `mkdocs build --strict`
Expected: build succeeds with no warnings — every `nav` entry now resolves.

- [ ] **Step 5: Commit**

```bash
git add docs/agents docs/engineering/freshness-and-validation.md backend/tests/test_agent_surface.py
git commit -m "docs: add the agent access pack and the freshness reference"
```

---

### Task 9: README rewrite

**Files:**
- Modify: `README.md`
- Test: `backend/tests/test_repository_furniture.py` (extend)

**Interfaces:**
- Consumes: the documentation site paths from Task 6, the agent files from Task 2, the licence from Task 1.
- Produces: the repository's front page. Nothing depends on it.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_repository_furniture.py`:

```python
class ReadmeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_readme_is_a_shopfront_not_a_manual(self) -> None:
        self.assertLess(
            len(self.text.splitlines()),
            160,
            "the README should be an overview; operational detail belongs in docs/operations/",
        )

    def test_the_first_forty_lines_describe_the_product(self) -> None:
        head = "\n".join(self.text.splitlines()[:40]).lower()
        self.assertIn("bitcoin", head)
        for phrase in ("accepted limitation", "remains pending", "unclaimed"):
            self.assertNotIn(phrase, head, "limitation language belongs in the operations tier, not the first screen")

    def test_readme_links_the_agent_surface_and_the_licence(self) -> None:
        self.assertIn("llms.txt", self.text)
        self.assertIn("/api/openapi.json", self.text)
        self.assertIn("Apache-2.0", self.text)

    def test_readme_keeps_the_advice_disclaimer(self) -> None:
        self.assertIn("not financial advice", self.text.lower())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest backend.tests.test_repository_furniture -v`
Expected: FAIL — the README is 223 lines and its first forty contain limitation language.

- [ ] **Step 3: Rewrite the README**

Target roughly 120 lines, in this order:

1. Title, one-sentence description, badges for CI, Apache-2.0, and the live site.
2. A screenshot of the first viewport, committed under `docs/assets/`.
3. The live link and a `curl` example against `/api/readiness` with a real response body.
4. **What it does** — five bullets.
5. **What makes it different** — visible freshness and readiness, a deterministic reproducible metric, the scenario ladder.
6. **For AI agents** — `llms.txt`, `/api/openapi.json`, and a link to the agent access pack.
7. **Architecture** — the existing four-row service table plus a mermaid diagram of the daily flow.
8. **Quick start** — unchanged from the current README.
9. **Documentation** — links into the documentation site.
10. Disclaimer and licence.

Replace the current sixty-line Current Status block with one line:

```markdown
Current operational status, evidence, and accepted limitations: [Production Readiness](docs/operations/production-readiness.md).
```

- [ ] **Step 4: Run the full check set**

Run: `./scripts/manage.sh test-python`
Expected: PASS.

Run: `mkdocs build --strict`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/assets backend/tests/test_repository_furniture.py
git commit -m "docs: rewrite the README as a product overview"
```

---

### Task 10: Publication

**Files:**
- Modify: `.github/workflows/ci.yml` (add the Pages deploy job)

**Interfaces:**
- Consumes: everything above. The branch must be complete, reviewed, and green before this task starts.
- Produces: the public repository, the live documentation site, and the deployed agent surface.

This task is operator work. It is not test-driven; each step is verified by observation.

- [ ] **Step 1: Re-run the secret scan**

```bash
git log --all --pretty=format: --name-only --diff-filter=A | sort -u \
  | grep -Ei '(^|/)\.env|secret|credential|\.pem$|\.key$|token|password' | grep -v example
git grep -nEI '(api[_-]?key|secret|password|token)\s*[:=]\s*["'"'"'][A-Za-z0-9_/+.-]{16,}' \
  | grep -vEi 'example|test|placeholder|your-|<|\$\{|CHANGE'
```

Expected: no output from either command. Stop and investigate if anything appears.

- [ ] **Step 2: Flip repository visibility and enable Discussions**

```bash
gh repo edit akarazhev/bitcoin-risk-brief --visibility public --accept-visibility-change-consequences
gh repo edit akarazhev/bitcoin-risk-brief --enable-discussions
gh repo edit akarazhev/bitcoin-risk-brief \
  --add-topic ai-agents --add-topic openapi --add-topic llms-txt --add-topic mcp --add-topic open-source
```

Then refresh the repository description and upload the social preview image in repository settings, so a link to the
repository expands into a meaningful card rather than the owner's avatar.

- [ ] **Step 3: Add the Pages deploy job**

This job can only succeed on a public repository, which is why it is added after Step 2. Append to `.github/workflows/ci.yml`:

```yaml
  docs-deploy:
    needs: docs-build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install documentation dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r docs/requirements.txt
      - name: Build documentation
        run: mkdocs build --strict
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - id: deployment
        uses: actions/deploy-pages@v4
```

Enable Pages with the GitHub Actions source in repository settings, then add a `CNAME` file containing `docs.bitcoinriskbrief.minihub.app` to `docs/` so MkDocs copies it into `site/`.

- [ ] **Step 4: Add the DNS record**

In Cloudflare, add a `CNAME` for `docs` pointing at `akarazhev.github.io`, proxied. **Snapshot the zone's records before and after, and confirm the `MX` entries are unchanged** — a broken page is an inconvenience, broken mail is silent.

- [ ] **Step 5: Deploy the product and verify**

Deploy through the USB kit. The agent files reach production only after this step.

```bash
bash deploy-from-usb.sh --with-backup https://bitcoinriskbrief.minihub.app
```

Then verify each acceptance criterion against the live host:

```bash
curl -fsS https://bitcoinriskbrief.minihub.app/robots.txt | head -3
curl -fsS https://bitcoinriskbrief.minihub.app/llms.txt | head -3
curl -fsS https://bitcoinriskbrief.minihub.app/api/openapi.json | python3 -c "import json,sys; print(sorted(json.load(sys.stdin)['paths']))"
curl -s -o /dev/null -w '%{http_code}\n' https://bitcoinriskbrief.minihub.app/this-path-does-not-exist
curl -fsS https://docs.bitcoinriskbrief.minihub.app/ >/dev/null && echo "docs site up"
```

Expected: the agent files return their real content, the schema lists all seven paths, the unknown path returns `404`, and the documentation site responds.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/ci.yml docs/CNAME
git commit -m "build: deploy the documentation site to GitHub Pages"
```

---

## Verification Summary

After Task 9, all of these must pass on the branch:

```bash
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
./scripts/manage.sh validate
mkdocs build --strict
```

After Task 10, the live checks in Step 5 must all succeed.
