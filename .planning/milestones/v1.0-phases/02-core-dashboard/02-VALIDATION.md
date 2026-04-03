---
phase: 02
slug: core-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python3 -m pytest tests/ -q --tb=short` |
| **Full suite command** | `python3 -m pytest tests/ -v --tb=long` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/ -q --tb=short`
- **After every plan wave:** Run `python3 -m pytest tests/ -v --tb=long`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DASH-03..07 | unit | `python3 -m pytest tests/test_queries.py -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | DASH-01,02 | unit | `python3 -m pytest tests/test_dashboard.py -q` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | DASH-01..07 | integration | manual browser verification | N/A | ⬜ pending |
| 02-03-01 | 03 | 3 | DASH-01..07 | manual | visual + functional checkpoint | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_queries.py` — stubs for get_filtered_stats, get_signal_history, calculate_roi, get_distinct_values
- [ ] `tests/test_dashboard.py` — stubs for app layout, KPI components, filter components

*Existing test infrastructure (conftest.py, pyproject.toml) covers framework setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard opens at localhost:8050 | DASH-01 | Browser render required | Open browser, verify dark theme and layout |
| Filters update all visualizations | DASH-04,05 | Reactive UI behavior | Select liga dropdown, verify stats change |
| AG Grid pagination + sort | DASH-06 | Interactive table behavior | Click column headers, navigate pages |
| Pending signals visually distinct | DASH-07 | Visual styling verification | Check row highlighting for null resultado |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
