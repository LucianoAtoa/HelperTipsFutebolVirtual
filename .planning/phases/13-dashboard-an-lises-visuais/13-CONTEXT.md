# Phase 13: Dashboard Analises Visuais - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Adicionar 3 secoes visuais de analise ao dashboard existente: (1) analise por liga com grafico de barras empilhadas e tabela, (2) equity curve com 3 linhas sobrepostas (principal, complementar, total), (3) analise de gale com donut chart e tabela. Todas as secoes sao reativas aos filtros globais existentes (periodo, mercado, liga). Substitui o `phase13-placeholder` div (L470 dashboard.py).

</domain>

<decisions>
## Implementation Decisions

### Esquema de Cores dos Graficos
- **D-01:** Paleta semantica alinhada ao tema DARKLY — reutilizar as cores ja associadas pelo usuario: `#00bc8c` (success DARKLY) para principal/lucro, `#e74c3c` (danger) para complementar/perda, `#f39c12` (warning) para total/acumulado. Mantém consistencia com KPI cards que ja usam `#28a745`/`#dc3545`.
- **D-02:** Donut chart de gale usa 4 tons derivados do success (`#00bc8c` com variações de lightness) para reforcar que todas as tentativas fazem parte do mesmo desfecho.
- **D-03:** Barras empilhadas por liga usam `#00bc8c` (P&L principal) e `#e74c3c` (P&L complementar) — mesma codificacao das linhas da equity curve.

### Layout e Ordem das Secoes
- **D-04:** Ordem narrativa: Liga -> Equity Curve -> Gale. Fluxo analitico: contexto dimensional (quais ligas performam) -> evolucao temporal (como saldo evolui) -> granularidade operacional (distribuicao por tentativa).
- **D-05:** Scroll continuo sem accordions, tabs ou collapse — confirma pattern D-08 da Phase 12. Cada secao em `dbc.Card` com header descritivo.
- **D-06:** Secoes inseridas no `phase13-placeholder` (L470 dashboard.py), antes do AG Grid de historico. Ordem final do layout: filtros globais -> KPIs -> simulacao -> config mercados -> performance -> **liga -> equity curve -> gale** -> historico.

### Dados de Gale Expandidos (DASH-07)
- **D-07:** Criar funcao pura `aggregate_pl_por_tentativa(pl_lista)` em queries.py que agrupa output de `calculate_pl_por_entrada()` por tentativa, calculando lucro_medio_green = sum(lucro_total for GREEN) / count(GREEN). Lucro depende de stake/odd/gale_on (parametros dinamicos da UI) — impossivel calcular no SQL.
- **D-08:** Reutilizar a chamada `calculate_pl_por_entrada()` ja existente no callback master (Phase 12) para alimentar tanto a tabela de performance quanto a nova secao de gale. Sem round-trip extra ao banco.
- **D-09:** `get_gale_analysis()` existente continua fornecendo quantidade e percentual por tentativa (greens, total, win_rate). A nova funcao complementa com lucro medio.

### Interatividade dos Graficos
- **D-10:** Hover tooltips ricos com `hovertemplate` formatado em todos os 3 graficos. Equity curve mostra data + P&L principal + complementar + total por ponto. Barras mostram liga + greens + reds + P&L. Donut mostra tentativa + percentual + lucro medio.
- **D-11:** Sem range slider na equity curve — periodo ja controlado pelos filtros globais, evita redundancia de controle e conflito visual.
- **D-12:** Sem click-to-filter (clickData) — filtro-liga dropdown existente ja satisfaz a necessidade, evita complexidade no callback master e problema de clickData stale.
- **D-13:** Zoom/pan nativo do Plotly permanece habilitado por padrao (comportamento default, sem configuracao extra).

### Claude's Discretion
- Organizacao interna dos builders de figuras Plotly (funcoes helper separadas ou inline)
- Nomes exatos dos IDs dos novos componentes (graficos e tabelas)
- Se tabelas de liga e gale usam `dbc.Table` ou `dash_table.DataTable`
- CSS adicional para estilos dos novos cards (se necessario)
- Estrategia de teste dos novos callbacks/helpers
- Template exato dos hovertemplates (formatacao de R$, decimais)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Dashboard Existente
- `helpertips/dashboard.py` — Layout v1.2 (693 linhas), callback master, `phase13-placeholder` (L470), `make_kpi_card()`, `_calcular_stakes_gale()`, `_agregar_por_entrada()`, imports de queries.py, `plotly.graph_objects as go` ja importado
- `helpertips/queries.py` — `calculate_equity_curve_breakdown()` (L959), `get_gale_analysis()` (L1128), `calculate_pl_por_entrada()` (L636), `_build_where()`, `get_filtered_stats()`, `get_distinct_values()`, `get_signals_com_placar()`

### Schema e Dados
- `helpertips/db.py` — `ensure_schema()`, tabelas mercados/complementares/signals
- `helpertips/store.py` — `ENTRADA_PARA_MERCADO_ID`, `_resolve_mercado_id()`

### Assets
- `helpertips/assets/` — CSS overrides para tema DARKLY (carregado automaticamente pelo Dash)

### Requisitos
- `.planning/REQUIREMENTS.md` secao DASH-05, DASH-06, DASH-07 — Requisitos especificos desta fase

### Contexto das Fases Anteriores
- `.planning/phases/10-l-gica-financeira/10-CONTEXT.md` — D-01: P&L on-the-fly, D-04/D-05: stake como input do dashboard
- `.planning/phases/11-dashboard-funda-o/11-CONTEXT.md` — D-01: reescrita layout, D-02: callback master unico, D-03: analytics removidas voltam 12-13, D-04: RadioItems btn-check pattern
- `.planning/phases/12-dashboard-mercados-e-performance/12-CONTEXT.md` — D-08: scroll continuo sem accordions, D-09: AG Grid apos novas secoes

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `calculate_equity_curve_breakdown(signals, comps, stake, odds, gale_on)`: Retorna {x, y_principal, y_complementar, y_total, colors} — base direta para DASH-06
- `get_gale_analysis(conn, liga, entrada, date_start, date_end)`: Retorna [{tentativa, greens, total, win_rate}] — base parcial para DASH-07 (falta lucro medio)
- `calculate_pl_por_entrada(signals, comps, stake, odds, gale_on)`: P&L detalhado por sinal — fonte para agregar lucro medio por tentativa
- `get_signals_com_placar(conn, ...)`: Sinais com placar em ordem ASC — input para equity curve e P&L
- `plotly.graph_objects as go`: Ja importado no dashboard.py (L28)
- `_calcular_stakes_gale(stake_base, percentual)`: Calcula T1-T4 — reutilizavel
- `_agregar_por_entrada()`: Pattern de agregacao por dimensao — replicar para `aggregate_pl_por_tentativa()`

### Established Patterns
- Dark theme DARKLY com `dbc.Card` para secoes
- Callback master unico (`update_dashboard`) com todos os Inputs de filtro
- Funcoes puras sem DB testaveis por TDD em queries.py
- `dbc.Table(color='dark')` para tabelas (nao `dark=True` — D do 12-CONTEXT)

### Integration Points
- `phase13-placeholder` div (L470 dashboard.py) — ponto de insercao
- Callback master ja recebe todos os filtros globais como Input — estender com novos Outputs
- `get_signals_com_placar()` e `calculate_pl_por_entrada()` ja chamados no callback — reutilizar resultados

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-dashboard-an-lises-visuais*
*Context gathered: 2026-04-04*
