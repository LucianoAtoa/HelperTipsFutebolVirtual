"""
dashboard.py — Shell minimo Dash Pages para HelperTips.

O conteudo do dashboard (layout, callbacks, helpers) esta em pages/home.py.
Este arquivo inicializa o app com use_pages=True e page_container.

Run as:
    python -m helpertips.dashboard
    DASH_DEBUG=true python -m helpertips.dashboard
"""

import os

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.DARKLY],
    title="HelperTips \u2014 Futebol Virtual",
)
server = app.server  # WSGI callable para gunicorn

app.layout = dbc.Container([
    dcc.Location(id="url-nav", refresh="callback-nav"),
    dbc.Nav(
        [
            dbc.NavLink("Dashboard", href="/", id="nav-link-home", active="exact"),
            dbc.NavLink("Configuracoes", href="/config", id="nav-link-config", active="exact"),
        ],
        id="nav-tabs",
        pills=True,
        className="my-3",
    ),
    dash.page_container,
], fluid=True)

if __name__ == "__main__":
    debug = os.getenv("DASH_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
