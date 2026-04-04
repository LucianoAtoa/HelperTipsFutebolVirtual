---
phase: 12-dashboard-mercados-e-performance
verified: 2026-04-04T18:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 12: Dashboard Mercados e Performance — Verification Report

**Phase Goal:** Usuário visualiza a configuração ativa dos mercados e analisa P&L por entrada em detalhe
**Verified:** 2026-04-04
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `_calcular_stakes_gale` retorna T1=stake*pct, T2=T1*2, T3=T1*4, T4=T1*8 | VERIFIED | dashboard.py L77-86; spot-check confirmado: (100, 0.20) → (20,40,80,160) |
| 2 | `_agregar_por_entrada` agrupa sinais por entrada com greens, reds, investido, lucro, taxa, roi | VERIFIED | dashboard.py L89-126; spot-check: 3 rows → 2 grupos com chaves corretas |
| 3 | `_get_colunas_visiveis` retorna colunas corretas para cada modo (pct, qty, pl) | VERIFIED | dashboard.py L136-145; spot-check confirmado para os 3 modos |
| 4 | `_build_config_card_mercado` retorna `dbc.Card` com header e tabela de complementares | VERIFIED | dashboard.py L154-182; spot-check: isinstance(card, dbc.Card) == True |
| 5 | `_build_performance_section` retorna DataTable com `style_data_conditional` para cores | VERIFIED | dashboard.py L197-305; `style_data_conditional` com filtros lucro>0/roi>0 em L293-297 |
| 6 | Painel de configuração mostra principal e tabela de complementares com stakes T1-T4 | VERIFIED | `_build_config_mercados_section` wired como Output no callback master (L540, L660) |
| 7 | Toggle Percentual/Quantidade/P&L muda colunas da tabela de performance | VERIFIED | `Input("perf-toggle-view", "value")` (L550) → `_get_colunas_visiveis(toggle_mode)` (L279) |
| 8 | Tabela de performance exibe dados para cada entrada com visão geral e por mercado | VERIFIED | `_build_performance_section` branches: entrada=None usa `_agregar_por_entrada`; entrada selecionada usa `calculate_roi`+`calculate_roi_complementares` |
| 9 | Layout segue ordem D-09: Config Mercados → Performance → Phase13 placeholder → AG Grid histórico | VERIFIED | layout L447→L470→L472: config-mercados-container, perf-table, phase13-placeholder antes do history-table |

**Score:** 9/9 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `helpertips/dashboard.py` | Funções helper puras + builders + callback estendido | VERIFIED | Contém todas as funções: `_calcular_stakes_gale`, `_agregar_por_entrada`, `_get_colunas_visiveis`, `_build_config_card_mercado`, `_build_config_mercados_section`, `_build_performance_section`, `MERCADOS_CONFIG`, `COLUNAS_PCT/QTY/PL` |
| `tests/test_dashboard.py` | Testes TDD cobrindo helpers e builders | VERIFIED | 6 novos testes: `test_config_stakes_calculo`, `test_agregar_por_entrada_visao_geral`, `test_agregar_por_entrada_vazio`, `test_performance_toggle_colunas`, `test_build_config_card_mercado`, `test_layout_has_phase12_component_ids` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_dashboard.py` | `helpertips/dashboard.py` | `from helpertips.dashboard import _calcular_stakes_gale` | WIRED | Import com try/except; `_HAS_STAKES`, `_HAS_AGREGAR`, `_HAS_COLUNAS` guards |
| `update_dashboard` (callback) | `get_mercado_config` (queries.py) | chamada dentro do callback master | WIRED | L41 (import) + L187 + L256 (uso em `_build_config_mercados_section` e `_build_performance_section`) |
| `update_dashboard` (callback) | `get_signals_com_placar` (queries.py) | chamada adicional para dados de P&L | WIRED | L44 (import) + L251 (uso na visão geral de `_build_performance_section`) |
| `config-mercados-container` | `update_dashboard` | `Output("config-mercados-container", "children")` | WIRED | L540 (Output) + L660 (`config_section = _build_config_mercados_section(conn, stake)`) + L682 (return) |
| `perf-table` | `update_dashboard` | `Output("perf-table", "children")` | WIRED | L541 (Output) + L663 (`perf_section = _build_performance_section(...)`) + L683 (return) |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_build_config_mercados_section` | `config`, `comps` | `get_mercado_config(conn, slug)` + `get_complementares_config(conn, slug)` — DB queries via psycopg2 | Sim — queries reais ao banco PostgreSQL | FLOWING |
| `_build_performance_section` (visão geral) | `pl_lista` | `get_signals_com_placar(conn, ...)` → `calculate_pl_por_entrada(...)` → `_agregar_por_entrada(...)` | Sim — pipeline completo de dados reais | FLOWING |
| `_build_performance_section` (visão por mercado) | `roi_princ`, `roi_comp` | `calculate_roi(history, ...)` + `calculate_roi_complementares(history, comp_config, ...)` | Sim — history vem de `get_signal_history` já carregado no callback | FLOWING |
| `perf-toggle-view` | `toggle_mode` | `Input("perf-toggle-view", "value")` — estado da UI | Sim — valor do RadioItems passado diretamente para `_get_colunas_visiveis` | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `_calcular_stakes_gale(100.0, 0.20)` retorna (20,40,80,160) | `python3 -c "from helpertips.dashboard import _calcular_stakes_gale; print(_calcular_stakes_gale(100.0, 0.20))"` | `(20.0, 40.0, 80.0, 160.0)` | PASS |
| `_agregar_por_entrada` retorna 2 grupos com campos corretos | spot-check via python3 | 2 grupos, Over 2.5 (greens=1,reds=1), Ambas Marcam (greens=1,reds=0), todas as chaves presentes | PASS |
| `_get_colunas_visiveis` retorna colunas corretas por modo | spot-check via python3 | pct: taxa_green/taxa_red/roi; qty: greens/reds/total; pl: investido/retorno/lucro/roi | PASS |
| `_build_config_card_mercado` retorna `dbc.Card` válido | `python3 -c "isinstance(card, dbc.Card)"` | `True` | PASS |
| Suite completa de testes verde | `python3 -m pytest tests/ -x -q` | `190 passed in 1.25s` | PASS |
| Módulo importa sem erros | `python3 -c "from helpertips.dashboard import _build_config_mercados_section, _build_performance_section; print('OK')"` | `OK` | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DASH-03 | 12-01-PLAN + 12-02-PLAN | Seção configuração de mercados: painel read-only com principal (odd, stake, progressão) e tabela complementares com stakes T1-T4 | SATISFIED | `_build_config_card_mercado` + `_build_config_mercados_section` wired como Output do callback master; T1-T4 calculados via `_calcular_stakes_gale`; reativos ao `stake-input` |
| DASH-04 | 12-01-PLAN + 12-02-PLAN | Seção performance das entradas: tabela P&L por mercado com toggle percentual/quantidade/R$ e visão geral vs por mercado | SATISFIED | `_build_performance_section` com `dash_table.DataTable`, `style_data_conditional` para cores, `_get_colunas_visiveis` para toggle, visão geral via `_agregar_por_entrada` e visão por mercado via `calculate_roi`+`calculate_roi_complementares` |

Sem requisitos órfãos — apenas DASH-03 e DASH-04 estão mapeados para Phase 12 em REQUIREMENTS.md (L75-76).

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| Nenhum | — | Nenhum padrão problemático encontrado | — | — |

Notas: ocorrências de `placeholder` em dashboard.py (L376, L377, L394, L404) são atributos HTML `placeholder` de campos de formulário (dbc.Input, dcc.Dropdown) — não são stubs de implementação.

`html.Div(id="phase13-placeholder")` é um container vazio intencional para Phase 13, não uma implementação incompleta da Phase 12.

---

## Human Verification Required

### 1. Verificação visual — Cards de Config Mercados

**Test:** Iniciar o dashboard com `python3 -m helpertips.dashboard`, abrir http://localhost:8050, verificar seção "Configuração dos Mercados"
**Expected:** 2 cards (Over 2.5, Ambas Marcam), cada um com header exibindo odd ref + stake base + progressão 1x 2x 4x 8x e tabela com colunas Complementar, %, Odd Ref, T1, T2, T3, T4. Ao alterar Stake no card de simulação, os valores T1-T4 devem atualizar reativamente.
**Why human:** Layout e reatividade visual não podem ser verificados programaticamente sem browser.

### 2. Verificação visual — Toggle de Performance

**Test:** No dashboard aberto, clicar nos 3 botões do toggle (Percentual / Quantidade / P&L)
**Expected:** Colunas da tabela mudam corretamente para cada modo; valores P&L positivos em verde, negativos em vermelho.
**Why human:** Rendering condicional de colunas e cores requer inspeção visual no browser.

### 3. Verificação visual — Visão por Mercado

**Test:** Selecionar "Over 2.5" no dropdown de mercado do filtro global
**Expected:** Tabela de performance exibe linhas separadas para "Over 2.5 (Principal)" e uma linha por complementar configurado. Ao selecionar "Todos", tabela volta a agregar por entrada.
**Why human:** Comportamento de filtro + dinâmica de dados do banco requer dados reais e inspeção visual.

---

## Gaps Summary

Nenhum gap encontrado. Todos os must-haves de ambos os planos foram verificados e passaram nos 4 níveis de verificação (existência, substância, wiring, data-flow). A suite completa de testes (190) está verde.

---

_Verified: 2026-04-04_
_Verifier: Claude (gsd-verifier)_
