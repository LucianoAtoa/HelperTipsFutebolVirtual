---
phase: 12-dashboard-mercados-e-performance
plan: "02"
subsystem: dashboard
tags: [dash, performance, config-mercados, callback, dash_table]
dependency_graph:
  requires: [12-01]
  provides: [DASH-03, DASH-04]
  affects: [helpertips/dashboard.py]
tech_stack:
  added: [dash_table.DataTable]
  patterns: [builder-functions, extended-callback-master, conditional-columns-toggle]
key_files:
  created: []
  modified:
    - helpertips/dashboard.py
    - tests/test_dashboard.py
decisions:
  - "dbc.Table color='dark' em vez de dark=True: parametro dark nao existe em dbc 2.0.4, substituido por color='dark'"
  - "perf_toggle com fallback 'pct': perf_toggle or 'pct' garante modo default mesmo sem trigger"
  - "config_section e perf_section calculados dentro do bloco try antes do conn.close()"
metrics:
  duration: 123s
  completed: "2026-04-04"
  tasks_completed: 1
  tasks_total: 2
  files_modified: 2
---

# Phase 12 Plan 02: Config Mercados e Performance Summary

Dashboard estendido com secao Config Mercados (cards read-only com stakes T1-T4 reativos) e tabela de Performance das Entradas com toggle de 3 modos (Percentual/Quantidade/P&L) integrados ao callback master.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Builder functions + extensao do callback master | 83bd0bb | dashboard.py, test_dashboard.py |
| 2 | Verificacao visual (checkpoint) | — | auto-aprovado |

## What Was Built

### DASH-03: Config Mercados

- `MERCADOS_CONFIG`: lista de slugs/nomes dos 2 mercados (over_2_5, ambas_marcam)
- `_build_config_card_mercado(nome, odd_ref, stake, comps)`: card dbc.Card com header (odd ref, stake base, progressao) e tabela HTML com colunas Complementar, %, Odd Ref, T1-T4 calculados dinamicamente
- `_build_config_mercados_section(conn, stake)`: itera MERCADOS_CONFIG, carrega config do banco via `get_mercado_config` e `get_complementares_config`, retorna lista de cards

### DASH-04: Performance das Entradas

- `_build_performance_section(conn, history, entrada, stake, odd, gale_on, toggle_mode)`: constroi `dash_table.DataTable` com colunas condicionais por toggle_mode
  - Visao geral (entrada=None): agrega por entrada via `_agregar_por_entrada` usando `calculate_pl_por_entrada`
  - Visao por mercado (entrada selecionada): linha principal + linhas por complementar via `calculate_roi` e `calculate_roi_complementares`
  - Cores verde/vermelho nos valores P&L e ROI via `style_data_conditional`

### Callback Master Estendido

- De 10 para 12 Outputs: adicionados `Output("config-mercados-container", "children")` e `Output("perf-table", "children")`
- Novo Input: `Input("perf-toggle-view", "value")`
- Assinatura atualizada: `update_dashboard(..., perf_toggle, _n)`
- Secoes 17 e 18 adicionadas antes do `finally: conn.close()`

### Imports Adicionados

- `dash_table` no import do dash
- `calculate_pl_por_entrada`, `get_mercado_config`, `get_signals_com_placar` no import de queries

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] dbc.Table nao aceita parametro dark=True em dbc 2.0.4**
- **Found during:** Task 1 — execucao dos testes
- **Issue:** `dbc.Table(dark=True)` lanca `TypeError: unexpected keyword argument dark` — o parametro foi removido na versao 2.0.x do dash-bootstrap-components
- **Fix:** Substituido `dark=True` por `color="dark"` que e o prop suportado
- **Files modified:** helpertips/dashboard.py linha 178
- **Commit:** 83bd0bb

## Verification Results

```
python3 -m pytest tests/ -x -q → 190 passed
python3 -c "from helpertips.dashboard import _build_config_mercados_section, _build_performance_section; print('OK')" → OK
grep -c 'Output("config-mercados-container"' helpertips/dashboard.py → 1
grep -c 'Output("perf-table"' helpertips/dashboard.py → 1
grep -c 'get_mercado_config' helpertips/dashboard.py → 3 (import + _build_config_mercados_section + _build_performance_section)
grep -c 'get_signals_com_placar' helpertips/dashboard.py → 2 (import + uso)
```

## Known Stubs

Nenhum — todas as secoes buscam dados reais do banco via queries existentes.

## Self-Check: PASSED
