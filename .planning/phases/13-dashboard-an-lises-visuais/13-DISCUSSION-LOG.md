# Phase 13: Dashboard Analises Visuais - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 13-dashboard-an-lises-visuais
**Areas discussed:** Esquema de cores, Layout e ordem, Dados de gale, Interatividade
**Mode:** --auto (all choices auto-selected as recommended defaults)

---

## Esquema de Cores dos Graficos

| Option | Description | Selected |
|--------|-------------|----------|
| Paleta nativa plotly_dark | Zero config, 10 cores otimizadas para fundo escuro, sem semantica financeira | |
| Paleta semantica alinhada ao DARKLY | Verde #00bc8c (success), vermelho #e74c3c (danger), amarelo #f39c12 (warning) — mesma linguagem dos KPIs | :white_check_mark: |
| Paleta personalizada independente | Tableau Dark/IBM Carbon, alto contraste, terceira linguagem de cor | |

**User's choice:** [auto] Paleta semantica alinhada ao DARKLY (recommended default)
**Notes:** Reutiliza cores ja treinadas pelo usuario nos KPI cards (#28a745/#dc3545). Donut usa tons derivados do success.

---

## Layout e Ordem das Secoes

| Option | Description | Selected |
|--------|-------------|----------|
| Liga -> Equity Curve -> Gale | Fluxo narrativo: agregado por liga -> evolucao temporal -> granularidade tentativa | :white_check_mark: |
| Equity Curve primeiro | Impacto visual imediato, equity como feature principal | |
| Scroll continuo (confirmacao) | Sem tabs/accordions — confirma D-08 Phase 12 | :white_check_mark: |

**User's choice:** [auto] Liga -> Equity Curve -> Gale com scroll continuo (recommended default)
**Notes:** Padrão ja decidido na Phase 12 (D-08). Ordem segue logica analitica existente no dashboard.

---

## Dados de Gale Expandidos

| Option | Description | Selected |
|--------|-------------|----------|
| Expandir get_gale_analysis() com SQL | AVG de lucro no banco — impossivel pois lucro depende de stake/odd/gale_on dinamicos | |
| Nova funcao pura aggregate_pl_por_tentativa() | Agrupa output de calculate_pl_por_entrada() por tentativa, calcula lucro_medio_green | :white_check_mark: |
| Campo lucro_medio via join com config | Nova tabela/coluna no schema — over-engineering | |

**User's choice:** [auto] Nova funcao pura aggregate_pl_por_tentativa() (recommended default)
**Notes:** Lucro depende de parametros dinamicos da UI (stake, odd, gale_on). Impossivel calcular no SQL. Segue padrao de funcoes puras testaveis.

---

## Interatividade dos Graficos

| Option | Description | Selected |
|--------|-------------|----------|
| Hover tooltips basicos | Zero callbacks adicionais, menos contexto por ponto | |
| Hover tooltips ricos com hovertemplate | Valores contextuais ricos (data, P&L, liga, tentativa), sem callbacks extras | :white_check_mark: |
| Zoom/pan + range slider | Navegacao temporal, conflita com filtro periodo existente | |
| Click-to-filter (clickData) | Alto valor analitico, complexidade no callback master, clickData stale | |

**User's choice:** [auto] Hover tooltips ricos com hovertemplate (recommended default)
**Notes:** Melhor custo-beneficio para dashboard pessoal. Sem range slider (periodo ja controlado por filtros globais). Sem click-to-filter (dropdown liga ja satisfaz).

---

## Claude's Discretion

- Organizacao interna dos builders de figuras Plotly
- Nomes dos IDs dos novos componentes
- Tipo de tabela (dbc.Table vs dash_table.DataTable)
- CSS adicional, estrategia de teste, formatacao dos hovertemplates

## Deferred Ideas

None — discussion stayed within phase scope
