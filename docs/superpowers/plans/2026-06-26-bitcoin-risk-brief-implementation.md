# Bitcoin Risk Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Bitcoin Risk Brief mini-product with collector, backend, frontend, TimescaleDB, and podman-compose orchestration.

**Architecture:** A scheduled Python collector writes BTC OHLCV, risk rows, validation, and brief snapshots into TimescaleDB. A FastAPI backend exposes read-only endpoints. A React/Vite frontend renders an EN/RU risk brief with charts and waitlist capture.

**Tech Stack:** Python 3.13, FastAPI, asyncpg, httpx, APScheduler, TimescaleDB/PostgreSQL, React 19, TypeScript, Vite, ECharts, nginx, podman-compose.

---

### Task 1: Risk Calculation Core

**Files:**
- Create: `backend/app/risk.py`
- Test: `backend/tests/test_risk.py`

- [x] Write failing unit tests for monotonic risk, bounded scores, and classification.
- [ ] Implement risk calculation from daily OHLCV rows.
- [ ] Run `PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v`.

### Task 2: Collector Transform

**Files:**
- Create: `collector/collector/coingecko.py`
- Test: `collector/tests/test_transform.py`

- [x] Write failing transform tests for CoinGecko market chart rows.
- [ ] Implement deterministic merge into daily OHLCV rows.
- [ ] Run `PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -v`.

### Task 3: Backend API

**Files:**
- Create: `backend/app/main.py`, `backend/app/repository.py`, `backend/app/brief.py`, `backend/app/risk_levels.py`
- [ ] Implement `/api/health`, `/api/risk/latest`, `/api/risk/history`, `/api/risk/levels`, `/api/brief/latest`.

### Task 4: Frontend

**Files:**
- Create: `frontend/src/App.tsx`, `frontend/src/App.css`, API/types helpers, nginx config.
- [ ] Render EN/RU BTC Risk Brief with latest state, charts, levels, daily brief, and waitlist capture.

### Task 5: Ops

**Files:**
- Create: `podman-compose.yml`, Dockerfiles, migrations, `scripts/manage.sh`, README.
- [ ] Verify scripts and compose config where local dependencies allow.
