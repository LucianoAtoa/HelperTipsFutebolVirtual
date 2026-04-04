---
phase: 10
slug: l-gica-financeira
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_queries.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_queries.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | FIN-01 | unit | `python -m pytest tests/test_queries.py -k "complementar" -x -q` | ✅ | ⬜ pending |
| 10-01-02 | 01 | 1 | FIN-02 | unit | `python -m pytest tests/test_queries.py -k "gale or martingale" -x -q` | ✅ | ⬜ pending |
| 10-01-03 | 01 | 1 | FIN-03 | unit | `python -m pytest tests/test_queries.py -k "mercado" -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

- pytest, conftest.py with DB fixtures, and test_queries.py all exist
- No new framework or fixture installation needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard renders P&L breakdown | FIN-01 | Visual verification | Open dashboard, check P&L values match expected calculation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
