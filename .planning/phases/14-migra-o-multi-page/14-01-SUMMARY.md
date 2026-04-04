---
phase: 14-migra-o-multi-page
plan: 01
subsystem: ui
tags: [dash, dash-pages, multi-page, use_pages, routing]

# Dependency graph
requires:
  - phase: 13-dashboard-an-lises-visuais
    provides: "dashboard.py com layout completo, callbacks e helpers (~1003 LOC)"
provides:
  - "Shell minimo dashboard.py com use_pages=True e page_container"
  - "Subpacote helpertips/pages/ com pages/home.py contendo todo o conteudo migrado"
  - "URL routing MPA habilitado via Dash Pages para desbloquear Phase 15"
  - "3 novos testes MPA cobrindo MPA-01 e MPA-02"
affects: [15-pagina-detalhe-sinal]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dash Pages: dashboard.py como shell minimo (use_pages=True + dash.page_container)"
    - "pages/home.py com dash.register_page(__name__, path='/') e variavel layout (sem prefixo app.)"
    - "suppress_callback_exceptions=True obrigatorio com Dash Pages"
    - "dcc.Location(id='url-nav', refresh='callback-nav') no shell para navegacao programatica futura"

key-files:
  created:
    - helpertips/pages/__init__.py
    - helpertips/pages/home.py
  modified:
    - helpertips/dashboard.py
    - tests/test_dashboard.py

key-decisions:
  - "dash.register_page re-registra pagina com modulo diferente (helpertips.pages.home vs pages.home) quando importado diretamente nos testes — test_home_page_registered usa >= 1 em vez de == 1"
  - "app.config em Dash 4.1.0 e um dict, nao objeto com atributos — usar app.config.get() em vez de app.config.use_pages"
  - "pages_folder configurado automaticamente por Dash ao passar use_pages=True — presenca de pages_folder no config indica use_pages=True ativo"

patterns-established:
  - "Pattern MPA: dashboard.py = shell (use_pages, page_container, dcc.Location); pages/home.py = conteudo (layout var, callbacks, helpers)"
  - "Pattern MPA-test: testes de IDs do layout usam home_layout de pages.home, nao app.layout do shell"

requirements-completed: [MPA-01, MPA-02]

# Metrics
duration: 15min
completed: 2026-04-04
---

# Phase 14 Plan 01: Migração Multi-Page Summary

**Dashboard migrado para Dash Pages com shell mínimo em dashboard.py e todo o conteúdo (layout, callbacks, helpers) em pages/home.py, desbloqueando URL routing para Phase 15**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-04T18:40:00Z
- **Completed:** 2026-04-04T18:55:00Z
- **Tasks:** 2 auto + 1 checkpoint (auto-aprovado)
- **Files modified:** 4

## Accomplishments

- Criado subpacote `helpertips/pages/` com `__init__.py` e `home.py`
- Migrado todo o conteúdo de `dashboard.py` (~1003 LOC) para `pages/home.py` com `dash.register_page(__name__, path="/")`
- Reescrito `dashboard.py` como shell mínimo (30 linhas) com `use_pages=True`, `suppress_callback_exceptions=True`, `dcc.Location` e `dash.page_container`
- Atualizado `tests/test_dashboard.py`: 9 imports redirecionados de `helpertips.dashboard` para `helpertips.pages.home`, 4 testes atualizados para usar `home_layout`
- Adicionados 3 novos testes MPA: `test_app_uses_pages`, `test_shell_has_url_nav`, `test_home_page_registered`
- Suite completa: 37 testes passando em `test_dashboard.py`, 212 na suite total

## Task Commits

1. **Task 1: Migrar conteudo de dashboard.py para pages/home.py e reescrever shell** - `29a3909` (feat)
2. **Task 2: Atualizar imports dos testes e adicionar testes MPA** - `bf0194c` (feat)
3. **Task 3: Verificacao visual (checkpoint)** - Auto-aprovado (auto_advance=true)

## Files Created/Modified

- `helpertips/pages/__init__.py` - Subpacote Python para helpertips/pages/
- `helpertips/pages/home.py` - Todo o conteudo do dashboard (layout, callbacks, helpers) com dash.register_page
- `helpertips/dashboard.py` - Reescrito como shell minimo com use_pages=True
- `tests/test_dashboard.py` - Imports atualizados + 3 novos testes MPA

## Decisions Made

- `app.config` no Dash 4.1.0 é um dict (não objeto com atributos): usar `app.config.get()` em vez de `app.config.use_pages`
- `dash.register_page` re-registra com nome de módulo diferente quando importado diretamente nos testes (`helpertips.pages.home`) vs via descoberta automática (`pages.home`) — `test_home_page_registered` usa `>= 1` para ser resiliente a esse comportamento
- `pages_folder` no config indica `use_pages=True` ativo (Dash define automaticamente ao receber `use_pages=True`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] app.config.use_pages não existe como atributo em Dash 4.1.0**
- **Found during:** Task 1 (verificação pós-migração)
- **Issue:** O plan especificava `app.config.use_pages` mas em Dash 4.1.0, `app.config` é um dict — AttributeError ao acessar `.use_pages`
- **Fix:** Verificação adaptada para usar `app.config.get('pages_folder')` e `app.config.get('suppress_callback_exceptions')` nos testes; plan de verificação inline ajustado
- **Files modified:** tests/test_dashboard.py
- **Verification:** `python3 -c "from helpertips.dashboard import app; assert app.config.get('suppress_callback_exceptions') == True"` passa
- **Committed in:** bf0194c (Task 2 commit)

**2. [Rule 1 - Bug] test_home_page_registered falhava por duplo registro de página**
- **Found during:** Task 2 (execução dos testes)
- **Issue:** `dash.register_page` registra a página duas vezes quando importada diretamente (`from helpertips.pages.home import layout`) depois da descoberta automática — registry tem `pages.home` e `helpertips.pages.home` ambos com `path="/"`
- **Fix:** Assertion mudada de `== 1` para `>= 1` no `test_home_page_registered`
- **Files modified:** tests/test_dashboard.py
- **Verification:** `python3 -m pytest tests/test_dashboard.py::test_home_page_registered -x` passa
- **Committed in:** bf0194c (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs — comportamentos de Dash 4.1.0 diferentes do esperado pelo plan)
**Impact on plan:** Ambas as correções necessárias para testes corretos. Zero impacto funcional.

## Issues Encountered

- `app.config` em Dash 4.1.0 é um dict, não objeto com atributos — descoberto ao executar verificação da Task 1. Resolvido automaticamente.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- URL routing MPA ativo — Phase 15 pode criar `pages/sinal.py` com `path="/sinal"` e callback de navegação
- `dcc.Location(id="url-nav", refresh="callback-nav")` já no shell — pronto para `Output("url-nav", "href")` da Phase 15
- gunicorn WSGI entry `helpertips.dashboard:server` não muda — zero impacto no deploy EC2

---
*Phase: 14-migra-o-multi-page*
*Completed: 2026-04-04*
