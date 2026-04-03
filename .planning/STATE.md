---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 02-core-dashboard 02-02-PLAN.md (dashboard layout, callbacks, tests)
last_updated: "2026-04-03T13:02:59.578Z"
last_activity: 2026-04-03
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 10
  completed_plans: 9
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-02)

**Core value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.
**Current focus:** Phase 02 — core-dashboard

## Current Position

Phase: 3
Plan: Not started
Status: Ready to execute
Last activity: 2026-04-03

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01-foundation P01 | 2min | 2 tasks | 7 files |
| Phase 01-foundation P02 | 2 | 2 tasks | 4 files |
| Phase 01-foundation P03 | 2min | 1 tasks | 2 files |
| Phase 01-foundation P04 | 4min | 2 tasks | 1 files |
| Phase 01-foundation P05 | 2min | 2 tasks | 9 files |
| Phase 01-foundation P06 | 5min | 2 tasks | 4 files |
| Phase 01-foundation P07 | 8min | 1 tasks | 6 files |
| Phase 02-core-dashboard P01 | 8min | 2 tasks | 3 files |
| Phase 02-core-dashboard P02 | 3min | 3 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Telethon user-client (not Bot API) — required to listen to private group without admin rights
- [Init]: psycopg2 wrapped in asyncio.to_thread() — must not block event loop or signals drop silently
- [Init]: Two separate processes (listener.py + dashboard.py) — Telethon blocks asyncio loop, Dash blocks process; no single-process mixing
- [Init]: Upsert-only write path (ON CONFLICT) — no SELECT-then-INSERT; handles both new signals and result edits atomically
- [Phase 01-foundation]: Upgraded Telethon from 1.40.0 to 1.42.0 (required by CLAUDE.md pin ~=1.42)
- [Phase 01-foundation]: validate_config() collects ALL missing vars before raising SystemExit — better UX than fail-on-first
- [Phase 01-foundation]: LIGA field is the signal gate in parser.py — returns None immediately if no LIGA match, preventing non-signal messages from being stored
- [Phase 01-foundation]: parser.py imports only re and datetime (stdlib) — zero external deps ensures listener integration requires no additional packages
- [Phase 01-foundation]: store.py is sync-only with no asyncio/telethon imports — listener.py wraps calls in asyncio.to_thread() per DB-04
- [Phase 01-foundation]: ON CONFLICT WHERE clause prevents overwriting GREEN/RED resultado with NULL — signals.resultado IS DISTINCT FROM EXCLUDED.resultado OR signals.resultado IS NULL
- [Phase 01-foundation]: validate_config() moved inside main() to allow safe module imports without .env — fail-fast preserved as first action in main()
- [Phase 01-foundation]: TelegramClient created inside main() with event handlers as nested decorator closures — requires env vars only at runtime
- [Phase 01-foundation]: Used setuptools.build_meta as build-backend (plan had invalid setuptools.backends._legacy:_Backend for setuptools 82)
- [Phase 01-foundation]: Removed pytest.ini — configuration migrated to pyproject.toml [tool.pytest.ini_options] (single config file)
- [Phase 01-foundation]: All inter-module imports use from helpertips.X import Y — no relative imports, no sys.path manipulation
- [Phase 01-foundation]: get_stats() changed return type from tuple to dict — enables named access to coverage and parse_failures count
- [Phase 01-foundation]: RichHandler replaces logging.basicConfig format string — all Telethon + helpertips logs rendered via rich
- [Phase 01-foundation]: log_parse_failure uses 'no_liga_match' reason — parser returns None only when LIGA regex fails
- [Phase 01-foundation]: Parser gate changed from LIGA_PATTERN to GATE_PATTERN (ExtremeTips|🏆 Liga:) — real messages always have group header
- [Phase 01-foundation]: tentativa field (SMALLINT, nullable) added to schema — captures which of 4 attempts triggered GREEN for future gale analysis
- [Phase 01-foundation]: horario is FIRST tentativa time (1️⃣ line), not a dedicated Horário: field — real format has no such label
- [Phase 01-foundation]: placar extracted from inline ✅ (X-Y) on tentativa line — real format does not use separate Placar: label
- [Phase 02-core-dashboard]: _build_where() helper centralizes WHERE clause construction — all query functions reuse it without duplication
- [Phase 02-core-dashboard]: calculate_roi is pure Python with no DB dependency — enables test-first development without PostgreSQL
- [Phase 02-core-dashboard]: get_distinct_values validates field name against frozenset allowlist before SQL interpolation — prevents SQL injection on column names
- [Phase 02-core-dashboard]: db_conn fixture truncates before AND after yield — test isolation against real listener data
- [Phase 02-core-dashboard]: received_at datetime objects converted to str() inside callback before returning rowData — psycopg2 returns Python datetime, AG Grid expects JSON-serializable values
- [Phase 02-core-dashboard]: Dash 4.x @callback decorator used at module level (not app.callback) — correct pattern for dashboard.py standalone module

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1 — Research flag]: Parser regex must be written against real captured messages. Capture 10–20 real messages before finalizing the parser. Format assumed from general virtual football group patterns.
- [Phase 3 — Research flag]: ANAL-06 (streak tracking) and ANAL-07 (gale analysis) require 100+ signals to be meaningful. Validate data volume before planning Phase 3.

## Session Continuity

Last session: 2026-04-03T12:50:09.501Z
Stopped at: Completed 02-core-dashboard 02-02-PLAN.md (dashboard layout, callbacks, tests)
Resume file: None
