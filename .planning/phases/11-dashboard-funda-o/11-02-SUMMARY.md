---
phase: 11-dashboard-funda-o
plan: "02"
subsystem: dashboard
tags: [dash, layout, kpi, filtros-globais, callback-master, pl-total]
dependency_graph:
  requires: [11-01]
  provides: [dashboard-v1.2, layout-filtros-globais, kpi-pl-total, callback-master]
  affects: [helpertips/dashboard.py]
tech_stack:
  added: []
  patterns:
    - _resolve_periodo para converter selecao de periodo em date_start/date_end ISO
    - Callback master unico com todos os 10 Outputs de KPI
    - dbc.Collapse para DatePickerRange condicional
    - P&L total = principal + complementares via calculate_roi + calculate_roi_complementares
key_files:
  created: []
  modified:
    - helpertips/dashboard.py
decisions:
  - "P&L total calculado on-the-fly no callback: principal (calculate_roi) + complementares (calculate_roi_complementares) somados em pl_total"
  - "Mercado vazio string ('') tratado como None para queries — entrada = mercado if mercado else None (Pitfall 2)"
  - "AG Grid preservado com time_casa/time_fora como strings vazias — get_signal_history nao retorna esses campos, nao gera erro"
  - "go importado com noqa: F401 para disponibilidade nas fases 12-13 (plotly.graph_objects)"
metrics:
  duration: 112s
  completed_date: "2026-04-04"
  tasks_completed: 2
  files_modified: 1
---

# Phase 11 Plan 02: Dashboard v1.2 Reescrita Summary

**One-liner:** Reescrita completa de dashboard.py com layout v1.2 — filtros globais via RadioItems/Dropdowns, 6 KPI cards financeiros incluindo P&L Total em R$ e ROI, card de simulacao Stake/Odd/Gale, e callback master unico com _resolve_periodo.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Reescrever dashboard.py — layout v1.2 + _resolve_periodo + callback master | b802a52 | helpertips/dashboard.py |
| 2 | Verificacao visual do dashboard v1.2 | (auto-aprovado) | — |

## Decisions Made

1. **P&L total on-the-fly no callback:** Soma `calculate_roi(history)["profit"]` + `calculate_roi_complementares(history)["profit"]` no mesmo callback. Complementares sao calculados apenas quando mercado especifico selecionado; quando "Todos" (mercado vazio), `pl_comp = 0`.

2. **Entrada como string, nao mercado_id:** Conforme Pitfall 2 do RESEARCH, o callback passa `entrada = mercado if mercado else None` diretamente para `get_filtered_stats` e `get_signal_history` (que aceitam `entrada: str`), nao converte para mercado_id.

3. **AG Grid com campos simplificados:** `get_signal_history` nao retorna `time_casa`/`time_fora` — campos deixados como string vazia no rowData. Nao causa erro funcional; sera resolvido se necessario em fase futura.

## Deviations from Plan

### Auto-fixed Issues

Nenhuma — plano executado exatamente como escrito.

### Auto-approved Checkpoints (auto_advance=true)

1. **Task 2 — checkpoint:human-verify** — Auto-aprovado. Dashboard v1.2 construido com layout completo, filtros globais, 6 KPI cards, card de simulacao e AG Grid historico. Todos os 184 testes passando.

## Known Stubs

- **AG Grid campos time_casa/time_fora:** `helpertips/dashboard.py`, funcao `update_dashboard`, loop de `row_data`. Campos sempre vazios pois `get_signal_history` nao os retorna. Nao impede o objetivo do plano (KPIs financeiros e filtros globais). Pode ser resolvido em fase futura adicionando JOIN na query ou campos alternativos.

## Self-Check: PASSED

- [x] `helpertips/dashboard.py` existe e contem 306 linhas (reescrita de 884 linhas)
- [x] Commit b802a52 existe: `feat(11-02): reescrever dashboard.py com layout v1.2 e callback master`
- [x] `python3 -m pytest tests/test_dashboard.py -x -q` — 17 testes passando
- [x] `python3 -m pytest tests/ -x -q` — 184 testes passando
- [x] `python3 -c "from helpertips.dashboard import app; print('OK')"` — imprime OK
- [x] `grep -c "periodo-selector" helpertips/dashboard.py` — 3 ocorrencias
- [x] `grep -c "_resolve_periodo" helpertips/dashboard.py` — 3 ocorrencias
- [x] `grep -c "kpi-pl-total" helpertips/dashboard.py` — 3 ocorrencias
- [x] NAO contem `update_tabs`, `tabs-analytics`, `graph-heatmap`
