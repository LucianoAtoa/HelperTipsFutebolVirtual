---
phase: 16-navega-o-schema-db
plan: 01
subsystem: ui, database
tags: [dash, dbc, postgresql, navigation, migration, dash-pages]

# Dependency graph
requires:
  - phase: 15-detalhe-sinal
    provides: Dash Pages (use_pages=True) multi-page routing shell

provides:
  - dbc.Nav pills com tabs Dashboard/Configuracoes no topo do shell
  - Pagina /config placeholder registrada via Dash Pages (pronta para Phase 17)
  - Colunas stake_base, fator_progressao, max_tentativas na tabela mercados com defaults

affects:
  - 17-formulario-config
  - 18-listener-config
  - 19-dashboard-ajustes

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "dbc.NavLink active='exact' para destacar tab ativa sem callback"
    - "ALTER TABLE ... ADD COLUMN IF NOT EXISTS para migrations idemptentes"

key-files:
  created:
    - helpertips/pages/config.py
  modified:
    - helpertips/db.py
    - helpertips/dashboard.py
    - tests/test_dashboard.py
    - tests/test_db.py

key-decisions:
  - "dbc.NavLink active='exact' destaca tab ativa nativamente sem callback Dash"
  - "ADD COLUMN IF NOT EXISTS garante idempotencia da migration Phase 16"
  - "Colunas stake_base/fator_progressao/max_tentativas com NOT NULL DEFAULT — registros existentes recebem default automaticamente"

patterns-established:
  - "Migration pattern: ALTER TABLE ... ADD COLUMN IF NOT EXISTS no bloco Phase XX dentro de ensure_schema"
  - "Navigation pattern: dbc.Nav pills com id='nav-tabs' no shell do dashboard"

requirements-completed: [NAV-01]

# Metrics
duration: 12min
completed: 2026-04-04
---

# Phase 16 Plan 01: Navegacao Schema DB Summary

**Menu de navegacao por pills (Dashboard/Configuracoes) no shell Dash com dbc.NavLink active='exact', pagina /config placeholder, e migration idempotente adicionando stake_base/fator_progressao/max_tentativas em mercados**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-04T22:30:00Z
- **Completed:** 2026-04-04T22:42:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Migration Phase 16 adiciona 3 colunas editaveis em mercados (stake_base=10.00, fator_progressao=2.00, max_tentativas=4) via ALTER TABLE IF NOT EXISTS
- Shell do dashboard atualizado com dbc.Nav pills (nav-tabs) contendo links para / e /config com destaque automatico de tab ativa
- Pagina /config criada como placeholder placeholder com register_page para Dash Pages — pronta para formulario na Phase 17
- 5 novos testes: test_mercados_config_columns_exist, test_ensure_schema_idempotent, test_nav_tabs_present, test_nav_links_present, test_config_page_registered

## Task Commits

1. **Task 1: Migration DB — colunas de config em mercados + testes** - `04719e6` (feat)
2. **Task 2: Navegacao por tabs no shell + pagina placeholder /config + testes** - `d00d74d` (feat)

**Plan metadata:** (final docs commit)

## Files Created/Modified

- `helpertips/db.py` — Migration Phase 16: 3 ALTER TABLE ADD COLUMN IF NOT EXISTS para stake_base, fator_progressao, max_tentativas
- `helpertips/dashboard.py` — dbc.Nav com pills (nav-tabs, nav-link-home, nav-link-config) + import html adicionado
- `helpertips/pages/config.py` — Pagina /config placeholder registrada via Dash Pages (criada nesta fase)
- `tests/test_db.py` — test_mercados_config_columns_exist + test_ensure_schema_idempotent
- `tests/test_dashboard.py` — test_nav_tabs_present + test_nav_links_present + test_config_page_registered + import dash

## Decisions Made

- **dbc.NavLink active='exact'**: Destaca a tab ativa nativamente sem callback adicional. Dash Pages + dbc 2.x atualiza o pathname automaticamente, e active="exact" responde a isso sem necessidade de callback manual. Elegante e zero-overhead.
- **NOT NULL DEFAULT nas colunas**: Garante que registros existentes em mercados recebem os valores default imediatamente na migration, sem precisar de UPDATE retroativo separado.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adicionado import dash em test_dashboard.py**
- **Found during:** Task 2 (execucao de test_config_page_registered)
- **Issue:** NameError: name 'dash' is not defined — test_config_page_registered usa dash.page_registry mas 'dash' nao estava importado no nivel do modulo
- **Fix:** Adicionado `import dash` ao bloco de imports do test_dashboard.py
- **Files modified:** tests/test_dashboard.py
- **Verification:** test_config_page_registered PASSED apos correcao
- **Committed in:** d00d74d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — import ausente)
**Impact on plan:** Correcao minima necessaria para execucao do teste planejado. Sem escopo adicional.

## Issues Encountered

Pre-existing failures em tests/test_queries.py (helpertips/queries.py e tests/test_queries.py ja estavam modificados antes desta phase — gitStatus inicial mostrou M em ambos). Nao sao causados pelas mudancas da Phase 16. Documentado em deferred-items.md.

## Known Stubs

- `helpertips/pages/config.py` — layout eh placeholder com dbc.Alert informativo. Formulario editavel sera implementado na Phase 17.

## Next Phase Readiness

- Phase 17 (formulario /config) pode comecar imediatamente: rota /config registrada, schema com colunas novas pronto
- Colunas stake_base, fator_progressao, max_tentativas existem com defaults corretos — Phase 17 pode fazer SELECT e UPDATE sem migration adicional
- dbc.Nav ja no lugar — Phase 17 pode adicionar conteudo ao layout de config.py sem tocar no shell

## Self-Check: PASSED

- FOUND: helpertips/pages/config.py
- FOUND: helpertips/db.py
- FOUND: helpertips/dashboard.py
- FOUND: commit 04719e6 (Task 1)
- FOUND: commit d00d74d (Task 2)

---
*Phase: 16-navega-o-schema-db*
*Completed: 2026-04-04*
