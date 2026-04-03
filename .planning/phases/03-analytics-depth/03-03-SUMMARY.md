---
phase: 03-analytics-depth
plan: "03"
subsystem: dashboard
tags: [dash, plotly, analytics, tabs, badge, modal, callbacks]
dependency_graph:
  requires: [03-01, 03-02]
  provides: [dashboard-analytics-ui]
  affects: [helpertips/dashboard.py, tests/test_dashboard.py]
tech_stack:
  added: []
  patterns:
    - "Callback separado para abas com lazy render (active_tab gate)"
    - "dbc.Badge com cor dinamica no header via master callback"
    - "dbc.Modal para parse failures com ctx.triggered_id routing"
    - "Helper functions _make_*_figure para cada tipo de grafico"
key_files:
  created: []
  modified:
    - helpertips/dashboard.py
    - tests/test_dashboard.py
decisions:
  - "Badge e Modal adicionados no mesmo commit que tabs — todos os componentes de layout sao atomicos"
  - "update_tabs usa lazy render via active_tab gate — abas inativas retornam no_update para evitar queries desnecessarias"
  - "toggle_modal usa ctx.triggered_id para distinguir badge click vs btn-close — padrao canonico Dash 4.x"
  - "Master callback atualizado com 2 novos outputs (badge children + color) sem quebrar outputs existentes"
metrics:
  duration: "~8 min"
  completed: "2026-04-03T19:27:35Z"
  tasks_completed: 2
  tasks_total: 3
  files_modified: 2
---

# Phase 03 Plan 03: Dashboard Integration Summary

Dashboard Fase 3 integrado com layout de 3 abas analiticas (Temporal, Gale & Streaks, Volume), badge de cobertura do parser com modal de parse failures, e callbacks separados conectando todas as funcoes de queries.py.

## Objective

Integrar todas as funcoes de dados (Plans 01-02) ao dashboard: layout com dbc.Tabs (3 abas tematicas), badge de cobertura do parser com modal, callback separado para abas com lazy render, e atualizacao do master callback para badge.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Layout — tabs, badge, modal + imports + helper functions | 0c92571 | helpertips/dashboard.py |
| 2 | Callbacks — update_tabs, toggle_modal, badge no master + testes | 8b42bbe | helpertips/dashboard.py, tests/test_dashboard.py |

## Task 3 — Checkpoint (Pending)

Task 3 e uma verificacao visual humana. O dashboard deve ser iniciado e aprovado visualmente pelo usuario antes de marcar o plano como completo.

**Como iniciar:** `cd /Users/luciano/helpertips && python3 -m helpertips.dashboard`
**URL:** http://localhost:8050

## What Was Built

### Layout Changes (Task 1)

**Imports novos em dashboard.py:**
- 9 funcoes de Phase 3 importadas de `helpertips.queries`
- `get_stats` importado de `helpertips.store`
- `State`, `no_update`, `ctx` importados de `dash`

**Header:**
- `dbc.Badge` com `id="badge-coverage"` inserido no `html.H2` com `cursor: pointer`

**Layout — dbc.Tabs com 3 abas:**
- `tab-temporal`: heatmap (400px) + equity curve (350px) + win rate por dia da semana (300px)
- `tab-gale`: gale analysis (barras horizontais, 300px) + 3 mini-cards de streaks
- `tab-volume`: volume chart (280px) + cross-dimensional breakdown table

**dbc.Modal:**
- `id="modal-parse-failures"` com header "Falhas de Parse", body `id="modal-failures-body"`, botao "Fechar"

**7 Helper functions:**
- `_make_heatmap_figure(data)` — go.Heatmap com RdYlGn colorscale
- `_make_equity_figure(data)` — go.Scatter dual-line (Stake Fixa + Gale + Breakeven)
- `_make_dow_figure(data)` — go.Bar win rate por dia da semana
- `_make_gale_figure(data)` — go.Bar horizontal com cores progressivas por tentativa
- `_make_volume_figure(data)` — go.Bar volume por dia
- `_format_streak(count, streak_type)` — formata "N wins" / "N losses" / "Sem dados"
- `_build_cross_table(data)` — dbc.Table com highlight para win_rate > 60%

### Callbacks (Task 2)

**update_tabs:** Callback separado com 9 outputs, 8 inputs. Lazy render via `active_tab`:
- `tab-temporal`: calcula heatmap + equity curve + win rate por DOW
- `tab-gale`: calcula gale analysis + streaks
- `tab-volume`: calcula volume + cross-dimensional
- Abas inativas retornam `no_update` para todas as saidas

**toggle_modal:** Abre modal ao clicar no badge, fecha com btn-close-modal. Usa `ctx.triggered_id` para routing.

**Master callback atualizado:** 2 novos outputs adicionados ao final:
- `Output("badge-coverage", "children")` — texto "Cobertura: XX%"
- `Output("badge-coverage", "color")` — "success" >= 95%, "warning" >= 90%, "danger" < 90%

### Testes (Task 2)

**test_layout_has_required_component_ids:** Atualizado com 12 novos IDs:
`tabs-analytics`, `badge-coverage`, `modal-parse-failures`, `graph-heatmap`, `graph-equity`, `graph-dow`, `graph-gale`, `graph-volume`, `kpi-streak-current`, `kpi-streak-max-green`, `kpi-streak-max-red`, `table-cross-dimensional`

**Novos testes adicionados:**
- `test_coverage_badge_thresholds` — valida logica success/warning/danger
- `test_format_streak` — valida helper _format_streak

**Suite completa:** 132 testes passando (anteriores: 79 em test_queries.py + novos em test_dashboard.py)

## Verification

```
cd /Users/luciano/helpertips && python3 -m pytest tests/ -x -q
# 132 passed in 0.54s
```

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito.

## Known Stubs

Nenhum — todos os componentes do layout estao conectados a funcoes de dados reais em queries.py. Os estados vazios ("Dados insuficientes", "Nenhum sinal") sao empty states legitimos, nao stubs.

## Self-Check: PASSED

- helpertips/dashboard.py — FOUND (modificado)
- tests/test_dashboard.py — FOUND (modificado)
- Commit 0c92571 — FOUND (git log)
- Commit 8b42bbe — FOUND (git log)
- 132 testes passando — VERIFICADO
