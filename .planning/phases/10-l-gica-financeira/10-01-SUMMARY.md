---
phase: 10-l-gica-financeira
plan: "01"
subsystem: data-layer
tags: [queries, mercado, financeiro, filtro, tdd]
dependency_graph:
  requires: []
  provides: [get_signals_com_placar, get_mercado_config, _build_where_mercado_id]
  affects: [helpertips/queries.py, tests/test_queries.py]
tech_stack:
  added: []
  patterns: [parameterized-sql, left-join, backward-compat-default-none]
key_files:
  created: []
  modified:
    - helpertips/queries.py
    - tests/test_queries.py
decisions:
  - _build_where estendido com mercado_id=None para zero breaking change em todas as chamadas existentes
  - get_signals_com_placar usa LEFT JOIN mercados para incluir sinais com mercado_id=NULL (sinais sem mercado associado)
  - Ordenacao ASC em get_signals_com_placar para calculo cronologico correto de P&L no Plan 02
metrics:
  duration: ~8 min
  completed: "2026-04-04T14:18:00Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 10 Plan 01: Queries Financeiras — SUMMARY

**One-liner:** Camada de queries estendida com filtro por mercado via `_build_where(mercado_id)`, `get_mercado_config(slug)` e `get_signals_com_placar()` com LEFT JOIN mercados para alimentar o calculo P&L do Plan 02.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Testes TDD failing para _build_where, get_mercado_config, get_signals_com_placar | a20ece0 | tests/test_queries.py |
| 1 (GREEN) | Implementar _build_where mercado_id + get_mercado_config | ebf9855 | helpertips/queries.py |
| 2 (GREEN) | Implementar get_signals_com_placar | ebf9855 | helpertips/queries.py |

## What Was Built

### `_build_where` estendido (helpertips/queries.py)

Parametro `mercado_id=None` adicionado — backward compatible. Quando fornecido, gera `AND mercado_id = %s` com valor parametrizado. Todas as 8+ chamadas existentes continuam funcionando sem alteracao.

### `get_mercado_config(conn, mercado_slug)` (helpertips/queries.py)

Query `SELECT id, slug, nome_display, odd_ref, ativo FROM mercados WHERE slug = %s AND ativo = TRUE`. Retorna dict ou None. Usado pelo Plan 02 para obter odd_ref do mercado principal para calculo de P&L.

### `get_signals_com_placar(conn, ...)` (helpertips/queries.py)

Query com `LEFT JOIN mercados m ON s.mercado_id = m.id`, filtra `resultado IN ('GREEN', 'RED')`, ordena por `received_at ASC` para calculo cronologico de equity curve. Aceita todos os filtros de `_build_where` incluindo `mercado_id`. Retorna 9 campos por sinal: id, resultado, placar, tentativa, mercado_id, mercado_slug, entrada, liga, received_at.

## Test Coverage

- 21 novos testes adicionados (era 138, passou para 159 total)
- 88 funcoes de teste em test_queries.py (era 67)
- Testes `_build_where_mercado_id*` sao puros (sem DB) — executam sempre
- Testes `get_mercado_config*` e `get_signals_com_placar*` requerem DB — skipados se indisponivel
- Suite completa: 159 passed, 0 failed, 0 regressions

## Decisions Made

1. **`_build_where` backward compat por default=None:** Todas as chamadas existentes (get_filtered_stats, get_signal_history, etc.) continuam sem necessidade de atualizacao. Decisao alinhada com D-07 (zero breaking change).

2. **LEFT JOIN em vez de INNER JOIN em get_signals_com_placar:** Sinais sem mercado_id associado (dados historicos pre-Phase 9) nao sao excluidos — mercado_slug aparece como NULL nesses casos. INNER JOIN excluiria esses sinais e quebraria analise historica.

3. **ORDER BY received_at ASC:** Calculo cronologico de P&L e equity curve exige ordem crescente. get_signal_history usa DESC (mais recente primeiro) — funcoes tem propositos opostos.

## Deviations from Plan

Nenhuma — plano executado exatamente como especificado.

## Known Stubs

Nenhum — todas as funcoes retornam dados reais do banco. Plan 02 consumira estas funcoes para calcular P&L.

## Self-Check: PASSED
