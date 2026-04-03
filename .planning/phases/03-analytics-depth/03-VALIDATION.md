---
phase: 3
slug: analytics-depth
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 7.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `python3 -m pytest tests/test_queries.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_queries.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | ANAL-01 | unit | `python3 -m pytest tests/test_queries.py::test_get_heatmap_data -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 0 | ANAL-01 | integration | `python3 -m pytest tests/test_queries.py::test_get_heatmap_data_db -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 0 | ANAL-02 | unit | `python3 -m pytest tests/test_queries.py::test_get_winrate_by_dow -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 0 | ANAL-03 | unit | `python3 -m pytest tests/test_queries.py::test_get_winrate_by_periodo -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 0 | ANAL-04 | unit | `python3 -m pytest tests/test_queries.py::test_get_cross_dimensional -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | 0 | ANAL-05 | unit | `python3 -m pytest tests/test_queries.py::test_calculate_equity_curve -x` | ❌ W0 | ⬜ pending |
| 03-01-07 | 01 | 0 | ANAL-05 | unit | `python3 -m pytest tests/test_queries.py::test_equity_curve_reversal -x` | ❌ W0 | ⬜ pending |
| 03-01-08 | 01 | 0 | ANAL-06 | unit | `python3 -m pytest tests/test_queries.py::test_calculate_streaks -x` | ❌ W0 | ⬜ pending |
| 03-01-09 | 01 | 0 | ANAL-07 | unit | `python3 -m pytest tests/test_queries.py::test_get_gale_analysis -x` | ❌ W0 | ⬜ pending |
| 03-01-10 | 01 | 0 | ANAL-08 | unit | `python3 -m pytest tests/test_queries.py::test_get_volume_by_day -x` | ❌ W0 | ⬜ pending |
| 03-01-11 | 01 | 0 | OPER-01 | unit | `python3 -m pytest tests/test_dashboard.py::test_coverage_badge_thresholds -x` | ❌ W0 | ⬜ pending |
| 03-01-12 | 01 | 0 | OPER-01 | unit (layout) | `python3 -m pytest tests/test_dashboard.py::test_layout_has_required_component_ids -x` | Parcial | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_queries.py` — stubs para `get_heatmap_data`, `get_winrate_by_dow`, `get_winrate_by_periodo`, `get_cross_dimensional`, `get_gale_analysis`, `get_volume_by_day`, `get_parse_failures_detail`
- [ ] `tests/test_queries.py` — stubs para `calculate_equity_curve`, `calculate_streaks` (puro Python, sem DB)
- [ ] `tests/test_dashboard.py` — atualizar `test_layout_has_required_component_ids` com IDs: `tabs-analytics`, `badge-parser-coverage`, `modal-parse-failures`

*Existing infrastructure covers framework install — pytest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Heatmap visual rendering (colors, tooltips) | ANAL-01 | Plotly rendering requires visual inspection | Open dashboard, verify heatmap shows correct colors for win rate ranges |
| Equity curve annotation positioning | ANAL-05 | Annotation placement is visual | Verify streak annotations (>=5) appear at correct positions without overlap |
| Badge click opens modal | OPER-01 | Click interaction in browser | Click coverage badge, verify modal opens with parse_failures table |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
