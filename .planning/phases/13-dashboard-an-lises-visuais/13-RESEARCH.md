# Phase 13: Dashboard Analises Visuais - Research

**Pesquisado:** 2026-04-04
**Dominio:** Plotly Dash 4.x — graficos interativos, barras empilhadas, equity curve, donut chart
**Confianca:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Esquema de Cores dos Graficos**
- D-01: Paleta semantica alinhada ao tema DARKLY — `#00bc8c` (success DARKLY) para principal/lucro, `#e74c3c` (danger) para complementar/perda, `#f39c12` (warning) para total/acumulado. Mantém consistencia com KPI cards que ja usam `#28a745`/`#dc3545`.
- D-02: Donut chart de gale usa 4 tons derivados do success (`#00bc8c` com variações de lightness) para reforcar que todas as tentativas fazem parte do mesmo desfecho.
- D-03: Barras empilhadas por liga usam `#00bc8c` (P&L principal) e `#e74c3c` (P&L complementar) — mesma codificacao das linhas da equity curve.

**Layout e Ordem das Secoes**
- D-04: Ordem narrativa: Liga -> Equity Curve -> Gale. Fluxo analitico: contexto dimensional -> evolucao temporal -> granularidade operacional.
- D-05: Scroll continuo sem accordions, tabs ou collapse — confirma pattern D-08 da Phase 12. Cada secao em `dbc.Card` com header descritivo.
- D-06: Secoes inseridas no `phase13-placeholder` (L470 dashboard.py), antes do AG Grid de historico. Ordem final do layout: filtros globais -> KPIs -> simulacao -> config mercados -> performance -> **liga -> equity curve -> gale** -> historico.

**Dados de Gale Expandidos (DASH-07)**
- D-07: Criar funcao pura `aggregate_pl_por_tentativa(pl_lista)` em queries.py que agrupa output de `calculate_pl_por_entrada()` por tentativa, calculando `lucro_medio_green = sum(lucro_total for GREEN) / count(GREEN)`. Lucro depende de stake/odd/gale_on — impossivel calcular no SQL.
- D-08: Reutilizar a chamada `calculate_pl_por_entrada()` ja existente no callback master (Phase 12) para alimentar tanto a tabela de performance quanto a nova secao de gale. Sem round-trip extra ao banco.
- D-09: `get_gale_analysis()` existente continua fornecendo quantidade e percentual por tentativa. A nova funcao complementa com lucro medio.

**Interatividade dos Graficos**
- D-10: Hover tooltips ricos com `hovertemplate` formatado em todos os 3 graficos. Equity curve mostra data + P&L principal + complementar + total por ponto. Barras mostram liga + greens + reds + P&L. Donut mostra tentativa + percentual + lucro medio.
- D-11: Sem range slider na equity curve — periodo ja controlado pelos filtros globais, evita redundancia.
- D-12: Sem click-to-filter (clickData) — filtro-liga dropdown existente ja satisfaz a necessidade.
- D-13: Zoom/pan nativo do Plotly permanece habilitado por padrao (comportamento default).

### Claude's Discretion

- Organizacao interna dos builders de figuras Plotly (funcoes helper separadas ou inline)
- Nomes exatos dos IDs dos novos componentes (graficos e tabelas)
- Se tabelas de liga e gale usam `dbc.Table` ou `dash_table.DataTable`
- CSS adicional para estilos dos novos cards (se necessario)
- Estrategia de teste dos novos callbacks/helpers
- Template exato dos hovertemplates (formatacao de R$, decimais)

### Deferred Ideas (OUT OF SCOPE)

Nenhum — discussao ficou dentro do escopo da fase.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descricao | Suporte da Pesquisa |
|----|-----------|---------------------|
| DASH-05 | Secao analise por liga: grafico de barras empilhadas (P&L principal vs complementar) + tabela com taxa, P&L principal, P&L complementar, P&L total por liga | `calculate_pl_por_entrada()` ja retorna `liga`, `lucro_principal` e `lucro_comp` por sinal — agregar por liga em Python puro. `go.Bar` com `barmode='stack'` e `hovertemplate` rico. |
| DASH-06 | Secao evolucao temporal: equity curve com 3 linhas sobrepostas (principal, complementar, total) controlado pelo filtro global de periodo | `calculate_equity_curve_breakdown()` retorna `{x, y_principal, y_complementar, y_total, colors}` — entrada direta para 3 `go.Scatter`. X-axis pode usar indice ou `received_at` do sinal para legibilidade. |
| DASH-07 | Secao analise de gale: donut chart de distribuicao por tentativa (1ª-4ª) + tabela com quantidade, percentual e lucro medio por green | `get_gale_analysis()` fornece quantidade e percentual. Nova `aggregate_pl_por_tentativa()` complementa com lucro medio. Donut via `go.Pie` com `hole=0.4`. |

</phase_requirements>

---

## Sumario

A Phase 13 adiciona 3 secoes visuais ao dashboard existente substituindo o `html.Div(id="phase13-placeholder")` em L470 de `dashboard.py`. Todo o calculo de dados ja existe em `queries.py` — o trabalho e: (1) uma nova funcao pura `aggregate_pl_por_tentativa()` em `queries.py`, (2) tres funcoes builder de figuras Plotly (`_build_liga_chart`, `_build_equity_curve_chart`, `_build_gale_chart`), (3) construcao do layout das 3 secoes como `dbc.Card`, e (4) extensao do callback master com 3 novos `Output`.

Os dados de `calculate_pl_por_entrada()` e `get_signals_com_placar()` ja sao chamados no callback master — reutilizacao direta sem round-trips adicionais ao banco. O unico dado novo e `get_gale_analysis()` que nao e chamado ainda no callback master (Phase 12 nao o usa), mais a nova `aggregate_pl_por_tentativa()` que opera sobre o resultado de `calculate_pl_por_entrada()` ja em memoria.

**Recomendacao principal:** Seguir o padrao da Phase 12 — funcoes builder puras + extensao do callback master `update_dashboard` com novos `Output`, reutilizando variaveis ja computadas no callback.

---

## Standard Stack

### Core (ja instalado, sem novas dependencias)

| Biblioteca | Versao | Proposito | Motivo |
|-----------|--------|-----------|--------|
| plotly.graph_objects (`go`) | bundled com Dash 4.1 | `go.Bar`, `go.Scatter`, `go.Pie` | Ja importado em L29 do dashboard.py (`import plotly.graph_objects as go`) |
| dash | `>=4.1,<5` | Layout, callbacks, `dcc.Graph` | Stack fixo no pyproject.toml |
| dash-bootstrap-components | `>=2.0` | `dbc.Card`, `dbc.CardHeader`, `dbc.CardBody`, `dbc.Table` | Stack fixo, padrao estabelecido nas Phases 11-12 |

### Sem novas instalacoes necessarias

Todos os pacotes ja estao em `requirements.txt` e instalados. Verificado pelo funcionamento da Phase 12.

---

## Architecture Patterns

### Estrutura de Arquivo (sem mudancas)

```
helpertips/
├── dashboard.py     # Layout + callback master — MODIFICAR
├── queries.py       # Data layer — ADICIONAR aggregate_pl_por_tentativa()
└── assets/          # CSS overrides DARKLY — sem mudancas
tests/
├── test_dashboard.py  # Testes estruturais — ESTENDER
└── test_queries.py    # Testes puros — ESTENDER
```

### Padrao 1: Funcao Builder de Figura Plotly (pura, sem DB)

**O que e:** Funcao Python que recebe dados pre-calculados e retorna `go.Figure`.
**Quando usar:** Para cada um dos 3 graficos. Separar logica de dados da logica de renderizacao.

```python
# Padrao estabelecido — replicar para cada grafico
def _build_liga_chart(pl_por_liga: list[dict]) -> go.Figure:
    """Constroi grafico de barras empilhadas P&L por liga."""
    if not pl_por_liga:
        return go.Figure()  # figura vazia — layout cuida do estado vazio

    ligas = [row["liga"] for row in pl_por_liga]
    pl_principal = [row["lucro_principal"] for row in pl_por_liga]
    pl_comp = [row["lucro_complementar"] for row in pl_por_liga]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Principal",
        x=ligas, y=pl_principal,
        marker_color="#00bc8c",
        hovertemplate="<b>%{x}</b><br>P&L Principal: R$ %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Complementar",
        x=ligas, y=pl_comp,
        marker_color="#e74c3c",
        hovertemplate="<b>%{x}</b><br>P&L Complementar: R$ %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor="#222",
        plot_bgcolor="#222",
        font={"color": "white"},
        legend={"orientation": "h"},
        margin={"t": 30, "b": 40},
    )
    return fig
```

### Padrao 2: `go.Scatter` com modo "lines+markers" para Equity Curve

**O que e:** 3 traces `go.Scatter` sobrepostos usando arrays `x`, `y_principal`, `y_complementar`, `y_total` de `calculate_equity_curve_breakdown()`.
**X-axis:** O retorno atual de `calculate_equity_curve_breakdown()` usa indices inteiros `[1, 2, ...]`. Para legibilidade, o planner pode optar por usar `received_at` dos sinais como eixo X — isso requer passar `received_at` para a funcao ou usar os indices com hover que mostra a data.

```python
def _build_equity_curve_chart(equity: dict) -> go.Figure:
    """3 linhas sobrepostas: principal, complementar, total."""
    fig = go.Figure()
    if not equity.get("x"):
        return fig

    fig.add_trace(go.Scatter(
        x=equity["x"], y=equity["y_principal"],
        mode="lines", name="Principal",
        line={"color": "#00bc8c", "width": 2},
        hovertemplate="Sinal #%{x}<br>Principal: R$ %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=equity["x"], y=equity["y_complementar"],
        mode="lines", name="Complementar",
        line={"color": "#e74c3c", "width": 2},
        hovertemplate="Sinal #%{x}<br>Complementar: R$ %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=equity["x"], y=equity["y_total"],
        mode="lines", name="Total",
        line={"color": "#f39c12", "width": 2},
        hovertemplate="Sinal #%{x}<br>Total: R$ %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#222", plot_bgcolor="#222",
        font={"color": "white"},
        xaxis={"showgrid": False},
        yaxis={"gridcolor": "#444"},
        legend={"orientation": "h"},
        margin={"t": 30, "b": 40},
    )
    return fig
```

### Padrao 3: `go.Pie` com `hole` para Donut Chart

**O que e:** `go.Pie` com `hole=0.4` para criar o visual de donut. Labels = tentativa, values = greens (quantidade).

```python
def _build_gale_chart(gale_data: list[dict]) -> go.Figure:
    """Donut de distribuicao de greens por tentativa."""
    if not gale_data:
        return go.Figure()

    labels = [f"{row['tentativa']}a Tentativa" for row in gale_data]
    values = [row["greens"] for row in gale_data]
    # 4 tons derivados de #00bc8c (verde success DARKLY) — D-02
    colors = ["#00bc8c", "#00a07a", "#008567", "#006a53"][:len(gale_data)]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.4,
        marker={"colors": colors},
        hovertemplate="<b>%{label}</b><br>Greens: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#222",
        font={"color": "white"},
        showlegend=True,
        legend={"orientation": "h"},
        margin={"t": 30, "b": 40},
    )
    return fig
```

### Padrao 4: `aggregate_pl_por_tentativa()` em queries.py

**O que e:** Funcao pura que agrega output de `calculate_pl_por_entrada()` por tentativa, calculando lucro medio dos greens.
**Onde fica:** `queries.py` — segue pattern estabelecido de funcoes puras sem DB.

```python
def aggregate_pl_por_tentativa(pl_lista: list[dict]) -> list[dict]:
    """
    Agrega P&L por tentativa para analise de gale (DASH-07).

    Recebe output de calculate_pl_por_entrada(). Retorna lista ordenada
    por tentativa com lucro_medio_green calculado.
    """
    from collections import defaultdict

    grupos: dict[int, dict] = defaultdict(lambda: {
        "greens": 0, "lucro_total_greens": 0.0,
    })
    for row in pl_lista:
        t = row.get("tentativa") or 1
        if row.get("resultado") == "GREEN":
            grupos[t]["greens"] += 1
            grupos[t]["lucro_total_greens"] += row.get("lucro_total", 0.0)

    result = []
    for tentativa in sorted(grupos.keys()):
        g = grupos[tentativa]
        lucro_medio = (
            g["lucro_total_greens"] / g["greens"] if g["greens"] > 0 else 0.0
        )
        result.append({
            "tentativa": tentativa,
            "greens": g["greens"],
            "lucro_medio_green": round(lucro_medio, 2),
        })
    return result
```

### Padrao 5: Extensao do Callback Master

**O que e:** Adicionar 3 novos `Output` ao `update_dashboard` para os containers das secoes Phase 13. O container `phase13-placeholder` e substituido por 3 `Output` separados (um por secao) OU um unico `Output` para o `html.Div(id="phase13-placeholder")` que retorna a lista de 3 cards.

**Opcao recomendada:** Um unico `Output("phase13-placeholder", "children")` que retorna a lista dos 3 cards. Isso minimiza o numero de outputs do callback e segue o padrao de `config-mercados-container`.

```python
# No callback master — adicionar Output
Output("phase13-placeholder", "children"),   # DASH-05, DASH-06, DASH-07

# No return tuple — adicionar valor
_build_phase13_section(signals_placar, pl_lista, gale_data, equity_data, stake, odd, gale_on, conn, entrada)
```

### Padrao 6: Merging de dados gale (D-08 e D-09)

**O que e:** `get_gale_analysis()` retorna `{tentativa, greens, total, win_rate}`. `aggregate_pl_por_tentativa()` retorna `{tentativa, greens, lucro_medio_green}`. Para a tabela DASH-07, precisa fazer um join em Python por `tentativa`.

```python
# Merge por tentativa — join em Python (sem DB)
pl_por_tent = {r["tentativa"]: r for r in aggregate_pl_por_tentativa(pl_lista)}
merged = []
for row in gale_data:
    t = row["tentativa"]
    pl_row = pl_por_tent.get(t, {})
    merged.append({
        "tentativa": t,
        "greens": row["greens"],
        "total": row["total"],
        "win_rate": row["win_rate"],
        "lucro_medio_green": pl_row.get("lucro_medio_green", 0.0),
    })
```

### Anti-Patterns a Evitar

- **Chamar `get_signals_com_placar()` de novo dentro de `_build_phase13_section`:** Os sinais ja foram buscados no callback master. Passar `signals_placar` como parametro.
- **Chamar `calculate_pl_por_entrada()` de novo:** Ja calculado para DASH-04. Reutilizar o `pl_lista` ja em memoria.
- **Retornar `go.Figure()` com `None` em vez de figura vazia:** Dash nao aceita `None` em `dcc.Graph(figure=...)`. Sempre retornar um `go.Figure()` vazio quando sem dados.
- **`dark=True` em `dbc.Table`:** O parametro nao existe em dbc 2.0.4. Usar `color='dark'` (D consolidada na Phase 12).
- **`updatemenus` ou `sliders` nativos do Plotly:** O periodo ja e controlado pelos filtros globais. Adicionar controles dentro da figura cria dupla interface e estado inconsistente.

---

## Don't Hand-Roll

| Problema | Nao Construir | Usar | Motivo |
|----------|--------------|------|--------|
| Barras empilhadas | Loop de `html.Div` proporcional | `go.Bar` com `barmode='stack'` | Plotly cuida de escala, hover, zoom, responsividade |
| Grafico de linha cumulativo | Array acumulado manual + `html.Canvas` | `go.Scatter` + `calculate_equity_curve_breakdown()` | Funcao ja existe e foi testada na Phase 10 |
| Donut de proporcoes | Calculos de angulo + `html.Svg` | `go.Pie(hole=0.4)` | Plotly cuida de percentuais, labels, hover |
| Tooltips ricos | `dbc.Tooltip` em cada barra | `hovertemplate` do Plotly | Plotly processa no browser, sem round-trip |
| Tabela com cores condicionais | Classes CSS manuais | `dash_table.DataTable(style_data_conditional=[...])` | Pattern ja estabelecido em `_build_performance_section` |

---

## Common Pitfalls

### Pitfall 1: `calculate_equity_curve_breakdown()` nao tem datas no eixo X

**O que vai errado:** A funcao retorna `x = [1, 2, 3, ...]` (indices). A equity curve fica sem datas no eixo, o que e menos legivel.
**Por que acontece:** `calculate_equity_curve_breakdown()` nao recebe `received_at` dos sinais — foca no calculo financeiro.
**Como evitar:** Os sinais de `get_signals_com_placar()` incluem `received_at`. Passar as datas como array paralelo aos indices e usar no `hovertemplate` do Scatter. Alternativa: usar `received_at` diretamente como `x` no trace (Plotly suporta datetime nativamente). Decisao de detalhe — Claude's Discretion.
**Sinal de aviso:** Eixo X mostrando "1, 2, 3..." sem contexto temporal.

### Pitfall 2: `go.Figure()` vazio retornado para `dcc.Graph` sem `figure`

**O que vai errado:** Se o callback retorna `None` ou uma lista vazia para o Output de um `dcc.Graph`, o Dash lanca `TypeError`.
**Por que acontece:** `dcc.Graph(figure=None)` nao e valido.
**Como evitar:** Sempre retornar `go.Figure()` (figura vazia valida) quando `signals_placar` esta vazio. Verificar em cada builder: `if not data: return go.Figure()`.

### Pitfall 3: `get_gale_analysis()` usa filtros globais mas nao tem ligacao com `calculate_pl_por_entrada()`

**O que vai errado:** `get_gale_analysis()` conta greens por tentativa direto no SQL (sem levar em conta stake/odd dinamicos). `aggregate_pl_por_tentativa()` usa `calculate_pl_por_entrada()` que considera os parametros de simulacao. Os dois precisam usar os mesmos filtros globais aplicados.
**Por que acontece:** `get_gale_analysis()` recebe `liga, entrada, date_start, date_end` como filtros. `calculate_pl_por_entrada()` opera sobre `signals_placar` que ja foi filtrado. Se os filtros forem os mesmos, os conjuntos de sinais sao equivalentes.
**Como evitar:** Chamar `get_gale_analysis()` com os mesmos `liga, entrada, date_start, date_end` usados em `get_signals_com_placar()`. Verificar que `gale_data["greens"]` bate com `aggregate_pl_por_tentativa()["greens"]` — devem ser iguais.

### Pitfall 4: Barras com P&L negativo em `barmode='stack'`

**O que vai errado:** Com `barmode='stack'`, se `lucro_complementar` for negativo para uma liga, Plotly empilha abaixo do zero — visual confuso.
**Por que acontece:** `barmode='stack'` soma algebricamente. P&L negativo complementar desloca a barra para baixo.
**Como evitar:** Aceitar esse comportamento — e correto financeiramente. P&L negativo abaixo de zero e informacao util. Garantir que o `hovertemplate` mostre o valor com sinal (R$ %{y:+.2f}).

### Pitfall 5: Callback master com muitos Outputs quebra Dash

**O que vai errado:** Dash tem limites praticos de Output. Se `phase13-placeholder` for dividido em muitos Outputs individuais (um por elemento de UI dentro da secao), o callback fica grande demais.
**Por que acontece:** Cada `dcc.Graph`, tabela e header seriam Outputs separados.
**Como evitar:** Usar um unico `Output("phase13-placeholder", "children")` que retorna a arvore completa das 3 secoes como lista de `dbc.Card`. Pattern ja usado para `config-mercados-container`.

### Pitfall 6: `dbc.Table(dark=True)` — parametro nao existe em dbc 2.0.4

**O que vai errado:** `AttributeError` ou parametro ignorado silenciosamente.
**Por que acontece:** O parametro foi renomeado/removido em dbc 2.0.x.
**Como evitar:** Usar `dbc.Table(color='dark', ...)` — padrao consolidado na Phase 12.

---

## Code Examples

### Exemplo: Layout da Secao Liga (DASH-05)

```python
# Retornado como parte de phase13-placeholder "children"
dbc.Card([
    dbc.CardHeader(html.H5("Analise por Liga", className="mb-0")),
    dbc.CardBody([
        dcc.Graph(id="liga-chart", figure=fig_liga, config={"displayModeBar": False}),
        html.Div(id="liga-table"),  # dash_table.DataTable ou dbc.Table
    ]),
], className="mb-3")
```

### Exemplo: Layout da Secao Equity Curve (DASH-06)

```python
dbc.Card([
    dbc.CardHeader(html.H5("Evolucao do Saldo (Equity Curve)", className="mb-0")),
    dbc.CardBody([
        dcc.Graph(id="equity-curve-chart", figure=fig_equity),
    ]),
], className="mb-3")
```

### Exemplo: Layout da Secao Gale (DASH-07)

```python
dbc.Card([
    dbc.CardHeader(html.H5("Analise de Gale", className="mb-0")),
    dbc.CardBody([
        dbc.Row([
            dbc.Col(dcc.Graph(id="gale-donut-chart", figure=fig_gale), md=6),
            dbc.Col(html.Div(id="gale-table"), md=6),
        ]),
    ]),
], className="mb-3")
```

### Exemplo: Extensao do Return do Callback Master

```python
# Callback master — novos outputs no decorador
Output("phase13-placeholder", "children"),

# No body do callback
phase13_children = _build_phase13_section(
    signals_placar=signals_placar,
    pl_lista=pl_lista,         # ja calculado para perf_section
    conn=conn,
    liga=liga, entrada=entrada,
    date_start=date_start, date_end=date_end,
    stake=stake, odd=odd, gale_on=gale_on,
)

# No return tuple
phase13_children,   # Output("phase13-placeholder", "children")
```

---

## State of the Art

| Abordagem Antiga | Abordagem Atual | Quando Mudou | Impacto |
|-----------------|-----------------|--------------|--------|
| `go.FigureWidget` (Jupyter) | `dcc.Graph(figure=go.Figure(...))` em Dash | Dash 1.x | Usar sempre `dcc.Graph` para integrar com callbacks |
| `plotly.express` para graficos simples | `plotly.graph_objects` para controle total | Sempre valido | `graph_objects` permite `hovertemplate` rico e configuracao fina — necessario aqui |
| `dbc.Table(dark=True)` | `dbc.Table(color='dark')` | dbc 2.0.x | Pitfall 6 — parametro renomeado |

---

## Open Questions

1. **X-axis da equity curve: indices ou datas?**
   - O que sabemos: `calculate_equity_curve_breakdown()` retorna indices `[1, 2, ...]`. `get_signals_com_placar()` inclui `received_at`.
   - O que esta indefinido: Passar datas como x requer ou modificar a funcao existente ou extrair datas separadamente dos sinais.
   - Recomendacao: Usar indices como x mas incluir data no `hovertemplate` (extraindo `received_at` de `signals_placar` como array paralelo). Nao modificar `calculate_equity_curve_breakdown()` — funcao ja testada.

2. **Tabelas de liga e gale: `dbc.Table` ou `dash_table.DataTable`?**
   - O que sabemos: Claude's Discretion. `dbc.Table` e mais simples e ja usado em config mercados. `dash_table.DataTable` tem `style_data_conditional` para colorir P&L negativo/positivo (ja usado em performance).
   - O que esta indefinido: Qual componente o planner vai escolher.
   - Recomendacao: `dash_table.DataTable` para liga (tem P&L que se beneficia de coloracao condicional) e `dbc.Table` para gale (dados mais simples, so quantidade e lucro medio).

---

## Environment Availability

Secao IGNORADA — phase e puramente de codigo Python/Dash sem dependencias externas novas. Stack ja instalado e verificado pela Phase 12.

---

## Validation Architecture

### Test Framework

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest (detectado, 190 testes coletados) |
| Arquivo de config | `pyproject.toml` (sem pytest.ini separado) |
| Comando rapido | `python3 -m pytest tests/test_dashboard.py tests/test_queries.py -x -q` |
| Suite completa | `python3 -m pytest tests/ -x -q` |

### Mapa Requisitos -> Testes

| ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|----|--------------|---------------|----------------------|-----------------|
| DASH-05 | `aggregate_pl_por_liga(pl_lista)` agrega lucro por liga | unit (puro Python) | `python3 -m pytest tests/test_queries.py -k "liga" -x` | Wave 0 |
| DASH-05 | `_build_liga_chart()` retorna `go.Figure` valido para dados e para lista vazia | unit | `python3 -m pytest tests/test_dashboard.py -k "liga_chart" -x` | Wave 0 |
| DASH-05 | Layout contem `id="liga-chart"` e `id="liga-table"` | unit (estrutural) | `python3 -m pytest tests/test_dashboard.py -k "phase13" -x` | Wave 0 |
| DASH-06 | `_build_equity_curve_chart()` retorna `go.Figure` com 3 traces | unit | `python3 -m pytest tests/test_dashboard.py -k "equity_chart" -x` | Wave 0 |
| DASH-06 | Layout contem `id="equity-curve-chart"` | unit (estrutural) | `python3 -m pytest tests/test_dashboard.py -k "phase13" -x` | Wave 0 |
| DASH-07 | `aggregate_pl_por_tentativa()` calcula `lucro_medio_green` correto | unit (puro Python) | `python3 -m pytest tests/test_queries.py -k "tentativa" -x` | Wave 0 |
| DASH-07 | `aggregate_pl_por_tentativa()` retorna lista vazia para input vazio | unit | `python3 -m pytest tests/test_queries.py -k "tentativa" -x` | Wave 0 |
| DASH-07 | `_build_gale_chart()` retorna `go.Figure` valido | unit | `python3 -m pytest tests/test_dashboard.py -k "gale_chart" -x` | Wave 0 |
| DASH-07 | Layout contem `id="gale-donut-chart"` e `id="gale-table"` | unit (estrutural) | `python3 -m pytest tests/test_dashboard.py -k "phase13" -x` | Wave 0 |

### Taxa de Amostragem

- **Por commit de task:** `python3 -m pytest tests/test_dashboard.py tests/test_queries.py -x -q`
- **Por merge de wave:** `python3 -m pytest tests/ -x -q`
- **Gate da fase:** Suite completa verde antes de `/gsd:verify-work`

### Wave 0 Gaps (arquivos de teste a criar)

- [ ] Testes para `aggregate_pl_por_liga()` em `tests/test_queries.py` — cobre DASH-05
- [ ] Testes para `aggregate_pl_por_tentativa()` em `tests/test_queries.py` — cobre DASH-07
- [ ] Testes para `_build_liga_chart()`, `_build_equity_curve_chart()`, `_build_gale_chart()` em `tests/test_dashboard.py` — cobre DASH-05, DASH-06, DASH-07
- [ ] Teste estrutural `test_layout_has_phase13_component_ids` em `tests/test_dashboard.py` — verifica IDs dos novos componentes

*(Arquivos de teste existem; as funcoes especificas nao existem ainda — adicionar aos arquivos existentes.)*

---

## Sources

### Primary (HIGH confidence)

- Codebase direta: `helpertips/dashboard.py` (693 linhas, lido completo) — estado atual do callback master, IDs existentes, patterns de builder
- Codebase direta: `helpertips/queries.py` (1200+ linhas, secoes relevantes lidas) — assinaturas de `calculate_equity_curve_breakdown()`, `get_gale_analysis()`, `calculate_pl_por_entrada()`, `get_signals_com_placar()`
- Codebase direta: `tests/test_dashboard.py` e `tests/test_queries.py` — patterns de teste estabelecidos
- `.planning/phases/13-dashboard-an-lises-visuais/13-CONTEXT.md` — decisoes locked D-01 a D-13
- `.planning/REQUIREMENTS.md` — definicao exata de DASH-05, DASH-06, DASH-07
- `.planning/STATE.md` — decisoes acumuladas das Phases 10-12

### Secondary (MEDIUM confidence)

- `.planning/phases/12-dashboard-mercados-e-performance/12-RESEARCH.md` — padrao builder + callback master extensao (usado com sucesso na Phase 12)

### Tertiary (LOW confidence)

- Nenhum. Todos os patterns criticos foram verificados diretamente no codigo existente.

---

## Metadata

**Breakdown de confianca:**
- Standard Stack: HIGH — todos os pacotes ja instalados e em uso
- Architecture Patterns: HIGH — replicacao direta de patterns estabelecidos nas Phases 11-12, verificado no codigo
- Pitfalls: HIGH — pitfalls 1-5 derivados de codigo existente e decisoes locked; pitfall 6 documentado no STATE.md
- Funcoes de dados: HIGH — assinaturas e retornos verificados diretamente no codigo

**Data da pesquisa:** 2026-04-04
**Valido ate:** 2026-05-04 (stack estavel, sem dependencias externas novas)
