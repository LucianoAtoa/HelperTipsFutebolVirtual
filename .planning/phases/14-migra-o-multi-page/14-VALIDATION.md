---
phase: 14
slug: migra-o-multi-page
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python3 -m pytest tests/test_dashboard.py -q` |
| **Full suite command** | `python3 -m pytest tests/ -q` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_dashboard.py -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | MPA-01, MPA-02 | unit + structural | `python3 -m pytest tests/test_dashboard.py -q` | ✅ | ⬜ pending |
| 14-01-02 | 01 | 1 | MPA-01, MPA-02 | unit | `python3 -m pytest tests/test_dashboard.py -q` | ✅ | ⬜ pending |
| 14-01-03 | 01 | 1 | MPA-02 | manual | visual verification | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test framework or fixtures needed. Existing `tests/test_dashboard.py` (34 tests) will be updated in Task 2 with:

- [ ] `test_app_uses_pages` — verifica `use_pages=True` e `suppress_callback_exceptions=True`
- [ ] `test_shell_has_url_nav` — verifica `dcc.Location(id="url-nav")` no layout
- [ ] `test_home_page_registered` — verifica `pages/home.py` no `dash.page_registry`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard abre identico ao estado pre-migracao | MPA-02 | Visual comparison requer browser | Abrir `http://localhost:8050/`, comparar layout, filtros, graficos, KPIs com estado anterior |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
