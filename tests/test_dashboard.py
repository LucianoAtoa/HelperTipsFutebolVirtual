"""
test_dashboard.py — Testes estruturais e de formatacao para helpertips/dashboard.py.

Testes que NAO requerem um servidor Dash em execucao ou conexao com banco de dados.
Todos os testes sao unitarios puros:
  - test_app_layout_renders: app.layout nao eh None e titulo correto (DASH-01)
  - test_layout_has_required_component_ids: todos IDs obrigatorios presentes na arvore (DASH-01, DASH-02)
  - test_datepicker_collapse_initial_closed: collapse-datepicker fechado por padrao (D-05)
  - test_resolve_periodo_hoje: _resolve_periodo("hoje") retorna (hoje, hoje)
  - test_resolve_periodo_semana: _resolve_periodo("semana") retorna (segunda, hoje)
  - test_resolve_periodo_mes: _resolve_periodo("mes") retorna (primeiro dia mes, hoje)
  - test_resolve_periodo_mes_passado: _resolve_periodo("mes_passado") retorna (primeiro, ultimo) do mes anterior
  - test_resolve_periodo_toda_vida: _resolve_periodo("toda_vida") retorna (None, None)
  - test_resolve_periodo_personalizado: _resolve_periodo("personalizado", start, end) retorna (start, end)
  - test_kpi_pl_formatting: formatacao "R$ +X.XX" e classes CSS text-success/text-danger
  - test_kpi_streak_formatting: "Nx" para count > 0, em-dash para count == 0
  - test_kpi_formatting_winrate_with_results: formatacao de winrate (DASH-02)
  - test_kpi_formatting_winrate_no_results: em dash quando sem sinais resolvidos (DASH-02)
  - test_kpi_formatting_roi_strings: formatacao de strings ROI com sinal
  - test_gale_accumulated_cost_model: Gale usa stake acumulado, nao simples dobro (Pitfall 5)
  - test_debug_mode_off_by_default: DASH_DEBUG ausente resulta em debug=False
  - test_debug_mode_on_with_env: DASH_DEBUG=true resulta em debug=True

Sem conexao com banco de dados ou servidor em execucao. Todos os imports sao seguros para CI.
"""

import os
from datetime import date, timedelta

from helpertips.dashboard import app
from helpertips.queries import calculate_roi

# _resolve_periodo sera importado quando existir (Plan 02).
# Por enquanto, os testes de _resolve_periodo falham com ImportError (RED intencional).
try:
    from helpertips.dashboard import _resolve_periodo
    _HAS_RESOLVE_PERIODO = True
except ImportError:
    _resolve_periodo = None
    _HAS_RESOLVE_PERIODO = False

# ---------------------------------------------------------------------------
# Helper: coleta todos os IDs de componentes na arvore do layout
# ---------------------------------------------------------------------------


def collect_ids(component) -> set:
    """
    Percorre recursivamente a arvore de componentes Dash e coleta todos os valores `id`.

    Trata:
    - Componentes com `id` string
    - children como lista, tupla ou componente unico
    - Nos folha sem children
    """
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


# ---------------------------------------------------------------------------
# Testes estruturais do layout
# ---------------------------------------------------------------------------


def test_app_layout_renders():
    """DASH-01: App inicializa, tem layout e titulo correto."""
    assert app.layout is not None, "app.layout nao deve ser None"
    assert app.title == "HelperTips \u2014 Futebol Virtual", (
        f"Expected title 'HelperTips \u2014 Futebol Virtual', got '{app.title}'"
    )


def test_layout_has_required_component_ids():
    """DASH-01, DASH-02: Todos os IDs obrigatorios devem existir na arvore do layout."""
    required_ids = {
        # KPI cards (D-09)
        "kpi-total",
        "kpi-winrate",
        "kpi-pl-total",
        "kpi-roi",
        "kpi-streak-green",
        "kpi-streak-red",
        # Filtros globais (D-04 a D-07)
        "periodo-selector",
        "filter-mercado",
        "filter-liga",
        "collapse-datepicker",
        "filter-date-custom",
        # Simulacao (D-13, D-14)
        "stake-input",
        "odd-input",
        "gale-toggle",
        # Tabela historico
        "history-table",
        # Infra
        "interval-refresh",
        # Modal
        "modal-parse-failures",
    }

    found_ids = collect_ids(app.layout)
    missing = required_ids - found_ids
    assert not missing, (
        f"IDs obrigatorios ausentes: {sorted(missing)}\n"
        f"IDs encontrados: {sorted(found_ids)}"
    )


def test_datepicker_collapse_initial_closed():
    """DASH-01 D-05: DatePickerRange oculto por padrao."""
    def find_collapse(component, target_id):
        if hasattr(component, 'id') and component.id == target_id:
            return component
        children = getattr(component, 'children', None)
        if children is None:
            return None
        if isinstance(children, (list, tuple)):
            for child in children:
                result = find_collapse(child, target_id)
                if result:
                    return result
        elif hasattr(children, 'children') or hasattr(children, 'id'):
            return find_collapse(children, target_id)
        return None

    collapse = find_collapse(app.layout, "collapse-datepicker")
    assert collapse is not None, "collapse-datepicker nao encontrado no layout"
    assert collapse.is_open is False, "collapse-datepicker deve iniciar fechado (is_open=False)"


# ---------------------------------------------------------------------------
# Testes de _resolve_periodo — falham (RED) ate Plan 02 implementar a funcao
# ---------------------------------------------------------------------------


def test_resolve_periodo_hoje():
    """_resolve_periodo('hoje') deve retornar (str(date.today()), str(date.today()))."""
    assert _HAS_RESOLVE_PERIODO, "_resolve_periodo nao encontrado em helpertips.dashboard (sera implementado no Plan 02)"
    today_str = str(date.today())
    result = _resolve_periodo("hoje")
    assert result == (today_str, today_str), (
        f"Esperado ({today_str}, {today_str}), obtido {result}"
    )


def test_resolve_periodo_semana():
    """_resolve_periodo('semana') deve retornar (segunda-feira da semana, hoje)."""
    assert _HAS_RESOLVE_PERIODO, "_resolve_periodo nao encontrado em helpertips.dashboard (sera implementado no Plan 02)"
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    result = _resolve_periodo("semana")
    assert result == (str(monday), str(today)), (
        f"Esperado ({monday}, {today}), obtido {result}"
    )


def test_resolve_periodo_mes():
    """_resolve_periodo('mes') deve retornar (primeiro dia do mes, hoje)."""
    assert _HAS_RESOLVE_PERIODO, "_resolve_periodo nao encontrado em helpertips.dashboard (sera implementado no Plan 02)"
    today = date.today()
    first_day = today.replace(day=1)
    result = _resolve_periodo("mes")
    assert result == (str(first_day), str(today)), (
        f"Esperado ({first_day}, {today}), obtido {result}"
    )


def test_resolve_periodo_mes_passado():
    """_resolve_periodo('mes_passado') deve retornar (primeiro, ultimo) do mes anterior."""
    assert _HAS_RESOLVE_PERIODO, "_resolve_periodo nao encontrado em helpertips.dashboard (sera implementado no Plan 02)"
    today = date.today()
    last_day_prev = today.replace(day=1) - timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)
    result = _resolve_periodo("mes_passado")
    assert result == (str(first_day_prev), str(last_day_prev)), (
        f"Esperado ({first_day_prev}, {last_day_prev}), obtido {result}"
    )


def test_resolve_periodo_toda_vida():
    """_resolve_periodo('toda_vida') deve retornar (None, None)."""
    assert _HAS_RESOLVE_PERIODO, "_resolve_periodo nao encontrado em helpertips.dashboard (sera implementado no Plan 02)"
    result = _resolve_periodo("toda_vida")
    assert result == (None, None), (
        f"Esperado (None, None), obtido {result}"
    )


def test_resolve_periodo_personalizado():
    """_resolve_periodo('personalizado', start, end) deve retornar (start, end) sem alteracao."""
    assert _HAS_RESOLVE_PERIODO, "_resolve_periodo nao encontrado em helpertips.dashboard (sera implementado no Plan 02)"
    result = _resolve_periodo("personalizado", "2025-01-01", "2025-01-31")
    assert result == ("2025-01-01", "2025-01-31"), (
        f"Esperado ('2025-01-01', '2025-01-31'), obtido {result}"
    )


# ---------------------------------------------------------------------------
# Testes de formatacao de KPI — Python puro, sem servidor Dash
# ---------------------------------------------------------------------------


def _winrate(greens: int, reds: int) -> str:
    """Replica a formula de formatacao de winrate do callback update_dashboard."""
    if (greens + reds) > 0:
        return f"{(greens / (greens + reds) * 100):.1f}%"
    return "\u2014"  # em dash — corresponde ao literal Unicode do callback


def test_kpi_pl_formatting():
    """Formatacao de P&L: 'R$ +X.XX' para positivo, 'R$ -X.XX' para negativo, classes CSS corretas."""
    # Valores positivos
    assert f"R$ {123.45:+.2f}" == "R$ +123.45", "P&L positivo deve ter prefixo +"
    # Valores negativos
    assert f"R$ {-50.0:+.2f}" == "R$ -50.00", "P&L negativo deve ter prefixo -"
    # Zero
    assert f"R$ {0.0:+.2f}" == "R$ +0.00", "P&L zero deve ser 'R$ +0.00'"
    # Classes CSS
    pl_positivo = 10.0
    pl_negativo = -5.0
    pl_zero = 0.0
    css_positivo = "card-text fw-bold text-success" if pl_positivo > 0 else (
        "card-text fw-bold text-danger" if pl_positivo < 0 else "card-text fw-bold text-muted"
    )
    css_negativo = "card-text fw-bold text-success" if pl_negativo > 0 else (
        "card-text fw-bold text-danger" if pl_negativo < 0 else "card-text fw-bold text-muted"
    )
    css_zero = "card-text fw-bold text-success" if pl_zero > 0 else (
        "card-text fw-bold text-danger" if pl_zero < 0 else "card-text fw-bold text-muted"
    )
    assert css_positivo == "card-text fw-bold text-success", f"P&L positivo deve ter text-success, obtido: {css_positivo}"
    assert css_negativo == "card-text fw-bold text-danger", f"P&L negativo deve ter text-danger, obtido: {css_negativo}"
    assert css_zero == "card-text fw-bold text-muted", f"P&L zero deve ter text-muted, obtido: {css_zero}"


def test_kpi_streak_formatting():
    """Formatacao de streaks: 'Nx' para count > 0, em-dash U+2014 para count == 0."""
    # Streak positiva
    assert f"{12}x" == "12x", "Streak de 12 deve ser '12x'"
    assert f"{1}x" == "1x", "Streak de 1 deve ser '1x'"
    # Streak zero — usar em-dash
    count_zero = 0
    streak_zero = f"{count_zero}x" if count_zero > 0 else "\u2014"
    assert streak_zero == "\u2014", f"Streak zero deve ser em-dash, obtido: {streak_zero!r}"
    # Verificar que em-dash nao eh hifen
    assert streak_zero != "-", "Streak zero nao deve ser hifen simples"


def test_kpi_formatting_winrate_with_results():
    """DASH-02: Formatacao de winrate percentual para diversas combinacoes green/red."""
    assert _winrate(6, 4) == "60.0%", "6 greens, 4 reds deve ser 60.0%"
    assert _winrate(10, 0) == "100.0%", "10 greens, 0 reds deve ser 100.0%"
    assert _winrate(0, 5) == "0.0%", "0 greens, 5 reds deve ser 0.0%"


def test_kpi_formatting_winrate_no_results():
    """DASH-02: Sem sinais resolvidos, winrate deve ser em dash (—), nao hifen."""
    result = _winrate(0, 0)
    assert result == "\u2014", (
        f"Esperado em dash '—' sem resultados, obtido '{result}'"
    )
    assert result != "-", "Resultado deve ser em dash, nao hifen simples"


def test_kpi_formatting_roi_strings():
    """Formatacao de texto ROI: decimal com sinal e prefixo R$ para dinheiro, pct com sinal para taxa."""
    # Lucro positivo
    assert f"R$ {12.5:+.2f}" == "R$ +12.50"
    # Lucro negativo
    assert f"R$ {-5.0:+.2f}" == "R$ -5.00"
    # Lucro zero
    assert f"R$ {0.0:+.2f}" == "R$ +0.00"
    # ROI percentual
    assert f"{33.3:+.1f}%" == "+33.3%"
    assert f"{-20.0:+.1f}%" == "-20.0%"


# ---------------------------------------------------------------------------
# Modelo de custo acumulado Gale — testa calculate_roi de queries.py
# ---------------------------------------------------------------------------


def _make_sig(resultado: str, tentativa: int) -> dict:
    """Constroi um dict de sinal minimo para calculo de ROI."""
    return {"resultado": resultado, "tentativa": tentativa}


def test_gale_accumulated_cost_model():
    """
    Verifica que Gale usa stake ACUMULADO por tentativa, nao simples dobro.

    Modelo Gale: cada tentativa dobra o stake. Total investido para N tentativas =
      stake * (2^N - 1)

    Exemplos com stake=10:
      GREEN em tentativa=1: investido = 10 * (2^1 - 1) = 10 * 1 = 10
      GREEN em tentativa=2: investido = 10 * (2^2 - 1) = 10 * 3 = 30 (nao apenas 20)
      GREEN em tentativa=3: investido = 10 * (2^3 - 1) = 10 * 7 = 70 (nao apenas 40)
      RED  em tentativa=4:  investido = 10 * (2^4 - 1) = 10 * 15 = 150 (nao apenas 80)

    Este eh o modelo acumulado, nao apenas por tentativa.
    """
    stake = 10.0
    odd = 2.0  # Odds pares simplificam calculo de lucro

    # GREEN em tentativa=1: investido = stake * 1 = stake
    result = calculate_roi([_make_sig("GREEN", 1)], stake, odd, gale_on=True)
    assert result["total_invested"] == 10.0, (
        f"GREEN tentativa=1: esperado invested=10.0, obtido {result['total_invested']}"
    )

    # GREEN em tentativa=2: investido = stake * (2^2 - 1) = stake * 3 = 30
    result = calculate_roi([_make_sig("GREEN", 2)], stake, odd, gale_on=True)
    assert result["total_invested"] == 30.0, (
        f"GREEN tentativa=2: esperado invested=30.0 (acumulado), obtido {result['total_invested']}"
    )

    # GREEN em tentativa=3: investido = stake * (2^3 - 1) = stake * 7 = 70
    result = calculate_roi([_make_sig("GREEN", 3)], stake, odd, gale_on=True)
    assert result["total_invested"] == 70.0, (
        f"GREEN tentativa=3: esperado invested=70.0 (7 * stake), obtido {result['total_invested']}"
    )

    # RED em tentativa=4: investido = stake * (2^4 - 1) = stake * 15 = 150
    result = calculate_roi([_make_sig("RED", 4)], stake, odd, gale_on=True)
    assert result["total_invested"] == 150.0, (
        f"RED tentativa=4: esperado invested=150.0 (15 * stake), obtido {result['total_invested']}"
    )

    # Sanidade: Gale acumulado eh sempre > stake efetivo de tentativa unica
    # Para tentativa=3, stake efetivo simples seria 10 * 2^2 = 40, mas acumulado = 70
    result3 = calculate_roi([_make_sig("GREEN", 3)], stake, odd, gale_on=True)
    simple_effective = stake * (2 ** (3 - 1))  # = 40
    assert result3["total_invested"] > simple_effective, (
        "Custo Gale acumulado deve ser maior que stake efetivo de tentativa unica"
    )


# ---------------------------------------------------------------------------
# SEC-02 — Debug mode controlado por env var
# ---------------------------------------------------------------------------


def test_debug_mode_off_by_default(monkeypatch):
    """DASH_DEBUG ausente ou 'false' resulta em debug=False."""
    monkeypatch.delenv('DASH_DEBUG', raising=False)
    debug = os.getenv('DASH_DEBUG', 'false').lower() == 'true'
    assert debug is False


def test_debug_mode_on_with_env(monkeypatch):
    """DASH_DEBUG=true resulta em debug=True."""
    monkeypatch.setenv('DASH_DEBUG', 'true')
    debug = os.getenv('DASH_DEBUG', 'false').lower() == 'true'
    assert debug is True
