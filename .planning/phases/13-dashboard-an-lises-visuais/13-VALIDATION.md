---
phase: 13
slug: dashboard-an-lises-visuais
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (190 testes coletados) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python3 -m pytest tests/test_dashboard.py tests/test_queries.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_dashboard.py tests/test_queries.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | DASH-05 | unit | `python3 -m pytest tests/test_queries.py -k "liga" -x` | W0 | pending |
| 13-01-02 | 01 | 1 | DASH-07 | unit | `python3 -m pytest tests/test_queries.py -k "tentativa" -x` | W0 | pending |
| 13-01-03 | 01 | 1 | DASH-05 | unit | `python3 -m pytest tests/test_dashboard.py -k "liga_chart" -x` | W0 | pending |
| 13-01-04 | 01 | 1 | DASH-06 | unit | `python3 -m pytest tests/test_dashboard.py -k "equity_chart" -x` | W0 | pending |
| 13-01-05 | 01 | 1 | DASH-07 | unit | `python3 -m pytest tests/test_dashboard.py -k "gale_chart" -x` | W0 | pending |
| 13-02-01 | 02 | 2 | DASH-05, DASH-06, DASH-07 | structural | `python3 -m pytest tests/test_dashboard.py -k "phase13" -x` | W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_queries.py` — testes para `aggregate_pl_por_liga()` e `aggregate_pl_por_tentativa()`
- [ ] `tests/test_dashboard.py` — testes para `_build_liga_chart()`, `_build_equity_curve_chart()`, `_build_gale_chart()`
- [ ] `tests/test_dashboard.py` — teste estrutural `test_layout_has_phase13_component_ids`

*Arquivos de teste existem; funcoes especificas a adicionar.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual de cores DARKLY nos graficos | D-01, D-02, D-03 | Verificacao visual de contraste em fundo escuro | Abrir dashboard, verificar cores dos graficos contra paleta DARKLY |
| Hovertemplate formatacao | D-10 | Interacao de hover requer browser | Hoverar sobre pontos dos 3 graficos, verificar dados formatados |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
