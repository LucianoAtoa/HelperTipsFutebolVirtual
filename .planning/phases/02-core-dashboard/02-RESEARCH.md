# Phase 02: Core Dashboard - Research

**Researched:** 2026-04-03
**Domain:** Plotly Dash 4.1.0 — interactive analytics dashboard with AG Grid, Bootstrap dark theme, ROI simulation, reactive filters
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Layout e Visual**
- D-01: Tema escuro fixo usando `dbc.themes.DARKLY` — visual de trading, sem toggle claro/escuro
- D-02: Template Plotly `plotly_dark` em todos os gráficos para consistência com o tema
- D-03: Layout vertical: KPI cards no topo → filtros → gráficos em grid 2 colunas → tabela de histórico na base
- D-04: Responsivo via Bootstrap 5 grid (`dbc.Row`/`dbc.Col`)

**Simulação de ROI**
- D-05: Stake fixa configurável (default R$ 10) + odd configurável (default 1.90, típico Over 2.5 virtual)
- D-06: Toggle Gale (martingale por tentativa) — stake dobra a cada tentativa (2x, 4x, 8x), campo `tentativa` já existe no banco
- D-07: Mostrar profit/loss acumulado — GREEN na tentativa 1 vs tentativa 4 tem custo completamente diferente com Gale
- D-08: Dois modos no card: "Stake Fixa" (sem Gale) e "Com Gale" (toggle), para o usuário comparar exposição real

**Filtros**
- D-09: Dropdowns horizontais no topo da página, reativos (sem botão Apply)
- D-10: Filtros compostos: liga + entrada simultâneos via callback multi-Input do Dash
- D-11: Botão Reset para limpar todos os filtros de uma vez
- D-12: DatePickerRange para filtrar por período de datas (mesmo layout horizontal)

**Tabela de Histórico**
- D-13: Dash AG Grid (dependência `dash-ag-grid`) — substituto oficial do DataTable, preparado para Dash 5
- D-14: 20 linhas por página, ordenação padrão por `received_at DESC`
- D-15: Todas as 6 colunas visíveis: liga, entrada, horario, resultado, placar, tentativa
- D-16: Sinais pendentes (resultado vazio) destacados com cor diferente na linha inteira via `getRowStyle`
- D-17: Sort interativo por coluna habilitado nativamente

### Claude's Discretion
- Cores exatas dos KPI cards (além de verde para GREEN, vermelho para RED)
- Formato dos números no ROI (R$ com 2 casas, percentual com 1 casa)
- Largura relativa das colunas no AG Grid
- Posição exata do DatePickerRange no layout de filtros
- Gráficos específicos para a Fase 2 (barras, linhas, etc — desde que cubram os success criteria)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | Dashboard web com interface elaborada e responsiva | dbc.themes.DARKLY + Bootstrap 5 grid provide responsive dark UI |
| DASH-02 | Card de estatísticas: total de sinais, greens, reds, taxa de acerto, percentuais | `get_stats()` in store.py already returns these; dbc.Card for display |
| DASH-03 | Simulação de ROI com stake fixa configurável | Pure Python math; dbc.Input for stake/odd; dbc.Switch for Gale toggle |
| DASH-04 | Filtro interativo por liga | dcc.Dropdown + multi-Input callback; distinct liga values from DB |
| DASH-05 | Filtro interativo por entrada (tipo de aposta) | Same pattern as liga filter; distinct entrada values from DB |
| DASH-06 | Lista de histórico de sinais paginada | dag.AgGrid with pagination=True, dashGridOptions paginationPageSize=20 |
| DASH-07 | Visualização de sinais pendentes (sem resultado) | getRowStyle with `!params.data.resultado` condition in AG Grid |
</phase_requirements>

---

## Summary

Phase 2 builds a Plotly Dash 4.1.0 dashboard that connects to the existing PostgreSQL database (via the established `get_connection()` and `get_stats()` from Phase 1) and answers "are these signals profitable?" The technology choices are already locked by CLAUDE.md: Dash 4.1.0, dash-bootstrap-components 2.0.x, and dash-ag-grid.

**Critical finding:** `dash-ag-grid` latest version is **35.2.0** (wrapping AG Grid 35.x), not 2.x as originally listed in some project docs. This is a major version bump that changes the theming API. The library still installs as `pip install dash-ag-grid` but dark theme requires `dashGridOptions={"theme": "legacy"}` plus `className="ag-theme-alpine-dark"` and `external_stylesheets=[dag.themes.BASE, dag.themes.ALPINE]`. The `getRowStyle` API is unchanged — it uses `styleConditions` with `params.data.fieldName` JavaScript expressions.

**Primary recommendation:** Create `helpertips/dashboard.py` as a new module in the existing package, using `get_connection()` from `helpertips.db` directly, and run it as a separate process (`python -m helpertips.dashboard`). Add Dash dependencies to `pyproject.toml` alongside existing deps.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| dash | 4.1.0 | Web framework + callback engine | Locked by CLAUDE.md; current latest on PyPI |
| dash-bootstrap-components | 2.0.4 | Dark theme + responsive layout | Locked by CLAUDE.md; Bootstrap 5 grid, DARKLY theme |
| dash-ag-grid | 35.2.0 | Signal history table | Locked by D-13; official DataTable replacement, Dash 5 ready |
| plotly | 6.6.0 | Charts (bundled with Dash) | Auto-installed by Dash; `plotly_dark` template available |
| psycopg2-binary | 2.9.11 | PostgreSQL queries | Already installed; sync driver fits dashboard read pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | >=1.0 | Load `.env` for DB credentials | Already in pyproject.toml; dashboard reuses same .env |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dag 35.2.0 legacy themes | New Theming API (v33+) | New API uses Python-only configuration but is less documented; legacy themes are proven |
| dcc.Dropdown | dbc.Select | dcc.Dropdown supports `multi=True` and clearable; dbc.Select is simpler but less featured |
| psycopg2 direct queries | SQLAlchemy | ORM adds overhead; raw SQL queries match existing store.py pattern |

**Installation:**
```bash
pip install "dash>=4.1,<5" "dash-bootstrap-components>=2.0" "dash-ag-grid>=31.0"
```

**Version verification (confirmed against PyPI on 2026-04-03):**
- dash: 4.1.0
- dash-bootstrap-components: 2.0.4
- dash-ag-grid: 35.2.0
- plotly: 6.6.0 (bundled with dash 4.1.0)

## Architecture Patterns

### Recommended Project Structure
```
helpertips/
├── db.py            # Existing — get_connection(), ensure_schema()
├── store.py         # Existing — get_stats(), upsert_signal()
├── listener.py      # Existing — Telethon listener (separate process)
├── dashboard.py     # NEW — Dash app entry point
└── queries.py       # NEW — Dashboard-specific SQL queries (filtered stats, history)

assets/              # NEW — Dash auto-loads CSS/JS from this folder
└── (empty or custom CSS overrides for AG Grid dark theme)
```

### Pattern 1: Dashboard Module Entry Point
**What:** `dashboard.py` creates the Dash app, defines layout, registers all callbacks, exposes `if __name__ == "__main__": app.run(...)`.
**When to use:** Single-file entry point keeps all Dash-specific code isolated from the listener.
**Example:**
```python
# Source: https://dash.plotly.com/installation (official docs)
import dash
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import dcc, html, Input, Output, callback

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        dag.themes.BASE,
        dag.themes.ALPINE,
    ],
)

app.layout = dbc.Container([
    # KPI cards row
    dbc.Row([...], className="mb-3"),
    # Filters row
    dbc.Row([...], className="mb-3"),
    # Charts row
    dbc.Row([...], className="mb-3"),
    # History table
    dag.AgGrid(id="history-table", ...),
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
```

### Pattern 2: Filtered Queries in queries.py
**What:** Separate module with SQL functions that accept filter params (liga, entrada, date_start, date_end) and return data for callbacks.
**When to use:** Keeps SQL out of callback functions; makes unit-testing queries possible.
**Example:**
```python
# helpertips/queries.py
def get_filtered_stats(conn, liga=None, entrada=None, date_start=None, date_end=None) -> dict:
    """Return stats dict filtered by optional parameters."""
    conditions = ["1=1"]
    params = []
    if liga:
        conditions.append("liga = %s")
        params.append(liga)
    if entrada:
        conditions.append("entrada = %s")
        params.append(entrada)
    if date_start:
        conditions.append("received_at >= %s")
        params.append(date_start)
    if date_end:
        conditions.append("received_at <= %s")
        params.append(date_end)
    where = " AND ".join(conditions)
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE resultado = 'GREEN') AS greens,
                COUNT(*) FILTER (WHERE resultado = 'RED') AS reds,
                COUNT(*) FILTER (WHERE resultado IS NULL) AS pending
            FROM signals WHERE {where}
        """, params)
        total, greens, reds, pending = cur.fetchone()
    return {"total": total, "greens": greens, "reds": reds, "pending": pending}


def get_distinct_ligas(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT liga FROM signals WHERE liga IS NOT NULL ORDER BY liga")
        return [row[0] for row in cur.fetchall()]


def get_signal_history(conn, liga=None, entrada=None, date_start=None, date_end=None, limit=500) -> list[dict]:
    """Return signal rows for the AG Grid table, pre-sorted received_at DESC."""
    # ... similar parameterized WHERE pattern
```

### Pattern 3: Multi-Input Reactive Callback
**What:** Single callback with multiple Input() triggers — fires whenever any filter changes.
**When to use:** All stats and charts update reactively when liga, entrada, or date range changes (D-09, D-10).
**Example:**
```python
# Source: https://dash.plotly.com/basic-callbacks (official docs)
from dash import Input, Output, callback

@callback(
    Output("kpi-total", "children"),
    Output("kpi-winrate", "children"),
    Output("roi-card", "children"),
    Output("history-table", "rowData"),
    Output("bar-chart", "figure"),
    Input("filter-liga", "value"),
    Input("filter-entrada", "value"),
    Input("filter-date", "start_date"),
    Input("filter-date", "end_date"),
    Input("gale-toggle", "value"),
    Input("stake-input", "value"),
    Input("odd-input", "value"),
)
def update_all(liga, entrada, date_start, date_end, gale_on, stake, odd):
    conn = get_connection()
    try:
        stats = get_filtered_stats(conn, liga, entrada, date_start, date_end)
        history = get_signal_history(conn, liga, entrada, date_start, date_end)
        roi = calculate_roi(history, stake or 10.0, odd or 1.90, gale_on)
        # build figure, format KPIs...
        return total_text, winrate_text, roi_content, history, fig
    finally:
        conn.close()
```

### Pattern 4: AG Grid with Dark Theme and Row Highlighting
**What:** AG Grid using legacy alpine-dark theme; pending signals highlighted via getRowStyle.
**When to use:** D-13, D-16 — table showing all signals with pending rows in amber.
**Example:**
```python
# Source: https://dash.plotly.com/dash-ag-grid/styling-themes (official docs)
import dash_ag_grid as dag

history_table = dag.AgGrid(
    id="history-table",
    columnDefs=[
        {"headerName": "Liga", "field": "liga", "width": 180},
        {"headerName": "Entrada", "field": "entrada", "width": 160},
        {"headerName": "Horário", "field": "horario", "width": 90},
        {"headerName": "Resultado", "field": "resultado", "width": 110},
        {"headerName": "Placar", "field": "placar", "width": 90},
        {"headerName": "Tent.", "field": "tentativa", "width": 70},
    ],
    rowData=[],  # populated by callback
    columnSize="sizeToFit",
    dashGridOptions={
        "theme": "legacy",
        "pagination": True,
        "paginationPageSize": 20,
        "paginationPageSizeSelector": False,
        "sortingOrder": ["desc", "asc", None],
    },
    defaultColDef={"sortable": True, "resizable": True},
    className="ag-theme-alpine-dark",
    getRowStyle={
        "styleConditions": [
            {
                "condition": "!params.data.resultado || params.data.resultado === ''",
                "style": {"backgroundColor": "#3a3000", "color": "#ffc107"},
            }
        ],
        "defaultStyle": {},
    },
    style={"height": "500px"},
)
```

### Pattern 5: ROI Calculation with Gale Logic
**What:** Pure Python function that iterates signal history and accumulates profit/loss.
**When to use:** D-05 through D-08 — ROI card with Stake Fixa and Com Gale modes.
**Example:**
```python
def calculate_roi(signals: list[dict], stake: float, odd: float, gale_on: bool) -> dict:
    """
    Calculate accumulated ROI for a list of signal dicts.
    Each signal has: resultado ('GREEN'/'RED'/None), tentativa (1-4 or None).
    With Gale: stake multiplies 2^(tentativa-1). Without Gale: stake is fixed.
    Returns: {"profit": float, "roi_pct": float, "total_invested": float}
    """
    total_profit = 0.0
    total_invested = 0.0
    for sig in signals:
        if sig["resultado"] is None:
            continue  # pending — skip
        tentativa = sig.get("tentativa") or 1
        if gale_on:
            effective_stake = stake * (2 ** (tentativa - 1))
        else:
            effective_stake = stake
        total_invested += effective_stake
        if sig["resultado"] == "GREEN":
            total_profit += effective_stake * (odd - 1)
        else:  # RED
            total_profit -= effective_stake
    roi_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0.0
    return {
        "profit": total_profit,
        "roi_pct": roi_pct,
        "total_invested": total_invested,
    }
```

### Pattern 6: Reset Filters Button
**What:** dbc.Button that fires a callback clearing all filter Dropdowns and DatePickerRange to None.
**When to use:** D-11 — single Reset button clears all filters simultaneously.
**Example:**
```python
@callback(
    Output("filter-liga", "value"),
    Output("filter-entrada", "value"),
    Output("filter-date", "start_date"),
    Output("filter-date", "end_date"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return None, None, None, None
```

### Anti-Patterns to Avoid
- **Opening a DB connection at module load time:** Connections become stale; open and close per callback instead. Use `try/finally: conn.close()`.
- **Sharing a single psycopg2 connection across callbacks:** Dash callbacks can run concurrently (with multi-threaded Flask); each callback must open its own connection.
- **Running `app.run()` inside listener.py:** Dashboard is a separate process (CLAUDE.md constraint). Never combine Dash and Telethon in one process.
- **Using DataTable instead of AG Grid:** DataTable is deprecated in Dash 4.x; the decision locks in AG Grid.
- **AG Grid `theme` in className without `dashGridOptions={"theme": "legacy"}`:** Without the legacy flag, v31+ uses the new Theming API and the `ag-theme-alpine-dark` className is silently ignored.
- **Calling `get_stats()` for filtered views:** `get_stats()` in `store.py` has no filter parameters — it always returns totals. Dashboard needs `get_filtered_stats()` in `queries.py`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reactive filter updates | Custom JS / polling | Dash multi-Input @callback | Dash callback engine handles reactivity, dependency graph, and concurrency |
| Dark-themed data grid with sort/paginate | HTML `<table>` with CSS | dag.AgGrid + ag-theme-alpine-dark | AG Grid handles virtual scroll, sorting, pagination, row styling natively |
| Responsive dark layout | Custom CSS framework | dbc.themes.DARKLY + dbc.Row/Col | Bootstrap 5 DARKLY provides full dark palette with zero custom CSS |
| Bar/line charts with dark bg | matplotlib/custom canvas | plotly.graph_objects with template="plotly_dark" | plotly_dark already inverts all chart colors for dark background |
| Date range picker | Custom HTML date inputs | dcc.DatePickerRange | Handles date parsing, locale, accessibility out of the box |
| Filter dropdown with clear | Custom HTML select | dcc.Dropdown(clearable=True) | Supports multi-select, search, clear — no custom JS needed |

**Key insight:** The entire interactive UI — filters, charts, table, KPI updates — is declarative Python. The Dash callback graph eliminates all manual DOM manipulation.

## Common Pitfalls

### Pitfall 1: AG Grid Theme Not Applied (Silent Failure)
**What goes wrong:** Grid renders with default light theme despite setting `className="ag-theme-alpine-dark"`. On dark DARKLY background, content is invisible.
**Why it happens:** dash-ag-grid v31+ switched to a new Theming API by default. Legacy theme classNames are ignored unless you explicitly opt in.
**How to avoid:** Always add `dashGridOptions={"theme": "legacy"}` when using `ag-theme-*` classNames. Also include `dag.themes.BASE` and `dag.themes.ALPINE` in `external_stylesheets`.
**Warning signs:** Grid shows no row lines, headers have white background while page is dark.

### Pitfall 2: Stale DB Connection in Callbacks
**What goes wrong:** PostgreSQL connection times out (default 10 minutes idle) and subsequent callbacks raise `InterfaceError: connection already closed`.
**Why it happens:** Holding one connection at module level between callback invocations.
**How to avoid:** Open a new connection per callback: `conn = get_connection()` inside the function body, always close in `finally` block.
**Warning signs:** First few interactions work, then errors start appearing after idle period.

### Pitfall 3: Callback Output Count Mismatch
**What goes wrong:** `dash.exceptions.InvalidCallbackReturnValue` at runtime when callback returns wrong number of outputs.
**Why it happens:** Multiple `Output()` declarations require the callback return tuple to have exactly the same count.
**How to avoid:** Count `Output()` declarations and count return values — they must match. Use a single master callback for all dashboard updates so outputs are clear.
**Warning signs:** App crashes on first interaction with cryptic Dash error.

### Pitfall 4: DatePickerRange Returns String Not datetime
**What goes wrong:** SQL query with `received_at >= %s` raises type error or returns wrong results.
**Why it happens:** `dcc.DatePickerRange` returns ISO strings ('2025-01-15') not Python datetime objects.
**How to avoid:** Cast strings in the query: `received_at::date >= %s::date` or parse in Python before passing to SQL.
**Warning signs:** Filter returns zero results even when data should match.

### Pitfall 5: ROI Gale Ignores Accumulated Loss Before Green
**What goes wrong:** Gale profit is calculated per-signal, not accounting for previous failed attempts in the same signal's cycle.
**Why it happens:** A signal may have tentativa=3 meaning attempts 1 and 2 were RED before attempt 3 was GREEN.
**How to avoid:** With Gale enabled, the cost for a GREEN at tentativa=3 must include the losses from tentativas 1 and 2 (stake * 1 + stake * 2). Use a model where each signal cycle accumulates all stake investments up to the GREEN. The `tentativa` field indicates where in the cycle the GREEN occurred.
**Warning signs:** ROI "Com Gale" shows higher profit than "Stake Fixa" for the same dataset — this is mathematically impossible if Gale is implemented correctly.

### Pitfall 6: get_stats() Not Suitable for Filtered Views
**What goes wrong:** KPI cards always show total counts regardless of active filters.
**Why it happens:** The existing `store.get_stats()` runs an unconditional `SELECT COUNT(*) FROM signals` — it has no filter parameters.
**How to avoid:** Create `queries.get_filtered_stats(conn, liga, entrada, date_start, date_end)` in a new `helpertips/queries.py`. Reuse `store.get_stats()` only for the "all signals" startup summary or unfiltered view.
**Warning signs:** Changing the liga dropdown has no effect on the stats cards.

## Code Examples

Verified patterns from official sources:

### Dash App Initialization with DARKLY + AG Grid Dark Theme
```python
# Source: https://dash.plotly.com/installation + https://dash.plotly.com/dash-ag-grid/styling-themes
import dash
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,       # Bootstrap 5 dark theme
        dag.themes.BASE,         # AG Grid base CSS (required for legacy themes)
        dag.themes.ALPINE,       # AG Grid alpine theme CSS
    ],
    title="HelperTips — Futebol Virtual",
)
```

### KPI Card with dbc.Card
```python
# Source: https://www.dash-bootstrap-components.com/docs/components/ (official docs)
def make_kpi_card(title, value_id, color_class="text-light"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title text-muted"),
            html.H3(id=value_id, className=f"card-text {color_class} fw-bold"),
        ]),
        className="mb-2",
    )

# Usage:
kpi_row = dbc.Row([
    dbc.Col(make_kpi_card("Total Sinais", "kpi-total"), md=2),
    dbc.Col(make_kpi_card("Greens", "kpi-greens", "text-success"), md=2),
    dbc.Col(make_kpi_card("Reds", "kpi-reds", "text-danger"), md=2),
    dbc.Col(make_kpi_card("Pendentes", "kpi-pending", "text-warning"), md=2),
    dbc.Col(make_kpi_card("Win Rate", "kpi-winrate", "text-info"), md=2),
], className="mb-3 g-2")
```

### Filter Row with DatePickerRange
```python
# Source: https://dash.plotly.com/dash-core-components/datepickerrange (official docs)
from dash import dcc
import dash_bootstrap_components as dbc

filter_row = dbc.Row([
    dbc.Col(
        dcc.Dropdown(
            id="filter-liga",
            placeholder="Todas as ligas",
            clearable=True,
        ),
        md=3,
    ),
    dbc.Col(
        dcc.Dropdown(
            id="filter-entrada",
            placeholder="Todas as entradas",
            clearable=True,
        ),
        md=3,
    ),
    dbc.Col(
        dcc.DatePickerRange(
            id="filter-date",
            display_format="DD/MM/YYYY",
            clearable=True,
        ),
        md=4,
    ),
    dbc.Col(
        dbc.Button("Reset", id="btn-reset", color="secondary", size="sm"),
        md=2,
        className="d-flex align-items-center",
    ),
], className="mb-3 g-2")
```

### Plotly Bar Chart with Dark Template
```python
import plotly.graph_objects as go

def make_results_bar(greens: int, reds: int, pending: int) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=["GREEN", "RED", "Pendente"],
            y=[greens, reds, pending],
            marker_color=["#28a745", "#dc3545", "#ffc107"],
        )
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=20, r=20),
        showlegend=False,
    )
    return fig
```

### Populate Dropdown Options from DB
```python
# Pattern for loading liga/entrada options reactively or at startup
def get_dropdown_options(conn, field: str) -> list[dict]:
    """Return Dash-format options list for a given text field."""
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT DISTINCT {field} FROM signals WHERE {field} IS NOT NULL ORDER BY {field}"
        )
        return [{"label": row[0], "value": row[0]} for row in cur.fetchall()]

# In layout (static) or in a callback that populates options:
conn = get_connection()
try:
    liga_options = get_dropdown_options(conn, "liga")
    entrada_options = get_dropdown_options(conn, "entrada")
finally:
    conn.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| dcc.DataTable | dag.AgGrid | Dash 3.x / AG Grid adoption | DataTable deprecated; AG Grid is official replacement with better performance |
| ag-theme-alpine (className only) | `dashGridOptions={"theme": "legacy"}` required | dash-ag-grid v31 | Breaking: old className approach silently ignored without legacy flag |
| `app.run_server(debug=True)` | `app.run(debug=True)` | Dash 2.x | `run_server` still works but `run` is the current API |
| dash.dependencies.Input/Output | `from dash import Input, Output` | Dash 2.x | Shorter import path |

**Deprecated/outdated:**
- `agGridColumn` child component: removed in dash-ag-grid v31+. Use `columnDefs` list of dicts instead.
- `dcc.DataTable`: deprecated in Dash 4.x. Use `dag.AgGrid`.
- `app.run_server()`: still works but `app.run()` is canonical in Dash 4.x docs.

## Open Questions

1. **Gale accumulated cost model**
   - What we know: `tentativa` field records which attempt produced GREEN (1-4). RED signals presumably have a tentativa too, or it may be NULL for RED.
   - What's unclear: Does a RED signal at tentativa=4 mean all 4 attempts failed? Or just the last one? This affects total Gale investment calculation.
   - Recommendation: Inspect real signal data in the DB before finalizing the ROI Gale formula. For planning purposes, assume tentativa for RED = the attempt number of the final RED, so total Gale cost = sum of stakes for all attempts up to and including that tentativa.

2. **Dropdown option loading strategy (static vs dynamic)**
   - What we know: Options for liga and entrada dropdowns need distinct values from DB.
   - What's unclear: Load options once at app start (simpler) vs reload dynamically via callback when new signals arrive (always fresh).
   - Recommendation: Load at callback time (each time filters change), fetching distinct values from DB. Overhead is negligible for this data volume; always reflects current state.

3. **Auto-refresh interval**
   - What we know: Requirements say no push real-time updates (OUT OF SCOPE); manual/periodic refresh is sufficient.
   - What's unclear: Whether a `dcc.Interval` every 60 seconds would be desirable.
   - Recommendation: Add a `dcc.Interval(interval=60_000)` as an additional Input to the master callback so the dashboard refreshes automatically without user action. This is a one-liner addition, stays within scope, and improves usability significantly.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | Runtime | ✓ (3.13.6) | 3.13.6 | — |
| psycopg2-binary | DB layer | ✓ | 2.9.11 | — |
| dash | Web framework | installable | 4.1.0 (pip) | — |
| dash-bootstrap-components | Dark theme + layout | installable | 2.0.4 (pip) | — |
| dash-ag-grid | History table | installable | 35.2.0 (pip) | — |
| PostgreSQL server | DB connection | ✗ (not in PATH) | — | Requires running PG instance via .env config |

**Missing dependencies with no fallback:**
- PostgreSQL server must be running and accessible via DB_* env vars in `.env`. `pg_isready` not in PATH on this machine but psycopg2 is importable, so connection depends on runtime DB availability.

**Missing dependencies with fallback:**
- dash, dash-bootstrap-components, dash-ag-grid are not yet installed but are pip-installable. Wave 0 plan must include `pip install` step.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x (configured in pyproject.toml) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/test_dashboard.py -x -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | Dashboard app initializes without error | unit | `pytest tests/test_dashboard.py::test_app_layout_renders -x` | ❌ Wave 0 |
| DASH-02 | KPI card shows correct counts from stats dict | unit | `pytest tests/test_dashboard.py::test_kpi_display -x` | ❌ Wave 0 |
| DASH-03 | ROI calculation — stake fixa and gale modes | unit | `pytest tests/test_queries.py::test_roi_calculation -x` | ❌ Wave 0 |
| DASH-04 | Liga filter returns filtered stats | unit | `pytest tests/test_queries.py::test_get_filtered_stats_liga -x` | ❌ Wave 0 |
| DASH-05 | Entrada filter returns filtered stats | unit | `pytest tests/test_queries.py::test_get_filtered_stats_entrada -x` | ❌ Wave 0 |
| DASH-06 | History query returns rows sorted by received_at DESC | unit | `pytest tests/test_queries.py::test_get_signal_history -x` | ❌ Wave 0 |
| DASH-07 | Pending signals (resultado=NULL) identified correctly | unit | `pytest tests/test_queries.py::test_pending_signals -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_queries.py -x`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_dashboard.py` — covers DASH-01, DASH-02 (app layout and KPI display unit tests)
- [ ] `tests/test_queries.py` — covers DASH-03 through DASH-07 (ROI logic and SQL query unit tests)

*Note: DASH-01 layout render test can be pure unit test (test that `app.layout` is not None and contains expected component IDs). DASH-03 ROI calculation is pure Python — no DB required. DASH-04..07 filtered query tests require DB connection (like test_store.py pattern with skip fixture).*

## Project Constraints (from CLAUDE.md)

| Directive | Impact on Dashboard |
|-----------|---------------------|
| Stack: Dash 4.1.0, dash-bootstrap-components 2.x, psycopg2-binary | No substitutions allowed |
| Dashboard runs as separate process from listener | `helpertips/dashboard.py` launched independently; never import Telethon in dashboard |
| Python 3.12+ | f-strings, walrus operator, match statements available |
| pip install -e . for dev | Dashboard module added to same package; no new package required |
| Telethon session file in .gitignore | Not relevant to dashboard; no Telegram access |
| GSD workflow enforcement | All file changes go through GSD execute-phase, not direct edits |

## Sources

### Primary (HIGH confidence)
- https://dash.plotly.com/installation — Dash 4.1.0 current version confirmed
- https://dash.plotly.com/dash-ag-grid/styling-themes — Legacy theme setup for ag-theme-alpine-dark
- https://dash.plotly.com/dash-ag-grid/migration-guide — Breaking changes v2 → v31+
- https://dash.plotly.com/dash-ag-grid/row-styling — getRowStyle API with styleConditions
- https://dash.plotly.com/basic-callbacks — Multi-Input callback @callback decorator
- https://dash.plotly.com/dash-core-components/datepickerrange — DatePickerRange properties
- https://www.dash-bootstrap-components.com/docs/components/ — dbc.themes.DARKLY, component list
- PyPI `pip3 index versions` — Verified dash 4.1.0, dash-ag-grid 35.2.0, dash-bootstrap-components 2.0.4

### Secondary (MEDIUM confidence)
- https://dashaggrid.pythonanywhere.com/layout/themes — Confirmed ag-theme-alpine-dark className + legacy flag pattern
- https://community.plotly.com/t/dark-light-theme-with-ag-grid/88264 — Community confirmation of legacy theme approach

### Tertiary (LOW confidence)
- None — all critical claims verified with official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified via `pip3 index versions` against PyPI on 2026-04-03
- Architecture: HIGH — patterns from official Dash docs; queries.py separation is standard Dash practice
- AG Grid theming: HIGH — verified via official Dash AG Grid theming docs + community confirmation
- ROI Gale model: MEDIUM — logic derived from CONTEXT.md description; exact tentativa semantics need DB data validation (see Open Questions)
- Pitfalls: HIGH — most sourced from official migration guides and verified breaking change notes

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (Dash 4.x is current stable; AG Grid theming API unlikely to change in 30 days)
