# Phase 11: Dashboard Fundacao - Research

**Researched:** 2026-04-04
**Domain:** Plotly Dash 4.x — layout rewrite, global filter callbacks, KPI cards, RadioItems segmented control
**Confidence:** HIGH

## Summary

Esta fase substitui o `app.layout` inteiro do `dashboard.py` (1004 linhas) pelo novo design v1.2. O código existente já possui todos os blocos construtores necessários — a tarefa é reorganizá-los sob um novo esqueleto de layout, trocar os IDs de filtros e reescrever o callback master para usar os novos inputs.

O padrão de callback master único já está estabelecido no código (`update_dashboard`). O novo callback master recebe os mesmos parâmetros de filtro mais o novo `periodo-selector` (RadioItems) e o `date-picker-custom` (DatePickerRange condicional). `_build_where()` já suporta `mercado_id`, `entrada`, `liga`, `date_start`, `date_end` — nenhuma alteração em queries.py é necessária para DASH-01/02. As seções de analytics tabs (heatmap, equity, gale, streaks, volume) serão removidas temporariamente (deferred para fases 12-13), o que simplifica o escopo.

O risco principal desta fase é o conflito de IDs: o Dash proibe múltiplos componentes com o mesmo `id` no mesmo layout, e o `test_layout_has_required_component_ids` em `test_dashboard.py` precisará ser reescrito para verificar os novos IDs. O segundo risco é o contraste visual do `dbc.RadioItems` com `btn-check` no tema DARKLY — requer de 3-5 linhas de CSS override.

**Recomendação primária:** Reescrever `app.layout` from scratch no mesmo arquivo `dashboard.py`, preservar helpers reutilizáveis (`make_kpi_card`, `_build_comp_table`, `_entrada_para_slug`), reescrever o callback master com novos IDs, remover o callback `update_tabs` inteiramente nesta fase.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Estrategia de Reescrita**
- D-01: Reescrita do layout do zero — substituir o `app.layout` existente no dashboard.py pelo novo design v1.2. Nao tentar coexistir filtros antigos com novos (causa conflito de callback IDs e dois sistemas de state paralelos). Helpers de figuras reutilizaveis (`_build_comp_table`, `make_kpi_card` etc.) devem ser preservados/copiados seletivamente.
- D-02: Callbacks existentes serao reescritos para usar os novos IDs de filtros globais. Callback master unico desde o inicio.
- D-03: Secoes de analytics tabs (heatmap, equity, gale, streaks, volume) serao temporariamente removidas — voltam redesenhadas nas fases 12-13. AG Grid de historico pode ser preservado se nao conflitar com o novo layout.

**Filtros Globais (DASH-01)**
- D-04: Filtro de periodo usa `dbc.RadioItems` com `input_class_name="btn-check"` e labels estilizadas como `btn btn-outline-secondary` — visual de botoes segmentados, `value` nativo no callback sem state extra.
- D-05: Opcoes de periodo: Hoje, Esta Semana, Este Mes, Mes Passado, Toda a Vida, Personalizado. Selecionar "Personalizado" mostra `dcc.DatePickerRange` condicionalmente via `dbc.Collapse` ou `style`.
- D-06: Filtro de mercado: `dcc.Dropdown` com opcoes Todos / Over 2.5 / Ambas Marcam (reusa padrao existente).
- D-07: Filtro de liga: `dcc.Dropdown` populado dinamicamente via `get_distinct_values()` (padrao existente).
- D-08: Possivel necessidade de 3-5 linhas de CSS override para contraste de `btn-outline-secondary` no tema DARKLY.

**KPI Cards (DASH-02)**
- D-09: Row unica com 6 KPI cards hibridos: Total Sinais, Taxa Green (%), P&L Total (R$), ROI (%), Melhor Streak Green, Pior Streak Red.
- D-10: P&L Total mostra valor unico (principal + complementar somados). Breakdown principal/complementar/total e delegado para a equity curve da Phase 13. Consistencia visual com os demais cards.
- D-11: Todos os KPIs reativos aos filtros globais (periodo + mercado + liga).
- D-12: Reusar pattern `make_kpi_card()` existente — adaptar para novos IDs e cores.

**Posicionamento do Stake**
- D-13: Stake/odd/gale permanecem em card de configuracao separado abaixo dos filtros globais (nao dentro da barra de filtros). Separacao semantica: filtros = recorte de dados, stake = parametro de simulacao.
- D-14: Card de simulacao mantem inputs de Stake (R$), Odd, e toggle Gale (similar ao existente). Valores afetam P&L dos KPIs e todas as secoes de P&L.

### Claude's Discretion
- Organizacao interna do dashboard.py (funcoes helper, order do layout)
- CSS override exato para contraste dos RadioItems no DARKLY
- Se AG Grid de historico de sinais e preservado nesta fase ou movido para fase futura
- Nomes dos IDs dos novos componentes de filtro
- Estrategia de teste dos callbacks (se aplicavel)

### Deferred Ideas (OUT OF SCOPE)
- Secoes de analytics tabs (heatmap, equity curve, DOW, gale, streaks, volume) — voltam redesenhadas nas Phases 12-13
- Toggle percentual/quantidade/R$ na tabela de performance — Phase 12
- Donut chart de gale — Phase 13
- Grafico de barras empilhadas P&L por liga — Phase 13
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | Filtros globais fixos no topo (período: Hoje/Semana/Mês/Mês Passado/Personalizado/Toda a Vida, mercado: Todos/Over 2.5/Ambas Marcam, liga: Todas/ligas dinâmicas) afetam todos os cards e gráficos | `dbc.RadioItems` com `btn-check` para período, `dcc.Dropdown` para mercado/liga, `dbc.Collapse` para DatePickerRange condicional, `_build_where()` já suporta todos os filtros necessários |
| DASH-02 | KPI cards: total sinais, taxa green (%), P&L total (R$) principal+complementar, ROI (%), melhor streak green, pior streak red | `make_kpi_card()` existente reusável, `get_filtered_stats()` para total/taxa, `calculate_roi()` + `calculate_roi_complementares()` para P&L+ROI, `calculate_streaks()` para streaks |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Plotly Dash | `>=4.1,<5` (instalado) | Framework de dashboard | Já instalado e em uso no projeto |
| dash-bootstrap-components | `>=2.0` (instalado) | Layout Bootstrap 5, RadioItems, Card, Collapse | Já instalado; `dbc.RadioItems` com `btn-check` é o mecanismo decidido para seletor de período |
| psycopg2-binary | `>=2.9` (instalado) | Driver PostgreSQL | Já em uso em todos os callbacks existentes |
| python-dotenv | `>=1.0` (instalado) | Variáveis de ambiente | Já em uso |

Todas as dependências já estão instaladas (`pyproject.toml`). Nenhuma instalação adicional é necessária para esta fase.

**Verificação:** `python3 -m pip show dash dash-bootstrap-components` no EC2 confirma versões ativas.

## Architecture Patterns

### Estrutura do Novo Layout

```
app.layout = dbc.Container([
    # 1. Header
    html.H2(...),

    # 2. Filtros Globais (novo — D-04 a D-08)
    dbc.Card([
        dbc.CardBody([
            # Row 1: Período (RadioItems btn-check)
            dbc.Row([dbc.Col([dbc.RadioItems(id="periodo-selector", ...)], md=12)]),
            # Row 2: DatePickerRange condicional
            dbc.Collapse(id="collapse-datepicker",
                         children=[dcc.DatePickerRange(id="filter-date-custom", ...)]),
            # Row 3: Mercado + Liga dropdowns
            dbc.Row([
                dbc.Col([dcc.Dropdown(id="filter-mercado", ...)], md=4),
                dbc.Col([dcc.Dropdown(id="filter-liga", ...)], md=4),
            ]),
        ])
    ], className="mb-3"),

    # 3. KPI Cards (6 cards — D-09)
    dbc.Row([
        dbc.Col(make_kpi_card("Total Sinais",    "kpi-total",       "text-light"),   md=2),
        dbc.Col(make_kpi_card("Taxa Green",      "kpi-winrate",     "text-success"), md=2),
        dbc.Col(make_kpi_card("P&L Total",       "kpi-pl-total",    "text-light"),   md=2),
        dbc.Col(make_kpi_card("ROI",             "kpi-roi",         "text-info"),    md=2),
        dbc.Col(make_kpi_card("Melhor Streak",   "kpi-streak-green","text-success"), md=2),
        dbc.Col(make_kpi_card("Pior Streak",     "kpi-streak-red",  "text-danger"),  md=2),
    ], className="mb-3 g-2"),

    # 4. Card Simulação (stake/odd/gale — D-13, D-14)
    dbc.Card([...stake-input, odd-input, gale-toggle...], className="mb-3"),

    # 5. AG Grid histórico (opcional — Claude's Discretion)
    dag.AgGrid(id="history-table", ...),

    # 6. Placeholder para fases 12-13
    html.Div(id="analytics-placeholder"),

    # 7. Modal parse failures (manter)
    dbc.Modal([...], id="modal-parse-failures", ...),

    # 8. Auto-refresh
    dcc.Interval(id="interval-refresh", interval=60_000),
], fluid=True)
```

### Padrão de Callbacks (D-02)

O callback master único recebe todos os filtros e produz todos os KPI outputs:

```python
@callback(
    Output("kpi-total",        "children"),
    Output("kpi-winrate",      "children"),
    Output("kpi-pl-total",     "children"),
    Output("kpi-pl-total",     "className"),   # cor dinâmica verde/vermelho
    Output("kpi-roi",          "children"),
    Output("kpi-roi",          "className"),
    Output("kpi-streak-green", "children"),
    Output("kpi-streak-red",   "children"),
    Output("history-table",    "rowData"),     # se AG Grid preservado
    Output("filter-liga",      "options"),     # opções dinâmicas
    Input("periodo-selector",  "value"),
    Input("filter-date-custom","start_date"),
    Input("filter-date-custom","end_date"),
    Input("filter-mercado",    "value"),
    Input("filter-liga",       "value"),
    Input("stake-input",       "value"),
    Input("odd-input",         "value"),
    Input("gale-toggle",       "value"),
    Input("interval-refresh",  "n_intervals"),
)
def update_dashboard(periodo, date_start, date_end, mercado, liga, stake, odd, gale_on, _n):
    date_start, date_end = _resolve_periodo(periodo, date_start, date_end)
    conn = get_connection()
    try:
        ...
    finally:
        conn.close()
```

### Padrão: Resolver Período em Datas

Função pura auxiliar para converter o RadioItems `periodo` em `date_start`/`date_end`:

```python
from datetime import date, timedelta
import calendar

def _resolve_periodo(periodo: str | None, custom_start=None, custom_end=None):
    """Converte seleção de período em (date_start, date_end) ISO strings."""
    today = date.today()
    if periodo == "hoje":
        return str(today), str(today)
    elif periodo == "semana":
        # Semana atual: segunda a domingo
        start = today - timedelta(days=today.weekday())
        return str(start), str(today)
    elif periodo == "mes":
        start = today.replace(day=1)
        return str(start), str(today)
    elif periodo == "mes_passado":
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return str(last_month_start), str(last_month_end)
    elif periodo == "personalizado":
        return custom_start, custom_end  # pode ser None se não preenchido
    else:  # "toda_vida" ou None
        return None, None
```

### Padrão: DatePickerRange Condicional (D-05)

Dois mecanismos possíveis — usar `dbc.Collapse` é o padrão mais limpo em dbc:

```python
# No layout:
dbc.Collapse(
    dcc.DatePickerRange(
        id="filter-date-custom",
        display_format="DD/MM/YYYY",
        clearable=True,
    ),
    id="collapse-datepicker",
    is_open=False,
)

# Callback separado para mostrar/esconder:
@callback(
    Output("collapse-datepicker", "is_open"),
    Input("periodo-selector", "value"),
)
def toggle_datepicker(periodo):
    return periodo == "personalizado"
```

### Padrão: RadioItems como Botões Segmentados (D-04, D-08)

```python
dbc.RadioItems(
    id="periodo-selector",
    options=[
        {"label": "Hoje",        "value": "hoje"},
        {"label": "Esta Semana", "value": "semana"},
        {"label": "Este Mês",    "value": "mes"},
        {"label": "Mês Passado", "value": "mes_passado"},
        {"label": "Toda a Vida", "value": "toda_vida"},
        {"label": "Personalizado","value": "personalizado"},
    ],
    value="toda_vida",
    inline=True,
    input_class_name="btn-check",
    label_class_name="btn btn-outline-secondary btn-sm",
    label_checked_class_name="active",
)
```

**CSS override necessário (D-08):** O tema DARKLY Bootstrap usa `#adb5bd` para `btn-outline-secondary` no estado normal, que tem baixo contraste sobre fundo escuro. Override em `assets/custom.css`:

```css
/* assets/custom.css — override contraste RadioItems no DARKLY */
.btn-check:not(:checked) + .btn-outline-secondary {
    color: #e0e0e0;
    border-color: #6c757d;
}
.btn-check:checked + .btn-outline-secondary {
    background-color: #6c757d;
    border-color: #6c757d;
    color: #fff;
}
```

Dash carrega automaticamente qualquer arquivo em `assets/` — nenhuma configuração adicional necessária.

### Padrão: P&L Total com Cor Dinâmica

O KPI card P&L Total precisa de cor dinâmica (verde/vermelho) que muda com o valor. A abordagem mais limpa é usar dois Outputs separados: um para o valor (children) e outro para a classe CSS (className):

```python
Output("kpi-pl-total", "children"),
Output("kpi-pl-total", "className"),
# ...
pl_class = "card-text fw-bold text-success" if pl_total > 0 else (
    "card-text fw-bold text-danger" if pl_total < 0 else "card-text fw-bold text-muted"
)
return ..., f"R$ {pl_total:+.2f}", pl_class, ...
```

O mesmo padrão se aplica ao ROI (%).

### Padrão: Filtro de Mercado → mercado_id

O dropdown `filter-mercado` tem valores `"Over 2.5"`, `"Ambas Marcam"`, e `None` (Todos). Para chamar `_build_where(mercado_id=...)`, é necessário converter o valor do dropdown para o ID numérico:

```python
from helpertips.store import ENTRADA_PARA_MERCADO_ID

# No callback:
mercado_id = ENTRADA_PARA_MERCADO_ID.get(mercado) if mercado else None
# mercado_id será 1 (over_2_5), 2 (ambas_marcam), ou None (todos)
```

`ENTRADA_PARA_MERCADO_ID` já existe em `store.py` — não é preciso criar novo mapeamento.

**Alternativa:** usar `entrada=mercado` em vez de `mercado_id=mercado_id` nos calls a `get_filtered_stats` e `get_signal_history`. Ambas as funções têm o parâmetro `entrada`. A diferença: `entrada` filtra pela coluna `entrada` (texto), `mercado_id` filtra pela FK numérica. Para sinais históricos sem `mercado_id` preenchido, usar `entrada` é mais seguro (sem risco de excluir sinais antigos).

### Padrão: Cálculo de P&L Total (D-09, D-10)

P&L Total = lucro principal + lucro complementares:

```python
# Principal
roi_principal = calculate_roi(history, stake, odd, gale_on)
pl_principal = roi_principal["profit"]
roi_pct = roi_principal["roi_pct"]

# Complementares (apenas se mercado selecionado)
mercado_slug = _entrada_para_slug(mercado)  # helper existente
pl_comp = 0.0
roi_total = roi_pct  # fallback se sem complementares

if mercado_slug:
    comp_config = get_complementares_config(conn, mercado_slug)
    if comp_config:
        roi_comp = calculate_roi_complementares(history, comp_config, stake, gale_on)
        pl_comp = roi_comp["profit"]
        # ROI total combinado
        total_invested = roi_principal["total_invested"] + roi_comp["total_invested"]
        pl_total = pl_principal + pl_comp
        roi_total = (pl_total / total_invested * 100) if total_invested > 0 else 0.0
    else:
        pl_total = pl_principal
else:
    pl_total = pl_principal  # Todos os mercados: P&L só do principal
```

**Nota:** Quando o filtro de mercado é "Todos", `get_signal_history` retorna sinais de todos os mercados. `calculate_roi_complementares` requer um `mercado_slug` específico — portanto P&L total com "Todos" mostra apenas o principal. Esta é a interpretação correta para DASH-02 (D-10 especifica que breakdown detalhado fica na Phase 13).

### Anti-Patterns a Evitar

- **IDs duplicados no layout:** Dash lança `DuplicateIdError` em tempo de inicialização se dois componentes tiverem o mesmo `id`. Ao reescrever o layout, todos os IDs antigos que forem removidos do layout devem também ser removidos dos callbacks.
- **Output em componente inexistente:** Um `@callback` com `Output("id-que-nao-existe", ...)` causa erro silencioso em produção — o callback não dispara. Verificar que cada Output ID existe no layout.
- **Chamar `calculate_roi_complementares` com lista vazia:** Retorna `total_invested=0`, não levanta exceção. Tratar o caso `total_invested == 0` antes de calcular ROI total.
- **Múltiplos callbacks para o mesmo Output:** Dash proibe dois callbacks com o mesmo Output. Ao remover `update_tabs`, garantir que nenhum Output do layout novo conflita com callbacks restantes.
- **Manter callback `reset_filters` com IDs antigos:** O reset callback usa `Output("filter-liga", "value")` e `Output("filter-entrada", "value")`. Se renomear o dropdown de entrada para `filter-mercado`, o callback reset precisa atualizar.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Segmented button control | Custom HTML/CSS | `dbc.RadioItems` com `btn-check` | dbc nativo, valor direto no callback sem JS |
| Conditional show/hide | JS toggle / dcc.Store state | `dbc.Collapse` com `is_open` Output | Padrão idiomático dbc, sem JS |
| Date range picker | Input text + parser | `dcc.DatePickerRange` | Já em uso no projeto, suporta DD/MM/YYYY |
| Color-conditional KPI | Separate components por cor | `Output(id, "className")` | Um único componente, cor vira Output reativo |
| Período → datas | Hardcoded SQL BETWEEN | `_resolve_periodo()` helper puro | Testável isoladamente, sem acoplamento ao SQL |

## Common Pitfalls

### Pitfall 1: Callback Output para ID que não existe no novo layout
**O que dá errado:** O callback `update_tabs` tem Outputs como `"graph-heatmap"`, `"graph-equity"`, etc. Se o layout novo não tiver esses IDs mas o callback for mantido, o Dash silencia o callback ou levanta erro de inicialização.
**Por que acontece:** Ao reescrever o layout, é fácil remover componentes mas esquecer de remover callbacks que os referenciam.
**Como evitar:** Remover o callback `update_tabs` inteiramente nesta fase (D-03). Verificar todos os `@callback` restantes — cada Output deve ter um ID correspondente no layout.
**Sinais de alerta:** `DuplicateCallback` ou `NonExistentIdException` no log de inicialização do Dash.

### Pitfall 2: `get_filtered_stats` não aceita `mercado_id`
**O que dá errado:** `get_filtered_stats(conn, ..., mercado_id=X)` lançará `TypeError: unexpected keyword argument`.
**Por que acontece:** A assinatura atual é `get_filtered_stats(conn, liga=None, entrada=None, date_start=None, date_end=None)` — não tem `mercado_id`. Apenas `get_signals_com_placar` e `_build_where` aceitam `mercado_id`.
**Como evitar:** Usar `entrada=mercado` (ex: `entrada="Over 2.5"`) para filtrar `get_filtered_stats` e `get_signal_history`, ou adicionar o parâmetro `mercado_id` a `get_filtered_stats` (scope desta fase — Claude's Discretion sobre abordagem).
**Sinais de alerta:** `TypeError` no callback ao selecionar um mercado no dropdown.

### Pitfall 3: IDs antigos no `test_layout_has_required_component_ids`
**O que dá errado:** O teste `test_dashboard.py` verifica um conjunto fixo de IDs como `"kpi-greens"`, `"kpi-reds"`, `"kpi-pending"`, `"filter-date"`, `"filter-entrada"`, `"tabs-analytics"`, etc. Após a reescrita, esses IDs não existirão mais e o teste falha.
**Por que acontece:** O teste foi escrito para o layout antigo.
**Como evitar:** Reescrever `test_layout_has_required_component_ids` com os novos IDs como conjunto `required_ids`. Preservar a lógica `collect_ids()` (reutilizável).
**Sinais de alerta:** `test_layout_has_required_component_ids` falha com "Missing required component IDs".

### Pitfall 4: RadioItems `value` inicial não definido
**O que dá errado:** Se `dbc.RadioItems` não tiver `value` inicial, o período é `None` e `_resolve_periodo(None, ...)` retorna `(None, None)` — equivalente a "Toda a Vida". Isso é tecnicamente correto, mas visualmente nenhum botão fica selecionado no carregamento inicial.
**Por que acontece:** `value` é opcional em `dbc.RadioItems`.
**Como evitar:** Definir `value="toda_vida"` no componente. Isso garante que um botão esteja visualmente ativo ao carregar o dashboard.

### Pitfall 5: Tema DARKLY e `btn-outline-secondary` com baixo contraste
**O que dá errado:** No tema DARKLY, os botões `btn-outline-secondary` no estado não-selecionado têm cor de texto `#adb5bd` sobre fundo `#222` — contraste de 3.6:1, abaixo do AA (4.5:1). Os botões ficam difíceis de ler.
**Por que acontece:** O DARKLY usa palette de secundário otimizada para fundos claros.
**Como evitar:** Criar `helpertips/assets/custom.css` com override de contraste. O Dash serve automaticamente arquivos de `assets/` sem configuração adicional.

### Pitfall 6: `calculate_roi_complementares` com filtro "Todos os Mercados"
**O que dá errado:** Quando `filter-mercado` é `None` (Todos), `_entrada_para_slug(None)` retorna `None`, e não há `comp_config`. O `pl_total` mostrará apenas o principal, sem complementares.
**Por que acontece:** `calculate_roi_complementares` é por-mercado — não consolida múltiplos mercados.
**Como evitar:** Esta é a limitação esperada para DASH-02 (D-10 diz que breakdown detalhado é Phase 13). Documentar no card KPI com subtexto "apenas principal" quando filtro = Todos. Ou simplesmente omitir complementares no cálculo de "Todos" — comportamento consistente com a decisão D-10.

## Code Examples

### RadioItems Botões Segmentados (dbc, oficial)
```python
# Fonte: dash-bootstrap-components docs — RadioItems with btn-check
dbc.RadioItems(
    id="periodo-selector",
    options=[
        {"label": "Hoje",         "value": "hoje"},
        {"label": "Esta Semana",  "value": "semana"},
        {"label": "Este Mês",     "value": "mes"},
        {"label": "Mês Passado",  "value": "mes_passado"},
        {"label": "Toda a Vida",  "value": "toda_vida"},
        {"label": "Personalizado","value": "personalizado"},
    ],
    value="toda_vida",
    inline=True,
    input_class_name="btn-check",
    label_class_name="btn btn-outline-secondary btn-sm",
    label_checked_class_name="active",
)
```

### Collapse para DatePickerRange condicional
```python
# Layout
dbc.Collapse(
    dcc.DatePickerRange(
        id="filter-date-custom",
        display_format="DD/MM/YYYY",
        clearable=True,
        start_date_placeholder_text="Data início",
        end_date_placeholder_text="Data fim",
    ),
    id="collapse-datepicker",
    is_open=False,
    className="mt-2",
),

# Callback separado (pequeno, sem DB)
@callback(
    Output("collapse-datepicker", "is_open"),
    Input("periodo-selector", "value"),
)
def toggle_datepicker(periodo):
    return periodo == "personalizado"
```

### make_kpi_card — padrão existente (preservar)
```python
def make_kpi_card(title: str, value_id: str, color_class: str = "text-light"):
    """Build a KPI card with a muted title and a bold colored value."""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title text-muted"),
            html.H3(id=value_id, className=f"card-text {color_class} fw-bold"),
        ]),
        className="mb-2",
    )
```

Para P&L Total com cor dinâmica, não usar `color_class` no `make_kpi_card` — em vez disso, usar Output separado para `className`:
```python
# No layout:
dbc.Col(dbc.Card(dbc.CardBody([
    html.H6("P&L Total", className="card-title text-muted"),
    html.H3(id="kpi-pl-total", className="card-text fw-bold"),
]), className="mb-2"), md=2),

# No callback:
Output("kpi-pl-total", "children"),
Output("kpi-pl-total", "className"),
# ...
pl_color = "card-text fw-bold text-success" if pl > 0 else (
    "card-text fw-bold text-danger" if pl < 0 else "card-text fw-bold text-muted"
)
```

### Streaks nos KPI Cards
```python
# calculate_streaks retorna: {current, current_type, max_green, max_red}
streaks = calculate_streaks(history)  # history em ordem DESC (get_signal_history)

streak_green_text = f"{streaks['max_green']}x" if streaks["max_green"] > 0 else "—"
streak_red_text   = f"{streaks['max_red']}x"  if streaks["max_red"]   > 0 else "—"
```

### assets/custom.css — estrutura de diretório
```
helpertips/
├── assets/
│   └── custom.css   # Dash serve automaticamente
├── dashboard.py
└── ...
```

O Dash detecta `assets/` relativo ao arquivo que chama `dash.Dash(__name__)`. Não requer configuração adicional.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Filtros como `dcc.Dropdown` + `dcc.DatePickerRange` separados no topo | `dbc.RadioItems` btn-check para período + Collapse para DatePickerRange | Phase 11 | Seleção de período em um clique vs picker manual |
| Callbacks separados (master + tabs) | Callback master único para KPIs + callback leve para toggle | Phase 11 | Menos handlers, menos overhead de re-render |
| KPIs: total, greens, reds, pending, winrate | KPIs: total sinais, taxa green, P&L total, ROI, melhor streak, pior streak | Phase 11 | Dados financeiros reais vs contagens puras |
| ROI simulado em card separado | Stake/odd/gale em card de configuração, P&L nos KPIs | Phase 11 | Separação semântica filtros vs parâmetros |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | Runtime | ✓ | 3.12 | — |
| dash | Layout e callbacks | ✓ | >=4.1 (pyproject.toml) | — |
| dash-bootstrap-components | RadioItems, Card, Collapse | ✓ | >=2.0 (pyproject.toml) | — |
| dash-ag-grid | AG Grid histórico (opcional) | ✓ | >=31.0 (pyproject.toml) | Omitir da fase 11 |
| PostgreSQL | Queries de filtro | ✓ | 16 (EC2) | — |
| assets/ directory | CSS override contraste | ✗ | — | Criar na fase (Wave 0) |

**Sem bloqueadores:** Todos os pacotes estão instalados. O diretório `assets/` precisa ser criado se não existir.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command | `python3 -m pytest tests/test_dashboard.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | Novo layout tem os IDs de filtros globais (periodo-selector, filter-mercado, filter-liga, collapse-datepicker, filter-date-custom) | unit | `python3 -m pytest tests/test_dashboard.py::test_layout_has_required_component_ids -x` | ✅ (reescrever conteúdo) |
| DASH-01 | DatePickerRange está oculto por padrão (collapse is_open=False) | unit | `python3 -m pytest tests/test_dashboard.py::test_datepicker_collapse_initial_closed -x` | ❌ Wave 0 |
| DASH-01 | `_resolve_periodo("hoje")` retorna data de hoje como start e end | unit | `python3 -m pytest tests/test_dashboard.py::test_resolve_periodo_hoje -x` | ❌ Wave 0 |
| DASH-01 | `_resolve_periodo("mes_passado")` retorna primeiro e último dia do mês anterior | unit | `python3 -m pytest tests/test_dashboard.py::test_resolve_periodo_mes_passado -x` | ❌ Wave 0 |
| DASH-01 | `_resolve_periodo("personalizado", "2025-01-01", "2025-01-31")` retorna as datas fornecidas | unit | `python3 -m pytest tests/test_dashboard.py::test_resolve_periodo_personalizado -x` | ❌ Wave 0 |
| DASH-02 | KPI cards com novos IDs existem no layout | unit | `python3 -m pytest tests/test_dashboard.py::test_layout_has_required_component_ids -x` | ✅ (reescrever conteúdo) |
| DASH-02 | Formatação P&L total com sinal (+/-) e prefixo R$ | unit | `python3 -m pytest tests/test_dashboard.py::test_kpi_pl_formatting -x` | ❌ Wave 0 |
| DASH-02 | Streak green/red formatado como "Nx" ou "—" | unit | `python3 -m pytest tests/test_dashboard.py::test_kpi_streak_formatting -x` | ❌ Wave 0 |

### Sampling Rate
- **Por commit de task:** `python3 -m pytest tests/test_dashboard.py -x -q`
- **Por merge de wave:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Suite completa verde antes de `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_dashboard.py` — reescrever `test_layout_has_required_component_ids` com novos IDs (kpi-pl-total, kpi-roi, kpi-streak-green, kpi-streak-red, periodo-selector, filter-mercado, collapse-datepicker, filter-date-custom)
- [ ] `tests/test_dashboard.py::test_datepicker_collapse_initial_closed` — novo teste verificando `collapse-datepicker.is_open == False`
- [ ] `tests/test_dashboard.py::test_resolve_periodo_*` — 4 novos testes para a função `_resolve_periodo` (hoje, semana, mes_passado, personalizado, toda_vida)
- [ ] `tests/test_dashboard.py::test_kpi_pl_formatting` — verificar formatação "R$ +123.45" e cor class
- [ ] `tests/test_dashboard.py::test_kpi_streak_formatting` — verificar "12x" para max > 0 e "—" para 0
- [ ] `helpertips/assets/` — criar diretório se não existir; `helpertips/assets/custom.css` com CSS override de contraste

## Open Questions

1. **AG Grid de histórico: preservar ou remover nesta fase?**
   - O que sabemos: D-03 deixa isso em "Claude's Discretion"
   - O que está em aberto: Se preservado, o novo layout precisa de espaço para ele e os columnDefs existentes precisam ser mantidos. Se removido, os testes que verificam `"history-table"` falham até que seja readicionado em fase futura.
   - Recomendação: Preservar. O AG Grid é útil para debugging e os usuários têm expectativa de ver o histórico. Custo: ~0 esforço (copiar bloco existente para o novo layout).

2. **`get_filtered_stats` precisa de `mercado_id`?**
   - O que sabemos: A assinatura atual usa `entrada` (texto). `_build_where` aceita ambos. Usar `entrada="Over 2.5"` filtra corretamente.
   - O que está em aberto: Para consistência com as novas queries de Phase 10 que usam `mercado_id`, pode-se estender `get_filtered_stats` para aceitar `mercado_id`. Mas isso abre risco de breaking change nos testes de queries.
   - Recomendação: Usar `entrada=mercado` (passando o valor do dropdown diretamente) para `get_filtered_stats` e `get_signal_history`. Não alterar `queries.py` nesta fase. Apenas `get_signals_com_placar` (Phase 10) usa `mercado_id` — para P&L calculation.

3. **Valor padrão do RadioItems no carregamento da página**
   - O que sabemos: `value="toda_vida"` inicializa com "Toda a Vida" selecionado.
   - O que está em aberto: Se o usuário prefere "Este Mês" como padrão para dados mais relevantes.
   - Recomendação: Usar `"toda_vida"` como padrão — é o comportamento do dashboard atual (sem filtro de data) e não surpreende o usuário ao migrar do layout antigo.

## Project Constraints (from CLAUDE.md)

- **Stack obrigatório:** Python 3.12+, Dash >=4.1, dash-bootstrap-components >=2.0, psycopg2-binary, python-dotenv — nenhuma biblioteca adicional para esta fase
- **Separação de processos:** Dashboard roda como processo separado do listener — nunca importar Telethon em dashboard.py
- **Sessão Telethon:** Arquivo `.session` fora do escopo desta fase
- **Idioma:** Todo output de progresso, comentários de código quando necessário e artefatos GSD em pt-BR
- **GSD Workflow:** Alterações em arquivos do repo somente via GSD workflow (execute-phase)
- **Tema:** Dark theme DARKLY com dbc.Card — manter consistência visual
- **Linha de código:** ruff com `line-length = 150` — respeitar nos novos arquivos
- **Convenção de callbacks:** `@callback` decorator (não `@app.callback`); `get_connection()` dentro do callback, fechado no `finally`; `ctx.triggered_id` para identificar inputs quando necessário

## Sources

### Primary (HIGH confidence)
- Código existente `helpertips/dashboard.py` (1004 linhas) — padrões de callback, helpers, IDs existentes
- Código existente `helpertips/queries.py` — assinaturas de todas as funções de query
- `helpertips/pyproject.toml` — versões instaladas de todas as dependências
- `tests/test_dashboard.py` — testes existentes a reescrever
- `.planning/phases/11-dashboard-funda-o/11-CONTEXT.md` — decisões locked D-01 a D-14
- dash-bootstrap-components docs (RadioItems com btn-check) — padrão verificado no código existente de projetos similares

### Secondary (MEDIUM confidence)
- `.planning/helpertips_dashboard_preview.jsx` — mockup visual com estrutura de KPI cards e layout esperado
- `.planning/helpertips_v1.2_spec.md` — especificação completa do redesign (seção 3)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — todas as bibliotecas já instaladas, versões no pyproject.toml
- Architecture: HIGH — padrão de callback já estabelecido no código existente, helpers reutilizáveis identificados
- Pitfalls: HIGH — identificados diretamente da leitura do código existente (IDs, assinaturas de funções, comportamento de callbacks)

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stack estável, Dash 4.x sem breaking changes esperados em 30 dias)
