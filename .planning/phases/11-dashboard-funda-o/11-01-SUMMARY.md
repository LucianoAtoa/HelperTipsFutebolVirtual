---
phase: 11-dashboard-funda-o
plan: "01"
subsystem: testing
tags: [dash, css, tdd, layout, kpi, periodo, streaks]

# Dependency graph
requires:
  - phase: 10-l-gica-financeira
    provides: calculate_pl_por_entrada, calculate_equity_curve_breakdown para uso no dashboard v1.2
provides:
  - helpertips/assets/custom.css com override de contraste DARKLY para RadioItems
  - tests/test_dashboard.py reescrito com novos IDs v1.2 (periodo-selector, kpi-pl-total, kpi-roi, kpi-streak-green, kpi-streak-red, collapse-datepicker, filter-date-custom, filter-mercado, filter-liga)
  - 6 testes de _resolve_periodo (hoje, semana, mes, mes_passado, toda_vida, personalizado)
  - Testes de formatacao KPI (P&L R$, streaks Nx/em-dash)
  - Estado RED intencional para testes de layout e _resolve_periodo ate Plan 02
affects: [11-02-PLAN, dashboard.py redesign]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD red-first: testes escritos antes da implementacao, falhas sao intencionais"
    - "assets/ Dash: arquivos CSS em helpertips/assets/ carregados automaticamente pelo Dash"
    - "try/except ImportError para importar funcoes futuras sem quebrar coleta de testes"

key-files:
  created:
    - helpertips/assets/custom.css
  modified:
    - tests/test_dashboard.py

key-decisions:
  - "Usar try/except ImportError para _resolve_periodo: testes coletam sem erro mesmo antes da implementacao, falhando graciosamente com assert _HAS_RESOLVE_PERIODO"
  - "CSS em helpertips/assets/: Dash carrega automaticamente, zero configuracao adicional necessaria"
  - "Remover test_coverage_badge_thresholds e test_format_streak: badge-coverage e _format_streak nao existem no layout v1.2"

patterns-established:
  - "TDD Plan N (testes RED) + Plan N+1 (implementacao GREEN): padrao para redesigns complexos"
  - "collect_ids helper reutilizavel para verificacao estrutural de layout Dash"
  - "find_collapse helper inline para verificar propriedades de componentes especificos"

requirements-completed: [DASH-01, DASH-02]

# Metrics
duration: 8min
completed: 2026-04-04
---

# Phase 11 Plan 01: Dashboard Fundacao — Testes e CSS Summary

**Testes TDD red-first para layout v1.2 com 17 IDs de componentes novos e CSS de contraste DARKLY para RadioItems**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-04T15:00:00Z
- **Completed:** 2026-04-04T15:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- CSS override criado em helpertips/assets/custom.css garantindo contraste dos RadioItems (btn-outline-secondary) no tema DARKLY
- tests/test_dashboard.py completamente reescrito com 17 novos IDs do layout v1.2 (periodo-selector, kpi-pl-total, kpi-roi, kpi-streak-green, kpi-streak-red, collapse-datepicker, filter-date-custom, filter-mercado, filter-liga)
- 6 testes de _resolve_periodo cobrindo todas as opcoes de periodo (hoje, semana, mes, mes_passado, toda_vida, personalizado)
- 2 novos testes de formatacao KPI (test_kpi_pl_formatting com R$ +X.XX e classes CSS, test_kpi_streak_formatting com Nx e em-dash)
- Estado RED intencional: 8 testes falhando ate Plan 02 implementar o novo dashboard.py, 9 testes passando (formatacao, gale, debug mode)

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Criar helpertips/assets/custom.css** - `7d12447` (feat)
2. **Task 2: Reescrever tests/test_dashboard.py** - `068eb31` (test)

## Files Created/Modified
- `helpertips/assets/custom.css` - Override de contraste para .btn-check:not(:checked) e .btn-check:checked no tema DARKLY
- `tests/test_dashboard.py` - Reescrito com 17 testes: novos IDs v1.2, _resolve_periodo (6), formatacao KPI (2), preservados (9)

## Decisions Made
- Usar `try/except ImportError` para importar `_resolve_periodo`: permite que testes sejam coletados sem erro de import mesmo antes da implementacao. Testes falham graciosamente com `assert _HAS_RESOLVE_PERIODO` mostrando mensagem clara.
- CSS em `helpertips/assets/`: Dash carrega automaticamente qualquer arquivo em assets/ relativo ao modulo — zero configuracao adicional.
- Remover `test_coverage_badge_thresholds` e `test_format_streak`: badge-coverage foi removido do layout v1.2, `_format_streak` sera substituida por formatacao inline no novo callback.

## Deviations from Plan

Nenhum — plano executado exatamente como escrito.

## Issues Encountered
Nenhum.

## User Setup Required
Nenhum — sem servicos externos requerendo configuracao manual.

## Known Stubs
Nenhum — este plano apenas cria testes e CSS, sem codigo de producao.

## Next Phase Readiness
- CSS de contraste pronto para ser servido automaticamente pelo Dash no novo layout
- Testes RED esperando implementacao do Plan 02 (reescrita do dashboard.py)
- Plan 02 deve implementar: novos IDs de componentes, _resolve_periodo, novo layout v1.2

---
*Phase: 11-dashboard-funda-o*
*Completed: 2026-04-04*
