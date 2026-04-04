# Phase 10: Lógica Financeira - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 10-lógica-financeira
**Areas discussed:** Armazenamento de P&L, Stake base, Trigger de cálculo, Regras por mercado
**Mode:** --auto (all areas auto-selected, recommended defaults chosen)

---

## Armazenamento de P&L

| Option | Description | Selected |
|--------|-------------|----------|
| On-the-fly (status quo) | `calculate_roi_complementares()` em Python puro, sem tabela nova | ✓ |
| Materializar P&L em tabela | Nova tabela `signal_pnl` com rows por sinal × complementar | |
| Materializar apenas agregados | Tabela `mercado_stats` com greens/reds/lucro por mercado + liga | |

**User's choice:** [auto] On-the-fly (status quo) — recommended default
**Notes:** Stake e gale_on são parâmetros dinâmicos do dashboard. Materializar valores absolutos seria invalidado a cada mudança de stake. Volume baixo não justifica sincronização de tabela extra.

---

## Stake Base

| Option | Description | Selected |
|--------|-------------|----------|
| Input do dashboard (status quo) | Stake como parâmetro de simulação no dashboard | ✓ |
| Variável no .env | `STAKE_BASE` lida pelo listener e funções | |
| Coluna na tabela mercados | `stake_base` por mercado, persistida no banco | |
| dcc.Store (localStorage) | Persiste no browser mas não no banco | |

**User's choice:** [auto] Input do dashboard (status quo) — recommended default
**Notes:** Decorre da decisão de manter P&L on-the-fly. Sem necessidade de persistir stake no banco quando o cálculo é feito em cada request do dashboard.

---

## Trigger de Cálculo

| Option | Description | Selected |
|--------|-------------|----------|
| On-the-fly no dashboard | Cálculo puro Python em callbacks do Dash, sem persistência | ✓ |
| No upsert (listener) | Listener calcula e persiste P&L quando resultado chega | |
| Batch job periódico | Script separado recalcula periodicamente | |

**User's choice:** [auto] On-the-fly no dashboard — recommended default
**Notes:** Consistente com decisão de armazenamento. `calculate_roi_complementares()` já existe e funciona. Sem schema change, sem migration na EC2.

---

## Regras de Complementares por Mercado

| Option | Description | Selected |
|--------|-------------|----------|
| Reusar mesmos 7 slugs (status quo) | Mesmas regras de validação, percentuais já diferem por mercado | ✓ |
| Substituir por complementares específicos | Resultado exato, handicap, mercados ortogonais para Ambas Marcam | |
| Complementares híbridos | Manter Over 3.5/5+ mas trocar exatos por Over 1.5 e Under 4.5 | |

**User's choice:** [auto] Reusar mesmos 7 slugs (status quo) — recommended default
**Notes:** Seeds e validators já corretos. Over 3.5 como complementar de Ambas Marcam diferencia dentro dos GREENs do principal (valor analítico válido). Redesenhar é decisão estratégica de apostas, não de engenharia.

---

## Claude's Discretion

- Organização interna das funções (refatorar vs estender existentes)
- Nomes de parâmetros e assinaturas das funções estendidas
- Estratégia de teste (quais cenários de P&L cobrir)
- Se queries.py deve ser dividido em módulos menores

## Deferred Ideas

- Materialização de P&L no banco como otimização de performance futura
- Redesenho de complementares de Ambas Marcam com mercados específicos
- Stake diferenciada por mercado (coluna stake_base na tabela mercados)
