# Phase 3: Analytics Depth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 03-analytics-depth
**Areas discussed:** Organizacao dos graficos, Curva de equity e streaks, Analise de Gale por nivel, Cobertura do parser

---

## Organizacao dos Graficos

| Option | Description | Selected |
|--------|-------------|----------|
| Abas (dbc.Tabs) | Agrupa por tema analitico. KPIs/filtros/ROI ficam fixos no topo, graficos novos em abas abaixo. Lazy render. | ✓ |
| Tudo com scroll | Pagina unica, todos os graficos visiveis rolando. Simples mas longo. | |
| Grid denso 2x3 | Graficos menores em grid. Alta densidade, mas heatmap e equity curve sofrem. | |

**User's choice:** Abas (dbc.Tabs) (Recomendado)
**Notes:** Advisor research recomendou abas com 3 categorias tematicas. Usuario concordou.

---

## Curva de Equity e Streaks

| Option | Description | Selected |
|--------|-------------|----------|
| Duas linhas + pontos coloridos | Eixo X por sinal cronologico, duas linhas (Stake Fixa azul + Gale laranja), pontos verde/vermelho por resultado, reset automatico ao filtro ativo. | ✓ |
| Linha unica com toggle | Uma linha so (Stake Fixa OU Gale, controlado pelo toggle existente). Mais limpo, menos comparativo. | |
| Duas linhas sem marcadores | Comparacao Fixa vs Gale mas sem pontos coloridos nos resultados individuais. Curva mais limpa. | |

**User's choice:** Duas linhas + pontos coloridos (Recomendado)
**Notes:** Advisor detalhou 4 sub-decisoes (eixo X, linhas, marcadores, reset). Usuario aceitou pacote completo recomendado.

---

## Analise de Gale por Nivel

| Option | Description | Selected |
|--------|-------------|----------|
| Card composto | Barras horizontais por tentativa (1a-4a) com taxa de GREEN + metricas inline de custo acumulado e perda media antes da recuperacao. | ✓ |
| Tabela simples (dbc.Table) | Tabela com linhas por tentativa: taxa GREEN, custo acumulado, impacto financeiro. Compacto e direto. | |
| Barras empilhadas | Grafico mostrando proporcao de sinais resolvidos em cada tentativa. Visual, mas nao mostra custo. | |

**User's choice:** Card composto (Recomendado)
**Notes:** Advisor identificou 3 perguntas-chave que o card composto responde num unico componente.

---

## Cobertura do Parser

| Option | Description | Selected |
|--------|-------------|----------|
| Badge no header + modal | Badge colorido (verde/amarelo/vermelho por threshold) no header. Clicando abre modal com tabela de parse_failures (raw_text, reason, data). | ✓ |
| KPI card na row existente | 6o card ao lado dos KPIs de aposta. Simples, mas mistura metrica operacional com metricas de negocio. | |
| Footer simples | Texto no rodape: 'Parser: 98.3% cobertura (12 falhas)'. Discreto. | |

**User's choice:** Badge no header + modal (Recomendado)
**Notes:** Advisor destacou separacao semantica: cobertura e metrica operacional, nao de aposta.

---

## Claude's Discretion

- Agrupamento exato das abas
- Posicao dos graficos existentes (manter fixos ou mover)
- Cores exatas alem do definido
- Formato das anotacoes de streak
- Nivel de detalhe do cross-dimensional breakdown

## Deferred Ideas

None — discussion stayed within phase scope
