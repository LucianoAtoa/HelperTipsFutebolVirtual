---
phase: 17-p-gina-de-configura-es
plan: 01
subsystem: database
tags: [postgresql, psycopg2, queries, tdd, pytest, pure-functions]

# Dependency graph
requires:
  - phase: 16-navega-o-schema-db
    provides: colunas stake_base, fator_progressao, max_tentativas em mercados + tabela complementares

provides:
  - get_mercado_config retorna 8 colunas incluindo stake_base, fator_progressao, max_tentativas
  - calculate_preview_stakes: funcao pura que calcula stakes T1-TN por complementar sem DB
  - calculate_total_risco: funcao pura que calcula risco total por tentativa sem DB
  - save_mercado_config: persiste config de stake no banco via UPDATE
  - save_complementares_config: persiste percentual e odd_ref de complementares via UPDATE

affects:
  - 17-p-gina-de-configura-es (Plan 02 — UI callbacks importam estas funcoes)
  - helpertips/pages/config.py (Plan 02 importa calculate_preview_stakes, save_mercado_config)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Funcoes puras de calculo separadas de I/O DB — calculate_preview_stakes e calculate_total_risco nao tocam banco"
    - "TDD RED-GREEN para queries: teste mock de cursor/conn antes de implementar"
    - "Chaves Tn dinamicas (T1..T{max_tentativas}) em dict de retorno"

key-files:
  created: []
  modified:
    - helpertips/queries.py
    - tests/test_queries.py

key-decisions:
  - "Chaves Tn sao dinamicas no retorno de calculate_preview_stakes — permite max_tentativas variavel sem hardcode"
  - "calculate_total_risco recebe odd_principal como parametro mas nao usa no calculo de risco — mantido para assinatura completa"
  - "save_complementares_config itera com cursor aberto em context manager — commit unico apos todos os UPDATEs"

patterns-established:
  - "Funcoes puras de preview: assinatura (stake_base, fator_progressao, max_tentativas, complementares) sem conn"
  - "Funcoes de persistencia: conn como primeiro arg, slug ou lista como segundo"

requirements-completed: [CFG-01, CFG-02, CFG-03, CFG-04, CFG-05]

# Metrics
duration: 18min
completed: 2026-04-04
---

# Phase 17 Plan 01: TDD Funcoes de Query e Calculo para Configuracoes Summary

**Camada de dados para config de mercado: get_mercado_config atualizado com 8 colunas, funcoes puras calculate_preview_stakes e calculate_total_risco, e persistencia via save_mercado_config e save_complementares_config — 6 testes TDD cobrindo todas as funcoes**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-04T22:59:17Z
- **Completed:** 2026-04-04T23:17:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `get_mercado_config` atualizado para retornar 8 chaves: id, slug, nome_display, odd_ref, ativo, stake_base, fator_progressao, max_tentativas
- `calculate_preview_stakes` e `calculate_total_risco` implementadas como funcoes puras testadas sem acesso ao banco
- `save_mercado_config` e `save_complementares_config` implementadas com UPDATE SQL correto e testadas via mock de cursor/conn
- 6 testes novos (4 na Task 1 + 2 na Task 2) todos passando com exit code 0

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: TDD — Atualizar get_mercado_config + funcoes puras de preview** - `0cc627d` (feat)
2. **Task 2: TDD — Funcoes de persistencia save_mercado_config e save_complementares_config** - `6a5b647` (feat)

## Files Created/Modified

- `/Users/luciano/helpertips/helpertips/queries.py` — get_mercado_config atualizado + 4 funcoes novas (calculate_preview_stakes, calculate_total_risco, save_mercado_config, save_complementares_config)
- `/Users/luciano/helpertips/tests/test_queries.py` — 6 testes novos para todas as funcoes implementadas

## Decisions Made

- Chaves Tn dinamicas no retorno de `calculate_preview_stakes` — permite `max_tentativas` variavel sem hardcode de T1-T4
- `calculate_total_risco` recebe `odd_principal` como parametro mas nao o usa no calculo de risco — mantido para assinatura completa e extensibilidade futura
- Commit unico apos todos os UPDATEs em `save_complementares_config` — um context manager cursor para todos os complementares

## Deviations from Plan

### Desvios Automaticos

**1. [Rule 1 - Bug] Ajuste nos asserts de SQL multi-linha nos testes de Task 2**

- **Found during:** Task 2 (test_save_mercado_config)
- **Issue:** Teste verificava `"UPDATE mercados SET stake_base" in sql` mas o SQL real tem quebra de linha entre `UPDATE mercados` e `SET stake_base`, causando falha
- **Fix:** Dividido em dois asserts: `"UPDATE mercados" in sql` e `"SET stake_base" in sql`; mesmo fix para `save_complementares_config`
- **Files modified:** tests/test_queries.py
- **Verification:** Testes passam com exit code 0
- **Committed in:** 6a5b647 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug em assert de teste)
**Impact on plan:** Correcao necessaria para o teste verificar o SQL corretamente. Sem mudanca de escopo.

## Issues Encountered

**Mudanca pre-existente em helpertips/queries.py:** O arquivo tinha modificacoes nao commitadas (visible no git status inicial como `M helpertips/queries.py`) que alteravam comportamento de `calculate_roi_complementares` e `calculate_pl_por_entrada`, causando 3 testes pre-existentes falharem. Essas mudancas estao fora do escopo do Plan 17-01 e foram documentadas em `deferred-items.md`. Os 6 testes novos deste plano passam independentemente.

## Next Phase Readiness

- Camada de dados completa para a pagina de configuracoes
- Plan 02 pode importar `calculate_preview_stakes`, `calculate_total_risco`, `save_mercado_config`, `save_complementares_config` de `helpertips.queries`
- Nenhum bloqueador para Plan 02

---
*Phase: 17-p-gina-de-configura-es*
*Completed: 2026-04-04*
