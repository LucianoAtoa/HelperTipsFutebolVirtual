---
phase: 3
slug: analytics-depth
status: draft
shadcn_initialized: false
preset: none
created: 2026-04-03
---

# Phase 3 — UI Design Contract

> Visual and interaction contract para a Fase 3: Analytics Depth.
> Gerado por gsd-ui-researcher. Verificado por gsd-ui-checker.

---

## Design System

| Property | Value | Source |
|----------|-------|--------|
| Tool | none | CONTEXT.md — projeto e ferramenta pessoal Python/Dash, sem React/Next.js |
| Preset | not applicable | Stack definida em CLAUDE.md |
| Component library | dash-bootstrap-components 2.0.4 (Bootstrap 5) | RESEARCH.md — Standard Stack |
| Icon library | none — Bootstrap classes via dbc (color badges, not icon glyphs) | CONTEXT.md D-20 |
| Font | Bootstrap 5 default (system-ui stack) | DARKLY theme via dbc.themes.DARKLY |
| Theme | DARKLY (Bootstrap 5 dark) + plotly_dark Plotly template | 02-CONTEXT.md D-01, D-02; dashboard.py line 44 |

Registry Safety: not applicable — projeto Python puro, sem NPM registry.

---

## Spacing Scale

Declarado em unidades do Bootstrap 5 (rem-based, 1 rem = 16px base):

| Token | Bootstrap class | px equiv | Usage |
|-------|----------------|----------|-------|
| xs | `p-1` / `g-1` | 4px | Icon gaps, badge padding inline |
| sm | `p-2` / `g-2` | 8px | Compact element spacing, card padding interno |
| md | `p-3` / `g-3` | 16px | Default element spacing, row gap |
| lg | `p-4` / `g-4` | 24px | Section padding, card body |
| xl | `p-5` / `g-5` | 32px | Layout gaps entre secoes principais |

Excecoes:
- `dcc.Graph` height: heatmap = 400px, equity curve = 350px, bar charts = 300px, volume chart = 280px
- `dbc.Tabs` margin-top: 24px (lg) acima da secao fixa existente
- Streak KPI mini-cards: padding interno 8px (sm), sem padding extra

---

## Typography

Tipografia controlada pelo tema DARKLY (Bootstrap 5). Declarar apenas sobreposicoes explicitas:

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Body | 14px (0.875rem Bootstrap default in dbc) | 400 (regular) | 1.5 | Legendas de graficos, labels de filtros, conteudo modal |
| Label | 12px (0.75rem, `small` Bootstrap) | 400 (regular) | 1.4 | Eixos dos graficos (plotly font_size=11), badge de cobertura |
| Heading | 16px (1rem, `h5` Bootstrap) | 600 (semibold, `fw-bold`) | 1.2 | Titulos de cards KPI, titulos de tabs |
| Display | 24px (1.5rem, `h3` Bootstrap) | 700 (bold, `fw-bold`) | 1.1 | Valores numericos nos KPI cards (win rate, streaks) |

Plotly chart axis font_size: 11 (consistente com graficos existentes em dashboard.py).
Plotly chart title font_size: 13 (nao usar titulo interno de figura — usar `dbc.CardHeader` como titulo).

---

## Color

Paleta derivada do tema DARKLY + cores semanticas ja em uso no dashboard.py.

| Role | Value | Usage | Source |
|------|-------|-------|--------|
| Dominant (60%) | `rgba(0,0,0,0)` / DARKLY bg (~#222) | Background de graficos (`paper_bgcolor`, `plot_bgcolor`), superficies de cards | dashboard.py lines 420-421, 459-460 |
| Secondary (30%) | DARKLY card bg (~#2a2a2a) | Cards KPI, cards de graficos, modal body, `dbc.Card` padrao | dbc.themes.DARKLY aplicado globalmente |
| Accent (10%) | `#17a2b8` (Bootstrap info/cyan) | Barras do win-rate-por-liga chart, linha de Stake Fixa na equity curve | dashboard.py line 452 |

Cores semanticas fixas (nao substituir):

| Semantica | Hex | Uso exclusivo |
|-----------|-----|---------------|
| GREEN | `#28a745` | Resultados GREEN, marcadores equity curve GREEN, barras positivas no Gale chart |
| RED | `#dc3545` | Resultados RED, marcadores equity curve RED |
| Pendente | `#ffc107` | Rows AG Grid pendentes, linha Gale na equity curve (laranja Bootstrap warning) |
| Cobertura OK | `#28a745` (success) | Badge cobertura >= 95% |
| Cobertura WARN | `#ffc107` (warning) | Badge cobertura >= 90% e < 95% |
| Cobertura CRIT | `#dc3545` (danger) | Badge cobertura < 90% |

Accent reservado para:
- Barras do grafico "win rate por liga" (horizontal bar, ja em uso)
- Linha "Stake Fixa" na equity curve (go.Scatter, cor `#17a2b8`)
- Linha tracejada de breakeven na equity curve (0 horizontal, cor `#6c757d` muted)

Segunda linha da equity curve (Gale):
- Cor: `#ffc107` (laranja Bootstrap warning) — semanticamente associado a risco/apostas, consistente com destacar pendentes

---

## Component Inventory

Componentes Dash/dbc necessarios para a Fase 3 (todos ja disponiveis, sem instalacoes novas):

### Layout Additions

| Componente | ID | Aba/Posicao | Requisito |
|------------|----|-------------|-----------|
| `dbc.Badge` | `badge-coverage` | Header do dashboard (fora das abas) | OPER-01, D-19 |
| `dbc.Modal` | `modal-parse-failures` | Triggered pelo badge | OPER-01, D-21 |
| `dbc.Tabs` | `tabs-analytics` | Abaixo do AG Grid existente | D-01 |
| `dbc.Tab` | `tab-temporal` | Aba 1: "Temporal" | D-02 |
| `dbc.Tab` | `tab-gale` | Aba 2: "Gale & Streaks" | D-02 |
| `dbc.Tab` | `tab-volume` | Aba 3: "Volume" | D-02 |

### Aba Temporal

| Componente | ID | Requisito |
|------------|----|-----------|
| `dcc.Graph` (go.Heatmap) | `graph-heatmap` | ANAL-01 — win rate por hora x dia da semana |
| `dcc.Graph` (go.Scatter dual-line) | `graph-equity` | ANAL-05 — curva de equity Stake Fixa vs Gale |
| `dcc.Graph` (go.Bar horizontal) | `graph-dow` | ANAL-02 — win rate por dia da semana |

### Aba Gale & Streaks

| Componente | ID | Requisito |
|------------|----|-----------|
| `dcc.Graph` (go.Bar horizontal) | `graph-gale` | ANAL-07 — taxa de recuperacao por tentativa |
| `html.Div` / KPI mini-cards | `kpi-streak-current` | ANAL-06 — streak atual |
| `html.Div` / KPI mini-cards | `kpi-streak-max-green` | ANAL-06 — maior streak de win historica |
| `html.Div` / KPI mini-cards | `kpi-streak-max-red` | ANAL-06 — maior streak de loss historica |

### Aba Volume

| Componente | ID | Requisito |
|------------|----|-----------|
| `dcc.Graph` (go.Bar) | `graph-volume` | ANAL-08 — volume por dia/semana |
| `html.Div` (tabela HTML) | `table-cross-dimensional` | ANAL-04 — cross-dimensional breakdown |

---

## Interaction Contract

### Badge de Cobertura do Parser

- Posicao: `dbc.Navbar` ou `html.Div` no topo do layout, alinhado a direita (`ms-auto`)
- Estado inicial: renderizado com valor de `get_stats()` no load inicial via master callback ou callback proprio
- Click: abre `dbc.Modal` com `dbc.Table` de parse_failures (raw_text, reason, received_at), max 50 linhas recentes
- Modal fechamento: botao "Fechar" (`dbc.Button`, `color="secondary"`)
- Cor dinamica do badge: atualiza junto com o intervalo de refresh de 60s

### Tabs (dbc.Tabs)

- `active_tab` default: `"tab-temporal"` — primeira aba ativa ao carregar
- Lazy render: graficos das abas inativas retornam `dash.no_update`
- Inputs compartilhados com master callback: `filter-liga`, `filter-entrada`, `filter-date`, `stake-input`, `odd-input`, `interval-refresh`
- Callback separado do master callback (nao extender o master) — confirmado em RESEARCH.md Architecture Patterns

### Equity Curve

- Dois traces `go.Scatter` sobrepostos no mesmo `dcc.Graph`
- Trace 1 "Stake Fixa": `mode="lines+markers"`, cor `#17a2b8`, nome "Stake Fixa"
- Trace 2 "Gale": `mode="lines+markers"`, cor `#ffc107`, nome "Com Gale", `line_dash="dot"`
- Marcadores: `marker_color` list com `#28a745` para GREEN e `#dc3545` para RED por sinal
- Linha de breakeven: `go.Scatter` horizontal em y=0, `line_dash="dash"`, `line_color="#6c757d"`, sem marcadores, nome "Breakeven"
- Anotacoes de streak: texto `"Streak >=5"` sobre o ponto de inicio, `font_size=10`, `arrowhead=2`
- Eixo X: label "Sinal #", numeros inteiros 1..N
- Eixo Y: label "Lucro (R$)", formato com 2 casas decimais
- Estado vazio: figura com anotacao central "Nenhum sinal com resultado no periodo selecionado"

### Heatmap

- `go.Heatmap` com `colorscale="RdYlGn"` — vermelho (0%) a verde (100%), confirmado em RESEARCH.md ANAL-01
- Eixo Y: horas 0-23 (24 linhas)
- Eixo X: dias da semana Dom-Sab (7 colunas), labels em pt-BR
- Celulas sem dados: mostrar como cinza neutro (`#444`) via `zmin=0`, `zmax=1`
- `hovetemplate`: "Hora: %{y}h<br>Dia: %{x}<br>Win Rate: %{z:.1%}"
- Estado vazio: figura com anotacao "Dados insuficientes para o periodo selecionado"

### Gale Analysis (barras horizontais)

- `go.Bar` com `orientation="h"`
- Eixo Y (categorias): "1a tentativa", "2a tentativa", "3a tentativa", "4a tentativa"
- Eixo X: win rate em percentual (0-100%), `ticksuffix="%"`
- `marker_color` progressivo: `#28a745`, `#ffc107`, `#fd7e14`, `#dc3545` (verde → laranja → laranja escuro → vermelho) — indica custo crescente de Gale
- Texto inline na barra: "XX% (N sinais)" via `text` e `textposition="inside"`
- Estado vazio: anotacao "Dados de tentativa indisponiveis"

### Streak Tracker (mini-cards dentro da aba Gale & Streaks)

- Layout: `dbc.Row` com 3 `dbc.Col` iguais
- Card 1: "Streak Atual" — valor com cor dinamica (verde se win, vermelho se loss, cinza se 0)
- Card 2: "Maior Sequencia GREEN" — valor em `#28a745`
- Card 3: "Maior Sequencia RED" — valor em `#dc3545`
- Formato do valor: "5 wins" / "3 losses" / "Sem dados"

### Volume Chart

- Usar `go.Bar` (barras, nao area chart) — mais legivel para dias discretos
- Eixo X: datas formatadas "DD/MM"
- Eixo Y: "Qtd. Sinais"
- `marker_color="#17a2b8"` — accent padrao
- Estado vazio: anotacao "Nenhum sinal no periodo selecionado"

### Cross-Dimensional Breakdown

- `dbc.Table` HTML (nao AG Grid) — resposta simples de aggregacao, sem paginacao necessaria
- Colunas: Liga | Entrada | Win Rate | Total Sinais
- Ordenacao: por Win Rate DESC
- Highlight: linha com win rate > 60% recebe `className="table-success"` (Bootstrap)
- Estado vazio: texto "Aplique filtros para ver breakdown"

---

## Copywriting Contract

| Element | Copy | Source |
|---------|------|--------|
| Primary CTA | nao aplicavel — dashboard e leitura, sem acoes destrutivas | — |
| Aba 1 label | "Temporal" | CONTEXT.md D-02 |
| Aba 2 label | "Gale & Streaks" | CONTEXT.md D-02 |
| Aba 3 label | "Volume" | CONTEXT.md D-02 |
| Badge cobertura (formato) | "Cobertura: XX%" | CONTEXT.md D-19 |
| Modal titulo | "Falhas de Parse" | CONTEXT.md D-21 |
| Modal botao fechar | "Fechar" | default |
| Equity: trace Stake Fixa | "Stake Fixa" | CONTEXT.md D-06 |
| Equity: trace Gale | "Com Gale" | CONTEXT.md D-06 |
| Equity: linha zero | "Breakeven" | padrao |
| Heatmap: titulo card | "Win Rate por Hora e Dia" | ANAL-01 |
| Dow chart: titulo card | "Win Rate por Dia da Semana" | ANAL-02 |
| Gale chart: titulo card | "Recuperacao por Nivel de Gale" | ANAL-07 |
| Streak: card titulo | "Streaks" | ANAL-06 |
| Volume: titulo card | "Volume de Sinais" | ANAL-08 |
| Cross-dim: titulo card | "Breakdown Cross-Dimensional" | ANAL-04 |
| Empty state — equity | "Nenhum sinal com resultado no periodo selecionado" | default |
| Empty state — heatmap | "Dados insuficientes para o periodo selecionado" | default |
| Empty state — gale | "Dados de tentativa indisponiveis" | default |
| Empty state — volume | "Nenhum sinal no periodo selecionado" | default |
| Empty state — cross-dim | "Aplique filtros para ver breakdown cruzado" | default |
| Error state (callback falha) | "Erro ao carregar dados. Verifique conexao com o banco." | default |
| Streak: sem dados | "Sem dados" | default |
| Streak: wins format | "{N} wins" | default |
| Streak: losses format | "{N} losses" | default |

Acoes destrutivas nesta fase: nenhuma. Modal e apenas leitura de parse_failures, sem delete.

---

## Graficos Existentes — Posicao

Os graficos da Fase 2 (bar chart resultados e win rate por liga) permanecem na secao fixa acima das abas, conforme ja implementado. Nao migrar para abas — manter a secao fixa intocada conforme CONTEXT.md D-01.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| PyPI (pip) | dash 4.1.0, plotly 6.6.0, dash-bootstrap-components 2.0.4 | not applicable — Python packages, nao NPM registry |
| shadcn | none | not applicable |

Nota: Este projeto usa Python/Dash, sem NPM, sem shadcn, sem React. O shadcn gate nao se aplica. Todos os componentes necessarios ja estao instalados (confirmado em RESEARCH.md "Sem novas instalacoes necessarias").

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
