# Phase 11: Dashboard Fundacao - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Redesign da fundacao do dashboard: filtros globais fixos no topo (periodo, mercado, liga) que afetam todos os cards e graficos, e KPI cards com P&L real (principal+complementar). Esta fase substitui o layout antigo do dashboard.py e estabelece a estrutura base que as fases 12-13 estendem.

</domain>

<decisions>
## Implementation Decisions

### Estrategia de Reescrita
- **D-01:** Reescrita do layout do zero — substituir o `app.layout` existente no dashboard.py pelo novo design v1.2. Nao tentar coexistir filtros antigos com novos (causa conflito de callback IDs e dois sistemas de state paralelos). Helpers de figuras reutilizaveis (`_build_comp_table`, `make_kpi_card` etc.) devem ser preservados/copiados seletivamente.
- **D-02:** Callbacks existentes serao reescritos para usar os novos IDs de filtros globais. Callback master unico desde o inicio.
- **D-03:** Secoes de analytics tabs (heatmap, equity, gale, streaks, volume) serao temporariamente removidas — voltam redesenhadas nas fases 12-13. AG Grid de historico pode ser preservado se nao conflitar com o novo layout.

### Filtros Globais (DASH-01)
- **D-04:** Filtro de periodo usa `dbc.RadioItems` com `input_class_name="btn-check"` e labels estilizadas como `btn btn-outline-secondary` — visual de botoes segmentados, `value` nativo no callback sem state extra.
- **D-05:** Opcoes de periodo: Hoje, Esta Semana, Este Mes, Mes Passado, Toda a Vida, Personalizado. Selecionar "Personalizado" mostra `dcc.DatePickerRange` condicionalmente via `dbc.Collapse` ou `style`.
- **D-06:** Filtro de mercado: `dcc.Dropdown` com opcoes Todos / Over 2.5 / Ambas Marcam (reusa padrao existente).
- **D-07:** Filtro de liga: `dcc.Dropdown` populado dinamicamente via `get_distinct_values()` (padrao existente).
- **D-08:** Possivel necessidade de 3-5 linhas de CSS override para contraste de `btn-outline-secondary` no tema DARKLY.

### KPI Cards (DASH-02)
- **D-09:** Row unica com 6 KPI cards hibridos: Total Sinais, Taxa Green (%), P&L Total (R$), ROI (%), Melhor Streak Green, Pior Streak Red.
- **D-10:** P&L Total mostra valor unico (principal + complementar somados). Breakdown principal/complementar/total e delegado para a equity curve da Phase 13. Consistencia visual com os demais cards.
- **D-11:** Todos os KPIs reativos aos filtros globais (periodo + mercado + liga).
- **D-12:** Reusar pattern `make_kpi_card()` existente — adaptar para novos IDs e cores.

### Posicionamento do Stake
- **D-13:** Stake/odd/gale permanecem em card de configuracao separado abaixo dos filtros globais (nao dentro da barra de filtros). Separacao semantica: filtros = recorte de dados, stake = parametro de simulacao.
- **D-14:** Card de simulacao mantem inputs de Stake (R$), Odd, e toggle Gale (similar ao existente). Valores afetam P&L dos KPIs e todas as secoes de P&L.

### Claude's Discretion
- Organizacao interna do dashboard.py (funcoes helper, order do layout)
- CSS override exato para contraste dos RadioItems no DARKLY
- Se AG Grid de historico de sinais e preservado nesta fase ou movido para fase futura
- Nomes dos IDs dos novos componentes de filtro
- Estrategia de teste dos callbacks (se aplicavel)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Dashboard Existente
- `helpertips/dashboard.py` -- Layout atual (1004 linhas), callbacks, helpers (`make_kpi_card`, `_build_comp_table`, `_entrada_para_slug`), imports de queries.py
- `helpertips/queries.py` -- Todas as funcoes de query e calculo: `_build_where()`, `get_filtered_stats()`, `calculate_roi()`, `calculate_roi_complementares()`, `calculate_pl_por_entrada()`, `calculate_equity_curve_breakdown()`, `calculate_streaks()`, `get_distinct_values()`, `get_signal_history()`

### Schema e Dados
- `helpertips/db.py` -- `ensure_schema()`, tabelas mercados/complementares/signals, `get_connection()`
- `helpertips/store.py` -- `ENTRADA_PARA_MERCADO_ID`, `_resolve_mercado_id()`

### Requisitos
- `.planning/REQUIREMENTS.md` secao DASH-01, DASH-02 -- Requisitos especificos desta fase

### Contexto das Fases Anteriores
- `.planning/phases/09-listener-multi-grupo/09-CONTEXT.md` -- Decisoes de multi-grupo e mercado_id
- `.planning/phases/10-l-gica-financeira/10-CONTEXT.md` -- Decisoes de P&L on-the-fly, stake como parametro

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `make_kpi_card(title, value_id, color_class)`: Helper de KPI card com dbc.Card — adaptar para novos IDs
- `_build_comp_table(por_mercado)`: Tabela de complementares — util na Phase 12
- `_entrada_para_slug(entrada)`: Mapeamento entrada → slug de mercado
- `_ENTRADA_SLUG_MAP`: Dict de mapeamento Over 2.5 → over_2_5, Ambas Marcam → ambas_marcam
- `get_distinct_values(conn, field)`: Popula dropdowns de liga/entrada dinamicamente
- `get_filtered_stats(conn, ...)`: Stats filtradas com `_build_where()` — base dos KPIs
- `calculate_roi()` / `calculate_roi_complementares()`: P&L principal e complementar
- `calculate_pl_por_entrada()`: P&L detalhado por entrada (novo na Phase 10)
- `calculate_streaks()`: Melhor/pior streaks — alimenta KPIs de streak

### Established Patterns
- Dark theme DARKLY com dbc.Card para sections
- Callbacks Dash com `@callback` decorator e `Input/Output/State`
- `get_connection()` dentro de callbacks para queries
- Auto-refresh via `dcc.Interval` (60 segundos)
- `ctx.triggered_id` para identificar qual input disparou o callback

### Integration Points
- `_build_where(mercado_id=...)`: Ja suporta filtro por mercado (adicionado na Phase 10)
- `get_signals_com_placar()`: Query que retorna sinais com JOIN em mercados — base para P&L
- `get_complementares_config(conn, mercado_slug)`: Config por mercado para calculo de complementares
- `dcc.Interval`: Manter auto-refresh para atualizar KPIs periodicamente

</code_context>

<specifics>
## Specific Ideas

- Dashboard e breaking change visual — todo o layout muda. Deploy coordenado apos teste local.
- Fases 12-13 adicionam secoes ao layout que esta fase cria — o "esqueleto" precisa ter placeholders claros.
- `_build_where()` ja suporta `mercado_id` (Phase 10) — filtro de mercado no dropdown e direto.
- Streaks (melhor green, pior red) ja calculados por `calculate_streaks()` — so precisa conectar ao KPI card.

</specifics>

<deferred>
## Deferred Ideas

- Secoes de analytics tabs (heatmap, equity curve, DOW, gale, streaks, volume) — voltam redesenhadas nas Phases 12-13
- Toggle percentual/quantidade/R$ na tabela de performance — Phase 12
- Donut chart de gale — Phase 13
- Grafico de barras empilhadas P&L por liga — Phase 13

</deferred>

---

*Phase: 11-dashboard-funda-o*
*Context gathered: 2026-04-04*
