"""
test_sinal_page.py — Testes estruturais da pagina de detalhe do sinal.

Testes que NAO requerem servidor Dash ou conexao com banco de dados:
  - test_sinal_page_registered: pagina registrada com path="/sinal"
  - test_sinal_page_has_location_and_content: layout contem sinal-url e sinal-content
  - test_render_sinal_invalid_id: search="?id=abc" retorna mensagem "invalido"
  - test_render_sinal_missing_id: search="" retorna mensagem "invalido"
"""

import dash


def test_sinal_page_registered():
    """SIG-02: pages/sinal.py deve estar registrado com path='/sinal'."""
    import helpertips.pages.sinal  # noqa: F401 — side effect: registra pagina

    registry = dash.page_registry
    sinal_entries = [v for v in registry.values() if v.get("path") == "/sinal"]
    assert len(sinal_entries) >= 1, (
        f"Esperado pelo menos 1 pagina com path='/sinal', encontrado {len(sinal_entries)}. "
        f"Registry: {list(registry.keys())}"
    )


def test_sinal_page_has_location_and_content():
    """Layout da pagina deve conter dcc.Location(id='sinal-url') e html.Div(id='sinal-content')."""
    from helpertips.pages.sinal import layout

    def collect_ids(component) -> set:
        ids: set = set()
        if hasattr(component, "id") and component.id:
            ids.add(component.id)
        children = getattr(component, "children", None)
        if children is None:
            return ids
        if isinstance(children, (list, tuple)):
            for child in children:
                if hasattr(child, "children") or hasattr(child, "id"):
                    ids.update(collect_ids(child))
        elif hasattr(children, "children") or hasattr(children, "id"):
            ids.update(collect_ids(children))
        return ids

    ids = collect_ids(layout)
    assert "sinal-url" in ids, f"sinal-url nao encontrado no layout. IDs: {sorted(ids)}"
    assert "sinal-content" in ids, f"sinal-content nao encontrado no layout. IDs: {sorted(ids)}"


def test_render_sinal_invalid_id():
    """render_sinal com search='?id=abc' deve retornar layout com 'invalido' sem excecao."""
    from helpertips.pages.sinal import render_sinal

    result = render_sinal("?id=abc")

    # Verificar que retornou algo (nao None, nao excecao)
    assert result is not None, "render_sinal nao deve retornar None para ID invalido"

    # Verificar que o conteudo menciona 'invalido'
    result_str = str(result)
    assert "invalido" in result_str.lower(), (
        f"Esperado 'invalido' no resultado para ID invalido, obtido: {result_str[:200]}"
    )


def test_render_sinal_missing_id():
    """render_sinal com search='' deve retornar layout com 'invalido' sem excecao."""
    from helpertips.pages.sinal import render_sinal

    result = render_sinal("")

    assert result is not None, "render_sinal nao deve retornar None para search vazio"

    result_str = str(result)
    assert "invalido" in result_str.lower(), (
        f"Esperado 'invalido' no resultado para search vazio, obtido: {result_str[:200]}"
    )
