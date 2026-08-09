# Repository Guidelines

## Project Structure & Module Organization

This repository contains a small production-oriented Bitcoin risk product. `backend/app/` is the FastAPI API, with unit tests in `backend/tests/`. `collector/collector/` owns CSV refresh, CoinMarketCap integration, database writes, and risk recomputation support, with tests in `collector/tests/`. `frontend/src/` is the React/Vite public UI and API client; `frontend/src/App.test.tsx` covers UI behavior. Operational assets live in `scripts/`, `migrations/`, `docs/`, and `podman-compose.yml`. The documentation layout is indexed in [docs/README.md](docs/README.md) and grouped into product, engineering, agents, and operations tiers. The canonical local BTC data source is `collector/btc-csv/btc_usd_daily.csv`.

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

## Required Project Context

Before implementation, read the project context that is relevant to the task:

1. `README.md`
2. `docs/operations/production-roadmap.md`
3. `docs/engineering/architecture.md`
4. `docs/superpowers/README.md`
5. a relevant current design spec under `docs/superpowers/specs/`, when one exists or the user selects one
6. a relevant current implementation plan under `docs/superpowers/plans/`, when one exists or the user selects one

Preserve the product guarantees from `README.md` and the core docs, especially the production-pilot scope, no financial
advice posture, canonical BTC CSV source, daily freshness/readiness semantics, waitlist privacy constraints, and operator
evidence requirements.

Treat old specs and plans under `docs/superpowers/` as historical execution artifacts unless a user explicitly selects
one as the active source for a new slice. Current-state claims live in `README.md`, `docs/README.md`,
`docs/engineering/architecture.md`, `docs/engineering/data-pipeline.md`, `docs/product/risk-methodology.md`,
`docs/operations/production-readiness.md`, `docs/operations/production-roadmap.md`,
`docs/operations/production-evidence-log.md`, `docs/engineering/security-and-privacy.md`, and
`docs/operations/operations.md`.

## Superpowers Workflow

Use Superpowers skills when they apply. User instructions and this `AGENTS.md` file take precedence over Superpowers
guidance when they conflict.

- Use `/plan` before implementation when scope is ambiguous, multi-step, or likely to affect several modules.
- Use `/goal` for longer-running implementation work, with a concrete outcome and verification criteria.
- For new feature or behavior design, use `superpowers:brainstorming`, then `superpowers:writing-plans`, then the
  implementation workflow below.
- For bug investigation, use `superpowers:systematic-debugging`, reproduce the failure before changing code, and use
  subagents only when failures are independent.
- For new behavior or bugfix implementation, use `superpowers:test-driven-development` when practical; add or update
  focused tests before implementation, then run the matching local verification command and any related build check.
- For implementation from a written plan, prefer `superpowers:subagent-driven-development` when multi-agent support is
  available; use a fresh implementer subagent per independent task, run a reviewer subagent after each task, close
  finished implementer and reviewer subagents, and run a final whole-branch review before completion. If multi-agent
  support is unavailable, execute the plan sequentially in the main agent while preserving review checkpoints.
- For review feedback, verify the finding before changing code, address confirmed findings, and rerun the relevant
  checks.
- Use `/review` before finalizing substantial diffs or PR-ready work.
- Before claiming work is complete, use the applicable verification workflow and report the exact checks run.
- For documentation-only changes, verify the edited files with a targeted read or diff and state that runtime tests were
  not run.

## Subagent Policy

Use parallel subagents only for independent work domains, such as unrelated failing test files, separate services, or
clearly separated documentation areas.

Do not dispatch multiple implementation subagents in parallel when they may edit overlapping files, share architectural
state, or need the same unresolved product decision.

The main agent remains responsible for:

- reading project-level context
- coordinating tasks
- resolving conflicts
- reviewing integrated diffs
- running final verification
- preserving product, data, privacy, and operational evidence constraints

## Coding Style & Naming Conventions

Python targets Python 3.13 in CI. Use four-space indentation, type hints where useful, `snake_case` for functions/modules, and `PascalCase` for Pydantic models and classes. Keep backend API routes under `/api/*` and prefer small pure helpers for risk logic. TypeScript uses ES modules, React function components, two-space indentation, single quotes, `PascalCase` components, and `camelCase` functions/state.

## Testing Guidelines

Python tests use `unittest` discovery with `PYTHONPATH=backend:collector`; name files `test_*.py` and keep tests near the service they cover. Frontend tests use Vitest and Testing Library; name UI tests `*.test.tsx`. For behavior changes, update or add focused tests and run the matching local command plus any related build check.

## Commit & Pull Request Guidelines

Recent history uses short imperative subjects, often Conventional Commit-style prefixes such as `docs:`, `feat:`, and `chore:`. Keep commits scoped, for example `docs: update operations guide` or `feat: add readiness badge state`. Pull requests should describe user-facing impact, list verification commands run, link related issues or docs, and include screenshots for frontend visual changes.

## Security & Configuration Tips

Do not commit real `.env` values, production secrets, database volumes, or ad hoc backups. Use `.env.production.example` as the production checklist and keep security, operations, and data-pipeline docs aligned when configuration behavior changes.
