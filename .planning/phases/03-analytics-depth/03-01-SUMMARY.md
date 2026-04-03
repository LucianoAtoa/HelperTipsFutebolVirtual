---
phase: 03-analytics-depth
plan: 01
subsystem: database
tags: [python, postgresql, psycopg2, analytics, heatmap, equity-curve, streaks]

# Dependency graph
requires:
  - phase: 02.1-market-config
    provides: "_build_where(), calculate_roi(), queries.py padrao conn-per-call"
provides:
  - "get_heatmap_data: matriz 24x7 win_rate por hora x dia da semana"
  - "get_winrate_by_dow: lista de dicts win_rate por dia da semana"
  - "calculate_equity_curve: curva bankroll Stake Fixa e Gale com annotations de streak"
  - "calculate_streaks: streak atual e maximos historicos O(n) single-pass"
affects: [03-analytics-depth/03-02, 03-analytics-depth/03-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Equity curve reversal: signals_desc invertido com list(reversed()) para ordem cronologica"
    - "Heatmap pivot: z[hora][dia] inicializado com None (nao zeros) — celulas sem dados ficam None"
    - "Streak detection: single-pass O(n) comparando resultado[i] com resultado[i-1]"
    - "Annotation de streak: streak_start rastreado no loop, annotation gerada no break e no final"

key-files:
  created: []
  modified:
    - "helpertips/queries.py — 4 novas funcoes adicionadas no final (sem alterar existentes)"
    - "tests/test_queries.py — 12 novos testes (5 equity_curve, 3 streaks, 2 heatmap, 2 winrate_by_dow)"

key-decisions:
  - "calculate_equity_curve e calculate_streaks sao funcoes puras Python sem DB — seguem padrao de calculate_roi()"
  - "get_heatmap_data e get_winrate_by_dow reutilizam _build_where() para filtros consistentes"
  - "Heatmap inicializado com None (nao 0) para distinguir 'sem dados' de 'win_rate=0%'"
  - "annotations de streak geradas inline em calculate_equity_curve sem funcao auxiliar adicional"

patterns-established:
  - "TDD RED/GREEN: testes importam funcoes inexistentes — _IMPORTS_OK catch no try/except de importacao"
  - "Testes puro Python usam guard 'if not _IMPORTS_OK: pytest.skip()' para separar de testes DB"

requirements-completed: [ANAL-01, ANAL-02, ANAL-05, ANAL-06]

# Metrics
duration: 3min
completed: 2026-04-03
---

# Phase 3 Plan 01: Analytics Depth — Temporal e Equity/Streaks Summary

**4 funcoes de dados adicionadas a queries.py: heatmap 24x7, win rate por dia da semana, curva de equity bankroll com anotacoes de streak, e calculo de streaks historicos em O(n)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-03T19:16:12Z
- **Completed:** 2026-04-03T19:18:42Z
- **Tasks:** 2 (TDD: 1 RED + 1 GREEN)
- **Files modified:** 2

## Accomplishments

- `get_heatmap_data`: consulta SQL com EXTRACT(HOUR/DOW) e pivot Python em matriz 24x7, celulas sem dados ficam None (nao zero)
- `get_winrate_by_dow`: lista de dicts por dia da semana com win_rate calculado, reutiliza `_build_where()`
- `calculate_equity_curve`: converte sinais DESC para ASC com `list(reversed())`, calcula bankroll acumulado para Stake Fixa e Gale simultaneamente, detecta streaks >= 5 e gera annotations `{x, y, text}`
- `calculate_streaks`: single-pass O(n) sem memoria extra, retorna `current`, `current_type`, `max_green`, `max_red`
- 12 novos testes passando (incluindo DB integration tests com PostgreSQL real)

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Testes RED** - `b74738b` (test)
2. **Task 2: Implementacao GREEN** - `b029217` (feat)

## Files Created/Modified

- `/Users/luciano/helpertips/helpertips/queries.py` — 4 novas funcoes adicionadas no final do arquivo (255 linhas inseridas, nenhuma funcao existente alterada)
- `/Users/luciano/helpertips/tests/test_queries.py` — 12 novos testes + import block atualizado (225 linhas inseridas)

## Decisions Made

- `calculate_equity_curve` e `calculate_streaks` sao funcoes puras Python sem dependencia de DB — seguem o padrao estabelecido por `calculate_roi()` na fase anterior
- Heatmap inicializado com `[[None] * 7 for _ in range(24)]` (nao zeros) para permitir que `go.Heatmap` do Plotly distinga celulas sem dados de win_rate real de 0%
- Annotations de streak geradas dentro do loop principal de `calculate_equity_curve` sem funcao auxiliar — simplicidade sobre abstracao prematura

## Deviations from Plan

Nenhum — plano executado exatamente como escrito. As 4 funcoes implementadas correspondem 1:1 com as especificacoes do PLAN.md e RESEARCH.md.

## Issues Encountered

Nenhum. Todos os 67 testes passaram na primeira execucao apos implementacao (55 existentes + 12 novos).

## Known Stubs

Nenhum — todas as funcoes retornam dados reais calculados a partir do banco ou dos sinais passados.

## Next Phase Readiness

- `get_heatmap_data`, `get_winrate_by_dow`, `calculate_equity_curve`, `calculate_streaks` prontos para consumo pelo dashboard (plano 03-02)
- Todas as funcoes seguem o padrao `conn per call` estabelecido — compativel com o callback separado de abas planejado
- Sem blockers para os proximos planos

---
*Phase: 03-analytics-depth*
*Completed: 2026-04-03*
