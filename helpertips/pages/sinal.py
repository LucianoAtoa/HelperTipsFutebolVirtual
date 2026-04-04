"""
pages/sinal.py — Pagina de detalhe individual do sinal.

Exibe breakdown completo de P&L: card da entrada principal,
tabela de complementares e totais consolidados.
Rota: /sinal?id=<n>
"""
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html, no_update  # noqa: F401

from helpertips.db import get_connection
from helpertips.queries import (
    calculate_pl_detalhado_por_sinal,
    get_complementares_config,
    get_mercado_config,
    get_sinal_detalhado,
)

dash.register_page(__name__, path="/sinal")

# Stake e gale defaults (mesmos valores padrao do home.py)
_DEFAULT_STAKE = 10.0
_DEFAULT_GALE_ON = True

layout = html.Div([
    dcc.Location(id="sinal-url", refresh=False),
    html.Div(id="sinal-content"),
])


# ---------------------------------------------------------------------------
# Helpers de layout
# ---------------------------------------------------------------------------


def _layout_not_found(signal_id):
    """Exibe mensagem amigavel para ID inexistente ou invalido (SIG-06)."""
    msg = (
        f"O sinal #{signal_id} nao existe ou foi removido."
        if signal_id
        else "ID de sinal invalido."
    )
    return dbc.Container([
        dbc.Row(dbc.Col([
            html.H4("Sinal nao encontrado", className="text-warning mt-4"),
            html.P(msg, className="text-muted"),
            dcc.Link(
                dbc.Button("Voltar ao Dashboard", color="primary", className="mt-3"),
                href="/",
            ),
        ], width={"size": 6, "offset": 3})),
    ])


def _build_detail_layout(sinal, pl):
    """Constroi layout completo da pagina de detalhe do sinal."""

    # 1. Header com botao Voltar (SIG-05)
    received_at = sinal.get("received_at")
    horario_str = (
        received_at.strftime("%d/%m/%Y %H:%M")
        if received_at is not None
        else "N/A"
    )
    header = dbc.Row(dbc.Col([
        dcc.Link(
            dbc.Button("<- Voltar", color="secondary", size="sm", className="mb-3"),
            href="/",
        ),
        html.H4(
            f"Sinal #{sinal['id']} — {sinal.get('entrada', '')}",
            className="text-light",
        ),
        html.P(
            f"Liga: {sinal.get('liga', 'N/A')} | "
            f"Horario: {horario_str} | "
            f"Tentativa: {sinal.get('tentativa', 1)}",
            className="text-muted",
        ),
    ]))

    # 2. Card da entrada principal (SIG-02)
    p = pl["principal"]
    resultado_color = "success" if p["resultado"] == "GREEN" else "danger"
    card_principal = dbc.Card(dbc.CardBody([
        html.H5("Entrada Principal", className="card-title"),
        dbc.Row([
            dbc.Col([
                html.Small("Mercado", className="text-muted"),
                html.P(sinal.get("entrada", "")),
            ]),
            dbc.Col([
                html.Small("Odd", className="text-muted"),
                html.P(f"{p['odd']:.2f}"),
            ]),
            dbc.Col([
                html.Small("Stake", className="text-muted"),
                html.P(f"R$ {p['investido']:.2f}"),
            ]),
            dbc.Col([
                html.Small("Resultado", className="text-muted"),
                html.P(p["resultado"], className=f"text-{resultado_color} fw-bold"),
            ]),
            dbc.Col([
                html.Small("Lucro/Prejuizo", className="text-muted"),
                html.P(
                    f"R$ {p['lucro']:+.2f}",
                    className=f"text-{resultado_color}",
                ),
            ]),
        ]),
    ]), className="mb-3")

    # 3. Tabela de complementares (SIG-03)
    comp_rows = []
    for c in pl["complementares"]:
        if c["resultado"] == "GREEN":
            cls = "text-success"
        elif c["resultado"] == "RED":
            cls = "text-danger"
        else:
            cls = "text-muted"
        comp_rows.append(html.Tr([
            html.Td(c["nome"]),
            html.Td(f"{c['odd']:.2f}"),
            html.Td(f"R$ {c['stake']:.2f}"),
            html.Td(c["resultado"], className=cls),
            html.Td(f"R$ {c['lucro']:+.2f}", className=cls),
        ]))

    tabela_comps = dbc.Card(dbc.CardBody([
        html.H5("Entradas Complementares", className="card-title"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Nome"),
                html.Th("Odd"),
                html.Th("Stake"),
                html.Th("Resultado"),
                html.Th("Lucro/Prejuizo"),
            ])),
            html.Tbody(comp_rows),
        ], bordered=True, hover=True, responsive=True, className="table-dark"),
    ]), className="mb-3")

    # 4. Totais consolidados (SIG-04)
    t = pl["totais"]
    lucro_cls = "text-success" if t["lucro"] >= 0 else "text-danger"
    totais_card = dbc.Card(dbc.CardBody([
        html.H5("Totais Consolidados", className="card-title"),
        dbc.Row([
            dbc.Col([
                html.Small("Investido Total", className="text-muted"),
                html.P(f"R$ {t['investido']:.2f}", className="fs-5"),
            ]),
            dbc.Col([
                html.Small("Retorno Total", className="text-muted"),
                html.P(f"R$ {t['retorno']:.2f}", className="fs-5"),
            ]),
            dbc.Col([
                html.Small("Lucro Liquido", className="text-muted"),
                html.P(
                    f"R$ {t['lucro']:+.2f}",
                    className=f"fs-5 fw-bold {lucro_cls}",
                ),
            ]),
        ]),
    ]), className="mb-3")

    return dbc.Container([header, card_principal, tabela_comps, totais_card], className="mt-3")


# ---------------------------------------------------------------------------
# Callback principal
# ---------------------------------------------------------------------------


@callback(
    Output("sinal-content", "children"),
    Input("sinal-url", "search"),
)
def render_sinal(search):
    """Renderiza o conteudo da pagina de detalhe do sinal."""
    params = parse_qs((search or "").lstrip("?"))
    try:
        signal_id = int(params.get("id", [None])[0])
    except (TypeError, ValueError):
        return _layout_not_found(None)

    conn = get_connection()
    try:
        sinal = get_sinal_detalhado(conn, signal_id)
        if sinal is None:
            return _layout_not_found(signal_id)

        mercado_slug = sinal.get("mercado_slug") or "over_2_5"
        comps_config = get_complementares_config(conn, mercado_slug)
        mercado_cfg = get_mercado_config(conn, mercado_slug)
        odd_principal = float(mercado_cfg["odd_ref"]) if mercado_cfg else 2.30
    finally:
        conn.close()

    pl = calculate_pl_detalhado_por_sinal(
        sinal, comps_config, _DEFAULT_STAKE, odd_principal, _DEFAULT_GALE_ON,
    )

    return _build_detail_layout(sinal, pl)
