# Cold Page Load Progressive Risk Levels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Speed up cold public page loads by rendering the first viewport without chart endpoints and serving `/api/risk/levels` from a persisted collector-generated snapshot.

**Architecture:** Split the page data model into core data (`latest`, `brief`, `readiness`) and chart data (`history`, `levels`). Add a persisted `risk_level_snapshots` table populated by the collector after every import/recompute, then make the backend read that snapshot first and use the existing expensive solver only as a local/dev fallback when no snapshot exists.

**Tech Stack:** FastAPI, asyncpg, PostgreSQL/TimescaleDB SQL migrations, Python `unittest`, React/Vite, Vitest, Testing Library.

---

## Current Context

- Issue: GitHub `#33`, "Speed up cold page load with progressive rendering and precomputed risk levels".
- Current frontend gate: `frontend/src/App.tsx` fetches `latest`, `history`, `levels`, `brief`, and `readiness` inside one `Promise.all`, then shows `Loading risk data...` until all five resolve.
- Current expensive backend path: `backend/app/main.py::_produce_risk_levels_payload()` calls `fetch_ohlcv_history()` and `build_risk_levels()` during the request/cache-build path.
- Existing persistence pattern to mirror: `brief_snapshots` table, `collector/collector/db_writer.py::write_brief()`, and `backend/app/repository.py::fetch_latest_brief()`.
- Existing migration runner only applies `migrations/001_initial_schema.sql` in `scripts/manage.sh migrate`. Add a new migration and update the runner so existing deployments can apply additive migrations.

## Files To Modify

- Create: `migrations/002_risk_level_snapshots.sql`
- Modify: `scripts/manage.sh`
- Modify: `backend/app/risk_levels.py`
- Modify: `backend/app/repository.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_public_cache_warmup.py`
- Modify: `collector/collector/db_writer.py`
- Modify: `collector/collector/main.py`
- Modify: `collector/tests/test_db_writer.py`
- Modify: `collector/tests/test_scheduled_refresh.py`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/App.css`
- Modify: `docs/api-reference.md`
- Modify: `docs/data-pipeline.md`

## Task 1: Add The Risk-Level Snapshot Schema

**Files:**
- Create: `migrations/002_risk_level_snapshots.sql`
- Modify: `scripts/manage.sh`

- [ ] **Step 1: Create the migration**

Create `migrations/002_risk_level_snapshots.sql`:

```sql
CREATE TABLE IF NOT EXISTS risk_level_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    as_of TIMESTAMPTZ NOT NULL,
    snapshot_version TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (as_of, snapshot_version)
);

CREATE INDEX IF NOT EXISTS idx_risk_level_snapshots_as_of_desc
    ON risk_level_snapshots (as_of DESC);
```

- [ ] **Step 2: Update the migration runner**

In `scripts/manage.sh`, replace the single-file `migrate)` body:

```bash
migrate)
  ${COMPOSE} -f "${COMPOSE_FILE}" exec timescaledb psql -U postgres -d bitcoin_risk_brief -f /docker-entrypoint-initdb.d/001_initial_schema.sql
  ;;
```

with an ordered migration loop:

```bash
migrate)
  for migration in migrations/*.sql; do
    name="$(basename "${migration}")"
    ${COMPOSE} -f "${COMPOSE_FILE}" exec timescaledb \
      psql -U postgres -d bitcoin_risk_brief \
      -f "/docker-entrypoint-initdb.d/${name}"
  done
  ;;
```

This keeps the existing container mount path and lets `./scripts/manage.sh migrate` apply both `001` and `002` to an existing database.

- [ ] **Step 3: Verify shell syntax**

Run:

```bash
bash -n scripts/manage.sh
```

Expected: exit code `0`.

- [ ] **Step 4: Commit if commits are allowed in the goal run**

```bash
git add migrations/002_risk_level_snapshots.sql scripts/manage.sh
git commit -m "feat: add risk level snapshot migration"
```

## Task 2: Add Backend Snapshot Fetching And Shared Payload Shaping

**Files:**
- Modify: `backend/app/risk_levels.py`
- Modify: `backend/app/repository.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_public_cache_warmup.py`

- [ ] **Step 1: Add a failing backend test for the persisted path**

In `backend/tests/test_public_cache_warmup.py`, add this test to `PublicPayloadSchemaRegressionTest`:

```python
    async def test_risk_levels_payload_uses_persisted_snapshot_without_solver(self) -> None:
        snapshot = {
            "data": [{"risk": 0.35, "price_usd": 82000.0}],
            "meta": {
                "base": {"timestamp": "2026-06-26T00:00:00+00:00", "risk": 0.7},
                "methodology_version": "crypto-scout-canonical-v1",
                "evaluation_date": "2026-06-26",
                "current_price": 100000.0,
                "current_risk": 0.7,
                "turnover_enabled": False,
                "risk_step": 0.025,
                "source_row_count": 5827,
            },
        }

        async def fake_snapshot(_pool):
            return snapshot

        def fail_solver(_rows, _validation):
            raise AssertionError("request path must not call build_risk_levels when a snapshot exists")

        self.patch_main("get_pool", lambda: object())
        self.patch_main("fetch_latest_risk_level_snapshot", fake_snapshot)
        self.patch_main("build_risk_levels", fail_solver)

        payload, status = await main._produce_risk_levels_payload()

        self.assertEqual(status, 200)
        self.assertEqual(payload, snapshot)
```

- [ ] **Step 2: Run the failing backend test**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache_warmup.PublicPayloadSchemaRegressionTest.test_risk_levels_payload_uses_persisted_snapshot_without_solver -v
```

Expected: FAIL because `fetch_latest_risk_level_snapshot` is not imported or used yet.

- [ ] **Step 3: Add a shared public payload adapter**

In `backend/app/risk_levels.py`, add this function near `build_risk_levels()`:

```python
def build_risk_levels_public_payload(
    *,
    latest: dict[str, Any],
    levels: dict[str, Any],
    source_row_count: int,
) -> dict[str, Any]:
    return {
        "data": [
            {"risk": row["risk"], "price_usd": round(row["price"], 2)}
            for row in levels["risk_level_rows"]
        ],
        "meta": {
            "base": latest,
            "methodology_version": METHODOLOGY_VERSION,
            "evaluation_date": levels["evaluation_date"].isoformat(),
            "current_price": levels["current_price"],
            "current_risk": levels["current_risk"],
            "turnover_enabled": levels["turnover_enabled"],
            "risk_step": RISK_STEP,
            "source_row_count": source_row_count,
        },
    }
```

Keep the response shape identical to the current `/api/risk/levels` output.

- [ ] **Step 4: Add repository snapshot read**

In `backend/app/repository.py`, add:

```python
async def fetch_latest_risk_level_snapshot(pool: asyncpg.Pool) -> dict[str, Any] | None:
    row = await pool.fetchrow(
        """
        SELECT payload_json
        FROM risk_level_snapshots
        ORDER BY as_of DESC
        LIMIT 1
        """
    )
    if not row:
        return None
    payload = row["payload_json"]
    return json.loads(payload) if isinstance(payload, str) else dict(payload)
```

- [ ] **Step 5: Use the snapshot first in the backend producer**

In `backend/app/main.py`:

1. Update imports:

```python
from app.repository import (
    fetch_latest_brief,
    fetch_latest_risk,
    fetch_latest_risk_level_snapshot,
    fetch_latest_validation,
    fetch_ohlcv_history,
    fetch_previous_risk,
    fetch_public_data_version,
    fetch_risk_history,
    upsert_waitlist_lead,
)
```

2. Update the risk levels import:

```python
from app.risk_levels import build_risk_levels, build_risk_levels_public_payload
```

3. Replace `_produce_risk_levels_payload()` with:

```python
async def _produce_risk_levels_payload() -> tuple[dict[str, Any], int]:
    pool = get_pool()
    persisted = await fetch_latest_risk_level_snapshot(pool)
    if persisted is not None:
        return persisted, 200

    latest = await fetch_latest_risk(pool)
    source_rows = await fetch_ohlcv_history(pool)
    if latest is None or len(source_rows) < 2:
        raise HTTPException(status_code=404, detail="Risk source data has not been collected yet")

    turnover_enabled = bool(latest["turnover_enabled"])
    levels = build_risk_levels(source_rows, {"turnover_enabled": turnover_enabled})
    return build_risk_levels_public_payload(
        latest=latest,
        levels=levels,
        source_row_count=len(source_rows),
    ), 200
```

This keeps the fallback for local/dev or missing snapshots while production should hit the persisted branch.

- [ ] **Step 6: Update the existing shape test to exercise fallback intentionally**

In `backend/tests/test_public_cache_warmup.py::test_risk_levels_payload_shape_is_unchanged`, add a fake missing snapshot before calling the producer:

```python
        async def no_snapshot(_pool):
            return None
```

and patch it:

```python
        self.patch_main("fetch_latest_risk_level_snapshot", no_snapshot)
```

Leave the rest of the existing test intact. It should still prove fallback response compatibility.

- [ ] **Step 7: Run focused backend tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_public_cache_warmup.PublicPayloadSchemaRegressionTest -v
```

Expected: PASS.

- [ ] **Step 8: Commit if commits are allowed in the goal run**

```bash
git add backend/app/risk_levels.py backend/app/repository.py backend/app/main.py backend/tests/test_public_cache_warmup.py
git commit -m "feat: serve risk levels from persisted snapshot"
```

## Task 3: Persist Risk-Level Snapshots From Collector Imports

**Files:**
- Modify: `collector/collector/db_writer.py`
- Modify: `collector/collector/main.py`
- Modify: `collector/tests/test_db_writer.py`
- Modify: `collector/tests/test_scheduled_refresh.py`

- [ ] **Step 1: Add failing writer and import tests**

In `collector/tests/test_db_writer.py`, update imports:

```python
import json
from types import SimpleNamespace
from unittest.mock import patch
```

Change:

```python
from collector.db_writer import delete_rows_after_csv_end
```

to:

```python
from collector.db_writer import delete_rows_after_csv_end, write_risk_level_snapshot
```

Update `FakePool` so it captures execute calls:

```python
class FakePool:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    async def execute(self, query: str, *params):
        self.calls.append((query, params))
        return "DELETE 1"
```

Add this test:

```python
class RiskLevelSnapshotWriterTest(unittest.IsolatedAsyncioTestCase):
    async def test_write_risk_level_snapshot_persists_public_payload(self) -> None:
        pool = FakePool()
        source_rows = [
            {
                "date": date(2026, 6, 24),
                "open": 98.0,
                "high": 102.0,
                "low": 95.0,
                "close": 100.0,
                "volume": 1_000_000.0,
                "market_cap": 100.0 * 19_000_000.0,
                "circulating_supply": 19_000_000.0,
            },
            {
                "date": date(2026, 6, 25),
                "open": 99.0,
                "high": 104.0,
                "low": 96.0,
                "close": 101.0,
                "volume": 1_000_000.0,
                "market_cap": 101.0 * 19_000_000.0,
                "circulating_supply": 19_000_000.0,
            }
        ]
        point = SimpleNamespace(
            day=date(2026, 6, 25),
            price_hlc3=100.33333333333333,
            risk=0.7,
            score=1.2,
            trend_dev=0.3,
            vol_regime=0.1,
            turnover=None,
            z_trend_dev=1.0,
            z_vol_regime=0.5,
            z_turnover=None,
            turnover_enabled=False,
        )

        with patch(
            "collector.db_writer.build_risk_levels",
            return_value={
                "risk_level_rows": [{"risk": 0.35, "price": 82000.125}],
                "evaluation_date": date(2026, 6, 25),
                "current_price": 100.33333333333333,
                "current_risk": 0.7,
                "turnover_enabled": False,
            },
        ):
            await write_risk_level_snapshot(pool, source_rows, [point])

        self.assertEqual(len(pool.calls), 1)
        query, params = pool.calls[0]
        self.assertIn("risk_level_snapshots", query)
        self.assertEqual(params[0], datetime(2026, 6, 25, tzinfo=timezone.utc))
        self.assertEqual(params[1], "crypto-scout-canonical-v1")
        payload = json.loads(params[2])
        self.assertEqual(payload["data"], [{"risk": 0.35, "price_usd": 82000.12}])
        self.assertEqual(payload["meta"]["base"]["timestamp"], "2026-06-25T00:00:00+00:00")
        self.assertEqual(payload["meta"]["base"]["model_price_usd"], 100.33333333333333)
        self.assertEqual(payload["meta"]["base"]["low_usd"], 96.0)
        self.assertEqual(payload["meta"]["base"]["high_usd"], 104.0)
        self.assertEqual(payload["meta"]["source_row_count"], 2)
```

In `collector/tests/test_scheduled_refresh.py`, add imports:

```python
from unittest.mock import AsyncMock, patch
```

Add a test to `ScheduledPublicCmcRefreshTest`:

```python
    async def test_import_csv_once_writes_risk_level_snapshot_after_recompute(self) -> None:
        pool = object()
        risk_point = SimpleNamespace(
            day=date(2026, 6, 26),
            price_hlc3=100.0,
            risk=0.7,
            score=1.0,
            trend_dev=0.2,
            vol_regime=0.1,
            turnover=None,
            z_trend_dev=1.0,
            z_vol_regime=0.5,
            z_turnover=None,
            turnover_enabled=False,
        )
        dataset = {
            "source_rows": [daily_row(date(2026, 6, 26), 100.0)],
            "risk_points": [risk_point],
            "validation": {"turnover_enabled": False},
            "validation_summary": "ok",
        }
        write_ohlcv = AsyncMock(return_value=1)
        write_risk = AsyncMock(return_value=1)
        write_validation = AsyncMock()
        write_brief = AsyncMock()
        write_levels = AsyncMock()
        delete_stale = AsyncMock(return_value={"ohlcv": 0, "risk": 0, "brief": 0, "levels": 0})

        with (
            patch.object(collector_main, "build_csv_risk_dataset", return_value=dataset),
            patch("collector.db_writer.write_ohlcv_rows", write_ohlcv),
            patch("collector.db_writer.write_risk_rows", write_risk),
            patch("collector.db_writer.write_validation", write_validation),
            patch("collector.db_writer.write_brief", write_brief),
            patch("collector.db_writer.write_risk_level_snapshot", write_levels),
            patch("collector.db_writer.delete_rows_after_csv_end", delete_stale),
        ):
            await collector_main.import_csv_once(pool, refresh_remote=False)

        write_levels.assert_awaited_once_with(pool, dataset["source_rows"], dataset["risk_points"])
```

- [ ] **Step 2: Run the failing collector tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest collector.tests.test_db_writer collector.tests.test_scheduled_refresh.ScheduledPublicCmcRefreshTest.test_import_csv_once_writes_risk_level_snapshot_after_recompute -v
```

Expected: FAIL because `write_risk_level_snapshot` does not exist and stale cleanup does not include snapshots yet.

- [ ] **Step 3: Implement the snapshot writer**

In `collector/collector/db_writer.py`, update imports:

```python
from app.risk import METHODOLOGY_VERSION, RiskPoint, classify_risk
from app.risk_levels import build_risk_levels, build_risk_levels_public_payload
```

Add these helpers after `write_brief()` or near the other persistence helpers:

```python
def _risk_point_public_payload(point: RiskPoint, source_row: dict[str, Any] | None) -> dict[str, Any]:
    payload = {
        "timestamp": as_timestamp(point.day).isoformat(),
        "price_usd": point.price_hlc3,
        "model_price_usd": point.price_hlc3,
        "low_usd": float(source_row["low"]) if source_row and "low" in source_row else None,
        "high_usd": float(source_row["high"]) if source_row and "high" in source_row else None,
        "risk": point.risk,
        "score": point.score,
        "risk_state": classify_risk(point.risk),
        "trend_dev": point.trend_dev,
        "vol_regime": point.vol_regime,
        "turnover": point.turnover,
        "z_trend_dev": point.z_trend_dev,
        "z_vol_regime": point.z_vol_regime,
        "z_turnover": point.z_turnover,
        "turnover_enabled": point.turnover_enabled,
    }
    return payload


async def write_risk_level_snapshot(
    pool: asyncpg.Pool,
    source_rows: list[dict[str, Any]],
    points: list[RiskPoint],
) -> None:
    if len(source_rows) < 2 or not points:
        return
    latest = points[-1]
    latest_source_row = source_rows[-1] if source_rows else None
    levels = build_risk_levels(source_rows, {"turnover_enabled": latest.turnover_enabled})
    payload = build_risk_levels_public_payload(
        latest=_risk_point_public_payload(latest, latest_source_row),
        levels=levels,
        source_row_count=len(source_rows),
    )
    await pool.execute(
        """
        INSERT INTO risk_level_snapshots (as_of, snapshot_version, payload_json)
        VALUES ($1, $2, $3::jsonb)
        ON CONFLICT (as_of, snapshot_version) DO UPDATE SET
          payload_json = EXCLUDED.payload_json,
          created_at = now()
        """,
        as_timestamp(latest.day),
        METHODOLOGY_VERSION,
        json.dumps(payload, default=str),
    )
```

- [ ] **Step 4: Include snapshots in stale cleanup**

In `delete_rows_after_csv_end()`, add a fourth delete:

```python
    levels_status = await pool.execute(
        """
        DELETE FROM risk_level_snapshots
        WHERE as_of > $1
        """,
        cutoff,
    )
```

Return:

```python
    return {
        "ohlcv": _parse_delete_count(ohlcv_status),
        "risk": _parse_delete_count(risk_status),
        "brief": _parse_delete_count(brief_status),
        "levels": _parse_delete_count(levels_status),
    }
```

Update `DbWriterCleanupTest.test_delete_rows_after_csv_end_removes_future_canonical_rows` expected values:

```python
        self.assertEqual(deleted, {"ohlcv": 1, "risk": 1, "brief": 1, "levels": 1})
        self.assertEqual(len(pool.calls), 4)
        self.assertIn("risk_level_snapshots", pool.calls[3][0])
```

- [ ] **Step 5: Call the writer after recompute/import**

In `collector/collector/main.py`, add `write_risk_level_snapshot` to the local import inside `import_csv_once()`:

```python
        write_risk_level_snapshot,
```

Then call it after `write_brief()`:

```python
    await write_brief(pool, dataset["risk_points"])
    await write_risk_level_snapshot(pool, dataset["source_rows"], dataset["risk_points"])
```

- [ ] **Step 6: Run focused collector tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest collector.tests.test_db_writer collector.tests.test_scheduled_refresh.ScheduledPublicCmcRefreshTest.test_import_csv_once_writes_risk_level_snapshot_after_recompute -v
```

Expected: PASS.

- [ ] **Step 7: Commit if commits are allowed in the goal run**

```bash
git add collector/collector/db_writer.py collector/collector/main.py collector/tests/test_db_writer.py collector/tests/test_scheduled_refresh.py
git commit -m "feat: persist risk level snapshots during import"
```

## Task 4: Make The Frontend Render Progressively

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/App.css`

- [ ] **Step 1: Add a deferred promise helper in the frontend test**

In `frontend/src/App.test.tsx`, add below `findPriceMetric()`:

```tsx
function deferred<T>() {
  let resolve: (value: T) => void = () => {}
  let reject: (error: Error) => void = () => {}
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve
    reject = promiseReject
  })
  return { promise, resolve, reject }
}
```

- [ ] **Step 2: Add failing progressive rendering tests**

Add these tests near the existing loading/error tests:

```tsx
test('renders main content while chart requests are still pending', async () => {
  const historyRequest = deferred<{ data: []; meta: { returned_points: number } }>()
  const levelsRequest = deferred<{ data: []; meta: { base: object } }>()
  apiMocks.fetchRiskHistory.mockReturnValueOnce(historyRequest.promise)
  apiMocks.fetchRiskLevels.mockReturnValueOnce(levelsRequest.promise)

  render(<App />)

  expect(await screen.findByText('Current risk')).toBeInTheDocument()
  expect(screen.getByText('Risk elevated')).toBeInTheDocument()
  expect(screen.queryByText('Loading risk data...')).not.toBeInTheDocument()
  expect(screen.getAllByText('Loading chart...')).toHaveLength(2)
})

test('chart request failures do not hide the current risk', async () => {
  apiMocks.fetchRiskHistory.mockRejectedValueOnce(new Error('history failed'))
  apiMocks.fetchRiskLevels.mockRejectedValueOnce(new Error('levels failed'))

  render(<App />)

  expect(await screen.findByText('Current risk')).toBeInTheDocument()
  expect(screen.getByText('Risk elevated')).toBeInTheDocument()
  expect(screen.getByText('Risk history is temporarily unavailable.')).toBeInTheDocument()
  expect(screen.getByText('Risk levels are temporarily unavailable.')).toBeInTheDocument()
  expect(screen.queryByText('Risk data is temporarily unavailable')).not.toBeInTheDocument()
})
```

- [ ] **Step 3: Run the failing frontend tests**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected: FAIL because `App.tsx` still gates rendering on history and levels and does not have chart-specific error states.

- [ ] **Step 4: Add chart state types and copy**

In `frontend/src/App.tsx`, add after `type ThresholdCallout`:

```tsx
type ChartLoadState<T> = {
  status: 'idle' | 'loading' | 'loaded' | 'error'
  data: T
  error: string | null
}
```

In English copy, add:

```tsx
    historyError: 'Risk history is temporarily unavailable.',
    levelsError: 'Risk levels are temporarily unavailable.',
```

In Russian copy, add:

```tsx
    historyError: 'История риска временно недоступна.',
    levelsError: 'Уровни риска временно недоступны.',
```

- [ ] **Step 5: Split core state from chart state**

Replace:

```tsx
  const [history, setHistory] = useState<RiskPoint[]>([])
  const [levels, setLevels] = useState<RiskLevel[]>([])
```

with:

```tsx
  const [historyState, setHistoryState] = useState<ChartLoadState<RiskPoint[]>>({
    status: 'idle',
    data: [],
    error: null,
  })
  const [levelsState, setLevelsState] = useState<ChartLoadState<RiskLevel[]>>({
    status: 'idle',
    data: [],
    error: null,
  })
```

Then derive:

```tsx
  const history = historyState.data
  const levels = levelsState.data
```

- [ ] **Step 6: Fetch only core data in the global effect**

Replace the first `useEffect()` body with:

```tsx
  useEffect(() => {
    let active = true
    Promise.all([fetchLatestRisk(), fetchBrief(), fetchReadiness()])
      .then(([latestResponse, briefResponse, readinessResponse]) => {
        if (!active) return
        setLatest(latestResponse.data)
        setBrief(briefResponse.data)
        setReadiness(readinessResponse)
      })
      .catch((err: Error) => {
        if (active) setError(err.message)
      })
    return () => {
      active = false
    }
  }, [])
```

- [ ] **Step 7: Fetch charts independently after the first viewport can render**

Add this effect after the core fetch effect:

```tsx
  useEffect(() => {
    if (!latest || !brief || !readiness) return
    let active = true

    setHistoryState({ status: 'loading', data: [], error: null })
    fetchRiskHistory()
      .then((historyResponse) => {
        if (!active) return
        setHistoryState({ status: 'loaded', data: historyResponse.data, error: null })
      })
      .catch((err: Error) => {
        if (!active) return
        setHistoryState({ status: 'error', data: [], error: err.message })
      })

    setLevelsState({ status: 'loading', data: [], error: null })
    fetchRiskLevels()
      .then((levelsResponse) => {
        if (!active) return
        setLevelsState({ status: 'loaded', data: levelsResponse.data, error: null })
      })
      .catch((err: Error) => {
        if (!active) return
        setLevelsState({ status: 'error', data: [], error: err.message })
      })

    return () => {
      active = false
    }
  }, [latest, brief, readiness])
```

This intentionally avoids using `/api/risk/history` or `/api/risk/levels` as a global page-render gate.

- [ ] **Step 8: Render chart-specific loading, error, empty, and success states**

For the history panel, replace the current conditional:

```tsx
          {history.length > 0 ? (
```

through its matching empty branch with this four-state conditional:

```tsx
          {historyState.status === 'loading' || historyState.status === 'idle' ? (
            <div className="chart-placeholder" role="status">{t.chartLoading}</div>
          ) : historyState.status === 'error' ? (
            <div className="chart-empty chart-error" role="alert">{t.historyError}</div>
          ) : history.length > 0 ? (
            <div className="chart-visual" role="img" aria-labelledby="risk-history-heading" aria-describedby="risk-history-chart-summary risk-history-chart-note">
              <Suspense fallback={<div className="chart-placeholder" role="status">{t.chartLoading}</div>}>
                <Chart option={riskOption} notMerge opts={AUTO_CHART_SIZE} onChartReady={resizeChartWhenReady} style={{ height: 360, width: '100%' }} />
              </Suspense>
            </div>
          ) : (
            <div className="chart-empty" role="status">{t.historyEmpty}</div>
          )}
```

For the levels panel, replace the current conditional:

```tsx
          {levels.length > 0 ? (
```

through its matching empty branch with:

```tsx
          {levelsState.status === 'loading' || levelsState.status === 'idle' ? (
            <div className="chart-placeholder" role="status">{t.chartLoading}</div>
          ) : levelsState.status === 'error' ? (
            <div className="chart-empty chart-error" role="alert">{t.levelsError}</div>
          ) : levels.length > 0 ? (
            <div className="chart-visual" role="img" aria-labelledby="risk-levels-heading" aria-describedby="risk-levels-chart-summary">
              <Suspense fallback={<div className="chart-placeholder" role="status">{t.chartLoading}</div>}>
                <Chart option={levelsOption} notMerge opts={AUTO_CHART_SIZE} onChartReady={resizeChartWhenReady} style={{ height: 360, width: '100%' }} />
              </Suspense>
            </div>
          ) : (
            <div className="chart-empty" role="status">{t.levelsEmpty}</div>
          )}
```

If the test output shows an accessibility warning for `risk-history-chart-note` when the chart is loaded with fewer than one history row, keep the current loaded chart branch only for `history.length > 0`; the note exists in that branch because `accessibleHistory.length > 0`.

- [ ] **Step 9: Add a visible chart error style**

Add to `frontend/src/App.css` near the existing chart state styles:

```css
.chart-error {
  border-color: rgba(255, 107, 95, 0.38);
  color: #ffb4ae;
}
```

- [ ] **Step 10: Run focused frontend tests**

Run:

```bash
npm test --prefix frontend -- App.test.tsx
```

Expected: PASS.

- [ ] **Step 11: Commit if commits are allowed in the goal run**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/App.css
git commit -m "feat: render risk page before chart data loads"
```

## Task 5: Update API And Pipeline Documentation

**Files:**
- Modify: `docs/api-reference.md`
- Modify: `docs/data-pipeline.md`

- [ ] **Step 1: Document the `/api/risk/levels` behavior**

In `docs/api-reference.md`, find the `/api/risk/levels` section. Update its operational note to state:

```markdown
`/api/risk/levels` returns the latest persisted collector-generated risk-level snapshot under normal production operation. If the snapshot is missing in local/dev data, the backend may fall back to computing the compatible payload from the available OHLCV history.
```

Do not change the documented response shape.

- [ ] **Step 2: Document snapshot persistence in the data pipeline**

In `docs/data-pipeline.md`, add a short paragraph near the collector import/recompute description:

```markdown
After each successful CSV import/recompute, the collector persists a `risk_level_snapshots` row for the latest observation. The public `/api/risk/levels` endpoint reads this snapshot so cold public requests do not run the expensive level solver on the backend request path.
```

- [ ] **Step 3: Verify docs diff**

Run:

```bash
git diff -- docs/api-reference.md docs/data-pipeline.md
```

Expected: only the intended documentation updates.

- [ ] **Step 4: Commit if commits are allowed in the goal run**

```bash
git add docs/api-reference.md docs/data-pipeline.md
git commit -m "docs: document risk level snapshot behavior"
```

## Task 6: Full Verification

**Files:**
- All changed files.

- [ ] **Step 1: Run all Python tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -v
PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend tests**

Run:

```bash
npm test --prefix frontend
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
npm run build --prefix frontend
```

Expected: PASS.

- [ ] **Step 4: Validate compose configuration**

Run:

```bash
./scripts/manage.sh validate
```

Expected: `compose config ok`.

- [ ] **Step 5: Optional local container verification if the environment supports Podman**

Run:

```bash
./scripts/manage.sh migrate
./scripts/manage.sh backfill
./scripts/manage.sh warm-public-cache
```

Expected:

- `migrate` applies `001_initial_schema.sql` and `002_risk_level_snapshots.sql`.
- `backfill` completes and writes a `risk_level_snapshots` row.
- warmup includes `GET /api/risk/levels` without invoking the expensive request-time fallback when a snapshot exists.

- [ ] **Step 6: Inspect final diff**

Run:

```bash
git diff --stat
git diff
```

Expected:

- Frontend core rendering no longer waits for `history` or `levels`.
- Chart panels have local loading, empty, and error states.
- Collector writes `risk_level_snapshots` after recompute/import.
- Backend reads persisted `/api/risk/levels` payload first and keeps fallback compatibility.
- Tests cover the issue acceptance criteria.

## Acceptance Criteria Mapping

- Frontend renders first viewport after `latest`, `brief`, and `readiness`: Task 4, tests in Step 2.
- `history` and `levels` load independently after main page is visible: Task 4, Steps 6 and 7.
- Chart panels have loading, empty, and error states: Task 4, Steps 4 and 8.
- `/api/risk/history` and `/api/risk/levels` are not global page gates: Task 4, progressive rendering test.
- Risk-level snapshot is persisted after import/recompute: Task 3, writer and import tests.
- `/api/risk/levels` serves persisted snapshot normally: Task 2, persisted-path backend test.
- API shape and cache headers remain compatible: Task 2 fallback shape test and existing public cache wrapper unchanged.
- Safe local/dev fallback remains: Task 2, `_produce_risk_levels_payload()` fallback branch and existing shape test.

## Suggested `/goal` Prompt

```text
/goal Implement GitHub issue #33 for bitcoin-risk-brief using docs/superpowers/plans/2026-07-13-cold-page-load-progressive-risk-levels.md as the execution plan. Complete the frontend progressive rendering changes and backend/collector persisted risk-level snapshot changes, add/update the tests named in the plan, and run the full verification commands from Task 6 before reporting completion.
```

## Self-Review Notes

- No endpoint response shape changes are intended.
- The expensive solver remains available only as a fallback when no persisted snapshot exists.
- The migration plan creates a new migration file and updates the migration runner so existing deployments can apply it.
- The frontend tests directly cover the perceived-load requirement: current risk stays visible while chart data is pending or failed.
