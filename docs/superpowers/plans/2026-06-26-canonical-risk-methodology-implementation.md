# Canonical Risk Methodology Implementation Plan

> Status: completed, historical. Last reviewed 2026-06-30. Unchecked boxes are stale tracking; canonical risk math,
> risk-level solving, source OHLCV reads, and validation metadata are implemented. Current CI targets Python 3.13.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** replace the mini-product risk calculation and risk-level heuristic with the canonical `crypto-scout-analytics` methodology while preserving frontend API compatibility.

**Architecture:** Keep the mini-product small, but port the canonical calculation units into `backend/app/risk.py` and `backend/app/risk_levels.py`. The collector writes refreshed OHLCV first, then recalculates over persisted history. The backend level endpoint reads OHLCV source rows and returns solved risk levels with compatibility mapping to `price_usd`.

**Tech Stack:** Python 3.13, FastAPI, asyncpg, TimescaleDB/PostgreSQL, unittest.

---

### Task 1: Canonical Formula Tests

**Files:**
- Modify: `backend/tests/test_risk.py`

- [ ] Add assertions for canonical robust-z constants and weights.
- [ ] Add coverage that turnover-disabled mode uses the two-factor fallback and stores `turnover=None`.
- [ ] Add coverage that a final price shock increases latest risk after the canonical minimum history is present.
- [ ] Run `PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_risk -v` and confirm the new expectations fail before implementation.

### Task 2: Canonical Formula Implementation

**Files:**
- Modify: `backend/app/risk.py`

- [ ] Port canonical helpers for EMA, rolling standard deviation, robust rolling z-scores, and sigmoid.
- [ ] Implement `calculate_risk_series(rows, turnover_enabled=True)` using canonical weights and returning existing `RiskPoint` objects.
- [ ] Preserve `classify_risk` and existing validation behavior for required OHLCV fields.
- [ ] Re-run `PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_risk -v` and confirm green.

### Task 3: Canonical Risk Level Solver Tests

**Files:**
- Modify: `backend/tests/test_risk.py`

- [ ] Add coverage for risk-level rows at `0.025` risk increments.
- [ ] Add coverage that a higher target risk solves to a higher hypothetical price and verifies through `calculate_current_risk_for_price`.
- [ ] Run the targeted test module and confirm failures before implementation.

### Task 4: Canonical Risk Level Solver Implementation

**Files:**
- Modify: `backend/app/risk_levels.py`
- Modify: `backend/app/repository.py`
- Modify: `backend/app/main.py`

- [ ] Port the canonical level context and binary-search solver.
- [ ] Add a repository query for source OHLCV rows.
- [ ] Change `/api/risk/levels` to calculate from source rows and return compatibility-shaped `data`.
- [ ] Re-run targeted backend tests.

### Task 5: Collector Full-History Recalculation Tests

**Files:**
- Create: `collector/tests/test_history_merge.py`

- [ ] Add coverage that fetched rows override persisted rows by date.
- [ ] Add coverage that merged rows stay sorted and duplicate-free.
- [ ] Run collector tests and confirm failures before implementation.

### Task 6: Collector Full-History Recalculation Implementation

**Files:**
- Modify: `collector/collector/db_writer.py`
- Modify: `collector/collector/main.py`

- [ ] Add persisted OHLCV loading and pure row merge helper.
- [ ] Write refreshed OHLCV before risk calculation.
- [ ] Calculate risk on merged persisted history.
- [ ] Store validation JSON with canonical methodology metadata.
- [ ] Re-run collector tests.

### Task 7: Verification and Commit

- [ ] Run `./scripts/manage.sh test-python`.
- [ ] Run `python3 -m compileall backend collector`.
- [ ] Run `npm test --prefix frontend`.
- [ ] Run `npm run build --prefix frontend`.
- [ ] Run `./scripts/manage.sh validate`.
- [ ] Review `git diff`.
- [ ] Commit local changes with conventional commits.
