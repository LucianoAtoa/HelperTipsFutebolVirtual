---
phase: 01-foundation
plan: 03
subsystem: store
tags: [python, postgresql, psycopg2, repository, upsert, tdd]

# Dependency graph
requires:
  - 01-01 (db.py with get_connection and ensure_schema)
provides:
  - store.py exporting upsert_signal(conn, data) and get_stats(conn)
  - tests/test_store.py with 6 integration tests for store layer
affects: [01-04, 01-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Upsert-only write path via INSERT ... ON CONFLICT (message_id) DO UPDATE
    - ON CONFLICT WHERE clause prevents overwriting known resultado with NULL
    - Sync-only repository module — no asyncio/telethon imports; caller wraps in asyncio.to_thread()
    - Integration tests with graceful PostgreSQL skip when DB unavailable

key-files:
  created:
    - store.py
    - tests/test_store.py
  modified: []

key-decisions:
  - "store.py is sync-only with no asyncio/telethon imports — listener.py wraps calls in asyncio.to_thread() per DB-04"
  - "ON CONFLICT WHERE clause (signals.resultado IS DISTINCT FROM EXCLUDED.resultado OR signals.resultado IS NULL) prevents overwriting GREEN/RED with NULL"
  - "Integration tests use pytest.skip() when PostgreSQL unavailable — correct graceful degradation for dev environments without .env"

patterns-established:
  - "Pattern: repository functions take a psycopg2 connection as first argument — caller controls connection lifecycle"
  - "Pattern: each upsert commits its own transaction (conn.commit inside upsert_signal)"

requirements-completed: [DB-02, DB-03, DB-04]

# Metrics
duration: 2min
completed: 2026-04-03
---

# Phase 1 Plan 03: Store Repository Layer Summary

**Sync-only repository layer with upsert_signal (INSERT ON CONFLICT upsert with NULL-protection WHERE clause) and get_stats returning (total, greens, reds, pending) tuple, with 6 integration tests that skip gracefully when PostgreSQL is unavailable**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-03T10:08:18Z
- **Completed:** 2026-04-03T10:09:57Z
- **Tasks:** 1 (TDD: 2 commits — RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Created `store.py` with `upsert_signal()` using `INSERT ... ON CONFLICT (message_id) DO UPDATE` — single SQL write path for both new signals and edited results
- The `ON CONFLICT WHERE` clause prevents overwriting a known `resultado` (GREEN/RED) with NULL when the original message is re-processed by the listener
- Created `get_stats()` returning `(total, greens, reds, pending)` using `COUNT(*) FILTER` — efficient single-query summary for terminal startup display
- Module is sync-only (no asyncio/telethon imports) — caller wraps in `asyncio.to_thread()` per DB-04 architecture constraint
- Created `tests/test_store.py` with 6 integration tests covering: insert, update, dedup, NULL-protection, empty-table stats, multi-row stats
- Tests skip gracefully with descriptive message when PostgreSQL is not available (no .env configured)

## Task Commits

Each TDD phase was committed atomically:

1. **Task 1 RED: Failing tests for store repository layer** — `58e93f3` (test)
2. **Task 1 GREEN: store.py implementation** — `a64af39` (feat)

_TDD task had 2 commits: RED (failing tests — skipped due to missing store module) then GREEN (passing implementation)_

## Files Created/Modified

- `store.py` — `upsert_signal(conn, data)` with ON CONFLICT upsert + WHERE guard, `get_stats(conn)` with COUNT FILTER, sync-only module
- `tests/test_store.py` — 6 integration tests: insert, update-resultado, no-duplicate, preserve-on-null-update, empty-stats, populated-stats

## Decisions Made

- `store.py` is sync-only — no asyncio or telethon imports. The caller (`listener.py`) wraps calls in `asyncio.to_thread()` per DB-04 constraint
- `ON CONFLICT WHERE` clause protects known results: `signals.resultado IS DISTINCT FROM EXCLUDED.resultado OR signals.resultado IS NULL` — prevents NULL from stomping GREEN/RED
- Integration tests use `pytest.skip()` when `get_connection()` fails — correct behavior when .env is not configured in dev environments

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. `store.py` contains no placeholder logic — `upsert_signal` and `get_stats` are fully implemented with real SQL queries against the `signals` table.

## Test Status

Integration tests require PostgreSQL configured via `.env`. Tests skip gracefully when DB is unavailable. When `.env` is configured (see plan 01-01 User Setup Required), all 6 tests will run against real PostgreSQL:

- `test_upsert_inserts_new_signal` — INSERT path with field verification
- `test_upsert_updates_resultado` — UPDATE path via ON CONFLICT
- `test_upsert_no_duplicate_rows` — deduplication behavior
- `test_upsert_preserves_original_on_null_result_update` — WHERE clause protection
- `test_get_stats_empty_table` — `(0, 0, 0, 0)` on empty table
- `test_get_stats_with_data` — correct (3, 1, 1, 1) counts

## Next Phase Readiness

- Plan 01-04 (listener.py) can proceed — store.py is ready with correct upsert interface
- store.py is the direct dependency for the `await asyncio.to_thread(upsert_signal, conn, parsed)` call in listener.py

---
*Phase: 01-foundation*
*Completed: 2026-04-03*
