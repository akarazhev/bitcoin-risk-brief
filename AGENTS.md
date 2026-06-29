# Repository Guidelines

## Project Structure & Module Organization

This repository contains a small production-oriented Bitcoin risk product. `backend/app/` is the FastAPI API, with unit tests in `backend/tests/`. `collector/collector/` owns CSV refresh, CoinMarketCap integration, database writes, and risk recomputation support, with tests in `collector/tests/`. `frontend/src/` is the React/Vite public UI and API client; `frontend/src/App.test.tsx` covers UI behavior. Operational assets live in `scripts/`, `migrations/`, `docs/`, and `podman-compose.yml`. The canonical local BTC data source is `collector/btc-csv/btc_usd_daily.csv`.

## Build, Test, and Development Commands

Use `cp .env.example .env` before local container work. Key commands:

- `./scripts/manage.sh validate`: validate the compose configuration.
- `./scripts/manage.sh start`: build and start TimescaleDB, collector, backend, and frontend.
- `./scripts/manage.sh migrate`: apply `migrations/001_initial_schema.sql`.
- `./scripts/manage.sh backfill`: import the bundled BTC CSV into TimescaleDB.
- `./scripts/manage.sh run-now`: refresh from CoinMarketCap when configured, then import.
- `./scripts/manage.sh test-python`: run backend and collector unit tests.
- `npm test --prefix frontend`: run Vitest frontend tests.
- `npm run build --prefix frontend`: type-check and build the frontend.

## Coding Style & Naming Conventions

Python targets Python 3.13 in CI. Use four-space indentation, type hints where useful, `snake_case` for functions/modules, and `PascalCase` for Pydantic models and classes. Keep backend API routes under `/api/*` and prefer small pure helpers for risk logic. TypeScript uses ES modules, React function components, two-space indentation, single quotes, `PascalCase` components, and `camelCase` functions/state.

## Testing Guidelines

Python tests use `unittest` discovery with `PYTHONPATH=backend:collector`; name files `test_*.py` and keep tests near the service they cover. Frontend tests use Vitest and Testing Library; name UI tests `*.test.tsx`. For behavior changes, update or add focused tests and run the matching local command plus any related build check.

## Commit & Pull Request Guidelines

Recent history uses short imperative subjects, often Conventional Commit-style prefixes such as `docs:`, `feat:`, and `chore:`. Keep commits scoped, for example `docs: update operations guide` or `feat: add readiness badge state`. Pull requests should describe user-facing impact, list verification commands run, link related issues or docs, and include screenshots for frontend visual changes.

## Security & Configuration Tips

Do not commit real `.env` values, production secrets, database volumes, or ad hoc backups. Use `.env.production.example` as the production checklist and keep security, operations, and data-pipeline docs aligned when configuration behavior changes.
