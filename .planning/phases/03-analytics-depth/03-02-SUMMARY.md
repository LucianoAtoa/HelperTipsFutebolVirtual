---
phase: 03-analytics-depth
plan: "02"
subsystem: queries
tags: [tdd, analytics, gale, volume, cross-dimensional, parse-failures, periodo]
dependency_graph:
  requires: [03-01]
  provides: [get_gale_analysis, get_volume_by_day, get_cross_dimensional, get_parse_failures_detail, get_winrate_by_periodo]
  affects: [helpertips/queries.py, tests/test_queries.py]
tech_stack:
  added: []
  patterns: [TDD-red-green, _build_where reuse, pure-SQL-aggregation]
key_files:
  created: []
  modified:
    - helpertips/queries.py
    - tests/test_queries.py
decisions:
  - get_winrate_by_periodo usa mesmo padrao WHERE periodo IS NOT NULL que get_gale_analysis usa para tentativa IS NOT NULL
  - get_cross_dimensional ordena em Python apos fetchall para garantir estabilidade da ordenacao
  - db_conn fixture atualizada para limpar parse_failures entre testes alem de signals
metrics:
  duration: 2min
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_modified: 2
requirements:
  - ANAL-03
  - ANAL-04
  - ANAL-07
  - ANAL-08
  - OPER-01
---

# Phase 03 Plan 02: Gale Analysis, Volume, Cross-Dimensional, Parse Failures, Periodo Summary

**One-liner:** 5 funcoes SQL adicionadas a queries.py (gale por tentativa, volume por dia, cross-dimensional liga x entrada, parse failures modal, win rate por periodo) com 12 testes TDD, suite completa 79/79.

## Objective

Completar a segunda metade da camada de dados para a Fase 3: analise de Gale por nivel, volume de sinais por dia, breakdown cross-dimensional, query de parse failures para o modal, e win rate por periodo (ANAL-03).

## What Was Built

### Task 1: Testes RED (TDD)
Adicionados 12 testes em `tests/test_queries.py` cobrindo:
- `test_get_gale_analysis` — 3 variantes (normal, excludes null, empty)
- `test_get_volume_by_day` — 2 variantes (normal, empty)
- `test_get_cross_dimensional` — 2 variantes (normal, empty)
- `test_get_parse_failures_detail` — 3 variantes (normal, limit, empty)
- `test_get_winrate_by_periodo` — 2 variantes (normal, empty)

Fixture `db_conn` atualizada para limpar tabela `parse_failures` alem de `signals`.

### Task 2: Implementacao GREEN
5 funcoes adicionadas ao final de `helpertips/queries.py`:

- **`get_gale_analysis(conn, ...)`** — agrupa por `tentativa` com `tentativa IS NOT NULL`, retorna `win_rate` por nivel (1-4). Suporta todos os filtros via `_build_where`.
- **`get_volume_by_day(conn, ...)`** — usa `DATE_TRUNC('day', received_at)` para agrupar sinais por dia. Retorna `{data: str, count: int}`.
- **`get_cross_dimensional(conn, ...)`** — breakdown `(liga, entrada)` com `HAVING COUNT > 0`, ordenado por `win_rate DESC` em Python.
- **`get_parse_failures_detail(conn, limit=100)`** — retorna ultimas N falhas de `parse_failures` ORDER BY `received_at DESC` para uso no modal de operacoes (OPER-01).
- **`get_winrate_by_periodo(conn, ...)`** — agrupa por `periodo` com `periodo IS NOT NULL`, retorna `{periodo, greens, total, win_rate}` para ANAL-03.

## Test Results

```
79 passed in 0.36s
```

Todos os testes do projeto passam, incluindo os 12 novos testes de Plan 02 e todos os testes existentes dos planos anteriores.

## Commits

| Hash | Task | Description |
|------|------|-------------|
| ab5dda4 | Task 1 (RED) | test(03-02): add failing tests RED para 5 novas funcoes |
| b3abe3a | Task 2 (GREEN) | feat(03-02): implement 5 funcoes, suite 79/79 |

## Deviations from Plan

None — plano executado exatamente como escrito.

## Known Stubs

None — todas as funcoes retornam dados reais do banco, nenhum stub ou placeholder.

## Self-Check: PASSED

- [x] `helpertips/queries.py` — funcoes `get_gale_analysis`, `get_volume_by_day`, `get_cross_dimensional`, `get_parse_failures_detail`, `get_winrate_by_periodo` existem
- [x] `tests/test_queries.py` — 12 novos testes adicionados
- [x] Commit `ab5dda4` existe (RED tests)
- [x] Commit `b3abe3a` existe (GREEN implementation)
- [x] Suite completa: 79 testes passando
