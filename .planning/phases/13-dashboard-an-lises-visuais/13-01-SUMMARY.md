---
phase: 13-dashboard-an-lises-visuais
plan: 01
subsystem: ui
tags: [plotly, dash, analytics, charts, tdd, queries]

# Dependency graph
requires:
  - phase: 12-dashboard-mercados-e-performance
    provides: helpers puros testaveis + callback master integrado

provides:
  - aggregate_pl_por_liga em helpertips/queries.py
  - aggregate_pl_por_tentativa em helpertips/queries.py
  - _build_liga_chart em helpertips/dashboard.py
  - _build_equity_curve_chart em helpertips/dashboard.py
  - _build_gale_chart em helpertips/dashboard.py
affects: [13-02, callback-master-integracao-phase13]

# Tech tracking
tech-stack:
  added: []
  patterns: [funcoes puras de agregacao sem DB + builders Plotly testados via TDD com try/except ImportError guard]

key-files:
  created: []
  modified:
    - helpertips/queries.py
    - helpertips/dashboard.py
    - tests/test_queries.py
    - tests/test_dashboard.py

key-decisions:
  - "aggregate_pl_por_tentativa ignora REDs: apenas rows com resultado=GREEN entram no agrupamento (tentativas com so REDs nao aparecem no resultado)"
  - "pytest adicionado como import em test_dashboard.py: necessario para pytest.skip nas guards try/except de Phase 13"
  - "builders Plotly seguem padrao TDD try/except ImportError estabelecido nas Phases 11-12"

patterns-established:
  - "Builders Plotly retornam go.Figure() vazio para input vazio — sem erros, sem None"
  - "Cores consistentes per Design Decisions: #00bc8c principal, #e74c3c complementar, #f39c12 total"
  - "Tema dark uniforme: paper_bgcolor=#222, plot_bgcolor=#222, font color=white"

requirements-completed: [DASH-05, DASH-06, DASH-07]

# Metrics
duration: 12min
completed: 2026-04-04
---

# Phase 13 Plan 01: Dashboard Analises Visuais — Funcoes Puras e Builders Plotly Summary

**Funcoes puras de agregacao por liga/tentativa em queries.py + 3 builders Plotly (stacked bar, equity curve, donut gale) com 17 testes TDD verdes**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-04T00:00:00Z
- **Completed:** 2026-04-04T00:12:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- `aggregate_pl_por_liga`: agrupa P&L de calculate_pl_por_entrada por liga, separa principal/complementar, calcula taxa_green, ordena por pl_total desc
- `aggregate_pl_por_tentativa`: agrupa greens e calcula lucro_medio_green por tentativa (gale level), base para analise de eficiencia do Gale
- `_build_liga_chart`: barras empilhadas Principal (verde) + Complementar (vermelho) com tema dark e hover rico
- `_build_equity_curve_chart`: 3 linhas sobrepostas principal/complementar/total com cores per D-01/D-11, sem range slider
- `_build_gale_chart`: donut com hole=0.4, 4 tons de #00bc8c, mostra distribuicao de greens por tentativa
- 17 testes TDD cobrindo inputs normais, vazios, edge cases (None liga, None tentativa, sem greens) e validacao de cores/tema

## Task Commits

1. **Task 1: Funcoes de agregacao em queries.py** - `76bb323` (feat)
2. **Task 2: Builders Plotly em dashboard.py** - `759b311` (feat)

## Files Created/Modified

- `helpertips/queries.py` - Adicionadas aggregate_pl_por_liga e aggregate_pl_por_tentativa ao final
- `helpertips/dashboard.py` - Adicionados _build_liga_chart, _build_equity_curve_chart, _build_gale_chart antes de make_kpi_card
- `tests/test_queries.py` - 8 testes TDD para funcoes de agregacao + guards try/except ImportError
- `tests/test_dashboard.py` - 9 testes TDD para builders Plotly + import pytest adicionado

## Decisions Made

- `aggregate_pl_por_tentativa` ignora REDs completamente: apenas greens entram no agrupamento. Tentativas com somente REDs nao aparecem no resultado. Decisao coerente com o objetivo do chart (lucro medio de greens por tentativa).
- `pytest` adicionado como import em `tests/test_dashboard.py` — nao estava importado antes, necessario para `pytest.skip` nas guards das novas funcoes Phase 13.
- Builders seguem exatamente o padrao TDD established nas Phases 11-12: try/except ImportError + guard condicional em cada teste.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pytest nao importado em test_dashboard.py**
- **Found during:** Task 2 (fase RED — execucao dos testes)
- **Issue:** `NameError: name 'pytest' is not defined` ao rodar testes — arquivo nao tinha `import pytest`
- **Fix:** Adicionado `import pytest` junto com os imports existentes
- **Files modified:** tests/test_dashboard.py
- **Verification:** Testes rodaram sem NameError, 9 passed
- **Committed in:** 759b311 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix necessario para execucao dos testes. Sem scope creep.

## Issues Encountered

Nenhum outro problema alem do pytest import acima.

## Known Stubs

Nenhum stub. As funcoes retornam dados calculados a partir dos inputs. Os builders retornam go.Figure() vazio para input vazio — comportamento intencional, nao stub.

## Next Phase Readiness

- Funcoes puras prontas para integracao no callback master (Plan 13-02)
- aggregate_pl_por_liga consumida por _build_liga_chart via callback
- aggregate_pl_por_tentativa consumida por _build_gale_chart via callback  
- calculate_equity_curve_breakdown (existente) consumida por _build_equity_curve_chart via callback
- Suite completa verde: 207 testes passando

## Self-Check: PASSED

- `helpertips/queries.py` contem `def aggregate_pl_por_liga` e `def aggregate_pl_por_tentativa`: FOUND
- `helpertips/dashboard.py` contem `def _build_liga_chart`, `def _build_equity_curve_chart`, `def _build_gale_chart`: FOUND
- Commit 76bb323: FOUND
- Commit 759b311: FOUND
- 17 testes novos passando: VERIFIED (207 total, zero falhas)

---
*Phase: 13-dashboard-an-lises-visuais*
*Completed: 2026-04-04*
