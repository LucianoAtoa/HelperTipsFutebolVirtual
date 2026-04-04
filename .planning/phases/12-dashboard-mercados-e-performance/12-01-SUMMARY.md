---
phase: 12-dashboard-mercados-e-performance
plan: "01"
subsystem: ui
tags: [dash, plotly, dashboard, tdd, helpers, python]

# Dependency graph
requires:
  - phase: 11-dashboard-funda-o
    provides: Layout v1.2 com filtros globais, KPIs P&L, callback master unico
  - phase: 10-l-gica-financeira
    provides: calculate_pl_por_entrada, get_complementares_config, get_mercado_config
provides:
  - _calcular_stakes_gale: funcao pura para calcular T1-T4 por complementar
  - _agregar_por_entrada: funcao pura para agregar P&L por entrada com greens/reds/roi
  - _get_colunas_visiveis: selecao de colunas por modo do toggle de performance
  - COLUNAS_PCT, COLUNAS_QTY, COLUNAS_PL: constantes de colunas
  - IDs de componentes no layout: config-mercados-container, perf-toggle-view, perf-table, phase13-placeholder
  - Layout reordenado D-09: novas secoes antes do AG Grid historico
affects: [12-02-PLAN, 13-analytics-avancadas]

# Tech tracking
tech-stack:
  added: [collections.defaultdict (stdlib)]
  patterns:
    - "try/except ImportError para imports de funcoes novas em testes (mesmo padrao de _resolve_periodo)"
    - "Funcoes helper puras sem acesso ao banco: testavel sem servidor Dash"
    - "TDD red-first: testes falham intencioanlmente ate a implementacao"
    - "COLUNAS_* constantes de modulo para toggle de visualizacao"

key-files:
  created: []
  modified:
    - tests/test_dashboard.py
    - helpertips/dashboard.py

key-decisions:
  - "try/except ImportError para _calcular_stakes_gale, _agregar_por_entrada, _get_colunas_visiveis — mesmo padrao de _resolve_periodo da Phase 11"
  - "analytics-placeholder substituido por novos IDs estaticos no layout (config-mercados-container, perf-toggle-view/perf-table, phase13-placeholder)"
  - "AG Grid historico movido para apos as novas secoes conforme D-09"
  - "Funcoes helper puras sem acesso ao banco: toda logica de dados e responsabilidade do callback master no Plan 02"

patterns-established:
  - "Pattern: Funcoes helper de logica pura separadas do callback — testavel sem servidor ou banco"
  - "Pattern: IDs de componentes declarados no layout estatico, children preenchidos pelo callback"

requirements-completed: [DASH-03, DASH-04]

# Metrics
duration: 2min
completed: 2026-04-04
---

# Phase 12 Plan 01: Config Mercados e Performance Summary

**Funcoes helper puras _calcular_stakes_gale, _agregar_por_entrada e _get_colunas_visiveis com testes TDD red-first e placeholders de layout para Config Mercados (DASH-03) e Performance (DASH-04)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-04T15:34:41Z
- **Completed:** 2026-04-04T15:36:54Z
- **Tasks:** 2 (1 RED + 1 GREEN)
- **Files modified:** 2

## Accomplishments

- Adicionados 5 novos testes TDD red-first cobrindo _calcular_stakes_gale (3 cenarios), _agregar_por_entrada (visao geral + vazio), _get_colunas_visiveis (3 modos) e IDs Phase 12
- Implementadas 3 funcoes helper puras sem acesso ao banco, todas testadas
- Layout reordenado conforme D-09: novas secoes (config + performance + phase13-placeholder) agora precedem o AG Grid historico
- Suite completa (189 testes) verde apos a implementacao

## Task Commits

1. **Task 1: Testes TDD red-first** - `1601823` (test)
2. **Task 2: Implementar helpers + placeholders** - `ebb7caf` (feat)

## Files Created/Modified

- `tests/test_dashboard.py` - Adicionados 5 testes: test_config_stakes_calculo, test_agregar_por_entrada_visao_geral, test_agregar_por_entrada_vazio, test_performance_toggle_colunas, test_layout_has_phase12_component_ids
- `helpertips/dashboard.py` - Adicionadas funcoes _calcular_stakes_gale, _agregar_por_entrada, _get_colunas_visiveis, constantes COLUNAS_*, import defaultdict, IDs placeholder no layout, reordenacao D-09

## Decisions Made

- Adicionado teste dedicado `test_layout_has_phase12_component_ids` em vez de expandir o `required_ids` do teste existente — melhor isolamento e legibilidade dos testes por fase
- `analytics-placeholder` substituido por IDs especificos dos novos componentes no layout estatico; children serao preenchidos pelo callback master no Plan 02
- Funcoes helper implementadas sem acesso ao banco para garantir testabilidade TDD pura

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito. A unica variacao foi criar `test_layout_has_phase12_component_ids` como teste separado em vez de expandir o `required_ids` do teste existente (mais legivel sem impacto funcional).

## Issues Encountered

Nenhum.

## User Setup Required

Nenhum — sem configuracao externa necessaria.

## Next Phase Readiness

- Plan 02 pode integrar as funcoes helper no callback master: `_calcular_stakes_gale` para cards de config mercados, `_agregar_por_entrada` e `_get_colunas_visiveis` para tabela de performance
- Placeholder `config-mercados-container` pronto para receber Output do callback master
- Placeholder `perf-table` pronto para receber `dash_table.DataTable` gerada no callback
- Suite completa verde (189 testes), sem regressoes

---
*Phase: 12-dashboard-mercados-e-performance*
*Completed: 2026-04-04*
