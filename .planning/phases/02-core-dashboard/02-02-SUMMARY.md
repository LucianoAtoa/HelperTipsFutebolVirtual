---
phase: 02-core-dashboard
plan: "02"
subsystem: dashboard
tags: [dash, dark-theme, ag-grid, callbacks, roi, kpi, charts]
dependency_graph:
  requires:
    - 02-01  # queries.py data layer and Dash deps
  provides:
    - helpertips/dashboard.py  # complete Dash app with layout and callbacks
    - tests/test_dashboard.py  # structural and formatting tests
  affects:
    - dashboard runtime (python -m helpertips.dashboard starts on port 8050)
tech_stack:
  added: []
  patterns:
    - "Dash 4.x @callback decorator (not app.callback) for standalone module pattern"
    - "AG Grid legacy theme via dashGridOptions={'theme': 'legacy'} + ag-theme-alpine-dark className"
    - "Master callback: 8 inputs -> 13 outputs — all dashboard state in one callback"
    - "Per-callback DB connection (open in function body, close in finally)"
    - "getRowStyle styleConditions for conditional row highlight without JS"
    - "received_at serialized to str() inside callback — datetime not JSON-serializable"
key_files:
  created:
    - helpertips/dashboard.py
    - tests/test_dashboard.py
  modified: []
decisions:
  - "received_at datetime objects converted to str() inside callback before returning rowData — psycopg2 returns Python datetime, AG Grid expects JSON-serializable values"
  - "Tasks 1 and 2 committed together — dashboard.py layout and callbacks are one atomic file"
metrics:
  duration: "3 min"
  completed: "2026-04-03"
  tasks: 3
  files: 2
---

# Phase 02 Plan 02: Dashboard Layout and Callbacks Summary

**One-liner:** Dash 4.x dark-themed dashboard with DARKLY theme, 5 KPI cards, multi-filter callbacks, AG Grid history table with amber pending-row highlighting, ROI card with Gale toggle, and auto-refresh every 60s.

## What Was Built

`helpertips/dashboard.py` (442 lines) — complete Dash application runnable via `python -m helpertips.dashboard`:

- **App initialization:** `dbc.themes.DARKLY` + `dag.themes.BASE` + `dag.themes.ALPINE` in `external_stylesheets`. App title "HelperTips — Futebol Virtual".
- **KPI cards:** 5 cards (total, greens, reds, pendentes, win rate) with Bootstrap color classes (text-success, text-danger, text-warning, text-info).
- **Filters row:** liga dropdown, entrada dropdown, DatePickerRange (`DD/MM/YYYY`), reset button.
- **ROI simulation card:** stake input (default R$10), odd input (default 1.90), Gale toggle switch. Displays lucro/prejuizo, ROI %, total investido.
- **Charts:** Bar chart (GREEN/RED/Pendente counts) + horizontal bar chart (win rate per liga), both with `plotly_dark` template and transparent background.
- **AG Grid:** `ag-theme-alpine-dark` class, `dashGridOptions={"theme": "legacy"}` (required for Dash-AG-Grid 31+), 20 rows/page, all 6 columns sortable/resizable. Amber row highlighting for pending signals via `getRowStyle.styleConditions`.
- **Auto-refresh:** `dcc.Interval(interval=60_000)` fires master callback every 60s.

**Two callbacks:**
1. **Master update** (8 inputs -> 13 outputs): fires on any filter, ROI input, or interval change. Opens DB connection per invocation in `try/finally`.
2. **Reset filters** (prevent_initial_call=True): clears liga, entrada, date range to None.

`tests/test_dashboard.py` (204 lines) — 6 pure-Python tests, no DB required:

- `test_app_layout_renders` — layout not None, title correct (DASH-01)
- `test_layout_has_required_component_ids` — all 19 component IDs present (DASH-01, DASH-02)
- `test_kpi_formatting_winrate_with_results` — 60%/100%/0% formatting
- `test_kpi_formatting_winrate_no_results` — em dash (—) when no resolved signals
- `test_kpi_formatting_roi_strings` — signed R$/% string format with +/- prefix
- `test_gale_accumulated_cost_model` — accumulated Gale stake: 10/30/70/150 at tentativa 1/2/3/4

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 & 2 | Dashboard layout + callbacks (dashboard.py) | 99b0395 |
| 3 | Structural and formatting tests (test_dashboard.py) | 92e0ee2 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Serialize received_at datetime before returning rowData**
- **Found during:** Task 2 — verifying the callback logic
- **Issue:** psycopg2 returns `received_at` as Python `datetime` objects. AG Grid's `rowData` must be JSON-serializable. Returning datetime objects would cause a Dash serialization error at runtime.
- **Fix:** Added `str(row["received_at"])` conversion for each history row before the return statement.
- **Files modified:** helpertips/dashboard.py (inside `update_dashboard` callback)
- **Commit:** 99b0395

**2. [Rule 1 - Minor] Tasks 1 and 2 executed in a single file commit**
- The plan separates "create layout" (Task 1) and "wire callbacks" (Task 2) as distinct tasks, but both target the same file `helpertips/dashboard.py`. The layout and callbacks were written together atomically. Task 2 acceptance criteria verified against the same file.

## Known Stubs

None — all data comes from live DB queries via `get_connection()`. ROI values, KPI cards, charts, and table are all wired to real data from `helpertips/queries.py`.

## Self-Check

Checking created files and commits exist...

## Self-Check: PASSED

- FOUND: helpertips/dashboard.py
- FOUND: tests/test_dashboard.py
- FOUND: .planning/phases/02-core-dashboard/02-02-SUMMARY.md
- FOUND: commit 99b0395 (layout + callbacks)
- FOUND: commit 92e0ee2 (tests)
