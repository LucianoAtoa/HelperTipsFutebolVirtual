---
phase: 02-core-dashboard
verified: 2026-04-03T13:01:04Z
status: human_needed
score: 11/11 automated must-haves verified
re_verification: false
human_verification:
  - test: "Open http://localhost:8050 after running `python3 helpertips/dashboard.py`. Confirm dark background (DARKLY theme), layout is vertical, all 5 KPI cards visible."
    expected: "Dark-themed dashboard loads with KPI cards showing real numbers from DB."
    why_human: "Visual rendering and dark theme appearance cannot be verified programmatically."
  - test: "Select a liga from the liga dropdown and observe whether KPI cards, charts, and history table update without clicking Apply."
    expected: "All stats, charts, and table rows update immediately to show only signals from that liga."
    why_human: "Reactive callback execution and browser DOM update require a live browser session."
  - test: "Toggle 'Com Gale' switch on, then off, and observe whether ROI values change between modes."
    expected: "ROI profit, ROI%, and total invested show different values when Gale is on vs off."
    why_human: "UI interaction state transitions require a live browser."
  - test: "Browse the history table. Locate a row without a resultado value and confirm it has amber/yellow row background."
    expected: "Pending signals (resultado IS NULL) render with #3a3000 background and #ffc107 text."
    why_human: "CSS/conditional styling in AG Grid requires visual inspection in a browser."
---

# Phase 2: Core Dashboard Verification Report

**Phase Goal:** Users can open a web dashboard and immediately answer "are these signals profitable?" with live data from PostgreSQL
**Verified:** 2026-04-03T13:01:04Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Opening the dashboard URL shows a card with total signals, greens, reds, win rate drawn from live DB | ✓ VERIFIED | `update_dashboard` callback calls `get_filtered_stats(conn)` and returns `str(total)`, `str(greens)`, `str(reds)`, `winrate` to kpi-total, kpi-greens, kpi-reds, kpi-winrate outputs |
| 2 | Selecting a liga from the filter updates all stats and charts | ✓ VERIFIED | Master callback receives `Input("filter-liga", "value")` and passes `liga` to all query calls; 13 outputs updated |
| 3 | Selecting an entrada from the filter updates all stats | ✓ VERIFIED | Master callback receives `Input("filter-entrada", "value")` and passes `entrada` to all query calls |
| 4 | ROI simulation shows profit/loss for a configurable fixed stake | ✓ VERIFIED | `calculate_roi(history, stake or 10.0, odd or 1.90, bool(gale_on))` wired to roi-profit, roi-pct, roi-invested outputs |
| 5 | Signal history table lists past signals with pagination and pending signals visually distinct | ✓ VERIFIED | AG Grid with `paginationPageSize: 20`; `getRowStyle.styleConditions` targets `!params.data.resultado` for amber highlight |
| 6 | Reset button clears all filters | ✓ VERIFIED | `reset_filters` callback with `prevent_initial_call=True` returns `None, None, None, None` to liga/entrada/start_date/end_date |
| 7 | get_filtered_stats returns correct filtered counts | ✓ VERIFIED | 5 DB integration tests pass (no filter, by liga, by entrada, combined, by date) — all 19 test_queries.py tests pass |
| 8 | calculate_roi correctly computes Gale accumulated cost | ✓ VERIFIED | GREEN at tentativa=3: `total_invested=70.0`, `profit=6.0` confirmed by direct execution; 7 ROI tests pass |
| 9 | Pending signals (resultado=NULL) counted separately | ✓ VERIFIED | `get_filtered_stats` SQL uses `COUNT(*) FILTER (WHERE resultado IS NULL) AS pending`; test_get_filtered_stats_no_filter asserts `pending==1` |
| 10 | Dashboard layout has all required component IDs | ✓ VERIFIED | `collect_ids(app.layout)` returns 19 IDs; all required IDs confirmed present |
| 11 | Dash dependencies installed and importable | ✓ VERIFIED | dash=4.1.0, dash-bootstrap-components=2.0.4, dash-ag-grid=35.2.0 imported without error |

**Score:** 11/11 truths verified (automated)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `helpertips/queries.py` | Filtered stats, signal history, ROI calculation, dropdown options | ✓ VERIFIED | 259 lines; exports `get_filtered_stats`, `get_signal_history`, `get_distinct_values`, `calculate_roi`; uses `_build_where` helper for parameterized WHERE construction |
| `tests/test_queries.py` | Unit tests for queries module | ✓ VERIFIED | 388 lines, 19 test functions; 5 DB integration tests + 4 history tests + 3 distinct values tests + 7 pure-Python ROI tests; all 19 pass |
| `pyproject.toml` | Dashboard dependencies declared | ✓ VERIFIED | Contains `dash>=4.1,<5`, `dash-bootstrap-components>=2.0`, `dash-ag-grid>=31.0` in `dependencies` |
| `helpertips/dashboard.py` | Dash app with layout and callbacks | ✓ VERIFIED | 442 lines; contains `dbc.themes.DARKLY`, `plotly_dark`, `ag-theme-alpine-dark`; 2 `@callback` decorators |
| `tests/test_dashboard.py` | Structural tests for dashboard layout and KPI formatting | ✓ VERIFIED | 204 lines, 6 test functions; all 6 pass without DB |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `helpertips/queries.py` | `helpertips/db.py` | `get_connection()` | ✓ WIRED | `from helpertips.db import get_connection` at line 18; re-exported for callers |
| `tests/test_queries.py` | `helpertips/queries.py` | import | ✓ WIRED | `from helpertips.queries import get_filtered_stats, get_signal_history, get_distinct_values, calculate_roi` |
| `helpertips/dashboard.py` | `helpertips/queries.py` | import | ✓ WIRED | `from helpertips.queries import (get_filtered_stats, get_signal_history, get_distinct_values, calculate_roi)` lines 28-33 |
| `helpertips/dashboard.py` | `helpertips/db.py` | `get_connection` per callback | ✓ WIRED | `from helpertips.db import get_connection` line 27; called inside `update_dashboard` with `conn.close()` in `finally` block |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `dashboard.py` KPI cards | `stats["total"]`, `stats["greens"]` etc. | `get_filtered_stats(conn, ...)` → SQL `COUNT(*) FILTER` on live `signals` table | Yes — parameterized SQL query on PostgreSQL, not hardcoded | ✓ FLOWING |
| `dashboard.py` ROI card | `roi["profit"]`, `roi["roi_pct"]` | `calculate_roi(history, stake, odd, gale_on)` — pure Python over `history` list | Yes — computed from live history data with Gale formula | ✓ FLOWING |
| `dashboard.py` bar-chart | `y=[greens, reds, pending]` | From `stats` dict returned by `get_filtered_stats` | Yes — direct from DB counts | ✓ FLOWING |
| `dashboard.py` winrate-chart | `liga_winrates` | Computed in-callback from `history` list (each signal's liga + resultado) | Yes — aggregated from live signal rows | ✓ FLOWING |
| `dashboard.py` history-table | `history` (rowData) | `get_signal_history(conn, ...)` → SQL `SELECT ... FROM signals ORDER BY received_at DESC` | Yes — real DB query, `received_at` serialized to str | ✓ FLOWING |
| `dashboard.py` dropdowns | `liga_options`, `entrada_options` | `get_distinct_values(conn, "liga/entrada")` → SQL `SELECT DISTINCT` | Yes — fresh query on each callback invocation | ✓ FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| queries.py imports cleanly | `python3 -c "from helpertips.queries import get_filtered_stats, get_signal_history, get_distinct_values, calculate_roi; print('OK')"` | All imports OK | ✓ PASS |
| dashboard.py imports cleanly | `python3 -c "from helpertips.dashboard import app; assert app.layout is not None"` | Layout not None | ✓ PASS |
| calculate_roi Gale t=3 | `calculate_roi([{resultado:'GREEN', tentativa:3}], 10, 1.9, True)` | `total_invested=70.0, profit=6.0` | ✓ PASS |
| All 19 query tests pass | `python3 -m pytest tests/test_queries.py -x -v` | 19 passed in 0.18s | ✓ PASS |
| All 6 dashboard tests pass | `python3 -m pytest tests/test_dashboard.py -x -v` | 6 passed in 0.04s | ✓ PASS |
| All 19 required component IDs found | `collect_ids(app.layout)` count check | 19/19 IDs found | ✓ PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DASH-01 | 02-02 | Dashboard web com interface elaborada e responsiva | ✓ SATISFIED | `dashboard.py` exists, 442 lines; `app.layout` not None; `dbc.themes.DARKLY` + `fluid=True` container; Bootstrap responsive grid |
| DASH-02 | 02-01, 02-02 | Card de estatísticas: total, greens, reds, taxa de acerto, percentuais | ✓ SATISFIED | 5 KPI cards with IDs kpi-total/greens/reds/pending/winrate; populated via `get_filtered_stats` in master callback |
| DASH-03 | 02-01, 02-02 | Simulação de ROI com stake fixa configurável | ✓ SATISFIED | ROI card with stake-input, odd-input, gale-toggle; `calculate_roi` wired to roi-profit/roi-pct/roi-invested outputs |
| DASH-04 | 02-01, 02-02 | Filtro interativo por liga | ✓ SATISFIED | `filter-liga` Dropdown → `Input("filter-liga", "value")` in master callback → `liga` param passed to all query functions |
| DASH-05 | 02-01, 02-02 | Filtro interativo por entrada | ✓ SATISFIED | `filter-entrada` Dropdown → `Input("filter-entrada", "value")` in master callback → `entrada` param passed to all query functions |
| DASH-06 | 02-01, 02-02 | Lista de histórico de sinais paginada | ✓ SATISFIED | AG Grid with `paginationPageSize: 20`, `pagination: True`, 6 columns, sortable; `get_signal_history` wired to rowData |
| DASH-07 | 02-01, 02-02 | Visualização de sinais pendentes (sem resultado) | ✓ SATISFIED | `getRowStyle.styleConditions` with `!params.data.resultado` condition applies `{backgroundColor: "#3a3000", color: "#ffc107"}`; `kpi-pending` card shows pending count |

All 7 DASH requirements have implementation evidence. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `dashboard.py` | 96, 104, 147, 161 | `placeholder=` | Info | UI field placeholder text — legitimate Dash/HTML `placeholder` attribute for form inputs, NOT a code stub |
| `queries.py` | 28 | "placeholders" | Info | Docstring word "placeholders" referring to SQL `%s` params — NOT a code stub |

No genuine stubs, no TODO/FIXME, no hardcoded empty returns, no disconnected data paths.

---

### Human Verification Required

Plan 02-03 is explicitly typed `autonomous: false` with a blocking human-verify checkpoint. The following must be confirmed with a running browser session:

#### 1. Dark Theme Renders Correctly

**Test:** Run `python3 helpertips/dashboard.py`, open http://localhost:8050
**Expected:** Dark background throughout — DARKLY theme applied to HTML elements, plotly_dark to charts, alpine-dark to AG Grid
**Why human:** CSS rendering and theme application requires visual inspection

#### 2. Filters Update Dashboard Reactively (No Apply Button)

**Test:** Select "Superliga" (or any available liga) from the liga dropdown
**Expected:** KPI cards, bar chart, win rate chart, and history table all update immediately to show only Superliga signals
**Why human:** Dash callback execution and browser reactivity require a live session

#### 3. ROI Gale Toggle Changes Values Visibly

**Test:** Note current ROI profit value. Toggle "Com Gale" switch on.
**Expected:** Profit, ROI%, and total invested change to reflect Gale accumulated stake model
**Why human:** State toggle interaction in live browser required

#### 4. Pending Row Highlighting in AG Grid

**Test:** Browse the signal history table. Locate rows where the Resultado column is empty.
**Expected:** Rows with no resultado have an amber/dark-yellow background (#3a3000) and yellow text (#ffc107)
**Why human:** AG Grid conditional row styling (`getRowStyle.styleConditions`) requires browser rendering

---

### Gaps Summary

No gaps found. All automated must-haves pass.

Plans 02-01 and 02-02 are complete. Plan 02-03 (`autonomous: false`) is the final checkpoint for this phase — it is a blocking human-verify task by design, not a gap in the implementation.

The codebase delivers:
- A complete data layer (`helpertips/queries.py`) with 4 real SQL functions, parameterized WHERE builder, pure-Python Gale ROI, and 19 passing tests
- A complete Dash application (`helpertips/dashboard.py`) with dark DARKLY theme, 5 KPI cards, 3 filters + reset, ROI simulation card with Gale toggle, 2 Plotly charts, AG Grid history table with pending row highlighting, auto-refresh interval, and 2 reactive callbacks wired to live DB data
- 6 structural/formatting tests that pass without a DB connection

Phase goal is technically achieved. Human visual confirmation (Plan 02-03) is the remaining gate.

---

_Verified: 2026-04-03T13:01:04Z_
_Verifier: Claude (gsd-verifier)_
