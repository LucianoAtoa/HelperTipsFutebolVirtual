---
phase: 15-p-gina-de-detalhe-do-sinal
plan: 01
subsystem: database
tags: [postgres, psycopg2, queries, tdd, pl-calculation, gale]

# Dependency graph
requires:
  - phase: 10-l-gica-financeira
    provides: calculate_pl_por_entrada, validar_complementar, logica de Gale progressivo
provides:
  - get_sinal_detalhado: busca sinal por ID com JOIN em mercados, retorna dict ou None
  - calculate_pl_detalhado_por_sinal: breakdown P&L individual com linha por complementar

affects:
  - 15-02 (pagina de detalhe Dash que consomera essas funcoes)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Funcao de detalhe retorna {principal, complementares, totais} — separacao clara de niveis"
    - "placar=None tratado como N/A nos complementares (sem penalidade financeira)"
    - "Gale progressivo: accumulated=stake*(2^t-1), winning=stake*(2^(t-1))"

key-files:
  created: []
  modified:
    - helpertips/queries.py
    - tests/test_queries.py

key-decisions:
  - "placar=None em calculate_pl_detalhado_por_sinal -> complementares N/A com lucro=0 e investido=0 (diferente de validar_complementar que retorna RED para placar=None)"
  - "stake_efetiva adicionada ao dict principal para expor winning_stake do Gale ao chamador"
  - "Sem refactor: logica Gale em calculate_pl_detalhado_por_sinal mantida separada de calculate_pl_por_entrada (funcoes independentes, menos de 10 linhas duplicadas no contexto de cada)"

patterns-established:
  - "Pattern: resultado_comp is None -> N/A (principal pendente); placar is None -> N/A antecipado sem chamar validar_complementar"

requirements-completed: [SIG-02, SIG-03, SIG-04, SIG-06]

# Metrics
duration: 2min
completed: 2026-04-04
---

# Phase 15 Plan 01: Funcoes de Dados para Pagina de Detalhe do Sinal Summary

**Duas novas funcoes em queries.py: get_sinal_detalhado (SELECT com JOIN mercados) e calculate_pl_detalhado_por_sinal (breakdown principal + complementares individuais + totais), com 6 testes TDD cobrindo GREEN/RED/Gale/N/A**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-04T19:29:59Z
- **Completed:** 2026-04-04T19:31:54Z
- **Tasks:** 1 (TDD — RED + GREEN phases)
- **Files modified:** 2

## Accomplishments

- `get_sinal_detalhado(conn, signal_id)`: busca sinal por ID com LEFT JOIN em mercados, retorna dict com 9 campos ou None se inexistente
- `calculate_pl_detalhado_por_sinal(sinal, complementares_config, stake, odd_principal, gale_on)`: breakdown P&L com principal, lista de complementares individuais (cada um com nome/odd/stake/resultado/lucro/investido/retorno) e totais consolidados
- Tratamento especial para `placar=None`: complementares retornam `resultado="N/A"` com `lucro=0.0` e `investido=0.0`
- Gale progressivo correto: `accumulated=stake*(2^t-1)`, `winning=stake*(2^(t-1))`, `stake_efetiva` exposta no principal
- 6 novos testes TDD, suite completa 218 testes verde

## Task Commits

1. **RED phase — testes falhos** - `8428ad3` (test)
2. **GREEN phase — implementacao** - `7b8c491` (feat)

## Files Created/Modified

- `/Users/luciano/helpertips/helpertips/queries.py` - Adicionadas `get_sinal_detalhado` e `calculate_pl_detalhado_por_sinal` apos `calculate_pl_por_entrada` (linhas 762-960 aprox.)
- `/Users/luciano/helpertips/tests/test_queries.py` - Adicionados 6 testes TDD na secao "Phase 15" no final do arquivo

## Decisions Made

- `placar=None` em `calculate_pl_detalhado_por_sinal` resulta em complementares `N/A` (sem penalidade) — diferente do comportamento de `validar_complementar` que retorna `"RED"` nesse caso. A pagina de detalhe deve exibir "sem informacao" em vez de penalizar financeiramente o usuario.
- `stake_efetiva` adicionada ao dict principal para que a pagina de detalhe possa exibir a stake efetiva da tentativa vencedora no Gale.
- REFACTOR phase omitida: logica Gale < 10 linhas duplicadas entre as duas funcoes, manutencao separada preferida para evitar acoplamento desnecessario.

## Deviations from Plan

None — plano executado exatamente como especificado. Unica adaptacao foi o tratamento de `placar=None` diretamente em `calculate_pl_detalhado_por_sinal` antes de chamar `validar_complementar` (ja previsto na action do plano: "Se resultado_comp is None: tratar como N/A"), estendido para cobrir tambem `placar=None` com principal GREEN (conforme os testes do plano exigiam).

## Issues Encountered

Nenhum.

## User Setup Required

None — sem configuracao externa necessaria.

## Next Phase Readiness

- `get_sinal_detalhado` e `calculate_pl_detalhado_por_sinal` prontas para consumo pelo Plan 02 (pagina Dash de detalhe)
- Exports funcionando: `from helpertips.queries import get_sinal_detalhado, calculate_pl_detalhado_por_sinal`
- Sem blockers

---
*Phase: 15-p-gina-de-detalhe-do-sinal*
*Completed: 2026-04-04*
