"""
pages/config.py — Pagina de Configuracoes de Mercado (placeholder Phase 16).

Conteudo real sera implementado na Phase 17.
"""
import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, path="/config", name="Configuracoes")

layout = dbc.Container([
    html.H2("Configuracoes de Mercado", className="mt-4 mb-3"),
    dbc.Alert(
        "Pagina em construcao. Configuracoes editaveis serao adicionadas na proxima versao.",
        color="info",
    ),
], fluid=True)
