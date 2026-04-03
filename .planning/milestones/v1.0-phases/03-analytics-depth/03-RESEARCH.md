# Phase 3: Analytics Depth - Research

**Researched:** 2026-04-03
**Domain:** Plotly Dash 4.x analytics — Heatmap, Equity Curve, Gale Analysis, Streaks, Volume, Cross-Dimensional Breakdown, Parser Coverage Badge
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Layout e Organizacao**
- D-01: Novos graficos organizados em `dbc.Tabs` abaixo da secao fixa (KPIs, filtros, ROI principal, ROI complementares, AG Grid)
- D-02: Abas tematicas: "Temporal" (heatmap + equity + dia da semana), "Gale & Streaks" (analise de Gale + streaks), "Volume" (volume por periodo + cross-dimensional)
- D-03: `active_tab` adicionado como Input no callback para lazy render — graficos so calculam quando a aba esta ativa

**Curva de Equity**
- D-05: Eixo X por sinal cronologico (indice 1, 2, 3…) — cada aposta com peso igual
- D-06: Duas linhas sobrepostas: Stake Fixa (azul) e Gale (laranja) — usando `calculate_roi()` com `gale_on=False` e `gale_on=True`
- D-07: Marcadores coloridos: verde para GREEN, vermelho para RED
- D-08: Anotacao de texto nos maiores streaks (>=5 consecutivos) marcando inicio da sequencia
- D-09: Reset automatico ao filtro ativo — curva sempre comeca em 0

**Analise de Gale por Nivel**
- D-10: Card composto com barras horizontais por tentativa (1a a 4a) mostrando taxa de GREEN + metricas inline
- D-11: Responde: (1) frequencia de recuperacao por tentativa, (2) custo acumulado medio, (3) impacto financeiro liquido
- D-12: Barras horizontais (nao verticais)

**Streaks**
- D-13: Streak tracker: streak atual (win/loss), maior streak historica (win e loss separados)
- D-14: Integrado na aba "Gale & Streaks"

**Heatmap e Breakdowns Temporais**
- D-15: Heatmap de win rate por horario do dia (eixo Y = hora, eixo X = dia da semana)
- D-16: Bar chart de win rate por dia da semana — atualiza com filtros
- D-17: Cross-dimensional: filtros compostos produzem breakdown de win rate e contagem

**Volume de Sinais**
- D-18: Grafico de volume de sinais por dia/semana

**Cobertura do Parser**
- D-19: Badge colorido no header do dashboard (semantica operacional separada dos KPIs)
- D-20: Cor por threshold: verde (>=95%), amarelo (>=90%), vermelho (<90%)
- D-21: Click no badge abre modal (`dbc.Modal`) com tabela de `parse_failures`
- D-22: Dados de `get_stats()` para coverage; query direta em `parse_failures` para o modal

### Claude's Discretion

- Agrupamento exato das abas (quais graficos em qual aba)
- Posicao dos graficos existentes (bar chart resultados, win rate por liga) — manter fixos ou mover para aba
- Cores exatas dos graficos alem do definido (equity: azul/laranja, marcadores: verde/vermelho)
- Tamanho e proporcao dos graficos dentro de cada aba
- Formato das anotacoes de streak na equity curve
- Nivel de detalhe do cross-dimensional breakdown
- Se o volume chart usa barras ou area chart

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descricao | Research Support |
|----|-----------|-----------------|
| ANAL-01 | Taxa de acerto por horario do dia (heatmap) | go.Heatmap com EXTRACT(HOUR) + pivot 24x7, colorscale RdYlGn verificado |
| ANAL-02 | Taxa de acerto por dia da semana | go.Bar horizontal com EXTRACT(DOW), labels Dom-Sab, filtros via _build_where() |
| ANAL-03 | Taxa de acerto por periodo (1T/2T/FT) | Campo `periodo` ja existe no schema; query GROUP BY periodo simples |
| ANAL-04 | Analise cross-dimensional (filtros compostos) | SQL GROUP BY liga, entrada com ROUND(win_rate, 1); _build_where() reutilizavel |
| ANAL-05 | Curva de equity (bankroll acumulado ao longo do tempo) | Padrao verificado: reversal DESC->ASC de get_signal_history() + dois go.Scatter sobrepostos |
| ANAL-06 | Tracking de sequencias (streaks) | Algoritmo puro Python verificado; calcula atual + max_green + max_red em O(n) |
| ANAL-07 | Analise de Gale por nivel (taxa de recuperacao por tentativa) | SQL GROUP BY tentativa + go.Bar horizontal; campo `tentativa` SMALLINT ja no schema |
| ANAL-08 | Grafico de volume de sinais por dia/semana | SQL DATE_TRUNC('day') + go.Bar ou go.Scatter com fill='tozeroy'; ambos verificados |
| OPER-01 | Exibir taxa de cobertura do parser | dbc.Badge com thresholds verificados; dbc.Modal para parse_failures; get_stats() ja retorna coverage |
</phase_requirements>

---

## Summary

A Fase 3 adiciona camadas analiticas avancadas ao dashboard existente sem alterar a secao fixa (KPIs, filtros, ROI, AG Grid). Todo o novo conteudo fica em `dbc.Tabs` inserido apos o componente AG Grid. O stack Dash 4.1.0 + plotly 6.6.0 + dbc 2.0.4 (instalados e verificados) suporta nativamente todos os componentes necessarios: `go.Heatmap`, `go.Scatter` multi-trace, `go.Bar` horizontal, `dbc.Modal`, `dbc.Badge`, e o padrao de lazy render via `no_update`.

A arquitetura de callback recomendada usa um callback separado para as abas (nao extensao do master callback), pois o master ja tem 14 Outputs e 8 Inputs. Dois callbacks podem ouvir os mesmos Inputs de filtro sem conflito no Dash. Toda a logica de calculo (equity curve, streaks, Gale analysis) fica como funcoes puras em `queries.py`, sem dependencia de Dash ou banco, seguindo o padrao estabelecido por `calculate_roi()`.

O banco de dados esta vazio no ambiente de desenvolvimento (0 sinais), mas todas as queries SQL foram validadas sintaticamente. O campo `tentativa SMALLINT` ja existe no schema — base essencial para ANAL-07. O `get_stats()` em `store.py` ja retorna `coverage` e `parse_failures` count — OPER-01 nao precisa de nova query de stats, apenas de uma query adicional para o conteudo do modal.

**Recomendacao principal:** Separar o callback de abas do master callback; implementar toda a logica de calculo como funcoes puras em `queries.py` antes de integrar ao dashboard.

---

## Standard Stack

### Core (ja instalado e verificado)

| Biblioteca | Versao | Proposito | Por que |
|------------|--------|-----------|---------|
| dash | 4.1.0 | Framework dashboard | Ja em uso; `@callback` decorator, `no_update` para lazy render |
| plotly | 6.6.0 | Graficos | Bundled com Dash; `go.Heatmap`, `go.Scatter`, `go.Bar` — todos verificados |
| dash-bootstrap-components | 2.0.4 | UI components | Ja em uso; `dbc.Tabs`, `dbc.Modal`, `dbc.Badge` — todos verificados |
| psycopg2-binary | 2.9.x | Driver PostgreSQL | Ja em uso; novas queries usam o mesmo padrao de cursor/fetchall |

### Sem novas instalacoes necessarias

Todos os componentes necessarios para a Fase 3 estao disponiveis nas dependencias ja instaladas. Nao ha novos pacotes a adicionar ao `pyproject.toml`.

---

## Architecture Patterns

### Estrutura de Arquivos Afetados

```
helpertips/
├── dashboard.py    # Adicionar: layout dbc.Tabs, badge no header, modal, callbacks de tabs e modal
├── queries.py      # Adicionar: get_heatmap_data(), get_winrate_by_dow(), get_gale_analysis(),
│                   #            get_volume_by_day(), get_cross_dimensional(),
│                   #            get_parse_failures_detail(),
│                   #            calculate_equity_curve(), calculate_streaks()
└── store.py        # Sem alteracoes — get_stats() ja retorna coverage
tests/
├── test_queries.py # Adicionar: testes para cada nova funcao pura e query
└── test_dashboard.py # Adicionar: IDs dos novos componentes em test_layout_has_required_component_ids
```

### Padrao 1: Callback Separado para Abas (Recomendado)

**O que e:** Um callback dedicado apenas para conteudo das abas, distinto do master callback.

**Por que:** O master callback ja tem 14 Outputs e 8 Inputs. Adicionar mais Outputs ao master aumentaria o tempo de execucao de TODA callback invocation (incluindo mudancas de filtro que nao afetam abas). O padrao de callback separado e idiomatico no Dash para conteudos tabulados.

**Quando usar:** Sempre que o conteudo tiver logica de lazy render baseada em `active_tab`.

**Exemplo:**
```python
# Source: padrao verificado com Dash 4.1.0 + dbc 2.0.4
from dash import no_update

@callback(
    Output("graph-heatmap", "figure"),
    Output("graph-equity", "figure"),
    Output("graph-dow", "figure"),
    Output("graph-gale", "figure"),
    Output("kpi-streak-current", "children"),
    Output("kpi-streak-max-green", "children"),
    Output("kpi-streak-max-red", "children"),
    Output("graph-volume", "figure"),
    Output("table-cross-dimensional", "children"),
    Input("tabs-analytics", "active_tab"),
    Input("filter-liga", "value"),
    Input("filter-entrada", "value"),
    Input("filter-date", "start_date"),
    Input("filter-date", "end_date"),
    Input("stake-input", "value"),
    Input("odd-input", "value"),
    Input("interval-refresh", "n_intervals"),
)
def update_tabs(active_tab, liga, entrada, date_start, date_end, stake, odd, _n):
    conn = get_connection()
    try:
        if active_tab == "tab-temporal":
            heatmap_fig = build_heatmap(conn, liga, entrada, date_start, date_end)
            equity_fig = build_equity_curve(conn, liga, entrada, date_start, date_end, stake, odd)
            dow_fig = build_winrate_by_dow(conn, liga, entrada, date_start, date_end)
            return heatmap_fig, equity_fig, dow_fig, no_update, no_update, no_update, no_update, no_update, no_update
        elif active_tab == "tab-gale":
            gale_fig = build_gale_analysis(conn, liga, entrada, date_start, date_end)
            streaks = calculate_streaks_from_db(conn, liga, entrada, date_start, date_end)
            return no_update, no_update, no_update, gale_fig, streaks["current_label"], streaks["max_green"], streaks["max_red"], no_update, no_update
        elif active_tab == "tab-volume":
            vol_fig = build_volume_chart(conn, liga, entrada, date_start, date_end)
            cross_table = build_cross_dimensional(conn, liga, entrada, date_start, date_end)
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, vol_fig, cross_table
        return (no_update,) * 9
    finally:
        conn.close()
```

### Padrao 2: Equity Curve — Reversal DESC para ASC

**O que e:** `get_signal_history()` retorna sinais em ordem DESC (mais recente primeiro). Para a equity curve cronologica, inverter a lista antes de iterar.

**Critico:** Nao mudar o ORDER BY na query — o AG Grid depende de DESC. Inverter na funcao de calculo.

```python
# Source: logica verificada com Python 3.12
def calculate_equity_curve(signals_desc: list, stake: float, odd: float) -> dict:
    """
    Constroi curva de equity para Stake Fixa e Gale sobrepostos.
    signals_desc: saida de get_signal_history() (DESC — mais recente primeiro).
    Retorna: {x, y_fixa, y_gale, colors} para plotar dois go.Scatter.
    """
    resolved = [s for s in signals_desc if s.get("resultado") in ("GREEN", "RED")]
    resolved_asc = list(reversed(resolved))  # ordem cronologica

    xs, y_fixa, y_gale, colors = [], [], [], []
    bk_fixa = bk_gale = 0.0

    for i, sig in enumerate(resolved_asc, 1):
        resultado = sig["resultado"]
        tentativa = sig.get("tentativa") or 1

        # Stake Fixa
        net_fixa = stake * (odd - 1) if resultado == "GREEN" else -stake
        bk_fixa += net_fixa

        # Gale
        accumulated = stake * (2 ** tentativa - 1)
        winning = stake * (2 ** (tentativa - 1))
        if resultado == "GREEN":
            net_gale = winning * (odd - 1) - (accumulated - winning)
        else:
            net_gale = -accumulated
        bk_gale += net_gale

        xs.append(i)
        y_fixa.append(round(bk_fixa, 2))
        y_gale.append(round(bk_gale, 2))
        colors.append("#28a745" if resultado == "GREEN" else "#dc3545")

    return {"x": xs, "y_fixa": y_fixa, "y_gale": y_gale, "colors": colors}
```

### Padrao 3: Heatmap 24x7 com Pivot

**O que e:** Query agrega win_rate por (hora, dia_semana), resultado e pivotado em matriz 24 linhas x 7 colunas para `go.Heatmap`.

```python
# Source: SQL verificado contra PostgreSQL 16; pivot verificado com Python 3.12
def get_heatmap_data(conn, liga=None, entrada=None, date_start=None, date_end=None) -> dict:
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            EXTRACT(HOUR FROM received_at)::INT AS hora,
            EXTRACT(DOW FROM received_at)::INT  AS dia,
            COUNT(*) FILTER (WHERE resultado = 'GREEN')              AS greens,
            COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED'))    AS total
        FROM signals
        WHERE resultado IN ('GREEN', 'RED') AND {where}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    # Pivot: z[hora][dia] = win_rate
    z = [[None] * 7 for _ in range(24)]
    for hora, dia, greens, total in rows:
        z[hora][dia] = round(greens / total * 100, 1) if total > 0 else None

    dias = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    horas = [f"{h:02d}h" for h in range(24)]
    return {"z": z, "x": dias, "y": horas}
```

### Padrao 4: Gale Analysis por Tentativa

```python
# Source: SQL verificado; campo tentativa SMALLINT confirmado no schema
def get_gale_analysis(conn, liga=None, entrada=None, date_start=None, date_end=None) -> list:
    where, params = _build_where(liga=liga, entrada=entrada,
                                 date_start=date_start, date_end=date_end)
    sql = f"""
        SELECT
            tentativa,
            COUNT(*) FILTER (WHERE resultado = 'GREEN')              AS greens,
            COUNT(*) FILTER (WHERE resultado IN ('GREEN', 'RED'))    AS total
        FROM signals
        WHERE resultado IN ('GREEN', 'RED')
          AND tentativa IS NOT NULL
          AND {where}
        GROUP BY tentativa
        ORDER BY tentativa
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        {
            "tentativa": int(t),
            "greens": int(g),
            "total": int(total),
            "win_rate": round(g / total * 100, 1) if total > 0 else 0.0,
        }
        for t, g, total in rows
    ]
```

### Padrao 5: Streak Calculation — Puro Python

```python
# Source: algoritmo verificado com Python 3.12; O(n) single-pass
def calculate_streaks(signals_desc: list) -> dict:
    """
    Calcula streaks a partir de sinais em ordem DESC (saida de get_signal_history).
    Retorna streak atual + maior streak historica de win e loss.
    """
    resolved = [
        s for s in signals_desc
        if s.get("resultado") in ("GREEN", "RED")
    ]
    resolved_asc = list(reversed(resolved))  # cronologico

    if not resolved_asc:
        return {"current": 0, "current_type": None, "max_green": 0, "max_red": 0}

    current = 1
    max_green = max_red = 0

    for i in range(1, len(resolved_asc)):
        if resolved_asc[i]["resultado"] == resolved_asc[i - 1]["resultado"]:
            current += 1
        else:
            prev = resolved_asc[i - 1]["resultado"]
            if prev == "GREEN":
                max_green = max(max_green, current)
            else:
                max_red = max(max_red, current)
            current = 1

    # Finalizar ultimo streak
    last = resolved_asc[-1]["resultado"]
    if last == "GREEN":
        max_green = max(max_green, current)
    else:
        max_red = max(max_red, current)

    return {
        "current": current,
        "current_type": last,
        "max_green": max_green,
        "max_red": max_red,
    }
```

### Padrao 6: Modal de Parse Failures

```python
# Source: dbc.Modal e dbc.Badge verificados com dbc 2.0.4
# Layout: badge no header
html.H2([
    "HelperTips — Futebol Virtual",
    dbc.Badge(
        id="badge-parser-coverage",
        className="ms-2 fs-6",
        style={"cursor": "pointer"},
    ),
], className="text-center my-3"),

# Modal separado
dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Falhas do Parser")),
    dbc.ModalBody(id="modal-failures-body"),
    dbc.ModalFooter(
        dbc.Button("Fechar", id="btn-close-modal", className="ms-auto")
    ),
], id="modal-parse-failures", is_open=False, size="lg", scrollable=True),

# Callback para badge (atualizado junto com o master callback)
# Callback separado para modal toggle
@callback(
    Output("modal-parse-failures", "is_open"),
    Output("modal-failures-body", "children"),
    Input("badge-parser-coverage", "n_clicks"),
    Input("btn-close-modal", "n_clicks"),
    State("modal-parse-failures", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal(badge_clicks, close_clicks, is_open):
    from dash import ctx
    if ctx.triggered_id == "badge-parser-coverage":
        # Carregar failures e abrir modal
        conn = get_connection()
        try:
            failures = get_parse_failures_detail(conn)
        finally:
            conn.close()
        return True, _build_failures_table(failures)
    return False, no_update
```

### Padrao 7: Badge Coverage — Integracao ao Master Callback

O badge precisa atualizar junto com os KPIs (quando filters mudam). Adicionar badge como Output adicional ao master callback existente.

```python
# Adicionar ao master callback (update_dashboard):
# Output adicional: Output("badge-parser-coverage", "children"), Output("badge-parser-coverage", "color")

from helpertips.store import get_stats

# Dentro do callback:
global_stats = get_stats(conn)  # sem filtros — coverage e sempre global
coverage = global_stats["coverage"]
badge_color = "success" if coverage >= 95 else ("warning" if coverage >= 90 else "danger")
badge_text = f"Parser: {coverage:.1f}%"
# Retornar badge_text, badge_color como Outputs adicionais
```

### Anti-Patterns a Evitar

- **Adicionar outputs de abas ao master callback:** Aumenta latencia em TODA interacao de filtro, mesmo quando o usuario nao esta na aba. Use callback separado.
- **ORDER BY ASC em get_signal_history():** O AG Grid depende de DESC. Inverter na funcao de equity/streaks com `reversed()`, nao na query.
- **Timezone em EXTRACT():** Nao usar `AT TIME ZONE` sem confirmar que o campo `received_at` armazena em UTC. Dados foram capturados localmente — usar sem conversao evita ambiguidade.
- **Heatmap com celulas None vs 0:** Celulas sem dados devem ser `None` (heatmap mostra em cinza), nao `0` (heatmap mostra como 0% e induz leitura errada).
- **Gale analysis com tentativa=NULL:** Sinais sem tentativa registrada devem ser excluidos da analise (`AND tentativa IS NOT NULL`) — nao default para tentativa=1.

---

## Don't Hand-Roll

| Problema | Nao construir | Usar em vez | Por que |
|----------|---------------|-------------|---------|
| Pivot de dados para heatmap | Loop manual com dicionarios aninhados | Lista de listas 24x7 com `None` para ausentes | go.Heatmap aceita diretamente; None = celula transparente |
| Formatacao de tabela HTML | HTML string manual | `dbc.Table` com `html.Thead`/`html.Tbody` | Padrao ja estabelecido em `_build_comp_table()` — reutilizar |
| Toggle de modal | Javascript customizado | `dbc.Modal` + `State(modal, is_open)` | dbc nativo; padrao verificado |
| Deteccao de aba ativa | `dcc.Store` + flags | `Input("tabs-analytics", "active_tab")` | dbc.Tabs expoe `active_tab` como prop diretamente |
| Agrupamento temporal SQL | Python loop sobre lista de sinais | `EXTRACT(HOUR/DOW FROM received_at)` | Agregacao no banco e drasticamente mais eficiente com 1000+ sinais |

---

## Common Pitfalls

### Pitfall 1: Master Callback com Muitos Outputs

**O que da errado:** Adicionar os ~9 novos Outputs das abas ao master callback torna CADA interacao de filtro lenta — o callback precisa recalcular todos os graficos de todas as abas mesmo quando o usuario esta na aba fixa.

**Por que acontece:** O master callback e um monolito que processa tudo de uma vez. Nao ha lazy render interno.

**Como evitar:** Callback separado para conteudo das abas com `active_tab` como Input. O lazy render usa `no_update` para tabs inativas.

**Sinais de alerta:** Latencia perceptivel ao mudar filtros; Dash callback queue com muitos Outputs.

---

### Pitfall 2: Equity Curve sem Reversal

**O que da errado:** `get_signal_history()` retorna sinais DESC (mais recente primeiro). Se iterar diretamente, a equity curve exibe o tempo na ordem errada — o sinal mais recente fica no ponto 1 e o mais antigo fica no ultimo ponto.

**Por que acontece:** O AG Grid precisa de DESC para mostrar sinais recentes no topo; a equity curve precisa de ASC para mostrar evolucao cronologica.

**Como evitar:** `resolved_asc = list(reversed([s for s in signals if s.get("resultado") in ("GREEN","RED")]))` — reverter apenas os sinais resolvidos, antes de iterar.

**Sinais de alerta:** Equity curve mostra queda inicial seguida de subida mesmo com historico lucrativo.

---

### Pitfall 3: Heatmap com Zeros onde Dados Ausentes

**O que da errado:** Usar `0.0` para celulas sem dados no heatmap (hora/dia sem sinais). O `RdYlGn` colorscale exibe zero como vermelho — parece win rate de 0%, nao ausencia de dados.

**Por que acontece:** Inicializacao com `[[0.0] * 7 for _ in range(24)]` preenche todas as celulas.

**Como evitar:** Inicializar com `[[None] * 7 for _ in range(24)]`. Plotly renderiza `None` como celula transparente/cinza sem coloracao.

**Sinais de alerta:** Heatmap mostra vermelho para horarios noturnos sem sinais.

---

### Pitfall 4: Modal sem `scrollable=True`

**O que da errado:** Tabela de parse_failures pode ter muitas linhas. Sem `scrollable=True` no dbc.Modal, o conteudo excede a viewport.

**Como evitar:** `dbc.Modal(..., scrollable=True)`.

---

### Pitfall 5: Badge Coverage com Filtros

**O que da errado:** Se o badge de cobertura usar os filtros do dashboard (liga, entrada, data), o calculo fica errado — `parse_failures` nao tem campos liga/entrada, entao a cobertura filtrada nao faz sentido semantico.

**Como evitar:** Coverage e sempre global (`get_stats(conn)` sem filtros). O badge exibe metrica operacional do parser, nao metrica das apostas. Conforme D-19 e D-22.

---

### Pitfall 6: Gale Analysis com Sinais sem `tentativa`

**O que da errado:** Sinais inseridos antes da adicao do campo `tentativa` tem `tentativa = NULL`. Incluir esses sinais com default `tentativa=1` distorce a analise de Gale.

**Como evitar:** `WHERE tentativa IS NOT NULL` na query de Gale analysis. Documentar no card que a analise exclui sinais sem tentativa registrada.

---

## Code Examples

### Heatmap Go Object

```python
# Source: verificado com plotly 6.6.0
import plotly.graph_objects as go

def make_heatmap_figure(heatmap_data: dict) -> go.Figure:
    """heatmap_data: saida de get_heatmap_data()"""
    fig = go.Figure(go.Heatmap(
        z=heatmap_data["z"],
        x=heatmap_data["x"],    # ["Dom","Seg","Ter","Qua","Qui","Sex","Sab"]
        y=heatmap_data["y"],    # ["00h","01h",...,"23h"]
        colorscale="RdYlGn",
        zmin=0,
        zmax=100,
        colorbar=dict(title="Win Rate %"),
        hoverongaps=False,
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=50, r=20),
        title_text="Win Rate por Hora e Dia da Semana",
        yaxis=dict(autorange="reversed"),  # 00h no topo, 23h na base
    )
    return fig
```

### Equity Curve Figure

```python
# Source: verificado com plotly 6.6.0 + go.Scatter multi-trace
def make_equity_figure(equity_data: dict) -> go.Figure:
    """equity_data: saida de calculate_equity_curve()"""
    fig = go.Figure()

    # Linha Stake Fixa
    fig.add_trace(go.Scatter(
        x=equity_data["x"],
        y=equity_data["y_fixa"],
        mode="lines+markers",
        name="Stake Fixa",
        line=dict(color="#4a90d9", width=2),
        marker=dict(color=equity_data["colors"], size=8),
    ))

    # Linha Gale
    fig.add_trace(go.Scatter(
        x=equity_data["x"],
        y=equity_data["y_gale"],
        mode="lines+markers",
        name="Gale",
        line=dict(color="#fd7e14", width=2),
        marker=dict(color=equity_data["colors"], size=8),
    ))

    # Anotacoes de streak >= 5
    for ann in equity_data.get("annotations", []):
        fig.add_annotation(
            x=ann["x"], y=ann["y"],
            text=ann["text"],
            showarrow=True, arrowhead=2,
            font=dict(size=10, color="#ffc107"),
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=60, r=20),
        title_text="Curva de Equity",
        xaxis_title="Sinal #",
        yaxis_title="Bankroll (R$)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
```

### Gale Analysis — Barras Horizontais

```python
# Source: go.Bar horizontal verificado com plotly 6.6.0
def make_gale_figure(gale_data: list) -> go.Figure:
    """gale_data: saida de get_gale_analysis()"""
    labels = [f"{d['tentativa']}a tentativa" for d in gale_data]
    win_rates = [d["win_rate"] for d in gale_data]
    colors = ["#28a745" if wr >= 60 else ("#ffc107" if wr >= 45 else "#dc3545") for wr in win_rates]

    fig = go.Figure(go.Bar(
        x=win_rates,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{wr:.1f}%" for wr in win_rates],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=120, r=20),
        title_text="Taxa de Recuperacao por Tentativa (Gale)",
        xaxis_title="Win Rate %",
        xaxis_range=[0, 100],
    )
    return fig
```

### Query Parse Failures para Modal

```python
# Source: padrao de query existente em queries.py (SELECT com cursor/fetchall)
def get_parse_failures_detail(conn, limit: int = 100) -> list:
    """Retorna ultimas parse_failures para exibir no modal."""
    sql = """
        SELECT raw_text, failure_reason, received_at
        FROM parse_failures
        ORDER BY received_at DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (limit,))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]
```

---

## State of the Art

| Abordagem Antiga | Abordagem Atual | Quando Mudou | Impacto |
|-----------------|-----------------|--------------|---------|
| `app.callback` decorator | `@callback` (module-level) | Dash 2.x | Nao requer referencia ao `app`; ja em uso no projeto |
| Callback unico monolitico | Multi-callback com separacao por dominio | Dash 2.x | Melhor performance e manutenibilidade |
| `dcc.Tab` (antigo) | `dbc.Tab` dentro de `dbc.Tabs` | dbc 1.x | Bootstrap styling nativo; `active_tab` prop built-in |

---

## Open Questions

1. **Timezone de received_at**
   - O que sabemos: `received_at` usa `TIMESTAMPTZ DEFAULT NOW()` — armazena em UTC se o PostgreSQL esta configurado em UTC
   - O que e incerto: Se o servidor local esta em America/Sao_Paulo, `NOW()` pode ja estar no horario de Brasilia
   - Recomendacao: Usar `EXTRACT(HOUR FROM received_at)` sem conversao; documentar no card do heatmap que as horas sao no timezone do servidor. Validar com primeiro dado real capturado.

2. **Volume de dados para analise de streaks/Gale**
   - O que sabemos: STATE.md registra concern — "ANAL-06 e ANAL-07 requerem 100+ sinais para ser significativos"
   - O que e incerto: Volume atual em producao
   - Recomendacao: Implementar os graficos; adicionar indicador de "dados insuficientes" (ex: `dbc.Alert("Menos de 20 sinais resolvidos — analise pode nao ser representativa")`) quando `total < 20`.

3. **Graficos existentes (bar chart + winrate por liga)**
   - O que sabemos: D-04 e "Claude's Discretion" — manter fixos ou mover para aba
   - Recomendacao: Manter os dois graficos na secao fixa (Charts Row atual). Eles sao o overview imediato que o usuario quer ver sem clicar em abas. As abas sao para analises avancadas opcionais.

---

## Environment Availability

| Dependencia | Necessaria por | Disponivel | Versao | Fallback |
|-------------|---------------|------------|--------|----------|
| Python 3.12+ | Runtime | sim | verificado via pyproject.toml | — |
| dash | Dashboard | sim | 4.1.0 | — |
| plotly | Graficos | sim | 6.6.0 | — |
| dash-bootstrap-components | Tabs, Modal, Badge | sim | 2.0.4 | — |
| psycopg2-binary | Queries | sim | >=2.9 | — |
| PostgreSQL 16 | Dados | sim (vazio) | 16 | — |

**Nenhuma dependencia faltando.** Todas as bibliotecas necessarias ja estao instaladas. O banco esta vazio no ambiente de desenvolvimento, mas as queries foram validadas sintaticamente.

---

## Validation Architecture

### Test Framework

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest >= 7.0 |
| Config | `pyproject.toml` `[tool.pytest.ini_options]` |
| Comando rapido | `python3 -m pytest tests/test_queries.py -x -q` |
| Suite completa | `python3 -m pytest tests/ -x -q` |

**Estado atual:** 61 testes passando (verificado).

### Mapeamento Requisitos → Testes

| ID | Comportamento | Tipo | Comando Automatizado | Arquivo Existe? |
|----|---------------|------|----------------------|-----------------|
| ANAL-01 | `get_heatmap_data()` retorna matriz 24x7 com None para ausentes | unit (puro Python) | `python3 -m pytest tests/test_queries.py::test_get_heatmap_data -x` | Nao — Wave 0 |
| ANAL-01 | Heatmap com dados reais do DB agrupa por hora/dia corretamente | integration (DB) | `python3 -m pytest tests/test_queries.py::test_get_heatmap_data_db -x` | Nao — Wave 0 |
| ANAL-02 | `get_winrate_by_dow()` retorna 7 entradas (uma por dia) | unit | `python3 -m pytest tests/test_queries.py::test_get_winrate_by_dow -x` | Nao — Wave 0 |
| ANAL-03 | `get_winrate_by_periodo()` agrupa por periodo corretamente | unit | `python3 -m pytest tests/test_queries.py::test_get_winrate_by_periodo -x` | Nao — Wave 0 |
| ANAL-04 | `get_cross_dimensional()` retorna win_rate e count por (liga, entrada) | unit | `python3 -m pytest tests/test_queries.py::test_get_cross_dimensional -x` | Nao — Wave 0 |
| ANAL-05 | `calculate_equity_curve()` com 3 sinais [G,G,R]: y_fixa=[9,18,8] | unit (puro Python) | `python3 -m pytest tests/test_queries.py::test_calculate_equity_curve -x` | Nao — Wave 0 |
| ANAL-05 | Equity curve reverte DESC para ASC antes de calcular | unit (puro Python) | `python3 -m pytest tests/test_queries.py::test_equity_curve_reversal -x` | Nao — Wave 0 |
| ANAL-06 | `calculate_streaks()` com [G,G,G,R,G]: max_green=3, max_red=1, current=1 | unit (puro Python) | `python3 -m pytest tests/test_queries.py::test_calculate_streaks -x` | Nao — Wave 0 |
| ANAL-07 | `get_gale_analysis()` agrupa por tentativa, exclui NULL | unit | `python3 -m pytest tests/test_queries.py::test_get_gale_analysis -x` | Nao — Wave 0 |
| ANAL-08 | `get_volume_by_day()` retorna (data, count) por dia | unit | `python3 -m pytest tests/test_queries.py::test_get_volume_by_day -x` | Nao — Wave 0 |
| OPER-01 | Badge exibe verde/amarelo/vermelho por threshold 95/90 | unit | `python3 -m pytest tests/test_dashboard.py::test_coverage_badge_thresholds -x` | Nao — Wave 0 |
| OPER-01 | Layout contem IDs: badge-parser-coverage, modal-parse-failures, tabs-analytics | unit (layout) | `python3 -m pytest tests/test_dashboard.py::test_layout_has_required_component_ids -x` | Parcial — atualizar |

### Sampling Rate

- **Por commit de task:** `python3 -m pytest tests/test_queries.py -x -q`
- **Por merge de wave:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Suite completa verde antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_queries.py` — adicionar testes para `get_heatmap_data`, `get_winrate_by_dow`, `get_winrate_by_periodo`, `get_cross_dimensional`, `get_gale_analysis`, `get_volume_by_day`, `get_parse_failures_detail` (DB + puro Python)
- [ ] `tests/test_queries.py` — adicionar testes para `calculate_equity_curve`, `calculate_streaks` (puro Python — sem DB)
- [ ] `tests/test_dashboard.py` — atualizar `test_layout_has_required_component_ids` com novos IDs: `tabs-analytics`, `badge-parser-coverage`, `modal-parse-failures`

---

## Project Constraints (from CLAUDE.md)

| Diretiva | Aplicacao nesta fase |
|----------|---------------------|
| Stack: Dash 4.1.0, dbc 2.x, plotly_dark template | Todos os novos graficos usam `template="plotly_dark"`. Nenhuma nova lib de UI. |
| psycopg2-binary (sync) | Todas as queries novas em `queries.py` sao sync; callback abre/fecha conn por invocacao |
| Dois processos separados (listener.py + dashboard.py) | Sem mudancas — fase e apenas dashboard.py e queries.py |
| Arquivo .session no .gitignore | Sem alteracao |
| GSD Workflow Enforcement | Todas as mudancas via `/gsd:execute-phase` |
| Idioma pt-BR | Labels, titulos e comentarios em pt-BR |
| @callback decorator (nao app.callback) | Padrao ja estabelecido; novos callbacks seguem o mesmo padrao |
| conn per invocation + close em finally | Master callback e novo tab callback ambos abrem/fecham conn no finally |

---

## Sources

### Primary (HIGH confidence)

- Verificacao direta com Python 3.12 / dash 4.1.0 / plotly 6.6.0 / dbc 2.0.4 instalados — todos os padroes de codigo verificados em runtime
- `helpertips/queries.py` — funcoes `calculate_roi()`, `_build_where()`, `get_signal_history()` — padrao estabelecido, reutilizado nas novas funcoes
- `helpertips/dashboard.py` — master callback, make_kpi_card(), _build_comp_table() — padrao para novos helpers
- `helpertips/db.py` — schema SQL verificado; campos `tentativa`, `periodo`, `dia_semana`, `received_at` confirmados
- `helpertips/store.py` — `get_stats()` retorna `coverage` e `parse_failures` count — confirmado

### Secondary (MEDIUM confidence)

- Padrao `active_tab` + `no_update` para lazy render: comportamento verificado via inspeção da API dbc.Tabs e `from dash import no_update` — `no_update` e instancia de `dash._no_update.NoUpdate`
- SQL `EXTRACT(HOUR/DOW FROM received_at)` — validado sintaticamente (DB vazio, 0 rows retornadas mas sem erro)

### Tertiary (LOW confidence)

- Timezone de `received_at`: comportamento depende da configuracao do servidor PostgreSQL. Nao verificado sem dados reais. Documentado como Open Question.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versoes verificadas em runtime
- Architecture patterns: HIGH — codigo verificado com Python 3.12 + bibliotecas instaladas
- SQL queries: HIGH (sintatico) / LOW (semantico) — DB vazio, 0 rows para validar comportamento real
- Pitfalls: HIGH — identificados por analise do codigo existente e verificacoes programaticas
- Streak/equity logic: HIGH — algoritmos verificados com asserts programaticos

**Research date:** 2026-04-03
**Valid until:** 2026-07-03 (stack estavel; dash 4.x sem breaking changes previstas ate dash 5)
