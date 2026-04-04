---
phase: 15-p-gina-de-detalhe-do-sinal
plan: 02
subsystem: dashboard
tags: [dash, pages, sinal, navegacao, ag-grid, layout]

# Dependency graph
requires:
  - phase: 15-p-gina-de-detalhe-do-sinal
    plan: 01
    provides: get_sinal_detalhado, calculate_pl_detalhado_por_sinal
---

## Summary

Criada página de detalhe do sinal (`pages/sinal.py`) com layout completo e navegação via link markdown no AG Grid.

## What was built

- **Página `/sinal?id=N`**: layout com card principal (mercado, placar, odd, stake, resultado, lucro), tabela de detalhamento numerada por entrada (#1 principal, #2+ complementares com destaque ✓ GREEN), e resumo por tipo (Principal vs Complementares vs Total)
- **Navegação AG Grid**: coluna "Ver" com link markdown `[Ver](/sinal?id=N)` — navegação direta sem callback
- **Tratamento de erros**: IDs inexistentes/inválidos exibem mensagem amigável
- **Botão Voltar**: retorna ao dashboard (`/`)

## Key files

### Created
- `helpertips/pages/sinal.py` — página de detalhe com register_page, render_sinal callback, layout helpers
- `tests/test_sinal_page.py` — testes estruturais (registro, layout, IDs inválidos)

### Modified
- `helpertips/pages/home.py` — campo `id` e `ver_link` no rowData, coluna markdown no AG Grid
- `helpertips/queries.py` — campo `odd` adicionado ao retorno de calculate_pl_detalhado_por_sinal
- `tests/test_dashboard.py` — testes de navegação atualizados para link markdown

## Deviations from plan

1. **Navegação**: plano usava `cellClicked` callback → implementado como link markdown nativo do AG Grid (mais confiável, sem JS custom)
2. **Layout enriquecido**: adicionado placar no card principal, tabela numerada por entrada com destaque GREEN, e resumo por tipo — não previstos no plano original mas solicitados pelo usuário durante verificação visual

## Verification

- 224 testes passando (suite completa)
- Verificação visual aprovada pelo usuário

## Self-Check: PASSED
