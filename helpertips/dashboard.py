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
from collections import defaultdict
from datetime import date, timedelta

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.graph_objects as go  # noqa: F401 — disponivel para fases futuras
from dash import Input, Output, State, callback, ctx, dash_table, dcc, html, no_update

from helpertips.db import get_connection
from helpertips.queries import (
    calculate_pl_por_entrada,
    calculate_roi,
    calculate_roi_complementares,
    calculate_streaks,
    get_complementares_config,
    get_distinct_values,
    get_filtered_stats,
    get_mercado_config,
    get_parse_failures_detail,
    get_signal_history,
    get_signals_com_placar,
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


def _calcular_stakes_gale(stake_base: float, percentual: float) -> tuple[float, float, float, float]:
    """Retorna (T1, T2, T3, T4) para um complementar dado stake base e percentual.

    T1 = stake_base * percentual
    T2 = T1 * 2  (gale nivel 2)
    T3 = T1 * 4  (gale nivel 3)
    T4 = T1 * 8  (gale nivel 4)
    """
    t1 = stake_base * percentual
    return t1, t1 * 2, t1 * 4, t1 * 8


def _agregar_por_entrada(pl_lista: list[dict]) -> list[dict]:
    """Agrega P&L por entrada (visao geral — mercado 'Todos').

    Recebe lista de dicts no formato de calculate_pl_por_entrada e retorna
    uma lista de dicts agrupados por campo 'entrada', com totais de greens,
    reds, investido, retorno, lucro, taxa_green, taxa_red e roi.
    """
    if not pl_lista:
        return []
    grupos: dict[str, dict] = defaultdict(lambda: {
        "greens": 0, "reds": 0,
        "investido": 0.0, "retorno": 0.0, "lucro": 0.0,
    })
    for row in pl_lista:
        g = grupos[row.get("entrada") or "?"]
        g["greens"] += 1 if row.get("resultado") == "GREEN" else 0
        g["reds"] += 1 if row.get("resultado") == "RED" else 0
        g["investido"] += row.get("investido_total", 0.0)
        g["retorno"] += row.get("retorno_principal", 0.0) + row.get("retorno_comp", 0.0)
        g["lucro"] += row.get("lucro_total", 0.0)
    result = []
    for entrada_nome, g in grupos.items():
        total = g["greens"] + g["reds"]
        taxa = g["greens"] / total * 100 if total > 0 else 0
        roi = g["lucro"] / g["investido"] * 100 if g["investido"] > 0 else 0
        result.append({
            "entrada": entrada_nome,
            "greens": g["greens"],
            "reds": g["reds"],
            "total": total,
            "investido": round(g["investido"], 2),
            "retorno": round(g["retorno"], 2),
            "lucro": round(g["lucro"], 2),
            "taxa_green": round(taxa, 1),
            "taxa_red": round(100 - taxa, 1) if total > 0 else 0,
            "roi": round(roi, 1),
        })
    return result


# Conjuntos de colunas para toggle de visualizacao de performance (D-05)
COLUNAS_SEMPRE = ["entrada"]
COLUNAS_PCT = COLUNAS_SEMPRE + ["taxa_green", "taxa_red", "roi"]
COLUNAS_QTY = COLUNAS_SEMPRE + ["greens", "reds", "total"]
COLUNAS_PL = COLUNAS_SEMPRE + ["investido", "retorno", "lucro", "roi"]


def _get_colunas_visiveis(modo: str) -> list[str]:
    """Retorna lista de colunas visiveis para o modo do toggle de performance.

    Modos:
      'pct' — Percentual: taxa green (%), taxa red (%), ROI (%)
      'qty' — Quantidade: greens (n), reds (n), total (n)
      'pl'  — P&L (R$): investido, retorno, lucro, ROI
    """
    mapa = {"pct": COLUNAS_PCT, "qty": COLUNAS_QTY, "pl": COLUNAS_PL}
    return mapa.get(modo, COLUNAS_PCT)


MERCADOS_CONFIG = [
    ("over_2_5", "Over 2.5"),
    ("ambas_marcam", "Ambas Marcam"),
]


def _build_config_card_mercado(nome: str, odd_ref: float, stake: float, comps: list[dict]) -> dbc.Card:
    """Constroi card read-only de config de um mercado com tabela de complementares e stakes T1-T4."""
    header_text = f"Odd ref: {odd_ref:.2f} | Stake base: R$ {stake:.2f} | Progressao: 1x 2x 4x 8x"
    rows = []
    for comp in comps:
        pct = float(comp["percentual"])
        t1, t2, t3, t4 = _calcular_stakes_gale(stake, pct)
        rows.append(html.Tr([
            html.Td(comp["nome_display"]),
            html.Td(f"{pct * 100:.0f}%"),
            html.Td(f"{float(comp['odd_ref']):.2f}"),
            html.Td(f"R$ {t1:.2f}"),
            html.Td(f"R$ {t2:.2f}"),
            html.Td(f"R$ {t3:.2f}"),
            html.Td(f"R$ {t4:.2f}"),
        ]))
    thead = html.Thead(html.Tr([
        html.Th("Complementar"), html.Th("%"), html.Th("Odd Ref"),
        html.Th("T1"), html.Th("T2"), html.Th("T3"), html.Th("T4"),
    ]))
    return dbc.Card([
        dbc.CardHeader(html.H6(nome, className="mb-0")),
        dbc.CardBody([
            html.P(header_text, className="text-muted small"),
            dbc.Table([thead, html.Tbody(rows)], bordered=True, color="dark", hover=True, size="sm"),
        ]),
    ], className="mb-3")


def _build_config_mercados_section(conn, stake: float) -> list:
    """Retorna lista de dbc.Card para cada mercado ativo (per D-01)."""
    cards = [html.H5("Configuracao dos Mercados", className="text-muted mb-3")]
    for slug, nome in MERCADOS_CONFIG:
        config = get_mercado_config(conn, slug)
        if config is None:
            continue
        comps = get_complementares_config(conn, slug)
        cards.append(_build_config_card_mercado(
            nome, float(config["odd_ref"]), stake, comps
        ))
    return cards


def _build_performance_section(
    conn, history: list, entrada: str | None, stake: float, odd: float,
    gale_on: bool, toggle_mode: str,
) -> "dash_table.DataTable | html.P":
    """Constroi DataTable de performance com colunas condicionais por toggle_mode."""
    if not history:
        return html.P("Sem dados para o periodo selecionado.", className="text-muted")

    if entrada:
        # Visao por mercado (D-06): principal + cada complementar como linha separada
        slug = _entrada_para_slug(entrada)
        if slug:
            comp_config = get_complementares_config(conn, slug)
            roi_princ = calculate_roi(history, stake, odd, gale_on)
            roi_comp = calculate_roi_complementares(history, comp_config, stake, gale_on)

            rows = []
            # Linha do principal
            p_total = roi_princ["greens"] + roi_princ["reds"]
            p_taxa = roi_princ["greens"] / p_total * 100 if p_total > 0 else 0
            p_roi = roi_princ["profit"] / roi_princ["total_invested"] * 100 if roi_princ["total_invested"] > 0 else 0
            rows.append({
                "entrada": f"{entrada} (Principal)",
                "greens": roi_princ["greens"],
                "reds": roi_princ["reds"],
                "total": p_total,
                "investido": round(roi_princ["total_invested"], 2),
                "retorno": round(roi_princ["total_invested"] + roi_princ["profit"], 2),
                "lucro": round(roi_princ["profit"], 2),
                "taxa_green": round(p_taxa, 1),
                "taxa_red": round(100 - p_taxa, 1) if p_total > 0 else 0,
                "roi": round(p_roi, 1),
            })
            # Linhas por complementar
            for pm in roi_comp.get("por_mercado", []):
                c_total = pm["greens"] + pm["reds"]
                c_taxa = pm["greens"] / c_total * 100 if c_total > 0 else 0
                c_roi = pm["lucro"] / pm["investido"] * 100 if pm["investido"] > 0 else 0
                rows.append({
                    "entrada": pm["nome_display"],
                    "greens": pm["greens"],
                    "reds": pm["reds"],
                    "total": c_total,
                    "investido": round(pm["investido"], 2),
                    "retorno": round(pm["investido"] + pm["lucro"], 2),
                    "lucro": round(pm["lucro"], 2),
                    "taxa_green": round(c_taxa, 1),
                    "taxa_red": round(100 - c_taxa, 1) if c_total > 0 else 0,
                    "roi": round(c_roi, 1),
                })
        else:
            rows = []
    else:
        # Visao geral (D-06): agrupado por entrada
        signals_placar = get_signals_com_placar(conn, entrada=entrada)
        # Obter configs de complementares e odds para todos os mercados
        comps_por_mercado = {}
        odds_por_mercado = {}
        for slug, nome in MERCADOS_CONFIG:
            cfg = get_mercado_config(conn, slug)
            if cfg:
                odds_por_mercado[slug] = float(cfg["odd_ref"])
                comps_por_mercado[slug] = get_complementares_config(conn, slug)
        pl_lista = calculate_pl_por_entrada(signals_placar, comps_por_mercado, stake, odds_por_mercado, gale_on)
        rows = _agregar_por_entrada(pl_lista)

    if not rows:
        return html.P("Sem dados para o periodo selecionado.", className="text-muted")

    # Mapas de nomes de colunas para headers legiveis
    col_headers = {
        "entrada": "Entrada",
        "greens": "Greens",
        "reds": "Reds",
        "total": "Total",
        "taxa_green": "Taxa Green (%)",
        "taxa_red": "Taxa Red (%)",
        "investido": "Investido (R$)",
        "retorno": "Retorno (R$)",
        "lucro": "P&L (R$)",
        "roi": "ROI (%)",
    }
    colunas_visiveis = _get_colunas_visiveis(toggle_mode)
    columns = [{"name": col_headers.get(c, c), "id": c} for c in colunas_visiveis]

    # Formatar valores monetarios nas rows para display
    for row in rows:
        for key in ("investido", "retorno", "lucro"):
            if key in row:
                row[key] = round(row[key], 2)

    return dash_table.DataTable(
        data=rows,
        columns=columns,
        style_header={"backgroundColor": "#303030", "color": "white", "fontWeight": "bold"},
        style_cell={"backgroundColor": "#222", "color": "white", "border": "1px solid #444", "textAlign": "center"},
        style_data_conditional=[
            {"if": {"filter_query": "{lucro} > 0", "column_id": "lucro"}, "color": "#28a745", "fontWeight": "bold"},
            {"if": {"filter_query": "{lucro} < 0", "column_id": "lucro"}, "color": "#dc3545", "fontWeight": "bold"},
            {"if": {"filter_query": "{roi} > 0", "column_id": "roi"}, "color": "#28a745"},
            {"if": {"filter_query": "{roi} < 0", "column_id": "roi"}, "color": "#dc3545"},
        ],
        page_size=20,
        style_table={"overflowX": "auto"},
    )


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

    # Secoes Phase 12: Config Mercados + Performance (D-08)
    html.Div(id="config-mercados-container", className="mb-3"),

    # Toggle de visualizacao + Tabela de Performance (D-04)
    dbc.Card(dbc.CardBody([
        html.H6("Performance das Entradas", className="card-title text-muted"),
        dbc.RadioItems(
            id="perf-toggle-view",
            options=[
                {"label": "Percentual", "value": "pct"},
                {"label": "Quantidade", "value": "qty"},
                {"label": "P&L (R$)", "value": "pl"},
            ],
            value="pct",
            inline=True,
            input_class_name="btn-check",
            label_class_name="btn btn-outline-secondary btn-sm",
            label_checked_class_name="active",
            className="mb-3",
        ),
        html.Div(id="perf-table"),
    ]), className="mb-3"),

    # Placeholder para Phase 13 (D-08)
    html.Div(id="phase13-placeholder"),

    # AG Grid historico (D-09 — movido para apos as novas secoes)
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
    Output("kpi-total",                   "children"),
    Output("kpi-winrate",                 "children"),
    Output("kpi-pl-total",                "children"),
    Output("kpi-pl-total",                "className"),
    Output("kpi-roi",                     "children"),
    Output("kpi-roi",                     "className"),
    Output("kpi-streak-green",            "children"),
    Output("kpi-streak-red",              "children"),
    Output("history-table",               "rowData"),
    Output("filter-liga",                 "options"),
    Output("config-mercados-container",   "children"),  # DASH-03
    Output("perf-table",                  "children"),  # DASH-04
    Input("periodo-selector",             "value"),
    Input("filter-date-custom",           "start_date"),
    Input("filter-date-custom",           "end_date"),
    Input("filter-mercado",               "value"),
    Input("filter-liga",                  "value"),
    Input("stake-input",                  "value"),
    Input("odd-input",                    "value"),
    Input("gale-toggle",                  "value"),
    Input("perf-toggle-view",             "value"),
    Input("interval-refresh",             "n_intervals"),
)
def update_dashboard(periodo, custom_start, custom_end, mercado, liga, stake, odd, gale_on, perf_toggle, _n):
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

        # 17. Config Mercados (DASH-03)
        config_section = _build_config_mercados_section(conn, stake)

        # 18. Performance (DASH-04)
        perf_section = _build_performance_section(
            conn, history, entrada, stake, odd, gale_on, perf_toggle or "pct"
        )

    finally:
        conn.close()

    # 19. Return tuple com todos os 12 Outputs na ordem
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
        config_section,   # NOVO
        perf_section,     # NOVO
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.getenv("DASH_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
