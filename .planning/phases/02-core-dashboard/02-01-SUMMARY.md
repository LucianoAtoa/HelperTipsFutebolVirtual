---
phase: 02-core-dashboard
plan: 01
subsystem: database
tags: [dash, postgresql, psycopg2, roi, gale, queries, python]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: db.py get_connection/ensure_schema, signals schema with tentativa field

provides:
  - helpertips/queries.py with get_filtered_stats, get_signal_history, get_distinct_values, calculate_roi
  - Parameterized WHERE clause builder for liga/entrada/date_start/date_end filters
  - Gale and Stake Fixa ROI calculation with exponential stake accumulation
  - Dash/DBC/AgGrid dependencies installed and importable

affects: [02-core-dashboard/02-02, 02-core-dashboard/02-03]

# Tech tracking
tech-stack:
  added: [dash>=4.1,<5, dash-bootstrap-components>=2.0, dash-ag-grid>=35.2]
  patterns:
    - "_build_where() helper centralizes WHERE clause construction — all query functions reuse it"
    - "Field allowlist in get_distinct_values() prevents SQL injection via column name interpolation"
    - "calculate_roi is pure Python with no DB dependency — testable without PostgreSQL"
    - "Gale mode uses 2**N exponential formula for stake accumulation per D-06"

key-files:
  created:
    - helpertips/queries.py
    - tests/test_queries.py
  modified:
    - pyproject.toml

key-decisions:
  - "_build_where() returns (sql_fragment, params_list) tuple — avoids repeating WHERE builder in each function"
  - "calculate_roi returns rounded floats (round(x, 10)) to avoid floating-point noise in assertions"
  - "db_conn fixture cleans up BEFORE and AFTER each test — prevents pre-existing data from polluting assertions"
  - "dash-ag-grid resolved to 35.2.0 (pip latest) despite plan spec >=31.0 — no conflict"

patterns-established:
  - "Query functions accept conn as first arg — caller manages connection lifecycle"
  - "All SQL uses %s parameterized placeholders — never f-strings for values"
  - "Field name interpolation only after allowlist validation (frozenset pattern)"

requirements-completed: [DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07]

# Metrics
duration: 8min
completed: 2026-04-03
---

# Phase 02 Plan 01: Dashboard Data Layer Summary

**Dash dependencies installed + queries.py with filtered SQL, Gale ROI calculation, and 19 passing unit/integration tests**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-03T12:38:00Z
- **Completed:** 2026-04-03T12:43:22Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Installed dash 4.1.0, dash-bootstrap-components 2.0.4, dash-ag-grid 35.2.0 — all importable
- Created `helpertips/queries.py` with 4 functions: get_filtered_stats, get_signal_history, get_distinct_values, calculate_roi
- Implemented Gale ROI with correct exponential formula: GREEN at tentativa N invests `stake * (2^N - 1)`, profit `= stake * 2^(N-1) * (odd-1) - prior_losses`
- 19 tests pass: 12 DB integration tests (skip gracefully when no PostgreSQL) + 7 pure Python ROI tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Dash dependencies to pyproject.toml** - `5267987` (chore)
2. **Task 2 RED: Failing tests for queries module** - `1af0e96` (test)
3. **Task 2 GREEN: Implement queries.py data layer** - `8a6a2c3` (feat)

**Plan metadata:** (docs commit — see below)

_Note: TDD task 2 has two commits (test RED → feat GREEN)_

## Files Created/Modified

- `helpertips/queries.py` — Data layer: parameterized filtered queries + pure Python ROI calculation
- `tests/test_queries.py` — 19 tests covering all query functions and ROI modes
- `pyproject.toml` — Added dash, dash-bootstrap-components, dash-ag-grid dependencies

## Decisions Made

- `_build_where()` private helper centralizes WHERE clause construction — called by both get_filtered_stats and get_signal_history without code duplication
- `get_distinct_values` validates field name against `frozenset({"liga", "entrada"})` before interpolating into SQL — PostgreSQL does not support parameterized column names
- `calculate_roi` uses `round(x, 10)` on all return values — avoids pytest.approx comparison noise from floating point accumulation
- `db_conn` fixture truncates signals table BEFORE yielding (not just after) — prevents pre-existing real data from causing assertion failures

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] db_conn fixture only cleaned up after tests, not before**
- **Found during:** Task 2 GREEN (first test run)
- **Issue:** First test failed with `assert 6 == 3` because the live DB had 3 existing signals from real listener runs
- **Fix:** Added `DELETE FROM signals` before `yield conn` in the fixture setup phase
- **Files modified:** tests/test_queries.py
- **Verification:** All 19 tests pass with clean-slate each time
- **Committed in:** 8a6a2c3 (Task 2 feat commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix necessary for correct test isolation. No scope creep.

## Issues Encountered

- `pip` not found in shell — used `pip3` instead. Install succeeded normally.
- dash-ag-grid resolved to version 35.2.0 (pip latest) despite plan specifying `>=31.0`. Version constraint satisfied, no issue.

## Known Stubs

None — all query functions execute real SQL against the database. calculate_roi operates on provided data. No hardcoded values, placeholder text, or unwired components.

## Next Phase Readiness

- `helpertips/queries.py` provides complete data API for dashboard callbacks in 02-02
- All 4 functions match the interface contract defined in the plan
- Dash + DBC + AgGrid installed and importable — dashboard scaffolding can proceed immediately
- No blockers

## Self-Check: PASSED

- helpertips/queries.py — FOUND
- tests/test_queries.py — FOUND
- .planning/phases/02-core-dashboard/02-01-SUMMARY.md — FOUND
- Commit 5267987 — FOUND (chore: dash deps)
- Commit 1af0e96 — FOUND (test: failing tests RED)
- Commit 8a6a2c3 — FOUND (feat: queries.py GREEN)

---
*Phase: 02-core-dashboard*
*Completed: 2026-04-03*
