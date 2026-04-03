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

import dash
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go

from helpertips.db import get_connection
from helpertips.queries import (
    get_filtered_stats,
    get_signal_history,
    get_distinct_values,
    calculate_roi,
    get_complementares_config,
    calculate_roi_complementares,
)

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
        html.H2(
            "HelperTips — Futebol Virtual",
            className="text-center my-3",
        ),

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
            l = sig.get("liga") or "Sem Liga"
            if l not in liga_stats:
                liga_stats[l] = {"greens": 0, "total": 0}
            if sig.get("resultado") in ("GREEN", "RED"):
                liga_stats[l]["total"] += 1
                if sig["resultado"] == "GREEN":
                    liga_stats[l]["greens"] += 1

        liga_names = sorted(liga_stats.keys())
        liga_winrates = [
            (
                liga_stats[l]["greens"] / liga_stats[l]["total"] * 100
                if liga_stats[l]["total"] > 0
                else 0
            )
            for l in liga_names
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
        )
    finally:
        conn.close()


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
    app.run(debug=True, host="0.0.0.0", port=8050)
