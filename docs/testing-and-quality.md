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
- database stale-row cleanup;
- database pool retry behavior;
- source preservation in database records;
- OHLCV merge helper behavior.

Frontend tests cover:

- app shell rendering;
- waitlist submission;
- no browser persistent storage for waitlist contacts.

## CI

GitHub Actions workflow: `.github/workflows/ci.yml`.

Jobs:

- Python tests and compile check.
- Frontend tests and build.
- Compose config validation.

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

## Known Build Warning

The frontend production build currently emits a Vite chunk-size warning because ECharts is bundled into the main app chunk. The build succeeds. Code-splitting ECharts is a future performance improvement, not a current correctness blocker.
