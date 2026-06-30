# Bitcoin Risk Brief Design

> Status: completed. Last reviewed 2026-06-30. The baseline product is implemented; production-pilot operations are
> tracked in `docs/production-readiness.md` and `docs/production-roadmap.md`.

## Goal

Build a standalone EN/RU mini-product that collects BTC market history, calculates a daily Bitcoin Risk score, stores it in TimescaleDB, and presents the latest risk state, history, levels, and brief in a focused frontend.

## Scope

The first implementation includes TimescaleDB, FastAPI backend, Python collector, React/Vite frontend, podman-compose orchestration, local waitlist capture, and operational scripts. It excludes auth, billing, multi-chart catalog expansion, and alert delivery.

## Architecture

The collector owns data acquisition and deterministic risk calculation. The backend exposes read-only API endpoints from TimescaleDB. The frontend consumes those endpoints and degrades to clear loading/error states when data is missing.
