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
- security headers;
- waitlist validation and upsert behavior;
- fixed-window rate limiter behavior.

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

Frontend tests cover:

- app shell rendering;
- waitlist submission;
- no browser persistent storage for waitlist contacts.

Planned production-pilot coverage should also include:

- readiness/freshness rendering, including degraded and API-error states;
- non-empty chart rendering checks for risk history and risk levels;
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
- `compose-validation`: runs `docker compose -f podman-compose.yml config >/dev/null`.

Branch protection expectations for `main`:

- Require a pull request before merging changes into `main`.
- Require status checks to pass before merging.
- Require branches to be up to date before merging.
- Require the six CI checks listed above.
- Restrict direct pushes to `main`; emergency direct pushes still run CI and should be fixed or reverted if any required check fails.

With those rules, a failing backend test, collector test, frontend test, frontend build, Python compile check, or compose
validation blocks promotion to `main`.

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
- locale switching if enabled on the page;
- text wrapping, spacing, contrast, and no overlapping UI at target widths.

Automated smoke checks should cover the highest-risk layout and chart failures. Manual QA can cover browser-specific
visual polish until the project has a broader e2e suite.

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

## Known Build Warning

The frontend production build currently emits a Vite chunk-size warning because ECharts is bundled into the main app chunk. The build succeeds. Code-splitting ECharts is a future performance improvement, not a current correctness blocker.
