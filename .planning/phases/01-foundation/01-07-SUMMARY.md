---
phase: 01-foundation
plan: 07
subsystem: testing
tags: [python, regex, parser, telegram, pytest, fixtures]

requires:
  - phase: 01-foundation
    plan: 05
    provides: parser.py with placeholder regex patterns and test scaffolding

provides:
  - Parser with regex tuned to the real {VIP} ExtremeTips Telegram message format
  - Real-format fixtures (PENDENTE, GREEN, RED, NAO-SINAL) in sample_signals.txt
  - 26 parser tests covering all fields including new tentativa field
  - tentativa column in DB schema (which of 4 attempts hit the result)
  - store.py upsert updated to persist tentativa

affects:
  - Phase 02 (dashboard): parser output dict now includes tentativa field
  - Phase 03 (analytics): tentativa enables gale analysis (which attempt hit)

tech-stack:
  added: []
  patterns:
    - "GATE_PATTERN checks for ExtremeTips header or 🏆 Liga: before attempting field extraction"
    - "Tentativa times extracted via TENTATIVA_PATTERN findall — first sorted time is horario"
    - "Placar extracted from ✅ (X-Y) inline on tentativa line, not from separate Placar: line"
    - "RED detected via ✖ Red or ✗ Red pattern (not emoji-based like old ❌ RED)"
    - "tentativa field (int 1-4 or None) tracks which attempt triggered GREEN"

key-files:
  created:
    - tests/fixtures/sample_signals.txt (134 lines, 10 real-format examples)
  modified:
    - helpertips/parser.py (full rewrite — new regex for real format + tentativa field)
    - helpertips/db.py (tentativa SMALLINT column in CREATE TABLE + ALTER TABLE migration)
    - helpertips/store.py (tentativa in INSERT and ON CONFLICT DO UPDATE)
    - tests/conftest.py (real-format fixtures: signal_new, signal_green_with_placar, signal_red_with_placar, signal_green_no_placar, garbage_message)
    - tests/test_parser.py (26 tests: PARS-01..07, LIST-04, tentativa, end-to-end RED/GREEN, dict contract)

key-decisions:
  - "Parser gate changed from LIGA_PATTERN to GATE_PATTERN (ExtremeTips|🏆 Liga:) — real messages always have group header"
  - "Liga extracted from '🏆 Liga: ...' line (not 'LIGA:' as in placeholder)"
  - "Entrada extracted from '📈 Entrada recomendada: 🔥 ... 🔥' with fire emoji stripped"
  - "Horario is FIRST tentativa time (1️⃣ line), not a dedicated Horário: field"
  - "Placar extracted from inline '✅ (X-Y)' on tentativa line, not a separate Placar: label"
  - "RED detected via ✖ Red pattern (real format uses ✖, not ❌ emoji)"
  - "tentativa field added (SMALLINT, nullable) to capture which of 4 attempts triggered GREEN"
  - "GREEN without placar: ✅ inline without parenthesized score — handled gracefully (placar=None)"
  - "db.py uses ALTER TABLE ADD COLUMN IF NOT EXISTS for backward-compatible migration"

patterns-established:
  - "Real messages confirmed: group always uses 4 tentativas (not variable count)"
  - "Real messages confirmed: RED never has a placar score in the group format"
  - "Test fixture naming: signal_new (PENDENTE), signal_green_with_placar, signal_red_with_placar, signal_green_no_placar"

requirements-completed: []

duration: 8min
completed: 2026-04-03
---

# Phase 01 Plan 07: Real-Format Parser Summary

**Parser rewritten for actual {VIP} ExtremeTips format — Liga/Entrada/tentativa times from real message structure, placar from inline ✅ (X-Y), tentativa field added to schema and upsert**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-03T10:21:00Z
- **Completed:** 2026-04-03T10:29:36Z
- **Tasks:** 1 (Task 1 completed prior — user provided real format documentation)
- **Files modified:** 6

## Accomplishments

- Replaced all placeholder regex (LIGA:, Entrada:, Horário:, Placar:) with patterns matching the real group format
- Added `tentativa` field (which of 4 attempts hit GREEN) to parser output, DB schema, and store upsert
- 26 new tests covering real message format pass — 0 failures in full suite (29 passed, 8 skipped for DB)
- sample_signals.txt populated with 10 real-format examples (134 lines) covering all 4 categories

## Task Commits

1. **Task 2: Parser, fixtures, and tests rewritten for real format** - `9e0b1e4` (feat)

## Files Created/Modified

- `tests/fixtures/sample_signals.txt` — 10 real-format message examples (PENDENTE x3, GREEN x3, RED x3, NAO-SINAL x2)
- `helpertips/parser.py` — full rewrite: GATE_PATTERN, LIGA_PATTERN, ENTRADA_PATTERN, TENTATIVA_PATTERN, GREEN/RED detection, PLACAR from ✅ (X-Y), tentativa field
- `helpertips/db.py` — tentativa SMALLINT added to CREATE TABLE and ALTER TABLE IF NOT EXISTS migration
- `helpertips/store.py` — tentativa included in INSERT columns and ON CONFLICT DO UPDATE SET
- `tests/conftest.py` — all 5 fixtures rewritten with real message format
- `tests/test_parser.py` — 26 tests covering PARS-01..07, LIST-04, tentativa extraction, full end-to-end RED/GREEN, dict contract

## Decisions Made

- Kept `parse_message(text, message_id) -> dict | None` signature unchanged — store.py and listener.py compatibility preserved
- Added `tentativa` key to return dict — store.py and db.py updated to handle it (no backward compat break since all are in-repo)
- Used `ALTER TABLE ADD COLUMN IF NOT EXISTS` for tentativa migration — idempotent, safe on fresh installs and existing DBs
- Gate logic changed from LIGA-only to `ExtremeTips|🏆 Liga:` — matches real group header and prevents false positives more reliably
- `horario` is derived from the first tentativa time line, not a dedicated label — matches real format (no dedicated Horário: field)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added tentativa field to DB schema and store**
- **Found during:** Task 2 (rewriting parser for real format)
- **Issue:** Real format provides which attempt (1-4) hit the result via ✅ inline on tentativa line. The original schema had no tentativa column; omitting it would lose valuable analytical data for future gale analysis (ANAL-07)
- **Fix:** Added tentativa SMALLINT to db.py CREATE TABLE and ALTER TABLE IF NOT EXISTS migration; added to store.py INSERT and DO UPDATE
- **Files modified:** helpertips/db.py, helpertips/store.py
- **Verification:** test_return_dict_keys passes; tentativa in all expected_keys set
- **Committed in:** 9e0b1e4

---

**Total deviations:** 1 auto-fixed (missing critical field)
**Impact on plan:** tentativa is required data for gale analysis (ANAL-07). Adding it now is the right time — no schema migrations needed later.

## Issues Encountered

None — all regex patterns matched real format on first implementation. 26/26 tests passed first run.

## Known Stubs

None — all fields extracted from real message format. No hardcoded values or placeholder data flows to DB.

## Next Phase Readiness

- Parser is now validated against the real message format — critical Pitfall 6 (RESEARCH.md) resolved
- `tentativa` field available for Phase 3 analytics (gale analysis: which attempt wins most)
- listener.py handler logic unchanged — `parse_message` signature and dict keys preserved, store.py updated
- Phase 01 foundation complete — all 7 plans executed

## Self-Check: PASSED

---

*Phase: 01-foundation*
*Completed: 2026-04-03*
