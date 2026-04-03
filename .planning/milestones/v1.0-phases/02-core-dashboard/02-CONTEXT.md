# Phase 2: Core Dashboard - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Dashboard web com Plotly Dash que responde "esses sinais são lucrativos?" usando dados live do PostgreSQL. Inclui: cards de KPI, simulação de ROI com Gale, filtros interativos por liga/entrada/período, e tabela de histórico com AG Grid. Análises avançadas (heatmaps, streaks, equity curve) são Fase 3.

</domain>

<decisions>
## Implementation Decisions

### Layout e Visual
- **D-01:** Tema escuro fixo usando `dbc.themes.DARKLY` — visual de trading, sem toggle claro/escuro
- **D-02:** Template Plotly `plotly_dark` em todos os gráficos para consistência com o tema
- **D-03:** Layout vertical: KPI cards no topo → filtros → gráficos em grid 2 colunas → tabela de histórico na base
- **D-04:** Responsivo via Bootstrap 5 grid (`dbc.Row`/`dbc.Col`)

### Simulação de ROI
- **D-05:** Stake fixa configurável (default R$ 10) + odd configurável (default 1.90, típico Over 2.5 virtual)
- **D-06:** Toggle Gale (martingale por tentativa) — stake dobra a cada tentativa (2x, 4x, 8x), campo `tentativa` já existe no banco
- **D-07:** Mostrar profit/loss acumulado — GREEN na tentativa 1 vs tentativa 4 tem custo completamente diferente com Gale
- **D-08:** Dois modos no card: "Stake Fixa" (sem Gale) e "Com Gale" (toggle), para o usuário comparar exposição real

### Filtros
- **D-09:** Dropdowns horizontais no topo da página, reativos (sem botão Apply)
- **D-10:** Filtros compostos: liga + entrada simultâneos via callback multi-Input do Dash
- **D-11:** Botão Reset para limpar todos os filtros de uma vez
- **D-12:** DatePickerRange para filtrar por período de datas (mesmo layout horizontal)

### Tabela de Histórico
- **D-13:** Dash AG Grid (dependência `dash-ag-grid`) — substituto oficial do DataTable, preparado para Dash 5
- **D-14:** 20 linhas por página, ordenação padrão por `received_at DESC`
- **D-15:** Todas as 6 colunas visíveis: liga, entrada, horario, resultado, placar, tentativa
- **D-16:** Sinais pendentes (resultado vazio) destacados com cor diferente na linha inteira via `getRowStyle`
- **D-17:** Sort interativo por coluna habilitado nativamente

### Claude's Discretion
- Cores exatas dos KPI cards (além de verde para GREEN, vermelho para RED)
- Formato dos números no ROI (R$ com 2 casas, percentual com 1 casa)
- Largura relativa das colunas no AG Grid
- Posição exata do DatePickerRange no layout de filtros
- Gráficos específicos para a Fase 2 (barras, linhas, etc — desde que cubram os success criteria)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Projeto
- `CLAUDE.md` — Stack definida (Dash 4.1.0, dash-bootstrap-components 2.x, psycopg2-binary), processos separados listener/dashboard
- `.planning/REQUIREMENTS.md` — Requisitos DASH-01..07
- `.planning/ROADMAP.md` — Phase 2 success criteria e dependências

### Fase anterior
- `.planning/phases/01-foundation/01-CONTEXT.md` — Decisões da Fase 1 (estrutura do package, schema do banco, campos da tabela signals)
- `helpertips/db.py` — Schema atual: signals (liga, entrada, horario, resultado, placar, tentativa, dia_semana, received_at, updated_at)
- `helpertips/store.py` — Funções `get_stats()` e `upsert_signal()` disponíveis para reuso

### Documentação de sinais
- `/Users/luciano/Downloads/documentacao_sinais.md` — Formato real das mensagens, ciclo de vida do sinal, regras de validação

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `helpertips/store.py:get_stats()` — já retorna dict com total, greens, reds, pending, coverage, parse_failures
- `helpertips/db.py:get_connection()` — conexão PostgreSQL pronta para reuso
- `helpertips/db.py:ensure_schema()` — schema com tabela signals completa
- Package `helpertips/` com `pyproject.toml` — dashboard pode ser novo módulo no mesmo package

### Established Patterns
- psycopg2 sync para queries (sem async necessário no dashboard)
- dotenv para configuração
- rich para terminal (não se aplica ao dashboard, mas mostra preferência por visual elaborado)

### Integration Points
- Dashboard roda como processo separado do listener (CLAUDE.md constraint)
- Conecta no mesmo PostgreSQL via `get_connection()`
- Pode reusar `get_stats()` para KPI cards ou criar queries específicas para filtros

</code_context>

<specifics>
## Specific Ideas

- Odd de 1.90 é o valor típico de Over 2.5 na Bet365 futebol virtual — default sensato
- Gale é relevante porque o grupo usa 4 tentativas por sinal — exposição real varia drasticamente
- Tema DARKLY combina com o contexto de apostas/trading — visual profissional
- AG Grid já prepara para Dash 5.0 e escala se volume de sinais crescer

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-core-dashboard*
*Context gathered: 2026-04-03*
