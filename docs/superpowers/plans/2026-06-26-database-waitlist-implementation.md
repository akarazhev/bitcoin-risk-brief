# Database Waitlist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist frontend waitlist submissions in PostgreSQL/TimescaleDB.

**Architecture:** Add a small backend validation module and repository upsert, a database table in the bootstrap migration, and a frontend API call from the existing waitlist form.

**Tech Stack:** FastAPI, asyncpg, PostgreSQL/TimescaleDB, React/Vite/Vitest.

---

### Task 1: Backend Validation And API

**Files:**
- Create: `backend/app/waitlist.py`
- Modify: `backend/app/repository.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_waitlist.py`

- [ ] Write failing tests for email normalization, Telegram normalization, invalid contact rejection, and repository upsert SQL behavior with a fake pool.
- [ ] Implement validation helpers and `upsert_waitlist_lead`.
- [ ] Add `POST /api/waitlist`.
- [ ] Run backend tests.

### Task 2: Schema And Docs

**Files:**
- Modify: `migrations/001_initial_schema.sql`
- Modify: `README.md`
- Modify: `.gitignore`

- [ ] Add `waitlist_leads` table with constraints and indexes.
- [ ] Document the endpoint and lead storage behavior.
- [ ] Ignore `.idea/` without deleting local IDE files.

### Task 3: Frontend Submission

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`

- [ ] Write failing test that the waitlist form posts to `/api/waitlist`.
- [ ] Add `joinWaitlist` API helper and form pending/success/error states.
- [ ] Run frontend tests and build.

### Task 4: Verification And Commits

- [ ] Run Python tests and compileall.
- [ ] Run frontend tests and production build.
- [ ] Validate compose config and rebuild images.
- [ ] Smoke-test `POST /api/waitlist` against the running stack.
- [ ] Commit docs/backend/schema and frontend changes locally.
