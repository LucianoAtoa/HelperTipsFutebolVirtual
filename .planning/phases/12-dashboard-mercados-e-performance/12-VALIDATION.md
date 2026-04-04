---
phase: 12
slug: dashboard-mercados-e-performance
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | DASH-03, DASH-04 | unit | `python -m pytest tests/test_dashboard.py -k "config_stakes or agregar" -v` | ✅ | ⬜ pending |
| 12-01-02 | 01 | 1 | DASH-03, DASH-04 | unit | `python -m pytest tests/test_dashboard.py -k "colunas or toggle" -v` | ✅ | ⬜ pending |
| 12-02-01 | 02 | 2 | DASH-03, DASH-04 | unit+integration | `python -m pytest tests/test_dashboard.py -k "config_card or performance" -v` | ✅ | ⬜ pending |
| 12-02-02 | 02 | 2 | DASH-04 | manual | Visual checkpoint: config cards + performance table | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements — tests written in `tests/test_dashboard.py` (Plan 01, Task 1 creates TDD stubs: `test_config_stakes_calculo`, `test_agregar_por_entrada_visao_geral`, `test_agregar_por_entrada_vazio`, `test_performance_toggle_colunas`).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual layout of config cards (dark theme, spacing) | DASH-03 | CSS/visual rendering | Open dashboard, verify cards display correctly with DARKLY theme |
| Toggle visual switch (RadioItems) | DASH-04 | Interactive UI behavior | Click each toggle option, verify table columns change |
| Reactive stakes T1-T4 when stake changes | DASH-03 | Callback chain | Change stake input, verify config cards update |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
