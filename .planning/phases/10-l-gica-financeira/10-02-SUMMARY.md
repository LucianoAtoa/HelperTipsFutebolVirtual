---
phase: 10-l-gica-financeira
plan: "02"
subsystem: data-layer
tags: [queries, financeiro, pl, equity-curve, tdd, gale, complementares]
dependency_graph:
  requires: [10-01]
  provides: [calculate_pl_por_entrada, calculate_equity_curve_breakdown]
  affects: [helpertips/queries.py, tests/test_queries.py]
tech_stack:
  added: []
  patterns: [pure-python-calculation, gale-formula, tdd-red-green]
key_files:
  created: []
  modified:
    - helpertips/queries.py
    - tests/test_queries.py
decisions:
  - calculate_equity_curve_breakdown implementada junto com calculate_pl_por_entrada no mesmo commit GREEN para desbloquear imports do arquivo de testes
  - Formulas Gale identicas a calculate_roi existente (accumulated_stake, winning_stake)
  - Complementares diferenciados por mercado via dict[str, list[dict]] sem acesso ao banco
metrics:
  duration: ~3 min
  completed: "2026-04-04T14:24:00Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 10 Plan 02: P&L por Entrada e Equity Curve Breakdown — SUMMARY

**One-liner:** Funcoes puras `calculate_pl_por_entrada` e `calculate_equity_curve_breakdown` com Gale T1-T4, breakdown principal/complementar/total diferenciado por mercado, 18 testes novos cobrindo todos os cenarios.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Testes TDD failing para calculate_pl_por_entrada | 82e0425 | tests/test_queries.py |
| 1 (GREEN) | Implementar calculate_pl_por_entrada e calculate_equity_curve_breakdown | 3320785 | helpertips/queries.py |
| 2 (GREEN) | Testes para calculate_equity_curve_breakdown | 7cb6230 | tests/test_queries.py |

## What Was Built

### `calculate_pl_por_entrada` (helpertips/queries.py)

Funcao pura que retorna lista de dicts com P&L discriminado por sinal. Para cada sinal resolvido:
- **Principal:** calcula `investido_principal`, `retorno_principal`, `lucro_principal` usando formulas Gale exatas de `calculate_roi` (`accumulated_stake = stake * (2^N - 1)`, `winning_stake = stake * (2^(N-1))`)
- **Complementares:** para cada complementar do mercado, aplica `validar_complementar()` com o placar, calcula stake com o percentual correto por mercado, acumula em `investido_comp`, `retorno_comp`, `lucro_comp`
- **Total:** `investido_total = investido_principal + investido_comp`, `lucro_total = lucro_principal + lucro_comp`
- Mercados diferentes (over_2_5 vs ambas_marcam) usam percentuais distintos via `complementares_por_mercado` dict

Exemplos verificados:
- GREEN T1 stake=100 odd=2.30: investido=100, lucro=130
- GREEN T2 Gale: accumulated=300, winning=200, lucro=200*1.30-100=160
- RED T4 Gale: investido=1500, lucro=-1500
- RED Stake Fixa: lucro=-100 (ignora tentativa)

### `calculate_equity_curve_breakdown` (helpertips/queries.py)

Funcao pura que retorna dict com 5 series para equity curve multi-linha:
- `x` — indices cronologicos [1, 2, ...]
- `y_principal` — equity acumulado do mercado principal
- `y_complementar` — equity acumulado dos complementares
- `y_total` — `y_principal + y_complementar` (invariante verificado em testes)
- `colors` — `"#28a745"` (GREEN) ou `"#dc3545"` (RED)

Sinais pendentes (resultado=None) sao ignorados. Lista vazia retorna todas as listas vazias.

## Test Coverage

- 18 novos testes adicionados (era 159, passou para 177 total)
- Testes `test_pl_*` (11): green T1-T4, red T4, stake fixa, complementares over_2_5, ambas_marcam, sem placar, retorno lista dicts, pendente ignorado
- Testes `test_equity_curve_breakdown_*` (7): retorna_chaves, total_soma, green_t1, red_acumula, lista_vazia, colors, pendentes_ignorados
- Todos os testes sao puros (sem DB) — executam sempre
- Suite completa: 177 passed, 0 failed, 0 regressions

## Decisions Made

1. **calculate_equity_curve_breakdown implementada junto com calculate_pl_por_entrada (Task 1 GREEN):** O arquivo de testes importa ambas as funcoes no mesmo bloco try/except. Como o Task 2 (tests) seria adicionado no RED phase mas o import falharia por calculate_equity_curve_breakdown nao existir, implementei ambas no mesmo commit GREEN de Task 1 para manter os imports funcionando sem alterar a logica TDD.

2. **Formulas Gale identicas a calculate_roi:** `accumulated_stake = stake * (2 ** tentativa - 1)` e `winning_stake = stake * (2 ** (tentativa - 1))` replicadas exatamente — zero divergencia de calculo entre funcoes.

3. **Funcoes puras sem DB:** `complementares_por_mercado` e `odd_por_mercado` recebidos como parametros dict — chamador e responsavel por buscar do banco via `get_complementares_config()` e `get_mercado_config()`.

## Deviations from Plan

**1. [Rule 2 - Funcionalidade critica] calculate_equity_curve_breakdown implementada em Task 1 GREEN**
- **Encontrado durante:** Task 1 RED phase
- **Situacao:** O bloco de import em tests/test_queries.py inclui ambas as funcoes no mesmo try/except. Com o import de `calculate_equity_curve_breakdown` falhando, `_IMPORTS_OK` ficava False e todos os 11 testes de Task 1 eram skipados em vez de falhar (RED invalido)
- **Fix:** Implementei `calculate_equity_curve_breakdown` junto com `calculate_pl_por_entrada` no mesmo commit GREEN, desbloquando os imports e permitindo RED/GREEN correto para Task 1
- **Arquivos modificados:** helpertips/queries.py
- **Commit:** 3320785

## Known Stubs

Nenhum — todas as funcoes retornam calculos reais. Phases 11-13 consumirao estas funcoes para tabelas P&L (DASH-04) e equity curve multi-mercado (DASH-06).

## Self-Check: PASSED
