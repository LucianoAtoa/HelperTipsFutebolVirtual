# Phase 3: Analytics Depth - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Breakdowns dimensionais (horario, dia da semana, periodo), curva de equity com comparacao Stake Fixa vs Gale, analise de Gale por nivel de tentativa, tracking de streaks, volume de sinais, cross-filtering avancado, e exibicao da taxa de cobertura do parser. Tudo integrado ao dashboard existente usando abas tematicas, mantendo KPIs/filtros/ROI fixos no topo.

</domain>

<decisions>
## Implementation Decisions

### Layout e Organizacao
- **D-01:** Novos graficos organizados em `dbc.Tabs` abaixo da secao fixa (KPIs, filtros, ROI principal, ROI complementares, AG Grid)
- **D-02:** Abas tematicas sugeridas: "Temporal" (heatmap + equity + dia da semana), "Gale & Streaks" (analise de Gale + streaks), "Volume" (volume por periodo + cross-dimensional)
- **D-03:** `active_tab` adicionado como Input no callback para lazy render — graficos so calculam quando a aba esta ativa
- **D-04:** Graficos existentes (bar chart resultados, win rate por liga) permanecem na secao fixa ou migram para aba relevante — Claude's discretion

### Curva de Equity
- **D-05:** Eixo X por sinal cronologico (indice 1, 2, 3…) — cada aposta com peso igual, streaks ficam uniformes
- **D-06:** Duas linhas sobrepostas: Stake Fixa (azul) e Gale (laranja) — comparacao direta do impacto usando `calculate_roi()` existente com `gale_on=False` e `gale_on=True`
- **D-07:** Marcadores coloridos nos pontos: verde para GREEN, vermelho para RED — resultado visivel em cada sinal
- **D-08:** Anotacao de texto nos maiores streaks (>=5 consecutivos) marcando inicio da sequencia
- **D-09:** Reset automatico ao filtro ativo — curva sempre comeca em 0 para o periodo selecionado, nao acumula historico fora do filtro

### Analise de Gale por Nivel
- **D-10:** Card composto com barras horizontais por tentativa (1a a 4a) mostrando taxa de GREEN + metricas inline de custo acumulado medio e perda media antes da recuperacao
- **D-11:** Responde 3 perguntas: (1) com que frequencia cada tentativa salva, (2) quanto custa o Gale acumulado, (3) qual o impacto financeiro liquido
- **D-12:** Barras horizontais (nao verticais) — mais legiveis para 4 categorias nomeadas

### Streaks
- **D-13:** Streak tracker mostra: streak atual (win/loss), maior streak historica (win e loss separados)
- **D-14:** Integrado na aba "Gale & Streaks" junto com analise de Gale — contexto relacionado

### Heatmap e Breakdowns Temporais
- **D-15:** Heatmap de win rate por horario do dia (eixo Y = hora, eixo X = dia da semana ou periodo)
- **D-16:** Bar chart de win rate por dia da semana — atualiza com filtros ativos
- **D-17:** Cross-dimensional: filtros compostos (liga + entrada + periodo) produzem breakdown de win rate e contagem

### Volume de Sinais
- **D-18:** Grafico de volume de sinais por dia/semana — revela padroes de atividade do grupo

### Cobertura do Parser
- **D-19:** Badge colorido no header do dashboard (nao misturado com KPIs de aposta — semantica operacional separada)
- **D-20:** Cor por threshold: verde (>=95%), amarelo (>=90%), vermelho (<90%)
- **D-21:** Click no badge abre modal (`dbc.Modal`) com tabela de `parse_failures` (raw_text, reason, received_at)
- **D-22:** Dados vem de `get_stats()` que ja retorna `coverage` e `parse_failures` count + query direta na tabela `parse_failures` para o modal

### Claude's Discretion
- Agrupamento exato das abas (quais graficos em qual aba)
- Posicao dos graficos existentes (bar chart resultados, win rate por liga) — manter fixos ou mover para aba
- Cores exatas dos graficos alem do definido (equity: azul/laranja, marcadores: verde/vermelho)
- Tamanho e proporcao dos graficos dentro de cada aba
- Formato das anotacoes de streak na equity curve
- Nivel de detalhe do cross-dimensional breakdown
- Se o volume chart usa barras ou area chart

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projeto
- `CLAUDE.md` — Stack (Dash 4.1.0, dbc 2.x, plotly_dark template, psycopg2-binary)
- `.planning/REQUIREMENTS.md` — Requisitos ANAL-01..08, OPER-01
- `.planning/ROADMAP.md` — Phase 3 success criteria e dependencias

### Fases anteriores
- `.planning/phases/02-core-dashboard/02-CONTEXT.md` — Decisoes de layout (D-01..D-17), tema DARKLY, filtros reativos, AG Grid, master callback pattern
- `.planning/phases/02.1-market-config/02.1-CONTEXT.md` — Decisoes de complementares, validacao por placar, ROI combinado

### Codigo existente
- `helpertips/dashboard.py` — Layout atual, master callback, imports, app init
- `helpertips/queries.py` — `calculate_roi()`, `_build_where()`, `get_filtered_stats()`, `get_signal_history()`, `_parse_placar()`, `validar_complementar()`
- `helpertips/store.py` — `get_stats()` retorna coverage e parse_failures count
- `helpertips/db.py` — Schema com tabelas signals, parse_failures, mercados, complementares

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `queries.py:calculate_roi()` — ROI puro Python com Gale, base para equity curve (iterar sinal a sinal acumulando)
- `queries.py:_build_where()` — WHERE builder para queries filtradas por liga/entrada/date
- `queries.py:get_signal_history()` — Retorna sinais ordenados por received_at DESC com filtros
- `queries.py:get_filtered_stats()` — Stats agregadas com COUNT FILTER
- `store.py:get_stats()` — Coverage e parse_failures count (sem filtros, global)
- `dashboard.py:make_kpi_card()` — Helper para criar KPI cards reutilizavel
- `dashboard.py:_build_comp_table()` — Helper para tabelas dbc.Table com totais

### Established Patterns
- Master callback multi-Input/Output com conn per invocation (close em finally)
- Tema DARKLY + plotly_dark template em todos os graficos
- Layout vertical com dbc.Container fluid + dbc.Row/Col grid
- Filtros reativos sem botao Apply (dropdown + DatePickerRange)
- Funcoes de query puras em queries.py, sem Dash dependency
- psycopg2 sync para queries

### Integration Points
- Master callback em dashboard.py — adicionar novos Outputs para abas e graficos
- `dbc.Tabs` inserido abaixo dos componentes fixos existentes
- `active_tab` como novo Input no callback para controlar lazy render
- `get_stats()` em store.py — ja fornece coverage para o badge
- Tabela `parse_failures` — query direta para popular o modal
- Campo `tentativa` nos sinais — base para analise de Gale

</code_context>

<specifics>
## Specific Ideas

- Equity curve com duas linhas sobrepostas permite o usuario ver exatamente quando o Gale ajuda vs quando amplifica perdas
- Heatmap de horario e util porque futebol virtual Bet365 roda 24/7 — pode revelar horarios com melhor taxa
- Analise de Gale por nivel e o insight mais valioso: mostra se vale a pena arriscar tentativas 3 e 4
- Badge de parser no header (nao nos KPIs) mantem separacao clara entre metricas operacionais e de apostas
- Cross-dimensional com filtros compostos ja funciona parcialmente via _build_where() — precisa apenas de novas queries de aggregacao

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-analytics-depth*
*Context gathered: 2026-04-03*
