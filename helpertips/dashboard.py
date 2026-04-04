"""
dashboard.py — Dash web dashboard for HelperTips — Futebol Virtual.

Provides a dark-themed interactive analytics dashboard with:
  - KPI cards: total signals, greens, reds, pendentes, win rate
  - Filters: liga dropdown, entrada dropdown, date range picker, reset button
  - ROI simulation card with stake, odd, and Gale toggle inputs
  - Bar chart: GREEN vs RED vs Pendente counts
  - Win rate per liga horizontal bar chart
  - AG Grid signal history table with pending row highlighting (amber)
  - Auto-refresh every 60 seconds via dcc.Interval

Run as:
    python -m helpertips.dashboard
    python helpertips/dashboard.py

Requires DB_* environment variables in .env. Dashboard runs as a separate
process from listener.py — do NOT import Telethon here.
"""

import os

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

from helpertips.db import get_connection
from helpertips.queries import (
    calculate_equity_curve,
    calculate_roi,
    calculate_roi_complementares,
    calculate_streaks,
    get_complementares_config,
    get_cross_dimensional,
    get_distinct_values,
    get_filtered_stats,
    get_gale_analysis,
    # Novas funcoes — Phase 3
    get_heatmap_data,
    get_parse_failures_detail,
    get_signal_history,
    get_volume_by_day,
    get_winrate_by_dow,
    get_winrate_by_periodo,
)
from helpertips.store import get_stats

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        dag.themes.BASE,
        dag.themes.ALPINE,
    ],
    title="HelperTips — Futebol Virtual",
)
server = app.server  # WSGI callable para gunicorn


# ---------------------------------------------------------------------------
# Complementares helpers
# ---------------------------------------------------------------------------

_ENTRADA_SLUG_MAP = {
    "Over 2.5": "over_2_5",
    "Ambas Marcam": "ambas_marcam",
}


def _entrada_para_slug(entrada: str | None) -> str | None:
    """Mapeia nome de entrada (dropdown) para slug do mercado."""
    if entrada is None:
        return None
    return _ENTRADA_SLUG_MAP.get(entrada)


def _build_comp_table(por_mercado: list[dict]) -> dbc.Table:
    """Constroi dbc.Table com breakdown de complementares."""
    header = html.Thead(html.Tr([
        html.Th("Mercado"),
        html.Th("Greens", className="text-end"),
        html.Th("Reds", className="text-end"),
        html.Th("Lucro (R$)", className="text-end"),
    ]))

    rows = []
    total_greens = 0
    total_reds = 0
    total_lucro = 0.0
    for m in por_mercado:
        lucro = m["lucro"]
        lucro_class = "text-success" if lucro > 0 else ("text-danger" if lucro < 0 else "text-muted")
        rows.append(html.Tr([
            html.Td(m["nome_display"]),
            html.Td(str(m["greens"]), className="text-end"),
            html.Td(str(m["reds"]), className="text-end"),
            html.Td(f"R$ {lucro:+.2f}", className=f"text-end {lucro_class}"),
        ]))
        total_greens += m["greens"]
        total_reds += m["reds"]
        total_lucro += lucro

    # Linha de totais
    total_class = "text-success" if total_lucro > 0 else ("text-danger" if total_lucro < 0 else "text-muted")
    rows.append(html.Tr([
        html.Td("Total", className="fw-bold"),
        html.Td(str(total_greens), className="text-end fw-bold"),
        html.Td(str(total_reds), className="text-end fw-bold"),
        html.Td(f"R$ {total_lucro:+.2f}", className=f"text-end fw-bold {total_class}"),
    ]))

    body = html.Tbody(rows)
    return dbc.Table(
        [header, body],
        size="sm",
        bordered=False,
        hover=True,
        dark=True,
        className="mt-3",
    )


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------


def make_kpi_card(title: str, value_id: str, color_class: str = "text-light"):
    """Build a KPI card with a muted title and a bold colored value."""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title text-muted"),
            html.H3(id=value_id, className=f"card-text {color_class} fw-bold"),
        ]),
        className="mb-2",
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

app.layout = dbc.Container(
    [
        # Header
        html.H2([
            "HelperTips — Futebol Virtual ",
            dbc.Badge(
                id="badge-coverage",
                className="ms-2 fs-6",
                style={"cursor": "pointer"},
            ),
        ], className="text-center my-3"),

        # KPI Cards Row
        dbc.Row(
            [
                dbc.Col(make_kpi_card("Total Sinais", "kpi-total", "text-light"), md=2),
                dbc.Col(make_kpi_card("Greens", "kpi-greens", "text-success"), md=2),
                dbc.Col(make_kpi_card("Reds", "kpi-reds", "text-danger"), md=2),
                dbc.Col(make_kpi_card("Pendentes", "kpi-pending", "text-warning"), md=2),
                dbc.Col(make_kpi_card("Win Rate", "kpi-winrate", "text-info"), md=2),
            ],
            className="mb-3 g-2",
        ),

        # Filters Row
        dbc.Row(
            [
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
                    dbc.Button(
                        "Reset",
                        id="btn-reset",
                        color="secondary",
                        size="sm",
                    ),
                    md=2,
                    className="d-flex align-items-center",
                ),
            ],
            className="mb-3 g-2",
        ),

        # ROI Simulation Card
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Simulacao de ROI", className="card-title text-muted mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Stake (R$)", html_for="stake-input"),
                                    dbc.Input(
                                        id="stake-input",
                                        type="number",
                                        value=10,
                                        min=1,
                                        step=1,
                                        placeholder="Stake R$",
                                    ),
                                ],
                                md=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Odd", html_for="odd-input"),
                                    dbc.Input(
                                        id="odd-input",
                                        type="number",
                                        value=1.90,
                                        min=1.01,
                                        step=0.01,
                                        placeholder="Odd",
                                    ),
                                ],
                                md=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Modo"),
                                    dbc.Switch(
                                        id="gale-toggle",
                                        label="Com Gale",
                                        value=False,
                                        className="mt-1",
                                    ),
                                ],
                                md=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Lucro/Prejuizo"),
                                    html.H5(
                                        id="roi-profit",
                                        className="fw-bold",
                                    ),
                                ],
                                md=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("ROI %"),
                                    html.H5(
                                        id="roi-pct",
                                        className="fw-bold",
                                    ),
                                ],
                                md=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Total Investido"),
                                    html.H5(
                                        id="roi-invested",
                                        className="fw-bold text-muted",
                                    ),
                                ],
                                md=2,
                            ),
                        ],
                        className="g-2",
                    ),
                ]
            ),
            className="mb-3",
        ),

        # Card ROI Complementares
        dbc.Card(
            dbc.CardBody([
                html.H5("ROI Complementares", className="card-title text-muted mb-3"),
                html.Div(id="roi-comp-container"),
            ]),
            className="mb-3",
        ),

        # Charts Row
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="bar-chart"),
                    md=6,
                ),
                dbc.Col(
                    dcc.Graph(id="winrate-chart"),
                    md=6,
                ),
            ],
            className="mb-3",
        ),

        # Signal History Table
        dag.AgGrid(
            id="history-table",
            columnDefs=[
                {"headerName": "Liga", "field": "liga", "flex": 2},
                {"headerName": "Entrada", "field": "entrada", "flex": 2},
                {"headerName": "Horario", "field": "horario", "flex": 1},
                {"headerName": "Resultado", "field": "resultado", "flex": 1},
                {"headerName": "Placar", "field": "placar", "flex": 1},
                {"headerName": "Tent.", "field": "tentativa", "flex": 0.5},
            ],
            rowData=[],
            columnSize="sizeToFit",
            dashGridOptions={
                "theme": "legacy",
                "pagination": True,
                "paginationPageSize": 20,
                "paginationPageSizeSelector": False,
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
            style={"height": "600px"},
        ),

        # Analytics Tabs (D-01, D-02)
        dbc.Row(
            dbc.Col(
                dbc.Tabs(
                    id="tabs-analytics",
                    active_tab="tab-temporal",
                    className="mt-4",
                    children=[
                        dbc.Tab(label="Temporal", tab_id="tab-temporal", children=[
                            # Heatmap (ANAL-01) — ancora visual, full width, 400px
                            dbc.Card([
                                dbc.CardHeader(html.H5("Win Rate por Hora e Dia", className="fw-bold mb-0")),
                                dbc.CardBody(dcc.Graph(id="graph-heatmap", style={"height": "400px"})),
                            ], className="mt-3"),
                            # Equity curve (ANAL-05) — 350px
                            dbc.Card([
                                dbc.CardHeader(html.H5("Curva de Equity", className="fw-bold mb-0")),
                                dbc.CardBody(dcc.Graph(id="graph-equity", style={"height": "350px"})),
                            ], className="mt-3"),
                            # Win rate por dia da semana (ANAL-02) — 300px
                            dbc.Card([
                                dbc.CardHeader(html.H5("Win Rate por Dia da Semana", className="fw-bold mb-0")),
                                dbc.CardBody(dcc.Graph(id="graph-dow", style={"height": "300px"})),
                            ], className="mt-3"),
                        ]),
                        dbc.Tab(label="Gale & Streaks", tab_id="tab-gale", children=[
                            # Gale analysis (ANAL-07) — barras horizontais, 300px
                            dbc.Card([
                                dbc.CardHeader(html.H5("Recuperacao por Nivel de Gale", className="fw-bold mb-0")),
                                dbc.CardBody(dcc.Graph(id="graph-gale", style={"height": "300px"})),
                            ], className="mt-3"),
                            # Streaks (ANAL-06) — 3 mini-cards
                            dbc.Card([
                                dbc.CardHeader(html.H5("Streaks", className="fw-bold mb-0")),
                                dbc.CardBody(
                                    dbc.Row([
                                        dbc.Col(dbc.Card(dbc.CardBody([
                                            html.H6("Streak Atual", className="text-muted"),
                                            html.H3(id="kpi-streak-current", className="fw-bold"),
                                        ]), className="text-center"), md=4),
                                        dbc.Col(dbc.Card(dbc.CardBody([
                                            html.H6("Maior Sequencia GREEN", className="text-muted"),
                                            html.H3(id="kpi-streak-max-green", className="fw-bold text-success"),
                                        ]), className="text-center"), md=4),
                                        dbc.Col(dbc.Card(dbc.CardBody([
                                            html.H6("Maior Sequencia RED", className="text-muted"),
                                            html.H3(id="kpi-streak-max-red", className="fw-bold text-danger"),
                                        ]), className="text-center"), md=4),
                                    ]),
                                ),
                            ], className="mt-3"),
                        ]),
                        dbc.Tab(label="Volume", tab_id="tab-volume", children=[
                            # Volume chart (ANAL-08) — 280px
                            dbc.Card([
                                dbc.CardHeader(html.H5("Volume de Sinais", className="fw-bold mb-0")),
                                dbc.CardBody(dcc.Graph(id="graph-volume", style={"height": "280px"})),
                            ], className="mt-3"),
                            # Win rate por periodo (ANAL-03, D-02)
                            dbc.Card([
                                dbc.CardHeader(html.H5("Win Rate por Periodo", className="fw-bold mb-0")),
                                dbc.CardBody(id="table-periodo"),
                            ], className="mt-3"),
                            # Cross-dimensional breakdown (ANAL-04)
                            dbc.Card([
                                dbc.CardHeader(html.H5("Breakdown Cross-Dimensional", className="fw-bold mb-0")),
                                dbc.CardBody(id="table-cross-dimensional"),
                            ], className="mt-3"),
                        ]),
                    ],
                ),
                md=12,
            ),
            className="mb-4",
        ),

        # Modal parse failures (OPER-01, D-21)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Falhas de Parse")),
            dbc.ModalBody(id="modal-failures-body"),
            dbc.ModalFooter(
                dbc.Button("Fechar", id="btn-close-modal", className="ms-auto", color="secondary")
            ),
        ], id="modal-parse-failures", is_open=False, size="lg", scrollable=True),

        # Auto-refresh interval — fires every 60 seconds
        dcc.Interval(
            id="interval-refresh",
            interval=60_000,
            n_intervals=0,
        ),
    ],
    fluid=True,
    className="py-3",
)


# ---------------------------------------------------------------------------
# Figure helper functions (Phase 3 — Analytics Depth)
# ---------------------------------------------------------------------------


def _make_heatmap_figure(data: dict) -> go.Figure:
    if not any(cell is not None for row in data["z"] for cell in row):
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para o periodo selecionado",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=14, color="#aaa"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
    fig = go.Figure(go.Heatmap(
        z=data["z"], x=data["x"], y=data["y"],
        colorscale="RdYlGn", zmin=0, zmax=100,
        colorbar=dict(title="Win Rate %"), hoverongaps=False,
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=50, r=20),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def _make_equity_figure(data: dict) -> go.Figure:
    if not data["x"]:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum sinal com resultado no periodo selecionado",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=14, color="#aaa"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
    fig = go.Figure()
    # Stake Fixa (D-06: azul #17a2b8)
    fig.add_trace(go.Scatter(
        x=data["x"], y=data["y_fixa"], mode="lines+markers", name="Stake Fixa",
        line=dict(color="#17a2b8", width=2), marker=dict(color=data["colors"], size=8),
    ))
    # Gale (D-06: laranja #ffc107, linha tracejada)
    fig.add_trace(go.Scatter(
        x=data["x"], y=data["y_gale"], mode="lines+markers", name="Com Gale",
        line=dict(color="#ffc107", width=2, dash="dot"), marker=dict(color=data["colors"], size=8),
    ))
    # Breakeven (y=0)
    fig.add_trace(go.Scatter(
        x=[data["x"][0], data["x"][-1]], y=[0, 0], mode="lines", name="Breakeven",
        line=dict(color="#6c757d", dash="dash"), showlegend=True,
    ))
    # Annotations de streaks >= 5 (D-08)
    for ann in data.get("annotations", []):
        fig.add_annotation(x=ann["x"], y=ann["y"], text=ann["text"],
                           showarrow=True, arrowhead=2, font=dict(size=10, color="#ffc107"))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=60, r=20),
        xaxis_title="Sinal #", yaxis_title="Lucro (R$)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def _make_dow_figure(data: list) -> go.Figure:
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="Dados insuficientes para o periodo selecionado",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=14, color="#aaa"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
    fig = go.Figure(go.Bar(
        x=[d["dia_nome"] for d in data], y=[d["win_rate"] for d in data],
        marker_color="#17a2b8",
        text=[f"{d['win_rate']:.1f}%" for d in data], textposition="auto",
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=50, r=20),
        yaxis_title="Win Rate %", yaxis_range=[0, 100],
    )
    return fig


def _make_gale_figure(data: list) -> go.Figure:
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="Dados de tentativa indisponiveis",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=14, color="#aaa"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
    labels = [f"{d['tentativa']}a tentativa" for d in data]
    win_rates = [d["win_rate"] for d in data]
    colors = ["#28a745", "#ffc107", "#fd7e14", "#dc3545"]
    bar_colors = [colors[min(i, len(colors)-1)] for i in range(len(data))]
    fig = go.Figure(go.Bar(
        x=win_rates, y=labels, orientation="h", marker_color=bar_colors,
        text=[f"{wr:.1f}% ({d['total']} sinais)" for wr, d in zip(win_rates, data)],
        textposition="inside",
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=120, r=20),
        xaxis_title="Win Rate %", xaxis=dict(range=[0, 100], ticksuffix="%"),
    )
    return fig


def _make_volume_figure(data: list) -> go.Figure:
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="Nenhum sinal no periodo selecionado",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=14, color="#aaa"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig
    fig = go.Figure(go.Bar(
        x=[d["data"] for d in data], y=[d["count"] for d in data],
        marker_color="#17a2b8",
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=50, r=20),
        xaxis_title="Data", yaxis_title="Qtd. Sinais",
    )
    return fig


def _format_streak(count: int, streak_type: str | None) -> str:
    if count == 0 or streak_type is None:
        return "Sem dados"
    return f"{count} {'wins' if streak_type == 'GREEN' else 'losses'}"


def _build_cross_table(data: list) -> dbc.Table | html.P:
    if not data:
        return html.P("Aplique filtros para ver breakdown cruzado", className="text-muted text-center")
    header = html.Thead(html.Tr([
        html.Th("Liga"), html.Th("Entrada"),
        html.Th("Win Rate", className="text-end"),
        html.Th("Total Sinais", className="text-end"),
    ]))
    rows = []
    for d in data:
        row_class = "table-success" if d["win_rate"] > 60 else ""
        rows.append(html.Tr([
            html.Td(d["liga"]), html.Td(d["entrada"]),
            html.Td(f"{d['win_rate']:.1f}%", className="text-end"),
            html.Td(str(d["total"]), className="text-end"),
        ], className=row_class))
    return dbc.Table([header, html.Tbody(rows)], size="sm", bordered=False, hover=True, dark=True)


def _build_periodo_table(periodo_data: list):
    """Constroi dbc.Table com win rate por periodo (1T/2T/FT). ANAL-03."""
    if not periodo_data:
        return html.P("Sem dados de periodo disponveis.", className="text-muted")
    header = html.Thead(html.Tr([
        html.Th("Periodo"),
        html.Th("Greens"),
        html.Th("Total"),
        html.Th("Win Rate"),
    ]))
    rows = []
    for row in periodo_data:
        wr = row["win_rate"]
        cls = "table-success" if wr >= 60 else ""
        rows.append(html.Tr([
            html.Td(row["periodo"]),
            html.Td(str(row["greens"])),
            html.Td(str(row["total"])),
            html.Td(f"{wr:.1f}%"),
        ], className=cls))
    body = html.Tbody(rows)
    return dbc.Table([header, body], size="sm", bordered=False, hover=True, dark=True, responsive=True)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@callback(
    Output("kpi-total", "children"),
    Output("kpi-greens", "children"),
    Output("kpi-reds", "children"),
    Output("kpi-pending", "children"),
    Output("kpi-winrate", "children"),
    Output("roi-profit", "children"),
    Output("roi-pct", "children"),
    Output("roi-invested", "children"),
    Output("history-table", "rowData"),
    Output("bar-chart", "figure"),
    Output("winrate-chart", "figure"),
    Output("filter-liga", "options"),
    Output("filter-entrada", "options"),
    Output("roi-comp-container", "children"),
    Output("badge-coverage", "children"),
    Output("badge-coverage", "color"),
    Input("filter-liga", "value"),
    Input("filter-entrada", "value"),
    Input("filter-date", "start_date"),
    Input("filter-date", "end_date"),
    Input("gale-toggle", "value"),
    Input("stake-input", "value"),
    Input("odd-input", "value"),
    Input("interval-refresh", "n_intervals"),
)
def update_dashboard(liga, entrada, date_start, date_end, gale_on, stake, odd, _n):
    """
    Master callback: updates all KPI cards, ROI simulation, charts, and AG Grid
    whenever any filter, ROI parameter, or interval fires.

    Opens a new DB connection per invocation and closes in finally block
    (per Pitfall 2 — never hold a module-level connection).
    """
    conn = get_connection()
    try:
        # --- Stats ---
        stats = get_filtered_stats(conn, liga, entrada, date_start, date_end)
        total = stats["total"]
        greens = stats["greens"]
        reds = stats["reds"]
        pending = stats["pending"]
        winrate = (
            f"{(greens / (greens + reds) * 100):.1f}%"
            if (greens + reds) > 0
            else "\u2014"
        )

        # --- History ---
        history = get_signal_history(conn, liga, entrada, date_start, date_end)

        # --- ROI (defaults: R$10 stake, 1.90 odd) ---
        roi = calculate_roi(history, stake or 10.0, odd or 1.90, bool(gale_on))
        profit_text = f"R$ {roi['profit']:+.2f}"
        roi_pct_text = f"{roi['roi_pct']:+.1f}%"
        invested_text = f"R$ {roi['total_invested']:.2f}"

        # --- Bar chart: GREEN vs RED vs Pendente ---
        bar_fig = go.Figure(
            go.Bar(
                x=["GREEN", "RED", "Pendente"],
                y=[greens, reds, pending],
                marker_color=["#28a745", "#dc3545", "#ffc107"],
            )
        )
        bar_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=30, b=30, l=20, r=20),
            showlegend=False,
            title_text="Resultados",
        )

        # --- Win rate per liga chart (horizontal bar) ---
        liga_stats: dict = {}
        for sig in history:
            liga_key = sig.get("liga") or "Sem Liga"
            if liga_key not in liga_stats:
                liga_stats[liga_key] = {"greens": 0, "total": 0}
            if sig.get("resultado") in ("GREEN", "RED"):
                liga_stats[liga_key]["total"] += 1
                if sig["resultado"] == "GREEN":
                    liga_stats[liga_key]["greens"] += 1

        liga_names = sorted(liga_stats.keys())
        liga_winrates = [
            (
                liga_stats[liga_key]["greens"] / liga_stats[liga_key]["total"] * 100
                if liga_stats[liga_key]["total"] > 0
                else 0
            )
            for liga_key in liga_names
        ]
        winrate_fig = go.Figure(
            go.Bar(
                x=liga_winrates,
                y=liga_names,
                orientation="h",
                marker_color="#17a2b8",
                text=[f"{wr:.1f}%" for wr in liga_winrates],
                textposition="auto",
            )
        )
        winrate_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=30, b=30, l=100, r=20),
            showlegend=False,
            title_text="Win Rate por Liga",
            xaxis_title="Win Rate %",
        )

        # --- Dropdown options (fresh on every callback) ---
        liga_options = [
            {"label": v, "value": v} for v in get_distinct_values(conn, "liga")
        ]
        entrada_options = [
            {"label": v, "value": v} for v in get_distinct_values(conn, "entrada")
        ]

        # Serialize received_at (datetime objects are not JSON-serialisable by default)
        for row in history:
            if "received_at" in row and row["received_at"] is not None:
                row["received_at"] = str(row["received_at"])

        # --- ROI Complementares (per D-15, D-16, D-17) ---
        mercado_slug = _entrada_para_slug(entrada)
        if mercado_slug:
            comp_config = get_complementares_config(conn, mercado_slug)
            if comp_config:
                roi_comp = calculate_roi_complementares(
                    history, comp_config, stake or 10.0, bool(gale_on)
                )
                if roi_comp["total_invested"] > 0:
                    comp_profit = roi_comp["profit"]
                    comp_pct = roi_comp["roi_pct"]
                    comp_invested = roi_comp["total_invested"]
                    profit_class = "text-success" if comp_profit > 0 else ("text-danger" if comp_profit < 0 else "text-muted")
                    pct_class = "text-success" if comp_pct > 0 else ("text-danger" if comp_pct < 0 else "text-info")

                    # --- ROI Total Combinado (per D-17) ---
                    principal_profit = roi["profit"]
                    principal_invested = roi["total_invested"]
                    combined_profit = principal_profit + comp_profit
                    combined_invested = principal_invested + comp_invested
                    combined_pct = (combined_profit / combined_invested * 100) if combined_invested > 0 else 0.0
                    combined_profit_class = "text-success" if combined_profit > 0 else ("text-danger" if combined_profit < 0 else "text-muted")
                    combined_pct_class = "text-success" if combined_pct > 0 else ("text-danger" if combined_pct < 0 else "text-info")

                    comp_content = html.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Mercado"),
                                html.H5(entrada, className="fw-bold text-light"),
                            ], md=2),
                            dbc.Col([
                                dbc.Label("Lucro/Prejuizo"),
                                html.H5(f"R$ {comp_profit:+.2f}", className=f"fw-bold {profit_class}"),
                            ], md=2),
                            dbc.Col([
                                dbc.Label("ROI %"),
                                html.H5(f"{comp_pct:+.1f}%", className=f"fw-bold {pct_class}"),
                            ], md=2),
                            dbc.Col([
                                dbc.Label("Total Investido"),
                                html.H5(f"R$ {comp_invested:.2f}", className="fw-bold text-muted"),
                            ], md=2),
                        ], className="g-2"),
                        _build_comp_table(roi_comp["por_mercado"]),
                        # --- Linha Total Combinado (per D-17) ---
                        html.Hr(className="border-secondary mt-3 mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.H6("Total Combinado", className="text-muted mb-0"),
                                html.Small("Principal + Complementares", className="text-muted"),
                            ], md=3),
                            dbc.Col([
                                dbc.Label("Lucro Total", className="small text-muted"),
                                html.H5(f"R$ {combined_profit:+.2f}", className=f"fw-bold {combined_profit_class}"),
                            ], md=3),
                            dbc.Col([
                                dbc.Label("ROI Total %", className="small text-muted"),
                                html.H5(f"{combined_pct:+.1f}%", className=f"fw-bold {combined_pct_class}"),
                            ], md=3),
                            dbc.Col([
                                dbc.Label("Investido Total", className="small text-muted"),
                                html.H5(f"R$ {combined_invested:.2f}", className="fw-bold text-muted"),
                            ], md=3),
                        ], className="g-2 bg-dark bg-opacity-50 rounded p-2"),
                    ])
                else:
                    comp_content = dbc.Alert(
                        [html.H6("Sem sinais no periodo", className="alert-heading"),
                         html.P("Nenhum sinal com resultado encontrado para os filtros selecionados.")],
                        color="warning",
                    )
            else:
                comp_content = dbc.Alert(
                    [html.H6("Sem complementares configuradas", className="alert-heading"),
                     html.P(f"Nenhuma complementar configurada para '{entrada}'.")],
                    color="info",
                )
        else:
            comp_content = dbc.Alert(
                [html.H6("Selecione uma entrada", className="alert-heading"),
                 html.P("Escolha Over 2.5 ou Ambas Marcam no filtro acima para ver o breakdown de complementares.")],
                color="info",
            )

        # Badge coverage (OPER-01, D-19, D-20) — sempre global, sem filtros
        global_stats = get_stats(conn)
        coverage = global_stats["coverage"]
        badge_color = "success" if coverage >= 95 else ("warning" if coverage >= 90 else "danger")
        badge_text = f"Cobertura: {coverage:.1f}%"

        return (
            str(total),
            str(greens),
            str(reds),
            str(pending),
            winrate,
            profit_text,
            roi_pct_text,
            invested_text,
            history,
            bar_fig,
            winrate_fig,
            liga_options,
            entrada_options,
            comp_content,     # NOVO — roi-comp-container
            badge_text,
            badge_color,
        )
    finally:
        conn.close()


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
    Output("table-periodo", "children"),
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
    """Callback separado para conteudo das abas. Lazy render: so calcula aba ativa."""
    conn = get_connection()
    try:
        stake = stake or 10.0
        odd = odd or 1.90

        if active_tab == "tab-temporal":
            # Heatmap (ANAL-01, D-15)
            heatmap_data = get_heatmap_data(conn, liga, entrada, date_start, date_end)
            heatmap_fig = _make_heatmap_figure(heatmap_data)

            # Equity curve (ANAL-05, D-05 a D-09)
            history = get_signal_history(conn, liga, entrada, date_start, date_end)
            equity_data = calculate_equity_curve(history, stake, odd)
            equity_fig = _make_equity_figure(equity_data)

            # Win rate por dia da semana (ANAL-02, D-16)
            dow_data = get_winrate_by_dow(conn, liga, entrada, date_start, date_end)
            dow_fig = _make_dow_figure(dow_data)

            return heatmap_fig, equity_fig, dow_fig, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        elif active_tab == "tab-gale":
            # Gale analysis (ANAL-07, D-10 a D-12)
            gale_data = get_gale_analysis(conn, liga, entrada, date_start, date_end)
            gale_fig = _make_gale_figure(gale_data)

            # Streaks (ANAL-06, D-13)
            history = get_signal_history(conn, liga, entrada, date_start, date_end)
            streaks = calculate_streaks(history)
            current_label = _format_streak(streaks["current"], streaks["current_type"])
            max_green_label = f"{streaks['max_green']} wins" if streaks["max_green"] > 0 else "Sem dados"
            max_red_label = f"{streaks['max_red']} losses" if streaks["max_red"] > 0 else "Sem dados"

            return no_update, no_update, no_update, gale_fig, current_label, max_green_label, max_red_label, no_update, no_update, no_update

        elif active_tab == "tab-volume":
            # Volume (ANAL-08, D-18)
            vol_data = get_volume_by_day(conn, liga, entrada, date_start, date_end)
            vol_fig = _make_volume_figure(vol_data)

            # Win rate por periodo (ANAL-03)
            periodo_data = get_winrate_by_periodo(conn, liga, entrada, date_start, date_end)
            periodo_table = _build_periodo_table(periodo_data)

            # Cross-dimensional (ANAL-04, D-17)
            cross_data = get_cross_dimensional(conn, liga, entrada, date_start, date_end)
            cross_table = _build_cross_table(cross_data)

            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, vol_fig, cross_table, periodo_table

        return (no_update,) * 10
    finally:
        conn.close()


@callback(
    Output("modal-parse-failures", "is_open"),
    Output("modal-failures-body", "children"),
    Input("badge-coverage", "n_clicks"),
    Input("btn-close-modal", "n_clicks"),
    State("modal-parse-failures", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal(badge_clicks, close_clicks, is_open):
    """Toggle modal de parse failures ao clicar no badge."""
    if ctx.triggered_id == "badge-coverage":
        conn = get_connection()
        try:
            failures = get_parse_failures_detail(conn, limit=50)
        finally:
            conn.close()
        if not failures:
            body = html.P("Nenhuma falha de parse registrada.", className="text-muted")
        else:
            header = html.Thead(html.Tr([html.Th("Texto"), html.Th("Motivo"), html.Th("Data")]))
            rows = [html.Tr([
                html.Td(f["raw_text"][:100], style={"maxWidth": "400px", "overflow": "hidden", "textOverflow": "ellipsis"}),
                html.Td(f["failure_reason"]),
                html.Td(str(f["received_at"])[:19]),
            ]) for f in failures]
            body = dbc.Table([header, html.Tbody(rows)], size="sm", bordered=False, hover=True, dark=True, responsive=True)
        return True, body
    return False, no_update


@callback(
    Output("filter-liga", "value"),
    Output("filter-entrada", "value"),
    Output("filter-date", "start_date"),
    Output("filter-date", "end_date"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    """Reset all filter controls to their initial (unfiltered) state."""
    return None, None, None, None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=os.getenv('DASH_DEBUG', 'false').lower() == 'true',
        host="0.0.0.0",
        port=8050,
    )
