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
                html.Small("Placar", className="text-muted"),
                html.P(sinal.get("placar") or "N/A", className="fw-bold"),
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

    # 3. Tabela de todas as entradas numeradas (principal + complementares)
    comps = pl["complementares"]

    def _resultado_style(resultado):
        if resultado == "GREEN":
            return "text-success fw-bold"
        elif resultado == "RED":
            return "text-danger fw-bold"
        return "text-muted"

    all_rows = []
    # Entrada 1 = Principal
    p_cls = _resultado_style(p["resultado"])
    all_rows.append(html.Tr([
        html.Td("1", className="text-center"),
        html.Td([sinal.get("entrada", ""), html.Small(" (Principal)", className="text-muted")]),
        html.Td(f"{p['odd']:.2f}"),
        html.Td(f"R$ {p['investido']:.2f}"),
        html.Td(p["resultado"], className=p_cls),
        html.Td(f"R$ {p['lucro']:+.2f}", className=p_cls),
    ]))

    # Entradas 2+ = Complementares
    for i, c in enumerate(comps, 2):
        c_cls = _resultado_style(c["resultado"])
        nome_parts = [c["nome"]]
        if c["resultado"] == "GREEN":
            nome_parts.append(html.Span(" ✓ GREEN", className="text-success fw-bold ms-1"))
        all_rows.append(html.Tr([
            html.Td(str(i), className="text-center"),
            html.Td(nome_parts),
            html.Td(f"{c['odd']:.2f}"),
            html.Td(f"R$ {c['investido']:.2f}"),
            html.Td(c["resultado"], className=c_cls),
            html.Td(f"R$ {c['lucro']:+.2f}", className=c_cls),
        ]))

    # Linha de total geral
    t = pl["totais"]
    t_cls = "text-success" if t["lucro"] >= 0 else "text-danger"
    all_rows.append(html.Tr([
        html.Td("", colSpan=3, className="fw-bold"),
        html.Td(f"R$ {t['investido']:.2f}", className="fw-bold"),
        html.Td("TOTAL", className="fw-bold"),
        html.Td(f"R$ {t['lucro']:+.2f}", className=f"fw-bold fs-5 {t_cls}"),
    ], className="table-secondary"))

    tabela_entradas = dbc.Card(dbc.CardBody([
        html.H5("Detalhamento por Entrada", className="card-title"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("#", style={"width": "50px"}),
                html.Th("Entrada"),
                html.Th("Odd"),
                html.Th("Apostado"),
                html.Th("Resultado"),
                html.Th("Lucro/Prejuizo"),
            ])),
            html.Tbody(all_rows),
        ], bordered=True, hover=True, responsive=True, className="table-dark"),
    ]), className="mb-3")

    # 4. Resumo por tipo (Principal vs Complementares vs Total)
    total_inv_comp = sum(c["investido"] for c in comps)
    total_ret_comp = sum(c["retorno"] for c in comps)
    total_lucro_comp = sum(c["lucro"] for c in comps)
    lucro_p_cls = "text-success" if p["lucro"] >= 0 else "text-danger"
    lucro_c_cls = "text-success" if total_lucro_comp >= 0 else "text-danger"
    lucro_t_cls = "text-success" if t["lucro"] >= 0 else "text-danger"

    resumo_rows = [
        html.Tr([
            html.Td("Principal", className="fw-bold"),
            html.Td(f"R$ {p['investido']:.2f}"),
            html.Td(f"R$ {p['retorno']:.2f}"),
            html.Td(f"R$ {p['lucro']:+.2f}", className=lucro_p_cls),
        ]),
        html.Tr([
            html.Td("Complementares", className="fw-bold"),
            html.Td(f"R$ {total_inv_comp:.2f}"),
            html.Td(f"R$ {total_ret_comp:.2f}"),
            html.Td(f"R$ {total_lucro_comp:+.2f}", className=lucro_c_cls),
        ]),
        html.Tr([
            html.Td("TOTAL", className="fw-bold"),
            html.Td(f"R$ {t['investido']:.2f}", className="fw-bold"),
            html.Td(f"R$ {t['retorno']:.2f}", className="fw-bold"),
            html.Td(f"R$ {t['lucro']:+.2f}", className=f"fw-bold fs-5 {lucro_t_cls}"),
        ], className="table-secondary"),
    ]

    resumo_card = dbc.Card(dbc.CardBody([
        html.H5("Resumo por Tipo de Entrada", className="card-title"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Tipo"),
                html.Th("Investido"),
                html.Th("Retorno"),
                html.Th("Lucro/Prejuizo"),
            ])),
            html.Tbody(resumo_rows),
        ], bordered=True, responsive=True, className="table-dark"),
    ]), className="mb-3")

    return dbc.Container([header, card_principal, tabela_entradas, resumo_card], className="mt-3")


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
