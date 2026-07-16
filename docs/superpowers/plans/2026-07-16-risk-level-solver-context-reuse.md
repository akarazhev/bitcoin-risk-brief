# Risk-Level Solver Context Reuse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optimize `build_risk_levels()` so it builds risk-level solver context once and reuses it for min/max and target-risk price solves.

**Architecture:** Keep the change local to `backend/app/risk_levels.py`. Extract the current solver body into a private context-aware helper, keep `solve_price_for_target_risk()` as the backward-compatible public wrapper, and make `build_risk_levels()` call the private helper with its already-built `LevelContext`.

**Tech Stack:** Python 3.13, FastAPI backend package layout, `unittest`, `unittest.mock.patch`.

## Global Constraints

- Preserve the current risk methodology, `RISK_STEP`, response shape, rounding, and metadata.
- Keep `solve_price_for_target_risk(rows, stitch_validation, target_risk)` backward-compatible for existing callers.
- Keep the optimization local to risk-level computation.
- Do not add new dependencies.
- Verification must include `PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_risk.py' -v`.
- Verification must include `PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -p 'test_db_writer.py' -v`.

---

## File Structure

- Modify `backend/app/risk_levels.py`: add a private context-aware solver helper and update `build_risk_levels()` to reuse its existing `LevelContext`.
- Modify `backend/tests/test_risk.py`: add a focused regression test proving `build_risk_levels()` calls `_build_level_context()` once.
- No migration, frontend, collector implementation, or public API changes are required.

---

### Task 1: Reuse LevelContext Across Risk-Level Solves

**Files:**
- Modify: `backend/app/risk_levels.py`
- Modify: `backend/tests/test_risk.py`

**Interfaces:**
- Consumes: existing `LevelContext`, `_build_level_context(rows, stitch_validation)`, `_calculate_current_risk_from_context(context, hypothetical_price)`, `_normalize_target_risk(target_risk, context)`, `_compute_hlc3(row)`.
- Produces: private helper `_solve_price_for_target_risk_from_context(rows: list[dict[str, Any]], context: LevelContext, target_risk: float) -> float`.
- Preserves: public function `solve_price_for_target_risk(rows: list[dict[str, Any]], stitch_validation: dict[str, Any], target_risk: float) -> float`.

- [ ] **Step 1: Add the failing context-reuse test**

In `backend/tests/test_risk.py`, add this import near the existing imports:

```python
from unittest.mock import patch
```

Also add this module import near the existing `app.risk_levels` imports:

```python
import app.risk_levels as risk_levels_module
```

Then add this test method to `RiskLevelSolverTest`, after `test_risk_levels_use_canonical_risk_step`:

```python
    def test_build_risk_levels_reuses_solver_context_for_all_targets(self) -> None:
        rows = make_rows(days=1500)
        stitch_validation = {"turnover_enabled": True}

        with patch(
            "app.risk_levels._build_level_context",
            wraps=risk_levels_module._build_level_context,
        ) as build_context:
            levels = build_risk_levels(rows, stitch_validation)

        self.assertEqual(build_context.call_count, 1)
        self.assertEqual(len(levels["risk_level_rows"]), 41)
        self.assertGreater(len(levels["price_level_rows"]), 0)
```

- [ ] **Step 2: Run the focused backend test and confirm it fails for the intended reason**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_risk.RiskLevelSolverTest.test_build_risk_levels_reuses_solver_context_for_all_targets -v
```

Expected result before implementation: the test fails because `_build_level_context()` is called more than once. On the current code path it should report a call count greater than `1` because `build_risk_levels()` calls `solve_price_for_target_risk()` for min, max, and each risk step.

- [ ] **Step 3: Extract the context-aware private solver helper**

In `backend/app/risk_levels.py`, replace the current `solve_price_for_target_risk()` body with a private helper plus wrapper.

The new private helper should sit immediately before `solve_price_for_target_risk()`:

```python
def _solve_price_for_target_risk_from_context(
    rows: list[dict[str, Any]],
    context: LevelContext,
    target_risk: float,
) -> float:
    effective_target_risk = _normalize_target_risk(target_risk, context)
    current_price = _compute_hlc3(rows[-1])
    current_risk = _calculate_current_risk_from_context(context, current_price)

    low_price = current_price
    low_risk = current_risk
    high_price = current_price
    high_risk = current_risk

    if effective_target_risk < current_risk:
        for _ in range(SOLVER_MAX_EXPANSIONS):
            low_price = max(low_price * 0.5, 1.0)
            low_risk = _calculate_current_risk_from_context(context, low_price)
            if low_risk <= effective_target_risk:
                break
    elif effective_target_risk > current_risk:
        for _ in range(SOLVER_MAX_EXPANSIONS):
            high_price = high_price * 1.5
            high_risk = _calculate_current_risk_from_context(context, high_price)
            if high_risk >= effective_target_risk:
                break

    if low_price == high_price:
        return float(current_price)

    for _ in range(SOLVER_BINARY_SEARCH_STEPS):
        midpoint_price = (low_price + high_price) / 2.0
        midpoint_risk = _calculate_current_risk_from_context(context, midpoint_price)
        if midpoint_risk < effective_target_risk:
            low_price = midpoint_price
            low_risk = midpoint_risk
        else:
            high_price = midpoint_price
            high_risk = midpoint_risk

    low_distance = abs(low_risk - effective_target_risk)
    high_distance = abs(high_risk - effective_target_risk)
    return float(low_price if low_distance <= high_distance else high_price)
```

Then keep the public wrapper with the same signature and validation:

```python
def solve_price_for_target_risk(
    rows: list[dict[str, Any]],
    stitch_validation: dict[str, Any],
    target_risk: float,
) -> float:
    if not rows:
        raise ValueError("rows must not be empty")

    context = _build_level_context(rows, stitch_validation)
    return _solve_price_for_target_risk_from_context(rows, context, target_risk)
```

- [ ] **Step 4: Update `build_risk_levels()` to reuse its existing context**

In `backend/app/risk_levels.py`, change the min/max solves from:

```python
    minimum_price = solve_price_for_target_risk(rows, stitch_validation, 0.0)
    maximum_price = solve_price_for_target_risk(rows, stitch_validation, 1.0)
```

to:

```python
    minimum_price = _solve_price_for_target_risk_from_context(rows, context, 0.0)
    maximum_price = _solve_price_for_target_risk_from_context(rows, context, 1.0)
```

Then change the risk-level row price solve from:

```python
            "price": float(solve_price_for_target_risk(rows, stitch_validation, step_index * RISK_STEP)),
```

to:

```python
            "price": float(_solve_price_for_target_risk_from_context(rows, context, step_index * RISK_STEP)),
```

Do not change the calculation of `evaluation_date`, `current_price`, `current_risk`, `price_step`, `price_level_rows`, `risk_level_rows`, or returned metadata.

- [ ] **Step 5: Run the focused context-reuse test and confirm it passes**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest backend.tests.test_risk.RiskLevelSolverTest.test_build_risk_levels_reuses_solver_context_for_all_targets -v
```

Expected result after implementation: `OK`.

- [ ] **Step 6: Run the issue-required backend risk tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -p 'test_risk.py' -v
```

Expected result: all tests in `backend/tests/test_risk.py` pass, including the existing solver accuracy test and the new context-reuse regression test.

- [ ] **Step 7: Run the issue-required collector snapshot tests**

Run:

```bash
PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -p 'test_db_writer.py' -v
```

Expected result: all tests in `collector/tests/test_db_writer.py` pass, proving snapshot persistence remains compatible with the unchanged public risk-level payload shape.

- [ ] **Step 8: Review the final diff**

Run:

```bash
git diff -- backend/app/risk_levels.py backend/tests/test_risk.py
```

Check that the diff only:

```text
- Adds the private helper `_solve_price_for_target_risk_from_context`.
- Leaves public `solve_price_for_target_risk()` signature unchanged.
- Changes `build_risk_levels()` to call the private helper with its existing `context`.
- Adds one focused context-reuse test.
```

- [ ] **Step 9: Commit the implementation**

Run:

```bash
git add backend/app/risk_levels.py backend/tests/test_risk.py
git commit -m "perf: reuse risk-level solver context"
```

Commit only the implementation and test files. Do not include this plan file in the implementation commit unless the repository owner explicitly wants planning artifacts committed with code.

---

## Self-Review Notes

- Spec coverage: the plan preserves public APIs, keeps the optimization local, adds the requested focused test, and runs both required verification commands.
- Placeholder scan: no placeholder markers, omitted edge handling, or unspecified tests remain.
- Type consistency: `_solve_price_for_target_risk_from_context(rows, context, target_risk)` uses the existing `LevelContext` and returns the same `float` value as `solve_price_for_target_risk()`.
