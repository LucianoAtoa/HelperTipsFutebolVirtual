# Phase 12: Dashboard Mercados e Performance - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 12-dashboard-mercados-e-performance
**Areas discussed:** Layout Config Mercados, Toggle Performance, Visao Geral vs Por Mercado, Posicionamento no Layout
**Mode:** --auto (all decisions auto-selected)

---

## Layout Config Mercados (DASH-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Cards separados por mercado | Um card por mercado (Over 2.5, Ambas Marcam) com header principal e tabela complementares interna | auto |
| Tabela unificada | Tabela unica com mercado como coluna/grupo | |
| Accordion por mercado | Secoes colapsaveis, uma por mercado | |

**User's choice:** Cards separados por mercado (auto-selected: recommended default)
**Notes:** Reusa pattern de `_build_comp_table()`, visual claro para 2 mercados, match direto com DASH-03.

---

## Toggle Performance (DASH-04)

| Option | Description | Selected |
|--------|-------------|----------|
| dbc.RadioItems btn-check | Segmented buttons igual filtros de periodo (Phase 11) | auto |
| dbc.Tabs | Tabs de navegacao entre modos | |
| dcc.Dropdown | Dropdown selector | |

**User's choice:** dbc.RadioItems btn-check (auto-selected: recommended default — consistencia com Phase 11)
**Notes:** Mesmo pattern dos filtros de periodo (D-04 do 11-CONTEXT). 3 opcoes: Percentual / Quantidade / P&L (R$).

---

## Visao Geral vs Por Mercado (DASH-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Filtro global de mercado | Reusar filtro existente — "Todos" = geral, especifico = por mercado | auto |
| Toggle dedicado | Switch/toggle separado para alternar visoes | |
| Tabs (Geral/Over/Ambas) | Tabs locais na secao de performance | |

**User's choice:** Filtro global de mercado (auto-selected: recommended default — DRY, zero UI adicional)
**Notes:** Consistencia com KPIs que ja mudam com filtro de mercado. Sem UI extra.

---

## Posicionamento no Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Substituir analytics-placeholder | Scroll continuo, secoes sempre visiveis | auto |
| Accordions/Collapse | Secoes colapsaveis para reduzir scroll | |
| Inserir entre simulacao e grid | Manter placeholder para Phase 13 separadamente | |

**User's choice:** Substituir analytics-placeholder (auto-selected: recommended default — hook ja existe, desktop-first)
**Notes:** Ordem: Config Mercados → Performance → Phase 13 placeholder → AG Grid historico.

---

## Claude's Discretion

- Organizacao interna dos callbacks
- CSS para estilos dos cards de config e tabela de performance
- IDs dos novos componentes
- Escolha entre AG Grid e DataTable para tabela de performance
- Formatacao de valores monetarios

## Deferred Ideas

- Graficos de liga, equity curve e gale — Phase 13
