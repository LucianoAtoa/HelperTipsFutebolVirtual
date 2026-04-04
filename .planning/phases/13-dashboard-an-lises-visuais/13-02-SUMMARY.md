---
phase: 13-dashboard-an-lises-visuais
plan: 02
subsystem: ui
tags: [dash, plotly, analytics, integration, callback-master, liga, equity-curve, gale]

# Dependency graph
requires:
  - phase: 13-01
    provides: aggregate_pl_por_liga, aggregate_pl_por_tentativa, _build_liga_chart, _build_equity_curve_chart, _build_gale_chart

provides:
  - _build_phase13_section em helpertips/dashboard.py
  - callback master com 13 Outputs (phase13-placeholder integrado)
affects: [dashboard-completo-v1.2]

# Tech tracking
tech-stack:
  added: []
  patterns: [_build_phase13_section como orquestrador de 3 secoes visuais + calculo de dados no nivel do callback para reutilizacao]

key-files:
  created: []
  modified:
    - helpertips/dashboard.py
    - tests/test_dashboard.py

key-decisions:
  - "Calculo de signals_placar/comps/odds/pl_lista no nivel do callback (step 19) — reutilizados por _build_phase13_section sem round-trips extras ao banco"
  - "Aceitar segunda chamada a get_signals_com_placar em relacao a _build_performance_section (visao geral) como trade-off de simplicidade: refatorar _build_performance_section seria invasivo e o dataset e pequeno"

# Metrics
duration: 15min
completed: 2026-04-04
---

# Phase 13 Plan 02: Dashboard Analises Visuais — Integracao no Callback Master Summary

**3 secoes visuais (liga, equity curve, gale) integradas no callback master via _build_phase13_section, substituindo phase13-placeholder com dbc.Cards reativos aos filtros globais**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-04T16:10:00Z
- **Completed:** 2026-04-04T16:23:26Z
- **Tasks:** 2 (1 auto + 1 checkpoint human-verify auto-aprovado)
- **Files modified:** 2

## Accomplishments

- `_build_phase13_section`: funcao orquestradora que recebe signals_placar, pl_lista, conn e parametros de filtro e retorna 3 dbc.Card (liga -> equity curve -> gale)
- **DASH-05 Analise por Liga**: grafico de barras empilhadas via `_build_liga_chart` + `dash_table.DataTable` com coloracao condicional P&L por liga
- **DASH-06 Equity Curve**: 3 linhas sobrepostas via `_build_equity_curve_chart` com datas de hover extraidas de `signals_placar.received_at`
- **DASH-07 Analise de Gale**: donut chart via `_build_gale_chart` + `dbc.Table` (color="dark") com merge de `get_gale_analysis` e `aggregate_pl_por_tentativa` para lucro_medio_green por tentativa
- Callback master estendido de 12 para 13 Outputs com `Output("phase13-placeholder", "children")`
- Dados calculados no nivel do callback (step 19) e passados para `_build_phase13_section` — sem round-trips extras ao banco
- 2 novos testes estruturais: `test_layout_has_phase13_component_ids` e `test_build_phase13_section_exists`

## Task Commits

1. **Task 1: _build_phase13_section + callback master + imports + testes** - `aa2645d` (feat)
2. **Task 2: Checkpoint human-verify** - auto-aprovado (sem commit adicional)

## Files Created/Modified

- `helpertips/dashboard.py` - Adicionados imports de 4 funcoes de queries.py, _build_phase13_section (113 linhas), Output phase13-placeholder no @callback, logica step 19 no corpo do callback, return tuple expandido de 12 para 13 elementos
- `tests/test_dashboard.py` - Adicionados test_layout_has_phase13_component_ids e test_build_phase13_section_exists

## Decisions Made

- Calcular signals_placar/comps/odds/pl_lista no nivel do callback (step 19) separado de _build_performance_section para evitar acoplamento invasivo. Trade-off aceito: segunda chamada a get_signals_com_placar na visao geral (dataset pequeno, impacto negligenciavel).
- `color="dark"` em dbc.Table para tabela de gale — conforme decisao estabelecida no Phase 12 (dark=True nao existe em dbc 2.0.4).

## Deviations from Plan

Nenhuma desvio. Plano executado exatamente conforme especificado.

## Auth Gates

Nenhum.

## Known Stubs

Nenhum stub. Todas as 3 secoes recebem dados reais do banco via callback reativo. Graceful degradation: secoes mostram mensagem "Sem dados" quando pl_lista ou gale_data estao vazios.

## Self-Check: PASSED

- `helpertips/dashboard.py` contem `def _build_phase13_section(`: FOUND
- `helpertips/dashboard.py` contem `Output("phase13-placeholder"`: FOUND
- `helpertips/dashboard.py` contem `aggregate_pl_por_liga` no import: FOUND
- `helpertips/dashboard.py` contem `aggregate_pl_por_tentativa` no import: FOUND
- `helpertips/dashboard.py` contem `calculate_equity_curve_breakdown` no import: FOUND
- `helpertips/dashboard.py` contem `get_gale_analysis` no import: FOUND
- `helpertips/dashboard.py` contem `id="liga-chart"`: FOUND
- `helpertips/dashboard.py` contem `id="equity-curve-chart"`: FOUND
- `helpertips/dashboard.py` contem `id="gale-donut-chart"`: FOUND
- `helpertips/dashboard.py` contem `color="dark"` na dbc.Table: FOUND
- Callback master tem 13 Outputs: VERIFIED (kpi-total, kpi-winrate, kpi-pl-total x2, kpi-roi x2, kpi-streak-green, kpi-streak-red, history-table, filter-liga, config-mercados-container, perf-table, phase13-placeholder)
- Commit aa2645d: FOUND
- Suite completa 209 testes: PASSED

---
*Phase: 13-dashboard-an-lises-visuais*
*Completed: 2026-04-04*
