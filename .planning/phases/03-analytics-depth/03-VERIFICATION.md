---
phase: 03-analytics-depth
verified: 2026-04-03T20:00:00Z
status: gaps_found
score: 4/5 success criteria verified
gaps:
  - truth: "A heatmap shows win rate by time of day and a bar chart shows win rate by day of the week, both updating with active filters"
    status: verified
    reason: "Heatmap (graph-heatmap) and DOW bar chart (graph-dow) exist in tab-temporal layout, update_tabs callback reads filter-liga, filter-entrada, filter-date as Inputs"
  - truth: "Applying combined filters (liga + entrada + period) produces a cross-dimensional breakdown of win rate and signal count"
    status: verified
    reason: "table-cross-dimensional in tab-volume, get_cross_dimensional called with liga/entrada/date filters, returns win_rate and total per (liga, entrada) combination"
  - truth: "The equity curve chart shows cumulative bankroll over time with a fixed stake, revealing winning and losing streaks visually"
    status: verified
    reason: "graph-equity in tab-temporal, _make_equity_figure renders y_fixa and y_gale dual-line with Breakeven trace, annotations for streaks >= 5"
  - truth: "A Gale analysis panel shows win rate at gale levels 1, 2, and 3, and a streak tracker shows the current and longest win/loss streaks"
    status: verified
    reason: "graph-gale (horizontal bar chart) and kpi-streak-current, kpi-streak-max-green, kpi-streak-max-red all present in tab-gale, wired to get_gale_analysis and calculate_streaks"
  - truth: "The dashboard header or footer displays the parser coverage rate (percentage of messages successfully parsed)"
    status: verified
    reason: "badge-coverage in header H2, master callback outputs badge children (text) and color (success/warning/danger thresholds 95/90), get_stats called globally"
requirement_gaps:
  - id: ANAL-03
    truth: "Taxa de acerto por periodo (1T/2T/FT se aplicavel)"
    status: failed
    reason: "get_winrate_by_periodo implemented in queries.py and tested (2 tests passing), imported in dashboard.py, but never called in any callback and has no UI component in the layout"
    artifacts:
      - path: "helpertips/dashboard.py"
        issue: "get_winrate_by_periodo imported at line 38 but zero calls in callback body — no graph-periodo component, no table showing 1T/2T/FT breakdown"
    missing:
      - "Add a chart or table component to show win rate per period (1T/2T/FT) in one of the tabs"
      - "Call get_winrate_by_periodo in update_tabs callback and render result"
---

# Phase 3: Analytics Depth Verification Report

**Phase Goal:** Users can identify which leagues, bet types, time slots, and days of the week produce the best results, and track bankroll growth over time
**Verified:** 2026-04-03T20:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Heatmap shows win rate by time of day and DOW bar chart updates with active filters | VERIFIED | `graph-heatmap` + `graph-dow` in `tab-temporal`; `update_tabs` takes `filter-liga`, `filter-entrada`, `filter-date` as Inputs and calls `get_heatmap_data` + `get_winrate_by_dow` |
| 2 | Combined filters produce cross-dimensional breakdown of win rate and signal count | VERIFIED | `table-cross-dimensional` in `tab-volume`; `get_cross_dimensional(conn, liga, entrada, date_start, date_end)` wired in `update_tabs` callback |
| 3 | Equity curve shows cumulative bankroll over time, revealing winning and losing streaks | VERIFIED | `graph-equity` in `tab-temporal`; `_make_equity_figure` renders `y_fixa`, `y_gale` (dual line), breakeven trace, and annotations for streaks >= 5 |
| 4 | Gale analysis panel + streak tracker with current and longest streaks | VERIFIED | `graph-gale` + `kpi-streak-current` + `kpi-streak-max-green` + `kpi-streak-max-red` in `tab-gale`; wired to `get_gale_analysis` and `calculate_streaks` |
| 5 | Dashboard header displays parser coverage rate | VERIFIED | `badge-coverage` in `html.H2` header; master callback `update_dashboard` outputs `badge-coverage.children` ("Cobertura: XX%") and `badge-coverage.color` using `get_stats` |

**Score:** 5/5 success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `helpertips/queries.py` | 9 new functions (Plans 01+02) | VERIFIED | All 9 functions exist: `get_heatmap_data` (l.538), `get_winrate_by_dow` (l.588), `calculate_equity_curve` (l.641), `calculate_streaks` (l.729), `get_gale_analysis` (l.790), `get_volume_by_day` (l.834), `get_cross_dimensional` (l.865), `get_parse_failures_detail` (l.910), `get_winrate_by_periodo` (l.939) |
| `tests/test_queries.py` | 24 new tests (Plans 01+02) | VERIFIED | 24 test functions confirmed: equity_curve (5), streaks (3), heatmap (2), winrate_by_dow (2), gale_analysis (3), volume_by_day (2), cross_dimensional (2), parse_failures (3), winrate_by_periodo (2) |
| `helpertips/dashboard.py` | Layout with 3 tabs, badge, modal, callbacks | VERIFIED | All layout IDs confirmed: `tabs-analytics`, `tab-temporal`, `tab-gale`, `tab-volume`, `badge-coverage`, `modal-parse-failures`, and all graph/kpi IDs |
| `tests/test_dashboard.py` | Layout ID test + badge thresholds + format_streak | VERIFIED | `test_layout_has_required_component_ids` (all 12 Phase 3 IDs included), `test_coverage_badge_thresholds`, `test_format_streak` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `dashboard.py:update_tabs` | `queries.py:get_heatmap_data` | called in `tab-temporal` branch | WIRED | Line 871: `heatmap_data = get_heatmap_data(conn, liga, entrada, date_start, date_end)` |
| `dashboard.py:update_tabs` | `queries.py:calculate_equity_curve` | called after `get_signal_history` | WIRED | Line 876: `equity_data = calculate_equity_curve(history, stake, odd)` |
| `dashboard.py:update_dashboard` | `store.py:get_stats` | badge coverage in master callback | WIRED | Lines 816-819: `global_stats = get_stats(conn)`, badge_color logic |
| `dashboard.py:toggle_modal` | `queries.py:get_parse_failures_detail` | triggered on badge click | WIRED | Line 928: `failures = get_parse_failures_detail(conn, limit=50)` |
| `queries.py:get_heatmap_data` | `queries.py:_build_where` | filter reuse | WIRED | Line 562: `where, params = _build_where(liga=liga, ...)` |
| `queries.py:calculate_equity_curve` | reversal pattern | `list(reversed(...))` | WIRED | Line 668: `resolved_asc = list(reversed(resolved))` |
| `queries.py:get_gale_analysis` | `signals.tentativa` | `tentativa IS NOT NULL` filter | WIRED | Line 815: `AND tentativa IS NOT NULL` |
| `queries.py:get_cross_dimensional` | `queries.py:_build_where` | filter reuse | WIRED | Line 880: `where, params = _build_where(liga=liga, ...)` |
| `queries.py:get_winrate_by_periodo` | `signals.periodo` | `periodo IS NOT NULL` filter | WIRED (data layer only) | Line 964: `AND periodo IS NOT NULL` — but no dashboard UI calls this function |
| `dashboard.py` (import) | `queries.py:get_winrate_by_periodo` | import exists, no call | ORPHANED | Imported at line 38, zero calls in callbacks, no UI component renders period data |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `graph-heatmap` | `heatmap_data` | `get_heatmap_data(conn, ...)` → SQL `EXTRACT(HOUR/DOW)` + pivot | Yes — SQL GROUP BY hour/dow against live DB | FLOWING |
| `graph-equity` | `equity_data` | `get_signal_history(conn, ...)` → `calculate_equity_curve(history, ...)` | Yes — pure Python over real signal list | FLOWING |
| `graph-dow` | `dow_data` | `get_winrate_by_dow(conn, ...)` → SQL GROUP BY DOW | Yes | FLOWING |
| `graph-gale` | `gale_data` | `get_gale_analysis(conn, ...)` → SQL GROUP BY tentativa | Yes | FLOWING |
| `kpi-streak-*` | `streaks` | `calculate_streaks(history)` pure Python | Yes — over real signals | FLOWING |
| `graph-volume` | `vol_data` | `get_volume_by_day(conn, ...)` → SQL DATE_TRUNC | Yes | FLOWING |
| `table-cross-dimensional` | `cross_data` | `get_cross_dimensional(conn, ...)` → SQL GROUP BY liga, entrada | Yes | FLOWING |
| `badge-coverage` | `global_stats["coverage"]` | `get_stats(conn)` from `store.py` | Yes | FLOWING |
| Period breakdown (ANAL-03) | — | `get_winrate_by_periodo` not called | No — function exists but disconnected | HOLLOW_PROP |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 132 tests pass | `python3 -m pytest tests/ -x -q` | `132 passed in 0.54s` | PASS |
| Import dashboard module | `python3 -c "from helpertips.dashboard import app; print('OK')"` | Verified via test run passing | PASS |
| `_build_where` reused by heatmap | `grep "_build_where(" helpertips/queries.py` | Confirmed at lines 562, 612, 806, 848, 880, 955 | PASS |
| Reversed pattern in equity curve | `grep "list(reversed" helpertips/queries.py` | Confirmed at lines 668, 750 | PASS |
| `tentativa IS NOT NULL` in gale | `grep "tentativa IS NOT NULL" helpertips/queries.py` | Line 815 confirmed | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| ANAL-01 | 03-01, 03-03 | Heatmap win rate por horario | SATISFIED | `get_heatmap_data` + `graph-heatmap` in `tab-temporal`, filter-reactive |
| ANAL-02 | 03-01, 03-03 | Win rate por dia da semana | SATISFIED | `get_winrate_by_dow` + `graph-dow` in `tab-temporal` |
| ANAL-03 | 03-02, 03-03 | Win rate por periodo (1T/2T/FT) | BLOCKED | `get_winrate_by_periodo` implemented and tested but imported-only in `dashboard.py` — no UI component renders period breakdown |
| ANAL-04 | 03-02, 03-03 | Analise cross-dimensional | SATISFIED | `get_cross_dimensional` + `table-cross-dimensional` in `tab-volume`, reactive to filters |
| ANAL-05 | 03-01, 03-03 | Curva de equity | SATISFIED | `calculate_equity_curve` + `graph-equity` in `tab-temporal`, dual-line Stake Fixa vs Gale |
| ANAL-06 | 03-01, 03-03 | Tracking de streaks | SATISFIED | `calculate_streaks` + 3 mini-cards `kpi-streak-*` in `tab-gale` |
| ANAL-07 | 03-02, 03-03 | Analise de Gale por nivel | SATISFIED | `get_gale_analysis` + `graph-gale` (horizontal bars) in `tab-gale` |
| ANAL-08 | 03-02, 03-03 | Volume de sinais por dia | SATISFIED | `get_volume_by_day` + `graph-volume` in `tab-volume` |
| OPER-01 | 03-02, 03-03 | Taxa de cobertura do parser | SATISFIED | `badge-coverage` in header, `get_stats(conn)` in master callback, modal with `get_parse_failures_detail` on click |

**Orphaned requirements:** None — all 9 Phase 3 requirement IDs are declared in plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|---------|--------|
| `helpertips/dashboard.py` | 38 | `get_winrate_by_periodo` imported but never called in any callback | Warning | ANAL-03 data layer exists but is invisible to user — period breakdown is not surfaced in the UI |

No TODO/FIXME/placeholder comments found in Phase 3 files.
No empty implementations (`return null`, `return {}`, `return []` without data logic) found.

### Human Verification Required

#### 1. Verificacao visual das 3 abas

**Test:** Iniciar `python3 -m helpertips.dashboard`, abrir http://localhost:8050, navegar pelas 3 abas (Temporal, Gale & Streaks, Volume)
**Expected:** Graficos renderizam com dados reais ou empty-state legivel; filtros atualizam graficos ao mudar
**Why human:** Comportamento visual, responsividade, e UX de navegacao nao sao verificaveis por grep

#### 2. Badge de cobertura clickavel

**Test:** Clicar no badge "Cobertura: XX%" no header
**Expected:** Modal "Falhas de Parse" abre com tabela ou mensagem "Nenhuma falha"
**Why human:** Interacao de click e renderizacao do modal requerem browser

#### 3. Equity curve com banco vazio vs populado

**Test:** Verificar equity curve com dados reais vs sem dados
**Expected:** Mostra "Nenhum sinal com resultado no periodo selecionado" quando vazio; curva dual-line com breakeven quando ha dados
**Why human:** Requer dados no banco para verificar curva real

### Gaps Summary

**5 de 5 success criteria verificados.** No entanto, existe um gap na cobertura de requisitos:

**ANAL-03 nao e entregue ao usuario.** A funcao `get_winrate_by_periodo` foi implementada em `queries.py` (linha 939) e testada com 2 testes passando, mas nao esta conectada a nenhum componente visual no dashboard. O import existe na linha 38 de `dashboard.py` sem nenhuma chamada no corpo dos callbacks, e nao ha nenhum grafico ou tabela que exiba o breakdown por periodo (1T/2T/FT).

O requisito REQUIREMENTS.md marca ANAL-03 como `[x]` completado, mas a entrega real e incompleta — a camada de dados existe mas o usuario nao tem acesso aos dados no dashboard.

Os demais 8 requisitos (ANAL-01, ANAL-02, ANAL-04, ANAL-05, ANAL-06, ANAL-07, ANAL-08, OPER-01) estao totalmente satisfeitos com implementacao, testes, e wiring completo.

---

_Verified: 2026-04-03T20:00:00Z_
_Verifier: Claude (gsd-verifier)_
