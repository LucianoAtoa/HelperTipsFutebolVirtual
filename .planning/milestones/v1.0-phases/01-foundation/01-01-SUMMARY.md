---
phase: 01-foundation
plan: 01
subsystem: database
tags: [python, postgresql, psycopg2, telethon, python-dotenv, pytest]

# Dependency graph
requires: []
provides:
  - .gitignore blocking *.session, *.session-journal, and .env from git
  - .env.example template with all 8 required environment variables
  - requirements.txt with pinned telethon==1.42.0, psycopg2-binary==2.9.11, python-dotenv==1.2.2, pytest==9.0.2
  - db.py exporting validate_config(), get_connection(), ensure_schema()
  - pytest.ini with testpaths = tests
  - tests/test_config.py with 3 passing config validation tests
affects: [01-02, 01-03, 01-04, 01-05, 01-06, 01-07]

# Tech tracking
tech-stack:
  added:
    - telethon==1.42.0
    - psycopg2-binary==2.9.11
    - python-dotenv==1.2.2
    - pytest==9.0.2
  patterns:
    - Fail-fast config validation at module import time via validate_config()
    - psycopg2 connection factory pattern (get_connection returns new connection)
    - ensure_schema with CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS
    - TDD: RED commit (failing tests) then GREEN commit (passing implementation)

key-files:
  created:
    - .gitignore
    - .env.example
    - requirements.txt
    - db.py
    - pytest.ini
    - tests/__init__.py
    - tests/test_config.py
  modified: []

key-decisions:
  - "Upgraded Telethon from 1.40.0 to 1.42.0 (required by CLAUDE.md pin ~=1.42)"
  - "validate_config() collects ALL missing vars before raising SystemExit — better UX than fail-on-first"
  - "ensure_schema() uses a single multi-statement execute for atomicity"

patterns-established:
  - "Pattern: db.py is the single entry point for all database concerns — connection, schema, validation"
  - "Pattern: validate_config() called at startup before any connections are attempted"
  - "Pattern: TDD RED commit (tests only) before GREEN commit (implementation)"

requirements-completed: [OPER-02, OPER-03, DB-01]

# Metrics
duration: 1min
completed: 2026-04-03
---

# Phase 1 Plan 01: Project Bootstrap Summary

**Project security and DB foundation: .gitignore with session protection, pinned dependencies (Telethon 1.42.0, psycopg2-binary 2.9.11), db.py with validate_config/get_connection/ensure_schema, and 3 passing TDD tests for config validation**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-03T10:04:10Z
- **Completed:** 2026-04-03T10:05:27Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Created .gitignore blocking *.session, *.session-journal, and .env before any code commit
- Installed and pinned all required dependencies: Telethon 1.42.0 (upgraded from 1.40.0), psycopg2-binary 2.9.11, python-dotenv 1.2.2, pytest 9.0.2
- Implemented db.py with validate_config() (collects all missing vars), get_connection() (psycopg2 factory), and ensure_schema() (signals table with 11 columns and 4 indexes)
- All 3 config validation tests pass: missing var, empty var, and all-vars-present

## Task Commits

Each task was committed atomically:

1. **Task 1: Project bootstrap — .gitignore, .env.example, requirements.txt** - `e544c09` (chore)
2. **Task 2 RED: Failing tests for validate_config()** - `b2d0985` (test)
3. **Task 2 GREEN: db.py implementation** - `77dd4a7` (feat)

_TDD task had 2 commits: RED (failing tests) then GREEN (implementation)_

## Files Created/Modified

- `.gitignore` — blocks *.session, *.session-journal, .env, __pycache__, venv
- `.env.example` — template with all 8 required environment variables and defaults for DB_HOST/DB_PORT
- `requirements.txt` — pinned versions: Telethon==1.42.0, psycopg2-binary==2.9.11, python-dotenv==1.2.2, pytest==9.0.2
- `db.py` — REQUIRED_VARS list, validate_config(), get_connection(), ensure_schema() with signals table + 4 indexes
- `pytest.ini` — testpaths = tests, python_files = test_*.py, python_functions = test_*
- `tests/__init__.py` — empty, makes tests/ a package
- `tests/test_config.py` — 3 tests: test_all_vars_present_passes, test_missing_var_raises, test_empty_var_raises

## Decisions Made

- Upgraded Telethon from 1.40.0 to 1.42.0 as required by CLAUDE.md pin `~=1.42`
- validate_config() collects ALL missing/empty vars before raising SystemExit(1) for better error UX
- ensure_schema() wraps all DDL in a single cursor execute for implicit atomicity

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration.** Before running any code, the user must:

1. Copy `.env.example` to `.env` and fill in all values:
   - `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` — get from https://my.telegram.org → API Development Tools
   - `TELEGRAM_GROUP_ID` — discovered at runtime via Telethon (plan 04 handles this)
   - `DB_PASSWORD` — choose a password for the PostgreSQL user

2. Create the PostgreSQL database and user (PostgreSQL 17 is at `/Library/PostgreSQL/17/bin/psql`):
   ```bash
   /Library/PostgreSQL/17/bin/psql -U postgres -c "CREATE DATABASE helpertips;"
   /Library/PostgreSQL/17/bin/psql -U postgres -c "CREATE USER helpertips_user WITH PASSWORD 'your_password';"
   /Library/PostgreSQL/17/bin/psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE helpertips TO helpertips_user;"
   ```

## Next Phase Readiness

- Plan 01-02 (parser.py) can proceed — pytest infrastructure is ready
- Plan 01-03 (store.py) can proceed — db.py is ready with correct schema
- Plan 01-04 (listener.py) can proceed — all dependencies installed
- Blocker: PostgreSQL database and user must be created manually before any DB connections (see User Setup Required)

---
*Phase: 01-foundation*
*Completed: 2026-04-03*
