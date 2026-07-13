# Testing and Quality

## Local Test Commands

Run backend and collector tests:

```bash
./scripts/manage.sh test-python
```

Compile Python modules:

```bash
python3 -m compileall backend collector
```

Run frontend tests:

```bash
npm test --prefix frontend
```

Run frontend browser smoke checks:

```bash
npm run smoke --prefix frontend
```

Build frontend:

```bash
npm run build --prefix frontend
```

Validate compose:

```bash
./scripts/manage.sh validate
```

Build containers:

```bash
podman-compose -f podman-compose.yml build backend data-collector frontend
```

Run containerized collector smoke:

```bash
./scripts/manage.sh run-now
```

## Current Test Coverage Areas

Backend tests cover:

- brief generation;
- risk constants and risk calculation behavior;
- risk levels and solver behavior;
- canonical CSV source loading and risk dataset construction;
- repository full-history behavior;
- readiness payload rules;
- cacheable public read cache headers, ETags, no-store readiness headers, and no-store waitlist headers;
- public payload cache warmup behavior, including warmed cache-key reuse, validation-version invalidation, and no-store
  readiness and waitlist isolation;
- security headers;
- waitlist validation and upsert behavior;
- fixed-window rate limiter behavior;
- Cloudflare edge-rule rendering, merge behavior, and apply flow;
- fully qualified container image references in Dockerfiles and compose files.

Collector tests cover:

- CoinMarketCap payload parsing;
- CoinMarketCap retry and permanent error behavior;
- CSV refresh and remote delta validation;
- automatic public CoinMarketCap CSV download validation;
- downloaded CoinMarketCap CSV intake validation;
- database stale-row cleanup;
- database pool retry behavior;
- source preservation in database records;
- OHLCV merge helper behavior.

Server-kit tests cover:

- rootless systemd service script safety checks;
- debug script evidence collection and secret masking.
- USB kit packaging behavior, including required docs/scripts, filtered project snapshot contents, excluded local state,
  executable server scripts, manifest contents, and checksums.
- The USB update wrapper contract: backup before deploy, backup checksum verification, off-server/USB backup copy,
  existing production `.env` preservation, service restart, and health/readiness checks.

Frontend tests cover:

- app shell rendering;
- waitlist submission;
- no browser persistent storage for waitlist contacts;
- readiness/freshness rendering, including degraded copy;
- API-unavailable copy for failed risk data loads;
- explicit empty chart states for missing history or levels rows;
- methodology/disclaimer copy and nearest threshold callouts;
- compact chart options, resize behavior, and accessible threshold labels.

Frontend browser smoke checks cover:

- desktop and mobile layout without horizontal overflow;
- non-empty risk history and risk levels chart canvases;
- degraded readiness state rendering;
- API failure rendering that does not look like fresh data;
- Playwright Chromium, Firefox, WebKit, Pixel 5, and iPhone 13 profiles.

Planned production-pilot coverage should also include:

- cache invalidation behavior after a successful collector/import run;
- waitlist abuse and edge-rate-limit smoke checks in the deployed environment.

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`.

The workflow runs on every push to `main` and on every pull request targeting `main`.

Required status checks:

- `backend-tests`: installs Python dependencies and runs `PYTHONPATH=backend:collector python -m unittest discover -s backend/tests -v`.
- `collector-tests`: installs Python dependencies and runs `PYTHONPATH=backend:collector python -m unittest discover -s collector/tests -v`.
- `python-compile`: runs `python3 -m compileall backend collector`.
- `frontend-tests`: installs frontend dependencies with `npm ci --prefix frontend` and runs `npm test --prefix frontend`.
- `frontend-build`: installs frontend dependencies with `npm ci --prefix frontend` and runs `npm run build --prefix frontend`.
- `frontend-smoke`: installs frontend dependencies, installs Playwright Chromium, Firefox, and WebKit, then runs
  `npm run smoke --prefix frontend`.
- `compose-validation`: runs `docker compose -f podman-compose.yml config >/dev/null`.

`server-kit/tests` is not part of the current CI workflow. Run it locally after changing `server-kit/` scripts or USB
packaging docs:

```bash
python3 -m unittest discover -s server-kit/tests -v
```

Also run shell syntax checks for the workstation wrapper, top-level deploy entrypoint, and update script:

```bash
bash -n server-kit/prepare-usb-kit.sh server-kit/deploy-from-usb.sh server-kit/scripts/07-update-bitcoin-risk-brief-from-usb.sh
```

For packaging changes, run a local smoke package to a temporary directory and verify `manifest.txt`, `SHA256SUMS`, and no
staged `.env`, secret `.env.*` files, or `.git` inside `project/bitcoin-risk-brief/`. The non-secret templates
`.env.example` and `.env.production.example` are expected project files.

Branch protection expectations for `main`:

- Require a pull request before merging changes into `main`.
- Require status checks to pass before merging.
- Require branches to be up to date before merging.
- Require the seven CI checks listed above.
- Restrict direct pushes to `main`; emergency direct pushes still run CI and should be fixed or reverted if any required check fails.

With those rules, a failing backend test, collector test, frontend test, frontend smoke check, frontend build, Python
compile check, or compose validation blocks promotion to `main`.

## Manual Smoke Checks

After services are running:

```bash
curl -fsS http://localhost:3001/api/health
curl -fsS http://localhost:3001/api/readiness
```

Check risk/levels consistency:

```bash
python3 - <<'PY'
import json
from urllib.request import urlopen
latest = json.load(urlopen('http://localhost:3001/api/risk/latest'))['data']
levels = json.load(urlopen('http://localhost:3001/api/risk/levels'))
print(abs(latest['risk'] - levels['meta']['current_risk']))
PY
```

The printed delta should be `0.0` or within floating-point noise.

## Browser And Device QA

Before public launch, verify the product page across the launch matrix:

- current desktop Chrome, Safari, and Firefox;
- mobile Safari on iOS;
- mobile Chrome on Android;
- narrow mobile, tablet, laptop, and wide desktop viewport widths.

The check should cover:

- first load, loading states, and API-error states;
- readiness/freshness badge and degraded-data copy;
- risk history and risk levels charts rendering non-empty and within their containers;
- waitlist form validation, success, and rate-limited/error states;
- locale switching for every enabled locale;
- localized copy fit for every enabled locale, including buttons, badges, brief panels, chart labels, waitlist states, and
  degraded/error states;
- text wrapping, spacing, contrast, and no overlapping UI at target widths.

Automated smoke checks should cover the highest-risk layout and chart failures. Manual QA can cover browser-specific
visual polish until the project has a broader e2e suite.

If issue #28 localization expansion is enabled before active traffic, repeat the launch pass for English, Russian,
Simplified Chinese (`zh`), German, French, Spanish, and Arabic. Check long localized labels in buttons, badges, chart
labels, waitlist states, degraded/error states, and mobile layouts. Arabic requires explicit `dir="rtl"` verification;
charts and numeric data should remain readable and not be visually reversed.

Current frontend QA results are recorded in [Frontend QA](frontend-qa.md).

## Documentation Hygiene

Documentation changes should keep the following files aligned:

- `docs/production-roadmap.md` for planned work and launch gates;
- `docs/data-pipeline.md` for supported data refresh paths;
- `docs/security-and-privacy.md` for current and planned security controls;
- `docs/production-readiness.md` for the deploy-time gate;
- `docs/operations.md` for operator commands.

Before launch, remove or clearly label stale assumptions from older docs. Historical files under `docs/superpowers/` can
remain as implementation history, but current operational docs should not require readers to reconcile conflicting
runtime behavior.

After implementation freeze, run a documentation and portfolio presentation pass before sharing the private repository
with external reviewers. Check that the root README, docs index, sibling product-ideas brief, GitHub
description/topics, optional screenshot or GIF, and repository hygiene reflect the implemented product rather than
future plans. Do not add open-source community files such as `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, or public issue
templates unless the repository is intentionally made public.

Before public traffic, also run a launch operations and governance checklist. Confirm that privacy/terms/disclaimer
copy, post-waitlist handling, dependency/security maintenance cadence, credential ownership, data-source terms,
SEO/social metadata, accessibility, and incident response notes are current or explicitly accepted as launch
limitations.

For the accessibility pass, check keyboard navigation, visible focus states, form labels and errors, chart context text,
color contrast, mobile text fit, and screen-reader labels for language switch, waitlist, readiness, and charts.

## Frontend Chart Bundle Budget

The frontend lazy-loads ECharts through `frontend/src/Chart.tsx`. The initial app chunk is expected to stay below
500 kB minified. The lazy chart chunk is accepted up to 650 kB minified because it contains the ECharts canvas renderer
and the small set of chart modules used by the public page. `npm run build --prefix frontend` should complete without
unexpected Vite chunk warnings.
