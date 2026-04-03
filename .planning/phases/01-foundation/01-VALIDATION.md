---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (latest) |
| **Config file** | none — Wave 0 installs and creates pytest.ini |
| **Quick run command** | `python3 -m pytest tests/test_parser.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_parser.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | OPER-02 | smoke | `git ls-files \| grep -c .session` == 0 | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 0 | OPER-03 | unit | `python3 -m pytest tests/test_config.py::test_missing_var_raises -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | PARS-01 | unit | `python3 -m pytest tests/test_parser.py::test_parse_liga -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | PARS-02 | unit | `python3 -m pytest tests/test_parser.py::test_parse_entrada -x` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | PARS-03 | unit | `python3 -m pytest tests/test_parser.py::test_parse_horario -x` | ❌ W0 | ⬜ pending |
| 1-02-04 | 02 | 1 | PARS-04 | unit | `python3 -m pytest tests/test_parser.py::test_parse_resultado -x` | ❌ W0 | ⬜ pending |
| 1-02-05 | 02 | 1 | PARS-05 | unit | `python3 -m pytest tests/test_parser.py::test_parse_placar -x` | ❌ W0 | ⬜ pending |
| 1-02-06 | 02 | 1 | PARS-06 | unit | `python3 -m pytest tests/test_parser.py::test_raw_text_always_stored -x` | ❌ W0 | ⬜ pending |
| 1-02-07 | 02 | 1 | PARS-07 | unit | `python3 -m pytest tests/test_parser.py::test_parse_returns_none_for_garbage -x` | ❌ W0 | ⬜ pending |
| 1-02-08 | 02 | 1 | LIST-04 | unit | `python3 -m pytest tests/test_parser.py::test_empty_text_returns_none -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 1 | DB-01 | schema | `psql -c "\d signals"` returns table description | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 1 | DB-02 | integration | Manual — upsert inserts new signal | N/A | ⬜ pending |
| 1-03-03 | 03 | 1 | DB-03 | integration | Manual — upsert updates resultado | N/A | ⬜ pending |
| 1-03-04 | 03 | 1 | DB-04 | integration | Manual — asyncio.to_thread wraps calls | N/A | ⬜ pending |
| 1-04-01 | 04 | 2 | LIST-01 | integration | Manual — new signal appears in DB | N/A | ⬜ pending |
| 1-04-02 | 04 | 2 | LIST-02 | integration | Manual — edited message updates DB | N/A | ⬜ pending |
| 1-04-03 | 04 | 2 | LIST-03 | integration | Manual — duplicate msg_id does not create new row | N/A | ⬜ pending |
| 1-04-04 | 04 | 2 | LIST-05 | integration | Manual — reconnects after disconnect | N/A | ⬜ pending |
| 1-04-05 | 04 | 2 | TERM-01 | smoke | Run listener, check startup output | N/A | ⬜ pending |
| 1-04-06 | 04 | 2 | TERM-02 | smoke | Run listener, check group name in output | N/A | ⬜ pending |
| 1-04-07 | 04 | 2 | TERM-03 | manual | Send Ctrl+C, verify clean exit | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_parser.py` — stubs for PARS-01 through PARS-07, LIST-04
- [ ] `tests/test_config.py` — covers OPER-03
- [ ] `tests/conftest.py` — shared fixtures (sample message strings)
- [ ] `pytest.ini` — test discovery config
- [ ] Package installs: `pip3 install "telethon~=1.42" --upgrade "psycopg2-binary>=2.9" "python-dotenv>=1.0" pytest`

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| New signal appears in DB | LIST-01 | Requires live Telegram group | Run listener, wait for signal, check `SELECT * FROM signals ORDER BY id DESC LIMIT 1` |
| Edited message updates resultado | LIST-02, DB-03 | Requires live Telegram group | Wait for result edit, verify `resultado` column updated |
| Reconnection after disconnect | LIST-05 | Requires network disruption | Disable network briefly, verify reconnection in logs |
| Ctrl+C clean exit | TERM-03 | Interactive terminal required | Run listener, press Ctrl+C, verify no traceback and "Shutting down" message |
| Startup summary accuracy | TERM-01, TERM-02 | Visual verification | Run listener, compare output against DB counts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
