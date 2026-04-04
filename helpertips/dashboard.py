"""
dashboard.py — Dash web dashboard for HelperTips — Futebol Virtual.

Layout v1.2 com filtros globais, KPI cards financeiros e callback master unico.

Provides:
  - Filtros globais: periodo (RadioItems), mercado (Dropdown), liga (Dropdown)
  - DatePickerRange condicional para periodo Personalizado
  - 6 KPI cards: Total Sinais, Taxa Green, P&L Total, ROI, Melhor Streak, Pior Streak
  - Card de parametros de simulacao: Stake, Odd, Gale toggle
  - AG Grid com historico de sinais paginado
  - Auto-refresh a cada 60 segundos

Run as:
    python -m helpertips.dashboard
    DASH_DEBUG=true python -m helpertips.dashboard

Requires DB_* environment variables in .env. Dashboard runs as a separate
process from listener.py — do NOT import Telethon here.
"""

import os
from datetime import date, timedelta

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.graph_objects as go  # noqa: F401 — disponivel para fases futuras
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

from helpertips.db import get_connection
from helpertips.queries import (
    calculate_roi,
    calculate_roi_complementares,
    calculate_streaks,
    get_complementares_config,
    get_distinct_values,
    get_filtered_stats,
    get_parse_failures_detail,
    get_signal_history,
)
from helpertips.store import ENTRADA_PARA_MERCADO_ID

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="HelperTips \u2014 Futebol Virtual",
)
server = app.server  # WSGI callable para gunicorn


# ---------------------------------------------------------------------------
# Helpers
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


def make_kpi_card(title: str, value_id: str, color_class: str = "text-light"):
    """Constroi um KPI card com titulo muted e valor em bold colorido."""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title text-muted"),
            html.H3(id=value_id, className=f"card-text {color_class} fw-bold"),
        ]),
        className="mb-2",
    )


# ---------------------------------------------------------------------------
# _resolve_periodo — converte selecao de periodo em date_start/date_end
# ---------------------------------------------------------------------------


def _resolve_periodo(periodo: str | None, custom_start=None, custom_end=None):
    """Converte selecao de periodo em (date_start, date_end) ISO strings."""
    today = date.today()
    if periodo == "hoje":
        return str(today), str(today)
    elif periodo == "semana":
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
        return custom_start, custom_end
    else:  # "toda_vida" ou None
        return None, None


# ---------------------------------------------------------------------------
# Layout v1.2
# ---------------------------------------------------------------------------

app.layout = dbc.Container([
    # Header
    html.H2("HelperTips \u2014 Futebol Virtual", className="text-center my-3"),

    # Filtros Globais (D-04 a D-08)
    dbc.Card(dbc.CardBody([
        dbc.Row([dbc.Col([
            html.Label("Periodo:", className="text-muted small mb-1"),
            dbc.RadioItems(
                id="periodo-selector",
                options=[
                    {"label": "Hoje",          "value": "hoje"},
                    {"label": "Esta Semana",   "value": "semana"},
                    {"label": "Este Mes",      "value": "mes"},
                    {"label": "Mes Passado",   "value": "mes_passado"},
                    {"label": "Toda a Vida",   "value": "toda_vida"},
                    {"label": "Personalizado", "value": "personalizado"},
                ],
                value="toda_vida",
                inline=True,
                input_class_name="btn-check",
                label_class_name="btn btn-outline-secondary btn-sm",
                label_checked_class_name="active",
            ),
        ], md=12)]),
        dbc.Collapse(
            dcc.DatePickerRange(
                id="filter-date-custom",
                display_format="DD/MM/YYYY",
                clearable=True,
                start_date_placeholder_text="Data inicio",
                end_date_placeholder_text="Data fim",
            ),
            id="collapse-datepicker",
            is_open=False,
            className="mt-2",
        ),
        dbc.Row([
            dbc.Col([
                html.Label("Mercado:", className="text-muted small mb-1"),
                dcc.Dropdown(
                    id="filter-mercado",
                    options=[
                        {"label": "Todos", "value": ""},
                        {"label": "Over 2.5", "value": "Over 2.5"},
                        {"label": "Ambas Marcam", "value": "Ambas Marcam"},
                    ],
                    value="",
                    placeholder="Todos os mercados",
                    clearable=True,
                ),
            ], md=4),
            dbc.Col([
                html.Label("Liga:", className="text-muted small mb-1"),
                dcc.Dropdown(
                    id="filter-liga",
                    options=[],
                    value=None,
                    placeholder="Todas as ligas",
                    clearable=True,
                ),
            ], md=4),
        ], className="mt-2"),
    ]), className="mb-3"),

    # KPI Cards — 6 cards em row unica (D-09, D-10, D-11, D-12)
    dbc.Row([
        dbc.Col(make_kpi_card("Total Sinais",    "kpi-total",        "text-light"),   md=2),
        dbc.Col(make_kpi_card("Taxa Green",       "kpi-winrate",      "text-success"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("P&L Total", className="card-title text-muted"),
            html.H3(id="kpi-pl-total", className="card-text fw-bold"),
        ]), className="mb-2"), md=2),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("ROI", className="card-title text-muted"),
            html.H3(id="kpi-roi", className="card-text fw-bold"),
        ]), className="mb-2"), md=2),
        dbc.Col(make_kpi_card("Melhor Streak",    "kpi-streak-green", "text-success"), md=2),
        dbc.Col(make_kpi_card("Pior Streak",      "kpi-streak-red",   "text-danger"),  md=2),
    ], className="mb-3 g-2"),

    # Card Simulacao (D-13, D-14)
    dbc.Card(dbc.CardBody([
        html.H6("Parametros de Simulacao", className="card-title text-muted"),
        dbc.Row([
            dbc.Col([
                html.Label("Stake (R$):", className="text-muted small"),
                dbc.Input(id="stake-input", type="number", value=10, min=1, step=1, className="bg-dark text-light"),
            ], md=3),
            dbc.Col([
                html.Label("Odd:", className="text-muted small"),
                dbc.Input(id="odd-input", type="number", value=1.65, min=1.01, step=0.01, className="bg-dark text-light"),
            ], md=3),
            dbc.Col([
                html.Label("Gale:", className="text-muted small"),
                dbc.Switch(id="gale-toggle", value=True, label="Ativo", className="mt-1"),
            ], md=3),
        ]),
    ]), className="mb-3"),

    # AG Grid historico (D-03 — preservado)
    dbc.Card(dbc.CardBody([
        html.H6("Historico de Sinais", className="card-title text-muted"),
        dag.AgGrid(
            id="history-table",
            columnDefs=[
                {"field": "data_hora", "headerName": "Data/Hora", "sortable": True, "filter": True, "width": 160},
                {"field": "liga", "headerName": "Liga", "sortable": True, "filter": True},
                {"field": "entrada", "headerName": "Mercado", "sortable": True, "filter": True},
                {"field": "time_casa", "headerName": "Casa", "filter": True},
                {"field": "time_fora", "headerName": "Fora", "filter": True},
                {"field": "resultado", "headerName": "Resultado", "sortable": True, "filter": True,
                 "cellStyle": {"styleConditions": [
                     {"condition": "params.value === 'GREEN'", "style": {"color": "#28a745"}},
                     {"condition": "params.value === 'RED'", "style": {"color": "#dc3545"}},
                 ]}},
                {"field": "tentativa", "headerName": "Tentativa", "sortable": True, "width": 100},
                {"field": "placar", "headerName": "Placar", "width": 80},
            ],
            defaultColDef={"resizable": True, "minWidth": 80},
            dashGridOptions={"pagination": True, "paginationPageSize": 20, "domLayout": "autoHeight"},
            className="ag-theme-alpine-dark",
            style={"width": "100%"},
        ),
    ]), className="mb-3"),

    # Placeholder para fases 12-13
    html.Div(id="analytics-placeholder"),

    # Modal parse failures (mantido — redesenho futuro)
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Falhas de Parse")),
        dbc.ModalBody(id="modal-failures-body"),
        dbc.ModalFooter(dbc.Button("Fechar", id="btn-close-modal", className="ms-auto")),
    ], id="modal-parse-failures", size="lg", is_open=False),

    # Auto-refresh 60s
    dcc.Interval(id="interval-refresh", interval=60_000, n_intervals=0),
], fluid=True)


# ---------------------------------------------------------------------------
# Callback: toggle datepicker (D-05)
# ---------------------------------------------------------------------------


@callback(
    Output("collapse-datepicker", "is_open"),
    Input("periodo-selector", "value"),
)
def toggle_datepicker(periodo):
    """Abre o DatePickerRange apenas quando periodo == 'personalizado'."""
    return periodo == "personalizado"


# ---------------------------------------------------------------------------
# Callback master unico (D-02, D-11)
# ---------------------------------------------------------------------------


@callback(
    Output("kpi-total",        "children"),
    Output("kpi-winrate",      "children"),
    Output("kpi-pl-total",     "children"),
    Output("kpi-pl-total",     "className"),
    Output("kpi-roi",          "children"),
    Output("kpi-roi",          "className"),
    Output("kpi-streak-green", "children"),
    Output("kpi-streak-red",   "children"),
    Output("history-table",    "rowData"),
    Output("filter-liga",      "options"),
    Input("periodo-selector",  "value"),
    Input("filter-date-custom", "start_date"),
    Input("filter-date-custom", "end_date"),
    Input("filter-mercado",    "value"),
    Input("filter-liga",       "value"),
    Input("stake-input",       "value"),
    Input("odd-input",         "value"),
    Input("gale-toggle",       "value"),
    Input("interval-refresh",  "n_intervals"),
)
def update_dashboard(periodo, custom_start, custom_end, mercado, liga, stake, odd, gale_on, _n):
    """Callback master: atualiza todos os KPIs, historico e opcoes de liga."""
    # 1. Resolver periodo em datas
    date_start, date_end = _resolve_periodo(periodo, custom_start, custom_end)

    # 2. Sanitizar parametros de simulacao
    stake = float(stake or 10)
    odd = float(odd or 1.65)
    gale_on = bool(gale_on)

    # 3. Converter mercado dropdown em entrada (string) para queries
    # Pitfall 2: usar 'entrada' (string), nao mercado_id
    entrada = mercado if mercado else None

    # 4. Conectar ao banco
    conn = get_connection()
    try:
        # 5. Stats agregados
        stats = get_filtered_stats(conn, liga=liga, entrada=entrada, date_start=date_start, date_end=date_end)

        # 6. Historico de sinais
        history = get_signal_history(conn, liga=liga, entrada=entrada, date_start=date_start, date_end=date_end)

        # 7. KPIs basicos
        total = stats["total"]
        greens = stats["greens"]
        reds = stats["reds"]
        winrate = f"{greens / (greens + reds) * 100:.1f}%" if (greens + reds) > 0 else "\u2014"

        # 8. P&L principal
        roi_principal = calculate_roi(history, stake, odd, gale_on)
        pl_principal = roi_principal["profit"]
        total_invested_principal = roi_principal["total_invested"]

        # 9. P&L complementar
        if entrada:  # mercado especifico selecionado
            slug = _entrada_para_slug(entrada)
            if slug:
                comp_config = get_complementares_config(conn, slug)
                roi_comp = calculate_roi_complementares(history, comp_config, stake, gale_on)
                pl_comp = roi_comp["profit"]
                total_invested_comp = roi_comp["total_invested"]
            else:
                pl_comp = 0.0
                total_invested_comp = 0.0
        else:
            pl_comp = 0.0
            total_invested_comp = 0.0

        # 10. P&L total
        pl_total = pl_principal + pl_comp

        # 11. ROI total
        total_invested = total_invested_principal + total_invested_comp
        roi_total = (pl_total / total_invested * 100) if total_invested > 0 else 0.0

        # 12. Formatacao P&L
        pl_text = f"R$ {pl_total:+.2f}"
        if pl_total > 0:
            pl_class = "card-text fw-bold text-success"
        elif pl_total < 0:
            pl_class = "card-text fw-bold text-danger"
        else:
            pl_class = "card-text fw-bold text-muted"

        # 13. Formatacao ROI
        roi_text = f"{roi_total:+.1f}%"
        if roi_total > 0:
            roi_class = "card-text fw-bold text-success"
        elif roi_total < 0:
            roi_class = "card-text fw-bold text-danger"
        else:
            roi_class = "card-text fw-bold text-muted"

        # 14. Streaks
        streaks = calculate_streaks(history)
        streak_green = f"{streaks['max_green']}x" if streaks["max_green"] > 0 else "\u2014"
        streak_red = f"{streaks['max_red']}x" if streaks["max_red"] > 0 else "\u2014"

        # 15. Liga options
        ligas = get_distinct_values(conn, "liga")
        liga_options = [{"label": v, "value": v} for v in ligas]

        # 16. History rowData para AG Grid
        row_data = []
        for sig in history:
            received_at = sig.get("received_at")
            if received_at is not None:
                try:
                    data_hora = received_at.strftime("%d/%m/%Y %H:%M")
                except AttributeError:
                    data_hora = str(received_at)
            else:
                data_hora = ""
            # Extrair time_casa e time_fora do campo horario (formato "HH:MM casa x fora" nao disponivel no get_signal_history)
            row_data.append({
                "data_hora": data_hora,
                "liga": sig.get("liga", ""),
                "entrada": sig.get("entrada", ""),
                "time_casa": "",
                "time_fora": "",
                "resultado": sig.get("resultado", ""),
                "tentativa": sig.get("tentativa", ""),
                "placar": sig.get("placar", ""),
            })

    finally:
        conn.close()

    # 17. Return tuple com todos os 10 Outputs na ordem
    return (
        str(total),
        winrate,
        pl_text,
        pl_class,
        roi_text,
        roi_class,
        streak_green,
        streak_red,
        row_data,
        liga_options,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.getenv("DASH_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
