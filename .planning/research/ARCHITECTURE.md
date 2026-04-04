# Architecture Research

**Domain:** Dash multi-page integration — signal detail page in existing single-page app
**Researched:** 2026-04-04
**Confidence:** HIGH (Dash Pages documented in official Plotly docs, AG Grid cellClicked documented, patterns verified against existing codebase)

---

## Context: What We Are Integrating

Milestone v1.3 adds a dedicated signal detail page to an existing single-file Dash app (`helpertips/dashboard.py`, ~970 lines). The detail page must:

- Display one signal's full P&L breakdown (principal + each complementar)
- Be reachable by clicking a row in the existing AG Grid history table
- Accept the signal's database `id` via the URL
- Be extensible for future detail expansions

The existing app has no URL routing. All interactivity is driven by one callback master. The challenge is introducing a second "page" without rewriting the existing architecture.

---

## Existing Architecture (Before Milestone v1.3)

```
helpertips/
├── dashboard.py          ← single file, ~970 LOC
│   ├── app = dash.Dash(...)                    ← no use_pages, no dcc.Location
│   ├── server = app.server                     ← gunicorn WSGI entry point
│   ├── app.layout = dbc.Container([...])       ← all layout defined inline
│   ├── @callback toggle_datepicker(...)        ← minor callback
│   └── @callback update_dashboard(...)         ← callback master (10 inputs, 13 outputs)
├── queries.py            ← all SQL + pure-Python P&L calculations
│   ├── get_signal_history(conn, ...)           ← returns list[dict] with signal id
│   ├── get_signals_com_placar(conn, ...)       ← returns id, resultado, placar, mercado_slug
│   └── calculate_pl_por_entrada(signals, ...) ← per-signal P&L, keyed by position/id
└── db.py                 ← get_connection()
```

### What the AG Grid Row Contains Today

`history-table` `rowData` dicts have these keys:
- `data_hora`, `liga`, `entrada`, `resultado`, `tentativa`, `placar`, `lucro`
- The signal database `id` is **NOT** currently included in `rowData`

This is the first integration point: `id` must be added to `rowData` so it can be read from `cellClicked`.

---

## Recommended Architecture: Dash Pages with pages/ Folder

### Why Dash Pages, Not Manual dcc.Location

Two valid approaches exist:

| Approach | How | Pros | Cons |
|---|---|---|---|
| **Dash Pages (recommended)** | `use_pages=True` + `pages/` folder + `dash.page_container` | Official pattern, automatic URL routing, each page is isolated, callbacks scoped per file | Requires restructuring `app.layout` to include `page_container` |
| Manual `dcc.Location` | One layout with `dcc.Location`, callback reads `pathname` and renders page | No file changes to page discovery | More boilerplate, all callbacks in one file, harder to extend |

**Decision: Dash Pages.** The feature has been available since Dash 2.5.0 (June 2022) and is the documented standard for multi-page Dash apps as of Dash 4.x. The `pages/` folder structure isolates the new detail page from `dashboard.py`, keeping the callback master untouched. Dash Pages handles URL routing automatically — no need to write a `pathname` → layout dispatch callback.

### Target File Structure

```
helpertips/
├── dashboard.py           ← modified (use_pages, page_container, dcc.Location nav)
├── pages/
│   ├── home.py            ← NEW: wraps existing main layout, registered as path='/'
│   └── sinal.py           ← NEW: signal detail page, registered as path='/sinal'
├── queries.py             ← modified (add get_signal_by_id query)
└── db.py                  ← unchanged
```

### dashboard.py Changes (Modified File)

Three changes only:

1. Add `use_pages=True` to `dash.Dash(...)` constructor.
2. Replace `app.layout = dbc.Container([... everything ...])` with a shell layout containing `dash.page_container` and a `dcc.Location` for programmatic navigation.
3. Move the existing full layout into `pages/home.py`.

```python
# dashboard.py — after changes

app = dash.Dash(
    __name__,
    use_pages=True,                          # ← ADD THIS
    external_stylesheets=[dbc.themes.DARKLY],
    title="HelperTips — Futebol Virtual",
)
server = app.server  # unchanged

app.layout = dbc.Container([
    dcc.Location(id="url-nav", refresh="callback-nav"),  # ← navigation trigger
    dash.page_container,                                  # ← renders active page
], fluid=True)
```

### pages/home.py (New File — Wraps Existing Layout)

```python
# pages/home.py

import dash
from dash import dcc, html, callback, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

from helpertips.queries import (...)  # same imports as today's dashboard.py
from helpertips.db import get_connection
from helpertips.store import ENTRADA_PARA_MERCADO_ID

dash.register_page(__name__, path="/")

# All helper functions moved here: _entrada_para_slug, _agregar_por_entrada,
# _build_config_card_mercado, _build_config_mercados_section,
# _build_performance_section, _build_phase13_section, make_kpi_card,
# _resolve_periodo, MERCADOS_CONFIG, COLUNAS_*, _get_colunas_visiveis

layout = dbc.Container([
    # ← exact same content as today's app.layout, MINUS the outer dbc.Container
    # AG Grid gets one new column: "id" (hidden), for cellClicked navigation
])

# Navigation callback: AG Grid row click → navigate to /sinal?id=<signal_id>
@callback(
    Output("url-nav", "href"),
    Input("history-table", "cellClicked"),
    prevent_initial_call=True,
)
def navigate_to_signal(cell_clicked):
    if cell_clicked is None:
        return no_update
    row_data = cell_clicked.get("rowData", {})
    signal_id = row_data.get("id")
    if signal_id is None:
        return no_update
    return f"/sinal?id={signal_id}"

# All existing callbacks stay here:
# toggle_datepicker, update_dashboard (callback master)
```

### pages/sinal.py (New File — Signal Detail Page)

```python
# pages/sinal.py

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

from helpertips.db import get_connection
from helpertips.queries import get_signal_by_id, get_signals_com_placar, ...

dash.register_page(__name__, path="/sinal")

def layout(id=None):
    """Layout function receives URL query params as kwargs."""
    return dbc.Container([
        dcc.Store(id="signal-id-store", data=id),
        html.Div(id="sinal-detail-container"),
        dbc.Button("← Voltar", href="/", external_link=False, color="secondary"),
    ], fluid=True)

@callback(
    Output("sinal-detail-container", "children"),
    Input("signal-id-store", "data"),
)
def render_signal_detail(signal_id):
    if signal_id is None:
        return html.P("Sinal não encontrado.")
    conn = get_connection()
    try:
        signal = get_signal_by_id(conn, int(signal_id))
        if signal is None:
            return html.P(f"Sinal #{signal_id} não encontrado no banco.")
        # Build detail cards using calculate_pl_por_entrada
        ...
    finally:
        conn.close()
```

---

## Data Flow: Navigating to Signal Detail

```
User clicks row in AG Grid (history-table)
    │
    ▼
cellClicked fires → navigate_to_signal callback (in pages/home.py)
    │
    ▼ Output("url-nav", "href") = "/sinal?id=42"
    │
    ▼ dcc.Location(refresh="callback-nav") performs client-side navigation
    │
    ▼ Dash Pages routes to pages/sinal.py
    │
    ▼ layout(id="42") called — creates dcc.Store with signal id
    │
    ▼ render_signal_detail("42") callback fires
    │
    ▼ queries.get_signal_by_id(conn, 42) → signal row
    │
    ▼ calculate_pl_por_entrada([signal], ...) → P&L breakdown
    │
    ▼ Renders dbc.Cards with principal + each complementar
```

### Key Data Available Per Signal

`get_signals_com_placar` returns per signal:
- `id`, `resultado`, `placar`, `tentativa`, `mercado_id`, `mercado_slug`, `entrada`, `liga`, `received_at`

`calculate_pl_por_entrada` returns per signal:
- `mercado_slug`, `resultado`, `tentativa`, `placar`, `liga`, `entrada`
- `investido_principal`, `retorno_principal`, `lucro_principal`
- `investido_comp`, `retorno_comp`, `lucro_comp`
- `investido_total`, `lucro_total`

For the detail page, `calculate_pl_por_entrada` must be called with `[single_signal]` to get the breakdown. The complementar validation (via `validar_complementar`) already runs per-complementar inside that function, so individual complementar results are available without a new function.

**Gap:** `calculate_pl_por_entrada` returns aggregate `investido_comp`/`lucro_comp` totals, not a row per complementar. The detail page needs per-complementar rows. Two options:

1. **Preferred:** Add a new function `calculate_pl_detalhado_por_sinal(signal, comp_config, stake, odd, gale_on) -> dict` in `queries.py` that returns the same loop output but with a list of per-complementar dicts instead of rolled-up totals.
2. **Alternative:** Inline the loop in `sinal.py`'s callback (acceptable for first phase, less clean).

---

## Component Boundaries

| Component | Responsibility | New or Modified |
|-----------|---------------|-----------------|
| `dashboard.py` | App init (`use_pages=True`), shell layout with `page_container` and `dcc.Location` | **Modified** (minimal changes) |
| `pages/home.py` | Full existing dashboard layout + all existing callbacks + navigation callback | **New** (receives content from `dashboard.py`) |
| `pages/sinal.py` | Signal detail layout function + render callback | **New** |
| `queries.py` | `get_signal_by_id(conn, id)` — single signal fetch; optionally `calculate_pl_detalhado_por_sinal` | **Modified** (2 new functions) |
| `db.py` | Unchanged | Unchanged |
| `store.py` | Unchanged | Unchanged |

---

## AG Grid rowData Change

Today `rowData` omits the signal `id`. The navigation callback requires it.

**Change in `update_dashboard` callback (callback master, step 16b):**

```python
# Before:
row_data.append({
    "data_hora": data_hora,
    "liga": sig.get("liga", ""),
    ...
})

# After:
row_data.append({
    "id": sig.get("id"),      # ← ADD THIS (used by navigation callback)
    "data_hora": data_hora,
    "liga": sig.get("liga", ""),
    ...
})
```

The AG Grid column def for `id` should be hidden so the user does not see it:

```python
{"field": "id", "hide": True},
```

The `cellClicked` event object exposes `rowData` (the full row dict) in addition to the clicked cell's `value`. This means clicking any column in the row gives access to `id` from `rowData`.

---

## URL Design

| URL | Content |
|-----|---------|
| `/` | Main dashboard (home.py) |
| `/sinal?id=42` | Signal detail page for signal with id=42 |

Using query params (`?id=42`) instead of path params (`/sinal/42`) is simpler to implement with Dash Pages. The `layout()` function in `sinal.py` receives query params as keyword arguments automatically when defined as `def layout(id=None)`.

**Confidence:** HIGH — this is the documented Dash Pages pattern for passing data via URL.

---

## Architectural Patterns

### Pattern 1: Dash Pages with `pages/` Folder

**What:** Each page is a Python file in `pages/`. Dash auto-discovers them and handles URL routing via `dash.page_container`.
**When to use:** When a Dash app needs more than one URL-addressable view.
**Trade-offs:** Small refactor required (moving layout to `pages/home.py`). No JavaScript needed. Each page's callbacks are isolated in its own file — no pollution of the callback master.

### Pattern 2: `dcc.Location(refresh="callback-nav")` for Programmatic Navigation

**What:** A `dcc.Location` component in the shell layout serves as the navigation target. Callbacks write to its `href` property. `refresh="callback-nav"` performs client-side navigation without a full page reload.
**When to use:** When navigation is triggered by user interaction in a callback (e.g., AG Grid row click), not by a static `dcc.Link`.
**Trade-offs:** Requires the `dcc.Location` to be in the top-level (shell) layout, not inside a page — because page layouts are replaced on navigation. The shell layout persists across navigation.

### Pattern 3: Layout Function with Query Params

**What:** Define `def layout(id=None)` instead of `layout = html.Div(...)` in the page file. Dash Pages calls the function on each request, passing URL query parameters as kwargs.
**When to use:** Any time a page needs dynamic data from the URL (detail pages, filtered views).
**Trade-offs:** The layout function runs on every navigation to that URL. Keep it lightweight — render a placeholder `dcc.Store` with the id, let a callback do the actual data fetch.

### Pattern 4: `dcc.Store` as Page-Scoped State

**What:** The layout function writes the signal id into `dcc.Store(id="signal-id-store", data=id)`. A callback reads `Input("signal-id-store", "data")` and renders the detail cards.
**When to use:** When the layout function must pass URL parameters into a callback.
**Trade-offs:** Adds one extra component, but makes the callback testable independently (can be unit tested by setting Store data directly). Avoids reading URL params inside the render callback.

---

## Anti-Patterns

### Anti-Pattern 1: Putting the Navigation Callback in dashboard.py (Shell)

**What people do:** Add `Input("history-table", "cellClicked")` in `dashboard.py`'s shell layout callback, where `history-table` is defined in `pages/home.py`.
**Why it's wrong:** Dash raises `ID not found in layout` errors during the initial render for inputs that live in page layouts (they are not always mounted). Cross-page callback references from the shell are fragile.
**Do this instead:** Put the navigation callback in `pages/home.py`, alongside the AG Grid it reads from. Only `Output("url-nav", "href")` crosses the page boundary, which is allowed because `url-nav` lives in the persistent shell layout.

### Anti-Pattern 2: Fetching Full Signal History in the Detail Page

**What people do:** Call `get_signal_history(conn, ...)` in the detail page callback and then filter by id in Python.
**Why it's wrong:** Fetches up to 500 rows just to get one. Wasteful.
**Do this instead:** Add `get_signal_by_id(conn, id)` to `queries.py`. Single-row query: `SELECT ... FROM signals WHERE id = %s`.

### Anti-Pattern 3: Replicating P&L Logic in sinal.py

**What people do:** Copy the P&L calculation loop from `calculate_pl_por_entrada` directly into the detail page callback.
**Why it's wrong:** Creates two sources of truth for the same financial calculation. If the Gale formula changes, must be updated in two places.
**Do this instead:** Extend `queries.py` with a function that reuses `calculate_pl_por_entrada([single_signal], ...)` or `calculate_roi_complementares` directly. Keep all financial math in `queries.py`.

### Anti-Pattern 4: Using `refresh=True` on dcc.Location

**What people do:** Set `refresh=True` on the `dcc.Location` for simplicity.
**Why it's wrong:** Full page reload on every navigation. Resets all filter state in the main dashboard. Jarring UX.
**Do this instead:** Use `refresh="callback-nav"` (available since Dash 2.9.2, current Dash 4.x supports it). Client-side navigation, no full reload.

### Anti-Pattern 5: Passing Full Signal Data via URL

**What people do:** Encode the entire signal dict as a URL query param (JSON encoded) to avoid a DB query on the detail page.
**Why it's wrong:** URLs become very long, may hit browser limits. Financial data in URL is not appropriate even for a personal tool. Misses opportunity to fetch fresh data.
**Do this instead:** Pass only the signal `id` in the URL. The detail page queries the DB with that id.

---

## Build Order (Phase Dependencies)

Dependencies flow from bottom to top. Each step unblocks the next.

```
Step 1: Add id to AG Grid rowData
  ├── In update_dashboard callback master: add "id": sig.get("id") to row_data dicts
  ├── In columnDefs: add {"field": "id", "hide": True}
  └── Verify: cellClicked event includes rowData.id

Step 2: Add get_signal_by_id to queries.py
  ├── Simple SELECT by primary key
  └── Verify: unit test returns expected dict

Step 3: Refactor dashboard.py → pages/ structure
  ├── Create helpertips/pages/ directory
  ├── Create pages/home.py: dash.register_page(__name__, path="/")
  ├── Move entire app.layout content into pages/home.py as layout = dbc.Container(...)
  ├── Move all helper functions and existing callbacks into pages/home.py
  ├── Change dashboard.py: use_pages=True, shell layout with page_container + dcc.Location
  └── Verify: / still renders identically to before

Step 4: Add navigation callback in pages/home.py
  ├── @callback Output("url-nav","href"), Input("history-table","cellClicked")
  └── Verify: clicking a row navigates to /sinal?id=<n>

Step 5: Create pages/sinal.py
  ├── dash.register_page(__name__, path="/sinal")
  ├── def layout(id=None): returns shell with dcc.Store
  ├── render callback: get_signal_by_id → calculate_pl_por_entrada → build cards
  └── Verify: /sinal?id=<n> renders correct signal detail

Step 6: Add calculate_pl_detalhado_por_sinal to queries.py (optional)
  ├── Returns per-complementar rows instead of rolled-up totals
  └── Verify: per-complementar P&L matches calculate_pl_por_entrada totals
```

**Critical dependency:** Step 3 (refactor to pages/) must happen before Step 4 and Step 5. The navigation callback needs `url-nav` to exist in the shell layout. Step 1 and Step 2 are independent of Step 3 and can be done first.

---

## Integration Points

### New Components Added to Existing App

| Component | File | Type | Notes |
|-----------|------|------|-------|
| `dcc.Location(id="url-nav", refresh="callback-nav")` | `dashboard.py` (shell) | New | Navigation trigger, lives outside pages |
| `dash.page_container` | `dashboard.py` (shell) | New | Replaces `app.layout` content |
| `pages/home.py` | new file | New | Contains all existing layout + callbacks |
| `pages/sinal.py` | new file | New | Signal detail page |
| `{"field": "id", "hide": True}` | `pages/home.py` | Modified | Hidden column in AG Grid |
| `"id": sig.get("id")` in rowData | `pages/home.py` | Modified | Adds id to each grid row |
| `get_signal_by_id(conn, id)` | `queries.py` | New function | Single-row fetch by PK |
| `calculate_pl_detalhado_por_sinal(...)` | `queries.py` | New function (optional) | Per-complementar P&L breakdown |

### Callbacks: Cross-Page Boundary

| Input | Output | Location | Notes |
|-------|--------|----------|-------|
| `history-table.cellClicked` (in home.py) | `url-nav.href` (in shell) | `pages/home.py` | Only cross-boundary allowed: Output in shell, Input in page |
| `signal-id-store.data` (in sinal.py) | `sinal-detail-container.children` (in sinal.py) | `pages/sinal.py` | Fully page-local |

---

## gunicorn Compatibility Note

The existing `server = app.server` WSGI entry point in `dashboard.py` is unaffected by `use_pages=True`. gunicorn's invocation (`gunicorn --bind 127.0.0.1:8050 helpertips.dashboard:server`) remains unchanged. No nginx changes required. No systemd changes required.

---

## Scaling Considerations

This is a single-user personal tool. No horizontal scaling concerns for v1.3.

| Concern | At current scale | If detail page becomes heavy |
|---------|-----------------|------------------------------|
| DB queries | 1 query per detail page load (single row) | Add index on signals.id (likely already PK-indexed) |
| gunicorn workers | 2 workers sufficient | Unchanged — detail queries are faster than dashboard master |
| Page registration | Dash Pages scans `pages/` at startup | No runtime cost — page registry built once |

---

## Sources

- Dash Pages official docs: https://dash.plotly.com/urls — HIGH confidence (official Plotly documentation)
- `dcc.Location` with `refresh="callback-nav"`: https://community.plotly.com/t/sharing-examples-of-navigation-without-refreshing-the-page-when-url-is-updated-in-a-callback-in-dash-2-9-2/74260 — HIGH confidence (Plotly community, feature confirmed in official PR https://github.com/plotly/dash/pull/2068)
- Dash AG Grid `cellClicked` properties (colId, rowId, rowIndex, value, rowData): https://dash.plotly.com/dash-ag-grid/cell-selection — HIGH confidence (official Plotly AG Grid docs)
- Multi-page Dash app structure with `pages/` folder: https://open-resources.github.io/dash_curriculum/part5/chapter14.html — MEDIUM confidence (community tutorial, consistent with official docs)
- `def layout(id=None)` query param pattern: https://dash.plotly.com/urls — HIGH confidence (official docs, "Layout Function" section)
- Existing codebase analysis: `helpertips/dashboard.py` (970 LOC), `helpertips/queries.py` — HIGH confidence (direct code inspection)

---

*Architecture research for: HelperTips v1.3 — Análise Individual de Sinais — Dash multi-page integration*
*Researched: 2026-04-04*
