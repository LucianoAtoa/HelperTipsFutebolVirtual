# Phase 10: Lógica Financeira - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Cada sinal gera entradas complementares com P&L calculado corretamente por mercado e tentativa. Cálculo on-the-fly via funções Python puras (sem materialização no banco). Estende as funções existentes em `queries.py` para suportar queries por mercado separado (Over 2.5 vs Ambas Marcam) necessárias para o dashboard redesign (Phases 11-13).

</domain>

<decisions>
## Implementation Decisions

### Armazenamento de P&L
- **D-01:** P&L permanece como cálculo on-the-fly (puro Python, sem tabela nova). Stake e gale_on são parâmetros dinâmicos do dashboard — materializar valores absolutos seria ineficaz pois qualquer mudança de stake invalidaria toda a tabela.
- **D-02:** Estender `calculate_roi_complementares()` e `calculate_equity_curve()` para suportar breakdown por mercado (principal, complementar, total) — 3 linhas na equity curve.
- **D-03:** Volume baixo (~dezenas de sinais/dia, single user) não justifica materialização. Se volume crescer, revisitar como otimização futura.

### Stake Base
- **D-04:** Stake base continua como input do dashboard (status quo). Sem persistência no banco, sem variável .env adicional.
- **D-05:** Dashboard Phases 11-13 usarão o mesmo input com filtros globais — stake como parâmetro de simulação, não dado fixo.

### Trigger de Cálculo
- **D-06:** Cálculo acontece on-the-fly no dashboard, nos callbacks do Dash. Sem trigger no listener, sem batch job.
- **D-07:** `calculate_roi_complementares()` já existe e funciona. Estender callbacks sem schema change nem migration na EC2.

### Regras de Complementares por Mercado
- **D-08:** Mesmos 7 slugs de complementares para Over 2.5 e Ambas Marcam (status quo). Seeds e validators já corretos.
- **D-09:** Percentuais já diferem por mercado no banco: Over 2.5 (20%, 1%, 10%, 1%, 1%, 1%, 1%) vs Ambas Marcam (10%, 1%, 5%, 1%, 1%, 1%, 1%).
- **D-10:** Redesenhar complementares de Ambas Marcam é decisão estratégica de apostas — backlog quando houver dados de produção suficientes para comparar rentabilidade.

### Claude's Discretion
- Organização interna das funções (refatorar vs estender existentes)
- Nomes de parâmetros e assinaturas das funções estendidas
- Estratégia de teste (quais cenários de P&L cobrir)
- Se queries.py deve ser dividido em módulos menores

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Lógica Financeira Existente
- `helpertips/queries.py` — `calculate_roi()`, `calculate_roi_complementares()`, `validar_complementar()`, `get_complementares_config()`, `calculate_equity_curve()`, `calculate_streaks()`, `_REGRA_VALIDATORS`
- `helpertips/store.py` — `upsert_signal()`, `_resolve_mercado_id()`, `ENTRADA_PARA_MERCADO_ID`

### Schema e Seeds
- `helpertips/db.py` — `ensure_schema()` com tabelas `mercados`, `complementares`, seeds de percentuais e odds de referência por mercado

### Dashboard Atual
- `helpertips/dashboard.py` — Callbacks existentes que usam as funções de queries.py

### Requisitos
- `.planning/REQUIREMENTS.md` §FIN-01, §FIN-02, §FIN-03 — Requisitos específicos desta fase
- `.planning/REQUIREMENTS.md` §DASH-01 a §DASH-07 — Dashboard redesign que consumirá os dados financeiros (Phases 11-13)

### Contexto da Phase 9
- `.planning/phases/09-listener-multi-grupo/09-CONTEXT.md` — Decisões de multi-grupo e mercado_id que alimentam Phase 10

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `calculate_roi_complementares()`: Já calcula P&L de complementares com Gale — retorna `profit`, `roi_pct`, `total_invested`, `por_mercado`
- `validar_complementar()`: Já determina GREEN/RED por regra de placar — 7 validators em `_REGRA_VALIDATORS`
- `get_complementares_config()`: Já lê config do banco com JOIN mercados/complementares
- `calculate_equity_curve()`: Já gera curva para Stake Fixa e Gale — precisa de versão para complementares
- `calculate_roi()`: P&L do mercado principal com Gale — funcional e testado
- `_build_where()`: Builder de WHERE clause parameterizado com filtros de liga/entrada/data

### Established Patterns
- Funções puras Python sem acesso ao banco para cálculos de ROI/P&L
- Queries SQL retornam list[dict] que alimentam funções puras
- Dash callbacks chamam queries → funções puras → renderizam gráficos
- `asyncio.to_thread()` para wrapping de psycopg2 sync dentro do event loop async

### Integration Points
- Dashboard callbacks precisarão filtrar por `mercado_id` (JOIN com signals) para breakdown por mercado
- `_build_where()` precisa suportar filtro por mercado (além de liga/entrada/data)
- Equity curve com 3 linhas: reusar `calculate_equity_curve()` para principal, criar análoga para complementares, somar para total
- `get_complementares_config()` já recebe `mercado_slug` — pronto para uso diferenciado

</code_context>

<specifics>
## Specific Ideas

- Phase 10 é essencialmente estender/refatorar funções existentes de queries.py para suportar o dashboard redesign, não criar infraestrutura nova
- As funções `calculate_roi_complementares` e `calculate_equity_curve` são o core — precisam de versões que retornem breakdown separado (principal vs complementar vs total)
- `_build_where()` precisa de filtro por mercado para que Phases 11-13 possam filtrar "Todos / Over 2.5 / Ambas Marcam"
- Testes devem cobrir cenários de P&L: GREEN T1, GREEN T2 (Gale), RED T4, mix de mercados

</specifics>

<deferred>
## Deferred Ideas

- Materialização de P&L no banco como otimização de performance (se volume crescer significativamente)
- Redesenho dos complementares de Ambas Marcam com mercados específicos (resultado exato, handicap) — backlog para quando houver dados de produção
- Stake diferenciada por mercado (coluna `stake_base` na tabela mercados) — revisitar se necessário

</deferred>

---

*Phase: 10-l-gica-financeira*
*Context gathered: 2026-04-04*
