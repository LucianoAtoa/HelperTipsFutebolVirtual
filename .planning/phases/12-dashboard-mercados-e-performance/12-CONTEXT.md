# Phase 12: Dashboard Mercados e Performance - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Adicionar duas secoes ao dashboard existente: (1) painel read-only de configuracao dos mercados mostrando principal e complementares com stakes por tentativa, e (2) tabela de performance P&L por entrada com toggle de visualizacao e visao geral vs por mercado. Estende o layout v1.2 criado na Phase 11 (filtros globais + KPIs).

</domain>

<decisions>
## Implementation Decisions

### Layout Config Mercados (DASH-03)
- **D-01:** Cards separados por mercado — um card para Over 2.5 e outro para Ambas Marcam. Cada card tem header com principal (odd referencia, stake base, progressao Gale T1-T4) e tabela interna de complementares (slug, nome, percentual, odd ref, stakes T1-T4 calculados).
- **D-02:** Dados carregados via `get_mercado_config()` (principal) e `get_complementares_config()` (complementares) — queries ja existem em queries.py.
- **D-03:** Stakes T1-T4 calculados on-the-fly a partir do stake base do card de simulacao: T1=stake*%, T2=T1*2, T3=T1*4, T4=T1*8.

### Toggle Performance (DASH-04)
- **D-04:** Toggle de visualizacao implementado com `dbc.RadioItems` usando `input_class_name="btn-check"` e labels `btn btn-outline-secondary` — mesmo pattern dos filtros de periodo da Phase 11 (D-04 do 11-CONTEXT). Opcoes: Percentual / Quantidade / P&L (R$).
- **D-05:** Modo "Percentual" mostra taxa green (%), taxa red (%), ROI (%). Modo "Quantidade" mostra greens (n), reds (n), total (n). Modo "P&L (R$)" mostra investido, retorno, P&L, ROI em reais.

### Visao Geral vs Por Mercado (DASH-04)
- **D-06:** Reusar o filtro global de mercado existente (Dropdown de Phase 11) para controlar a granularidade da tabela de performance. Quando "Todos" selecionado → visao geral (linhas agrupadas por entrada). Quando mercado especifico selecionado → visao por mercado com principal + cada complementar como linha separada.
- **D-07:** Sem UI adicional (toggle, tabs) para visao geral vs por mercado — o filtro global ja faz isso naturalmente. Consistencia com comportamento dos KPIs que tambem mudam com o filtro de mercado.

### Posicionamento no Layout
- **D-08:** Novas secoes substituem o `html.Div(id="analytics-placeholder")` existente. Ordem: Config Mercados → Performance → placeholder para Phase 13. Scroll continuo (sem accordions ou collapse).
- **D-09:** AG Grid de historico de sinais permanece apos as novas secoes. Ordem final do layout: filtros globais → KPIs → simulacao → config mercados → performance → historico → (Phase 13 placeholder).

### Claude's Discretion
- Organizacao interna dos callbacks (se um callback master atualiza tudo ou callbacks separados por secao)
- CSS para estilos dos cards de config e tabela de performance
- Nomes dos IDs dos novos componentes
- Se tabela de performance usa AG Grid ou dash_table.DataTable
- Formatacao dos valores monetarios (R$ com 2 casas decimais, cores verde/vermelho)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Dashboard Existente
- `helpertips/dashboard.py` — Layout v1.2 (426 linhas), callback master, `make_kpi_card()`, `analytics-placeholder` div, filtros globais, card simulacao
- `helpertips/queries.py` — `get_complementares_config()` (L379), `get_mercado_config()` (L421), `calculate_pl_por_entrada()` (L636), `_build_where()`, `get_filtered_stats()`, `calculate_roi()`, `calculate_roi_complementares()`

### Schema e Dados
- `helpertips/db.py` — `ensure_schema()`, tabelas mercados/complementares/signals, seeds de percentuais e odds por mercado
- `helpertips/store.py` — `ENTRADA_PARA_MERCADO_ID`, `_resolve_mercado_id()`

### Assets
- `helpertips/assets/` — CSS overrides para tema DARKLY (carregado automaticamente pelo Dash)

### Requisitos
- `.planning/REQUIREMENTS.md` secao DASH-03, DASH-04 — Requisitos especificos desta fase

### Contexto das Fases Anteriores
- `.planning/phases/10-l-gica-financeira/10-CONTEXT.md` — D-01: P&L on-the-fly, D-04/D-05: stake como input do dashboard
- `.planning/phases/11-dashboard-funda-o/11-CONTEXT.md` — D-01: reescrita layout, D-03: analytics removidas voltam 12-13, D-04: RadioItems btn-check pattern, D-13/D-14: card simulacao separado

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_complementares_config(conn, mercado_slug)`: Retorna lista de complementares com percentual, odd_ref, regra_validacao — base direta para DASH-03
- `get_mercado_config(conn, mercado_slug)`: Retorna config do mercado principal (odd_ref, nome_display) — header do card DASH-03
- `calculate_pl_por_entrada(signals, comps, stake, odds, gale_on)`: Retorna P&L detalhado por sinal — dados da tabela DASH-04
- `make_kpi_card(title, value_id, color_class)`: Helper de KPI card — pattern para novos cards
- `_build_where(mercado_id=...)`: Ja suporta filtro por mercado
- `dbc.RadioItems` com `btn-check` pattern: Ja implementado nos filtros de periodo

### Established Patterns
- Dark theme DARKLY com `dbc.Card` para secoes
- Callback master unico (`update_dashboard`) com todos os Inputs de filtro
- `get_connection()` dentro de callbacks
- Auto-refresh via `dcc.Interval` (60 segundos)
- `ctx.triggered_id` para identificar trigger

### Integration Points
- `html.Div(id="analytics-placeholder")` (L242): Hook para inserir novas secoes
- Callback master (L271-L382): Precisa ser estendido com Outputs para novas secoes
- Card simulacao (stake-input, odd-input, gale-toggle): Valores alimentam calculo de stakes T1-T4 na config e P&L na performance

</code_context>

<specifics>
## Specific Ideas

- Config de mercados e read-only — nao precisa de inputs editaveis, apenas display dos valores atuais do banco
- Stakes T1-T4 sao dinamicos (mudam com stake base do card de simulacao) — os cards de config precisam ser reativos ao callback
- Tabela de performance precisa agregar dados de `calculate_pl_por_entrada()` por entrada (entrada principal + cada complementar) — agrupamento em Python
- DASH-03 e DASH-04 compartilham o callback master pois dependem dos mesmos filtros globais + parametros de simulacao

</specifics>

<deferred>
## Deferred Ideas

- Grafico de barras empilhadas P&L por liga — Phase 13 (DASH-05)
- Equity curve com 3 linhas (principal, complementar, total) — Phase 13 (DASH-06)
- Donut chart de gale com distribuicao por tentativa — Phase 13 (DASH-07)

</deferred>

---

*Phase: 12-dashboard-mercados-e-performance*
*Context gathered: 2026-04-04*
