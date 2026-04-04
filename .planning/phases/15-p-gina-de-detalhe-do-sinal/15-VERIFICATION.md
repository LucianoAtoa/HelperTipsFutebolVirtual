---
phase: 15-p-gina-de-detalhe-do-sinal
verified: 2026-04-04T20:00:00Z
status: human_needed
score: 8/8 must-haves verified
human_verification:
  - test: "Abrir dashboard, clicar em qualquer linha do AG Grid — verificar coluna 'Ver' com link markdown navega para /sinal?id=N sem full page reload"
    expected: "URL muda para /sinal?id=N, página de detalhe carrega com card principal, tabela de complementares e totais"
    why_human: "Comportamento de navegação client-side com link markdown no AG Grid não é verificável programaticamente sem servidor"
  - test: "Na página de detalhe /sinal?id=N, verificar cores: resultado GREEN aparece em verde, RED em vermelho, N/A em cinza"
    expected: "Card principal e tabela de entradas usam text-success/text-danger/text-muted de acordo com resultado"
    why_human: "Aparência visual requer renderização no browser"
  - test: "Clicar em 'Voltar' / '<- Voltar' na página de detalhe"
    expected: "Retorna ao dashboard em /"
    why_human: "Comportamento de navegação client-side"
  - test: "Acessar /sinal?id=999999 manualmente"
    expected: "Exibe 'Sinal nao encontrado' com mensagem amigável, sem erro 500"
    why_human: "Requer conexão com banco de dados e servidor Dash rodando"
  - test: "Acessar /sinal?id=abc manualmente"
    expected: "Exibe 'ID de sinal invalido' sem erro"
    why_human: "Requer servidor Dash rodando para validar resposta HTTP"
---

# Phase 15: Página de Detalhe do Sinal — Verification Report

**Phase Goal:** Usuário clica em um sinal no histórico e visualiza breakdown completo de P&L (principal + cada complementar)
**Verified:** 2026-04-04T20:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `get_sinal_detalhado` retorna dict completo para ID existente | ✓ VERIFIED | `queries.py:768` — SELECT com LEFT JOIN mercados WHERE s.id = %s, retorna dict com 9 keys |
| 2 | `get_sinal_detalhado` retorna None para ID inexistente | ✓ VERIFIED | `queries.py:795` — `if row is None: return None` |
| 3 | `calculate_pl_detalhado_por_sinal` retorna breakdown principal + cada complementar + totais | ✓ VERIFIED | `queries.py:954` — retorna `{principal, complementares, totais}` |
| 4 | Complementar sem placar retorna resultado N/A e lucro 0.0 | ✓ VERIFIED | `queries.py:879-890` — bloco `if not placar_disponivel` com N/A, lucro=0.0, investido=0.0 |
| 5 | Gale progressivo aplica fator correto na stake de cada tentativa | ✓ VERIFIED | `queries.py:839-843` — `accumulated_stake = stake*(2**tentativa-1)`, `winning_stake = stake*(2**(tentativa-1))` |
| 6 | Clicar em linha do AG Grid navega para /sinal?id=N | ✓ VERIFIED (code) / ? HUMAN (behavior) | `home.py:936` — coluna `ver_link` com `[Ver](/sinal?id=N)`, `cellRenderer: "markdown"` (dash-ag-grid 35.2.0) |
| 7 | Página exibe card da entrada principal + tabela complementares + totais consolidados | ✓ VERIFIED | `sinal.py:88-225` — `_build_detail_layout` com card principal, `tabela_entradas`, `resumo_card` |
| 8 | ID inexistente exibe mensagem amigável sem erro 500 | ✓ VERIFIED | `sinal.py:39-55` — `_layout_not_found` com "Sinal nao encontrado" e "ID de sinal invalido" |

**Score:** 8/8 truths verified (5 automated + 3 require human confirmation for runtime behavior)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `helpertips/queries.py` | `get_sinal_detalhado` e `calculate_pl_detalhado_por_sinal` | ✓ VERIFIED | Ambas as funções presentes em linhas 768 e 804; substanciais (não stubs) |
| `tests/test_queries.py` | Testes TDD para as novas funções | ✓ VERIFIED | 6 testes na seção Phase 15; `test_get_sinal_detalhado` e 5× `test_calculate_pl_detalhado` |
| `helpertips/pages/sinal.py` | Página de detalhe do sinal | ✓ VERIFIED | 263 linhas; `register_page`, `render_sinal` callback, `_build_detail_layout`, `_layout_not_found` |
| `helpertips/pages/home.py` | Navegação AG Grid + campo `id` no rowData | ✓ VERIFIED | `ver_link` coluna markdown + `"id": sig.get("id")` no rowData |
| `tests/test_sinal_page.py` | Testes estruturais da página de detalhe | ✓ VERIFIED | 4 testes: registro, layout, IDs inválidos |
| `tests/test_dashboard.py` | Testes do callback de navegação | ✓ VERIFIED | `test_rowdata_ver_link_format` + `test_history_rowdata_includes_id` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `helpertips/pages/home.py` | `helpertips/pages/sinal.py` | `ver_link` markdown link `[Ver](/sinal?id=N)` | ✓ WIRED | `home.py:936` — coluna markdown com URL `/sinal?id=N`; desvio do plano (cellClicked → markdown link) |
| `helpertips/pages/sinal.py` | `helpertips/queries.py` | `get_sinal_detalhado` + `calculate_pl_detalhado_por_sinal` | ✓ WIRED | `sinal.py:15-20` importação; `sinal.py:247,258` chamadas no callback |
| `helpertips/pages/sinal.py` | dashboard shell | `dcc.Location(id='sinal-url')` lê `search` | ✓ WIRED | `sinal.py:29` e `sinal.py:233-235` — `Input("sinal-url", "search")` |
| `helpertips/queries.py` | `signals` table | `SELECT ... WHERE s.id = %s` | ✓ WIRED | `queries.py:784-791` — query com LEFT JOIN mercados |
| `helpertips/queries.py` | `validar_complementar` | chamada interna | ✓ WIRED | `queries.py:892` — `validar_complementar(comp["regra_validacao"], placar, resultado)` |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `sinal.py` → `render_sinal` | `sinal` (dict) | `get_sinal_detalhado(conn, signal_id)` → PostgreSQL SELECT | Sim — SQL com `WHERE s.id = %s` | ✓ FLOWING |
| `sinal.py` → `_build_detail_layout` | `pl` (dict) | `calculate_pl_detalhado_por_sinal(sinal, comps_config, ...)` | Sim — cálculo determinístico sobre dados do BD | ✓ FLOWING |
| `sinal.py` → `_layout_not_found` | `signal_id` | parse_qs do URL search | Sim — extrai ID da URL | ✓ FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suite TDD phase 15 (queries) | `pytest tests/test_queries.py -k "detalhado or sinal_detalhado" -q` | 6 passed | ✓ PASS |
| Suite sinal_page (full suite order) | `pytest -x -q` | 224 passed | ✓ PASS |
| Testes sinal_page em isolamento | `pytest tests/test_sinal_page.py -x -q` | 4 FAILED — `PageError: register_page() must be called after app instantiation` | ⚠️ WARN |
| Testes sinal_page após dashboard | `pytest tests/test_dashboard.py tests/test_sinal_page.py -q` | 43 passed | ✓ PASS |

**Nota sobre isolamento de testes:** `test_sinal_page.py` depende de que `test_dashboard.py` seja executado antes para instanciar o app Dash. Na execução normal (`pytest` sem filtros), os arquivos seguem ordem alfabética e `test_dashboard.py` precede `test_sinal_page.py`, portanto a suite completa sempre passa. Porém `pytest tests/test_sinal_page.py` isolado falha. Este é um anti-padrão de acoplamento de testes (Warning), mas não bloqueia o objetivo da fase.

---

### Requirements Coverage

| Requirement | Source Plan | Descrição | Status | Evidência |
|-------------|-------------|-----------|--------|-----------|
| SIG-01 | 15-02-PLAN | Usuário navega do AG Grid para página de detalhe | ✓ SATISFIED | `home.py:735-736,936` — coluna `ver_link` com link markdown `[Ver](/sinal?id=N)` e `cellRenderer: "markdown"` |
| SIG-02 | 15-01-PLAN, 15-02-PLAN | Card da entrada principal com todos os campos | ✓ SATISFIED | `sinal.py:85-119` — card com mercado, placar, odd, stake, resultado, lucro |
| SIG-03 | 15-01-PLAN, 15-02-PLAN | Lista de complementares com breakdown individual | ✓ SATISFIED | `sinal.py:121-181` — tabela numerada com linha por complementar |
| SIG-04 | 15-01-PLAN, 15-02-PLAN | Totais consolidados: investido, retorno, lucro líquido | ✓ SATISFIED | `sinal.py:183-223` — resumo por tipo (Principal / Complementares / TOTAL) |
| SIG-05 | 15-02-PLAN | Botão para voltar ao dashboard | ✓ SATISFIED | `sinal.py:70-71` — `dcc.Link(... href="/")` no header + `sinal.py:52-53` no not_found |
| SIG-06 | 15-01-PLAN, 15-02-PLAN | Tratamento de IDs inexistentes/inválidos | ✓ SATISFIED | `sinal.py:39-55` — `_layout_not_found` com mensagens distintas por caso |

**Discrepância REQUIREMENTS.md:** SIG-01 e SIG-05 aparecem marcados como `[ ]` (Pending) no arquivo `.planning/REQUIREMENTS.md` e na tabela de tracking (linhas 103-108). O código implementa ambos corretamente. O arquivo REQUIREMENTS.md não foi atualizado após a execução do Plan 02 — stale state, não uma lacuna real de implementação.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_sinal_page.py` | 14-77 | Dependência de ordem de execução — falha em isolamento | ⚠️ Warning | Testes passam na suite completa mas falham com `pytest tests/test_sinal_page.py` |
| `.planning/REQUIREMENTS.md` | 17, 21 | Checkboxes `[ ]` desatualizados para SIG-01 e SIG-05 | ℹ️ Info | Documento desatualizado; não afeta código |

---

### Human Verification Required

#### 1. Navegação AG Grid → Página de Detalhe (SIG-01)

**Teste:** Iniciar `python -m helpertips.dashboard`. Na página principal, clicar na célula "Ver" de qualquer linha do histórico de sinais.
**Esperado:** URL muda para `/sinal?id=N` sem recarregar a página inteira. Página de detalhe renderiza com card "Entrada Principal", tabela "Detalhamento por Entrada" e card "Resumo por Tipo de Entrada".
**Por que humano:** Comportamento de navegação client-side com link markdown no AG Grid não é verificável sem browser.

#### 2. Cores por Resultado Visual (SIG-02, SIG-03)

**Teste:** Na página de detalhe de um sinal GREEN, verificar cores na tabela e card principal.
**Esperado:** GREEN exibido em verde (text-success), RED em vermelho (text-danger), N/A em cinza (text-muted). Complementares com "✓ GREEN" em destaque verde.
**Por que humano:** Aparência visual requer renderização no browser.

#### 3. Botão Voltar (SIG-05)

**Teste:** Na página de detalhe, clicar no botão "<- Voltar" no topo ou "Voltar ao Dashboard" na página de erro.
**Esperado:** Retorna ao dashboard em `/` sem reload de página completa.
**Por que humano:** Comportamento de navegação client-side via `dcc.Link(href="/")`.

#### 4. Sinal Inexistente (SIG-06 — runtime)

**Teste:** Com dashboard rodando, acessar `/sinal?id=999999` no browser.
**Esperado:** Exibe "Sinal nao encontrado" com mensagem "O sinal #999999 nao existe ou foi removido." e botão "Voltar ao Dashboard". Nenhum traceback ou erro 500.
**Por que humano:** Requer conexão real com PostgreSQL e servidor rodando.

#### 5. ID Inválido (SIG-06 — runtime)

**Teste:** Acessar `/sinal?id=abc` no browser.
**Esperado:** Exibe "ID de sinal invalido." com botão de volta. Nenhum erro.
**Por que humano:** Verificação da mensagem exata requer browser; testes unitários cobrem logicamente mas não via HTTP.

---

### Gaps Summary

Nenhum gap de implementação identificado. Todos os 8 must-haves foram verificados no código. A fase atingiu seu objetivo.

**Desvio de implementação documentado (não é gap):** O Plan 02 especificava navegação via `cellClicked` callback com `Output("url-nav", "href")`. A implementação optou por link markdown nativo do AG Grid (`cellRenderer: "markdown"`) — abordagem mais robusta e sem JavaScript custom, conforme documentado no SUMMARY. O objetivo SIG-01 é igualmente satisfeito.

**Item de atenção (não bloqueador):** `test_sinal_page.py` é order-dependent — falha em isolamento, passa na suite completa. Recomendado adicionar fixture de app instantiation no `conftest.py` para resolver o acoplamento em fase futura.

---

_Verified: 2026-04-04T20:00:00Z_
_Verifier: Claude (gsd-verifier)_
