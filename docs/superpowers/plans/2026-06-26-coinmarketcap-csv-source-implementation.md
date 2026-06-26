# CoinMarketCap CSV Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** replace CoinGecko runtime collection with a CoinMarketCap CSV-first collector that updates `btc_usd_daily.csv` daily and imports it into TimescaleDB.

**Architecture:** Keep source parsing in `backend/app/risk_sources.py` because it feeds risk calculation. Add `collector/collector/coinmarketcap.py` for official CMC API fetching/parsing only. Keep orchestration in `collector/collector/main.py`: update CSV if possible, then import CSV and recalculate risk.

**Tech Stack:** Python 3.13, httpx, asyncpg, TimescaleDB, podman-compose, unittest.

---

### Task 1: CSV Dataset Tests

**Files:**
- Modify: `backend/tests/test_risk_sources.py`

- [x] Add failing tests for `load_btc_usd_daily_csv` using `collector/btc-csv/btc_usd_daily.csv`.
- [x] Add failing tests for `build_csv_risk_dataset` over the full CSV.
- [x] Verify RED with `PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_risk_sources -v`.

### Task 2: CMC API Parsing Tests

**Files:**
- Modify: `collector/tests/test_transform.py`

- [x] Replace CoinGecko transform test with CMC OHLCV historical response parsing.
- [x] Test that parsed rows include open/high/low/close/volume/market_cap/circulating_supply and `source='coinmarketcap_api'`.
- [x] Verify RED with `PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -p 'test_transform.py' -v`.

### Task 3: Source and API Implementation

**Files:**
- Modify: `backend/app/risk_sources.py`
- Create: `collector/collector/coinmarketcap.py`
- Delete: `collector/collector/coingecko.py`

- [x] Implement full CSV load/write/merge helpers.
- [x] Implement `build_csv_risk_dataset(csv_path)`.
- [x] Implement CMC API client and parser for `/v2/cryptocurrency/ohlcv/historical`.
- [x] Remove CoinGecko runtime module.

### Task 4: Collector Wiring

**Files:**
- Modify: `collector/collector/config.py`
- Modify: `collector/collector/main.py`
- Modify: `collector/collector/records.py`
- Modify: `podman-compose.yml`
- Modify: `.env.example`

- [x] Replace CoinGecko env vars with CoinMarketCap settings.
- [x] Add `./collector/btc-csv:/app/collector/btc-csv` bind mount for data-collector.
- [x] Make scheduled run update CSV when API key exists, then import full CSV into DB.
- [x] Make backfill import the CSV without network dependency.

### Task 5: Verification and Commit

- [x] Run Python tests, compileall, frontend tests/build, compose validate.
- [x] Build backend/data-collector/frontend containers.
- [x] Run `./scripts/manage.sh run-now` and verify API consistency.
- [x] Add stale-row cleanup so CSV import removes DB rows after the CSV tail.
- [x] Commit local changes.
