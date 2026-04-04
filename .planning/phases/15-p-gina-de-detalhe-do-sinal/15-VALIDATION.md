---
phase: 15
slug: p-gina-de-detalhe-do-sinal
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python3 -m pytest tests/test_dashboard.py -x -q` |
| **Full suite command** | `python3 -m pytest -x -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_dashboard.py -x -q`
- **After every plan wave:** Run `python3 -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | SIG-01,SIG-02,SIG-03 | unit | `python3 -m pytest tests/test_queries.py -x -q` | ✅ | ⬜ pending |
| 15-02-01 | 02 | 1 | SIG-01,SIG-05,SIG-06 | unit+integration | `python3 -m pytest tests/test_dashboard.py -x -q` | ✅ | ⬜ pending |
| 15-02-02 | 02 | 1 | SIG-04 | unit | `python3 -m pytest tests/test_dashboard.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green �� ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. pytest + test_dashboard.py + test_queries.py already exist.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AG Grid row click navigates to /sinal?id=N | SIG-01 | Requires browser interaction | Click row in AG Grid, verify URL changes to /sinal?id=N |
| Visual layout of signal detail page | SIG-02,SIG-03 | Visual verification | Open /sinal?id=N, verify cards and table render correctly |
| Botão Voltar preserva filtros | SIG-05 | Requires browser state | Set filters, navigate to detail, click Voltar, verify filters |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
