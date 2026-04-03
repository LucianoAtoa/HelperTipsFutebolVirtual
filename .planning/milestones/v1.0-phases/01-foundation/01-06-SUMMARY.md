---
phase: 01-foundation
plan: "06"
subsystem: persistence + terminal-ui
tags: [parse_failures, rich, logging, coverage]
dependency_graph:
  requires: [01-05]
  provides: [parse_failures-table, log_parse_failure, rich-terminal]
  affects: [helpertips/db.py, helpertips/store.py, helpertips/listener.py, tests/test_store.py]
tech_stack:
  added: [rich>=13.0]
  patterns:
    - parse_failures table as safety net for unrecognized messages
    - get_stats() returns dict (breaking change from tuple)
    - RichHandler integrates with stdlib logging
    - Console/Panel/Table for formatted terminal output
key_files:
  created: []
  modified:
    - helpertips/db.py
    - helpertips/store.py
    - helpertips/listener.py
    - tests/test_store.py
decisions:
  - "get_stats() changed return type from tuple to dict — enables named access and extensibility"
  - "parse_fail_count renamed from parse_failures to avoid shadowing the module-level concept"
  - "log_parse_failure reason hardcoded as 'no_liga_match' — parser returns None only for missing LIGA"
  - "RichHandler replaces logging.basicConfig format — all Telethon + helpertips logs flow through rich"
metrics:
  duration: 5min
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_modified: 4
---

# Phase 01 Plan 06: parse_failures + rich terminal Summary

## One-liner

Added `parse_failures` PostgreSQL table as safety net, `log_parse_failure()` store function, `get_stats()` returning dict with coverage %, and replaced all `print()`/`basicConfig` with rich Panel/Table/RichHandler.

## What Was Built

### Task 1: parse_failures schema, log_parse_failure, get_stats dict

**helpertips/db.py** — `ensure_schema()` now creates two tables:
- `parse_failures (id SERIAL PK, raw_text TEXT NOT NULL, received_at TIMESTAMPTZ, failure_reason TEXT)`
- `idx_parse_failures_received_at` index for time-range queries

**helpertips/store.py** — Two changes:
- `get_stats()` return type changed from `tuple` to `dict` with keys: `total`, `greens`, `reds`, `pending`, `parse_failures`, `coverage`. Coverage calculated as `total / (total + parse_failures) * 100` (100.0 when both are 0).
- New `log_parse_failure(conn, raw_text, reason)` — inserts into parse_failures and commits.

**tests/test_store.py** — Four changes:
- `test_get_stats_empty_table`: asserts full dict equality including `coverage: 100.0`
- `test_get_stats_with_data`: uses dict key access
- `test_log_parse_failure`: inserts a failure, verifies `raw_text` and `failure_reason`
- `test_coverage_with_failures`: 3 signals + 1 failure = 75.0% coverage
- `db_conn` fixture: added `DELETE FROM parse_failures` cleanup

### Task 2: Rich terminal output

**helpertips/listener.py** — Full terminal overhaul:
- Imports: `Console`, `Table`, `Panel` from `rich`, `RichHandler` from `rich.logging`
- `logging.basicConfig` now uses `RichHandler(rich_tracebacks=True, show_path=False)` — format `"%(message)s"` with `[%X]` timestamps
- `console = Console()` global instance
- `print_startup_summary()` replaced with rich `Panel` containing a `Table` with 7 rows: total, GREEN, RED, pending, taxa de acerto, cobertura parser, falhas de parse
- Signal output in `handle_signal()`: `[bold green]GREEN[/bold green]`, `[bold red]RED[/bold red]`, `[yellow]NOVO[/yellow]`
- Parse failures now call `log_parse_failure(conn, text, "no_liga_match")` via `asyncio.to_thread()`
- Shutdown summary uses `console.print()` with bold markup

## Commits

| Task | Commit | Files |
|------|--------|-------|
| 1: parse_failures + log_parse_failure | a01506b | helpertips/db.py, helpertips/store.py, tests/test_store.py |
| 2: rich terminal output | 33f4c21 | helpertips/listener.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Renamed in-memory counter to avoid shadowing**
- **Found during:** Task 2
- **Issue:** Plan used `parse_failures` as both the module-level counter variable and the function name — would shadow `log_parse_failure` conceptually and confuse readers
- **Fix:** Renamed module-level counter from `parse_failures` to `parse_fail_count` (original name from plan 05 was already `parse_failures` as a counter; renamed to avoid collision with the new concept)
- **Files modified:** helpertips/listener.py
- **Commit:** 33f4c21

## Known Stubs

None — all parse_failures data flows to the `get_stats()` dict and surfaces in the startup Panel.

## Self-Check: PASSED

Files exist:
- helpertips/db.py: FOUND (CREATE TABLE IF NOT EXISTS parse_failures confirmed)
- helpertips/store.py: FOUND (log_parse_failure and get_stats dict confirmed)
- helpertips/listener.py: FOUND (rich imports, Panel, Table, RichHandler confirmed)
- tests/test_store.py: FOUND (test_log_parse_failure and test_coverage_with_failures confirmed)

Commits exist:
- a01506b: FOUND
- 33f4c21: FOUND
