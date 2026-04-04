---
phase: 10-l-gica-financeira
verified: 2026-04-04T14:45:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 10: Lógica Financeira — Relatório de Verificação

**Phase Goal:** Cada sinal gera entradas complementares com P&L calculado corretamente por mercado e tentativa
**Verificado:** 2026-04-04T14:45:00Z
**Status:** PASSED
**Re-verificação:** Não — verificação inicial

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `_build_where(mercado_id=1)` gera cláusula SQL com `mercado_id = %s` | VERIFIED | `queries.py:68-70` — bloco `if mercado_id is not None:` adiciona `"mercado_id = %s"` |
| 2 | `get_signals_com_placar()` retorna sinais resolvidos com `mercado_id` e `mercado_slug` | VERIFIED | `queries.py:457-507` — LEFT JOIN mercados, SELECT inclui `s.mercado_id, m.slug AS mercado_slug` |
| 3 | `get_mercado_config()` retorna config de um mercado por slug | VERIFIED | `queries.py:421-449` — query `FROM mercados WHERE slug = %s AND ativo = TRUE`, retorna dict ou None |
| 4 | `calculate_pl_por_entrada` retorna P&L por sinal com breakdown principal vs complementar | VERIFIED | `queries.py:636-754` — retorna `investido_principal, lucro_principal, investido_comp, lucro_comp, lucro_total` por sinal |
| 5 | Fórmulas Gale T1-T4 matematicamente corretas | VERIFIED | `queries.py:682-698` — `accumulated_stake = stake * (2 ** tentativa - 1)`, `winning_stake = stake * (2 ** (tentativa - 1))` — idênticas a `calculate_roi` existente |
| 6 | Complementares usam percentuais diferenciados por mercado (Over 2.5 vs Ambas Marcam) | VERIFIED | `queries.py:702-753` — `complementares_por_mercado.get(mercado_slug, [])` com percentual por comp; testes `test_pl_complementares_over_2_5` e `test_pl_complementares_ambas_marcam` passam |
| 7 | `calculate_equity_curve_breakdown` retorna 3 séries: `y_principal`, `y_complementar`, `y_total` | VERIFIED | `queries.py:959-1064` — dict com 5 chaves: x, y_principal, y_complementar, y_total, colors |
| 8 | `y_total[i] == y_principal[i] + y_complementar[i]` para todo i | VERIFIED | `queries.py:1055` — `y_total.append(round(bk_principal + bk_comp, 2))`; `test_equity_curve_breakdown_total_soma` passa |

**Pontuação:** 8/8 verdades verificadas

---

### Artefatos Requeridos

| Artefato | Fornece | Status | Detalhes |
|----------|---------|--------|----------|
| `helpertips/queries.py` | `_build_where`, `get_signals_com_placar`, `get_mercado_config`, `calculate_pl_por_entrada`, `calculate_equity_curve_breakdown` | VERIFIED | Todas as 5 funções presentes, substantivas e operacionais |
| `tests/test_queries.py` | Testes TDD cobrindo todos os cenários | VERIFIED | 106 funções de teste totais; 27 novas da Phase 10; todas passam |

---

### Verificação de Key Links

| From | To | Via | Status | Detalhes |
|------|----|-----|--------|---------|
| `get_signals_com_placar` | `_build_where` | chamada com `mercado_id=mercado_id` | WIRED | `queries.py:488-492` — chamada explícita com todos os filtros incluindo `mercado_id` |
| `get_signals_com_placar` | `tabela signals JOIN mercados` | `LEFT JOIN mercados m ON s.mercado_id = m.id` | WIRED | `queries.py:497` — LEFT JOIN presente, mantém sinais históricos sem mercado_id |
| `calculate_pl_por_entrada` | `validar_complementar` | chamada para cada complementar | WIRED | `queries.py:711-715` — `validar_complementar(comp["regra_validacao"], signal.get("placar"), signal.get("resultado"))` |
| `calculate_equity_curve_breakdown` | `validar_complementar` | chamada na curva de complementares | WIRED | `queries.py:1029-1033` — mesma chamada replicada na lógica de equity |

---

### Data-Flow Trace (Level 4)

Estas funções são utilitários de cálculo puro (não renderizam dados diretamente), portanto o fluxo relevante é: dados de entrada (sinais do DB) → cálculo → resultado consumido pelas Phases 11-13.

| Artefato | Tipo | Origem dos Dados | Status |
|----------|------|-----------------|--------|
| `get_signals_com_placar` | Query DB | `signals` + `mercados` via LEFT JOIN | FLOWING — query real, não retorno estático |
| `get_mercado_config` | Query DB | tabela `mercados` WHERE slug + ativo | FLOWING — query real com parâmetro |
| `calculate_pl_por_entrada` | Função pura | recebe `signals` e `complementares_por_mercado` como params | FLOWING — sem DB, chamador fornece dados reais |
| `calculate_equity_curve_breakdown` | Função pura | recebe `signals` e `complementares_por_mercado` como params | FLOWING — sem DB, chamador fornece dados reais |

Nota: As funções puras (`calculate_pl_por_entrada`, `calculate_equity_curve_breakdown`) são intencionalmente desacopladas do banco — o padrão D-01/D-06 exige que o chamador forneça os dados. Esse é o design correto, não um gap.

---

### Spot-Checks Comportamentais

| Comportamento | Comando | Resultado | Status |
|---------------|---------|-----------|--------|
| Suite completa sem regressão | `python3 -m pytest tests/ -q` | 177 passed in 1.19s | PASS |
| Testes da Phase 10 (27 novos) | `pytest -k "test_pl_ or test_equity_curve_breakdown or test_build_where_mercado_id or test_get_mercado_config or test_get_signals_com_placar"` | 27 passed, 79 deselected | PASS |
| GREEN T1: lucro_principal=130 | `test_pl_green_t1` | PASSED | PASS |
| GREEN T2 Gale: lucro=160 | `test_pl_green_t2_gale` | PASSED | PASS |
| RED T4: lucro=-1500 | `test_pl_red_t4` | PASSED | PASS |
| y_total = y_principal + y_complementar | `test_equity_curve_breakdown_total_soma` | PASSED | PASS |
| Lista vazia → séries vazias | `test_equity_curve_breakdown_lista_vazia` | PASSED | PASS |

---

### Cobertura de Requisitos

| Requisito | Plano | Descrição | Status | Evidência |
|-----------|-------|-----------|--------|-----------|
| FIN-01 | 10-01, 10-02 | Cada sinal gera entradas complementares com stake proporcional (% da principal) e odds de referência configuráveis por mercado | SATISFIED | `get_mercado_config` retorna `odd_ref`; `calculate_pl_por_entrada` usa `percentual` por complementar por mercado |
| FIN-02 | 10-02 | Cálculo de P&L por entrada (investido, retorno, lucro) com Martingale progressivo T1-T4 | SATISFIED | `calculate_pl_por_entrada` retorna todos os campos; testes cobrem T1-T4 com valores exatos |
| FIN-03 | 10-01, 10-02 | Complementares têm configuração diferenciada por mercado — Over 2.5 vs Ambas Marcam com % específicos | SATISFIED | `_build_where` filtra por `mercado_id`; `complementares_por_mercado` dict separa configs por mercado; testes `test_pl_complementares_over_2_5` e `test_pl_complementares_ambas_marcam` verificam valores distintos |

Todos os 3 requisitos declarados nos PLANs estão presentes em REQUIREMENTS.md com status "Complete" no campo Traceability. Nenhum requisito órfão detectado.

---

### Anti-Patterns Encontrados

Nenhum anti-pattern bloqueante detectado.

| Arquivo | Linha | Padrão | Severidade | Impacto |
|---------|-------|--------|------------|---------|
| `queries.py` | 47 (docstring) | "placeholders" em texto de documentação | Info | Falso positivo — é texto da docstring de `_build_where`, não código stub |

---

### Verificação Humana Necessária

Nenhum item requer verificação humana nesta phase. As funções são lógica pura verificável por testes unitários automatizados. A integração com o dashboard (renderização visual, filtros interativos) será verificada nas Phases 11-13.

---

## Resumo dos Gaps

Nenhum gap encontrado. Todos os must-haves foram verificados com evidência direta no código e nos testes executados.

**Pontuação final: 8/8 verdades verificadas. Suite completa: 177 testes passando sem regressão.**

---

_Verificado: 2026-04-04T14:45:00Z_
_Verificador: Claude (gsd-verifier)_
