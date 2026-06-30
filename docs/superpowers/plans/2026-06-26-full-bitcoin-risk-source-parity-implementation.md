# Full Bitcoin Risk Source Parity Implementation Plan

> Status: superseded. Last reviewed 2026-06-30. This CoinGecko-oriented plan is not a current implementation guide.
> Current data-source behavior is the canonical CoinMarketCap CSV source with public/manual CSV intake and optional CMC
> API delta refresh.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** add early BTC CSV bootstrap, source stitch validation, and merged backfill to Bitcoin Risk Brief.

**Architecture:** Add a focused backend source module for CSV loading, CoinGecko row normalization, stitch validation, and risk dataset construction. Keep collector orchestration thin: backfill uses the source-parity dataset builder, rolling refresh recalculates from persisted OHLCV rows. Store diagnostics in existing validation JSON; no schema migration is required.

**Tech Stack:** Python 3.13, FastAPI modules imported by collector through `PYTHONPATH`, asyncpg, TimescaleDB, unittest.

---

### Task 1: Source Parity Tests

**Files:**
- Create: `backend/tests/test_risk_sources.py`

- [ ] Write a failing test that `load_early_btc_history("collector/btc-csv")` returns daily rows from `2010-07-13` through `2013-12-31` with no gaps.
- [ ] Write a failing test that `build_merged_risk_dataset` merges CSV plus synthetic CoinGecko rows from `2014-01-01`, returns gap-free rows, disables turnover without overlap/manual audit, and emits bounded risk points.
- [ ] Write a failing test that manual audit signoff enables turnover when there is no overlap.
- [ ] Run `PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_risk_sources -v` and confirm failures before implementation.

### Task 2: Source Module Implementation

**Files:**
- Create: `backend/app/risk_sources.py`
- Create: `collector/btc-csv/*.csv`

- [ ] Copy the four early BTC CSV files from `crypto-scout-analytics/collector/btc-csv`.
- [ ] Implement CSV loading with header normalization and strict daily validation.
- [ ] Implement CoinGecko market-chart daily row normalization.
- [ ] Implement source stitch validation with no-overlap provisional/manual-audit behavior.
- [ ] Implement `build_merged_risk_dataset(csv_dir, coingecko_market_chart, manual_audit_signoff=None)` returning `source_rows`, `risk_points`, `validation`, `stitch_validation`, and `validation_summary`.
- [ ] Re-run targeted source tests and confirm green.

### Task 3: Collector Storage Tests

**Files:**
- Modify: `collector/tests/test_history_merge.py`

- [ ] Add a failing test that source rows preserve `source='csv'` or `source='coingecko'` when written through `write_ohlcv_rows` record construction.
- [ ] Add a failing test for validation payload containing `stitch_validation` and `methodology_version`.
- [ ] Run collector tests and confirm failures before implementation.

### Task 4: Collector Wiring Implementation

**Files:**
- Modify: `collector/collector/db_writer.py`
- Modify: `collector/collector/main.py`
- Modify: `collector/collector/history.py`

- [ ] Let OHLCV writes preserve each row's `source`.
- [ ] Add pure record builders so tests can verify records without a live DB pool.
- [ ] Add `backfill_once` path that builds the merged CSV+CoinGecko dataset and writes all records.
- [ ] Keep `run-now` as persisted-history refresh.
- [ ] Store stitch diagnostics in `validation_json`.

### Task 5: Docs and Verification

**Files:**
- Modify: `README.md`

- [ ] Document that canonical backfill now includes CSV bootstrap and stitch validation.
- [ ] Run `./scripts/manage.sh test-python`.
- [ ] Run `python3 -m compileall backend collector`.
- [ ] Run `npm test --prefix frontend`.
- [ ] Run `npm run build --prefix frontend`.
- [ ] Run `./scripts/manage.sh validate`.
- [ ] Run container build for backend, collector, and frontend.
- [ ] Run live smoke for `/api/risk/latest` and `/api/risk/levels`.
- [ ] Commit local changes.
