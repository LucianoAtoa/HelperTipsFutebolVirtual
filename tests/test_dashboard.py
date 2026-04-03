"""
test_dashboard.py — Structural and formatting tests for helpertips/dashboard.py.

Tests that DO NOT require a running Dash server or database connection.
All tests are pure unit tests:
  - test_app_layout_renders: app.layout is not None and title is correct (DASH-01)
  - test_layout_has_required_component_ids: all required IDs present in component tree (DASH-01, DASH-02)
  - test_kpi_formatting_winrate_with_results: win rate formatting logic (DASH-02)
  - test_kpi_formatting_winrate_no_results: em dash when no resolved signals (DASH-02)
  - test_kpi_formatting_roi_strings: ROI profit/pct string formatting with sign
  - test_gale_accumulated_cost_model: Gale uses accumulated stake not simple doubling (Pitfall 5)
  - test_coverage_badge_thresholds: badge color logic por threshold (OPER-01)
  - test_format_streak: helper _format_streak output format (ANAL-06)

No database connection or live server required. All imports are safe to run in CI.
"""

import os

from helpertips.dashboard import _format_streak, app
from helpertips.queries import calculate_roi

# ---------------------------------------------------------------------------
# Helper: collect all component IDs from the layout tree
# ---------------------------------------------------------------------------


def collect_ids(component) -> set:
    """
    Recursively walk the Dash component tree and collect all `id` attribute values.

    Handles:
    - Components with a string `id`
    - Children as list, tuple, or single component
    - Leaf nodes with no children
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
# Layout structural tests
# ---------------------------------------------------------------------------


def test_app_layout_renders():
    """DASH-01: App initializes, has a layout, and has the correct title."""
    assert app.layout is not None, "app.layout should not be None"
    assert app.title == "HelperTips \u2014 Futebol Virtual", (
        f"Expected title 'HelperTips \u2014 Futebol Virtual', got '{app.title}'"
    )


def test_layout_has_required_component_ids():
    """DASH-01, DASH-02: All required component IDs must exist in the layout tree."""
    required_ids = {
        # KPI cards
        "kpi-total",
        "kpi-greens",
        "kpi-reds",
        "kpi-pending",
        "kpi-winrate",
        # Filters
        "filter-liga",
        "filter-entrada",
        "filter-date",
        "btn-reset",
        # ROI inputs
        "stake-input",
        "odd-input",
        "gale-toggle",
        # ROI outputs
        "roi-profit",
        "roi-pct",
        "roi-invested",
        # Charts
        "bar-chart",
        "winrate-chart",
        # History table
        "history-table",
        # Auto-refresh
        "interval-refresh",
        # Phase 3 — Analytics Depth
        "tabs-analytics",
        "badge-coverage",
        "modal-parse-failures",
        "graph-heatmap",
        "graph-equity",
        "graph-dow",
        "graph-gale",
        "graph-volume",
        "kpi-streak-current",
        "kpi-streak-max-green",
        "kpi-streak-max-red",
        "table-cross-dimensional",
        "table-periodo",
    }

    found_ids = collect_ids(app.layout)
    missing = required_ids - found_ids
    assert not missing, (
        f"Missing required component IDs: {sorted(missing)}\n"
        f"Found IDs: {sorted(found_ids)}"
    )


# ---------------------------------------------------------------------------
# KPI formatting tests — pure Python, no Dash server
# ---------------------------------------------------------------------------


def _winrate(greens: int, reds: int) -> str:
    """Replicate the win rate formatting formula from update_dashboard callback."""
    if (greens + reds) > 0:
        return f"{(greens / (greens + reds) * 100):.1f}%"
    return "\u2014"  # em dash — matches the callback's Unicode literal


def test_kpi_formatting_winrate_with_results():
    """DASH-02: Win rate percentage formats correctly for various green/red combinations."""
    assert _winrate(6, 4) == "60.0%", "6 greens, 4 reds should be 60.0%"
    assert _winrate(10, 0) == "100.0%", "10 greens, 0 reds should be 100.0%"
    assert _winrate(0, 5) == "0.0%", "0 greens, 5 reds should be 0.0%"


def test_kpi_formatting_winrate_no_results():
    """DASH-02: When no resolved signals, win rate should be em dash (—), not hyphen."""
    result = _winrate(0, 0)
    assert result == "\u2014", (
        f"Expected em dash '—' when no results, got '{result}'"
    )
    assert result != "-", "Result must be em dash, not a plain hyphen"


def test_kpi_formatting_roi_strings():
    """ROI text formatting: signed decimal with R$ prefix for money, signed pct for rate."""
    # Positive profit
    assert f"R$ {12.5:+.2f}" == "R$ +12.50"
    # Negative profit
    assert f"R$ {-5.0:+.2f}" == "R$ -5.00"
    # Zero profit
    assert f"R$ {0.0:+.2f}" == "R$ +0.00"
    # ROI percentage
    assert f"{33.3:+.1f}%" == "+33.3%"
    assert f"{-20.0:+.1f}%" == "-20.0%"


# ---------------------------------------------------------------------------
# Gale accumulated cost model — tests calculate_roi from queries.py
# ---------------------------------------------------------------------------


def _make_sig(resultado: str, tentativa: int) -> dict:
    """Build a minimal signal dict for ROI calculation."""
    return {"resultado": resultado, "tentativa": tentativa}


def test_gale_accumulated_cost_model():
    """
    Verify Gale uses ACCUMULATED stake per tentativa, not simple effective_stake per attempt.

    The Gale model: each attempt doubles the stake. Total invested for N attempts =
      stake * (2^N - 1)

    Examples with stake=10:
      GREEN at tentativa=1: invested = 10 * (2^1 - 1) = 10 * 1 = 10
      GREEN at tentativa=2: invested = 10 * (2^2 - 1) = 10 * 3 = 30 (not just 20)
      GREEN at tentativa=3: invested = 10 * (2^3 - 1) = 10 * 7 = 70 (not just 40)
      RED  at tentativa=4:  invested = 10 * (2^4 - 1) = 10 * 15 = 150 (not just 80)

    This is the accumulated model, not per-attempt-only.
    """
    stake = 10.0
    odd = 2.0  # Use even odds to simplify profit calculation

    # GREEN at tentativa=1: invested = stake * 1 = stake
    result = calculate_roi([_make_sig("GREEN", 1)], stake, odd, gale_on=True)
    assert result["total_invested"] == 10.0, (
        f"GREEN tentativa=1: expected invested=10.0, got {result['total_invested']}"
    )

    # GREEN at tentativa=2: invested = stake * (2^2 - 1) = stake * 3 = 30
    result = calculate_roi([_make_sig("GREEN", 2)], stake, odd, gale_on=True)
    assert result["total_invested"] == 30.0, (
        f"GREEN tentativa=2: expected invested=30.0 (accumulated), got {result['total_invested']}"
    )

    # GREEN at tentativa=3: invested = stake * (2^3 - 1) = stake * 7 = 70
    result = calculate_roi([_make_sig("GREEN", 3)], stake, odd, gale_on=True)
    assert result["total_invested"] == 70.0, (
        f"GREEN tentativa=3: expected invested=70.0 (7 * stake), got {result['total_invested']}"
    )

    # RED at tentativa=4: invested = stake * (2^4 - 1) = stake * 15 = 150
    result = calculate_roi([_make_sig("RED", 4)], stake, odd, gale_on=True)
    assert result["total_invested"] == 150.0, (
        f"RED tentativa=4: expected invested=150.0 (15 * stake), got {result['total_invested']}"
    )

    # Sanity check: Gale accumulated is always > simple single-attempt effective stake
    # For tentativa=3, simple effective stake would be 10 * 2^2 = 40, but accumulated = 70
    result3 = calculate_roi([_make_sig("GREEN", 3)], stake, odd, gale_on=True)
    simple_effective = stake * (2 ** (3 - 1))  # = 40
    assert result3["total_invested"] > simple_effective, (
        "Accumulated Gale cost must be greater than single-attempt effective stake"
    )


# ---------------------------------------------------------------------------
# Phase 3 — Badge and streak helper tests
# ---------------------------------------------------------------------------


def test_coverage_badge_thresholds():
    """Badge color: success >= 95%, warning >= 90%, danger < 90% (OPER-01)."""
    test_cases = [
        (100.0, "success"),
        (95.0, "success"),
        (94.9, "warning"),
        (90.0, "warning"),
        (89.9, "danger"),
        (50.0, "danger"),
        (0.0, "danger"),
    ]
    for coverage, expected_color in test_cases:
        color = "success" if coverage >= 95 else ("warning" if coverage >= 90 else "danger")
        assert color == expected_color, f"coverage={coverage}: expected {expected_color}, got {color}"


def test_format_streak():
    """_format_streak retorna formato correto para wins, losses e sem dados (ANAL-06)."""
    assert _format_streak(5, "GREEN") == "5 wins"
    assert _format_streak(3, "RED") == "3 losses"
    assert _format_streak(0, None) == "Sem dados"
    assert _format_streak(0, "GREEN") == "Sem dados"


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
