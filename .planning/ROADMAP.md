# Roadmap: HelperTips — Futebol Virtual

## Overview

Build a personal betting analytics system in three sequential phases. Phase 1 lays the irreplaceable data foundation: a Telethon listener that captures signals and result edits from the VIP Telegram group, a regex parser that structures them, and a PostgreSQL store that persists them via upsert — all validated with real data before any dashboard is built. Phase 2 delivers the primary user value: a Plotly Dash dashboard answering "are these signals profitable?" with filters, ROI simulation, and signal history. Phase 3 deepens the analytics with dimensional breakdowns, equity curves, and cross-filtering once enough data has accumulated.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Listener pipeline captures signals into PostgreSQL with terminal validation
- [ ] **Phase 2: Core Dashboard** - Plotly Dash dashboard with aggregate stats, filters, ROI simulation, and signal history
- [ ] **Phase 3: Analytics Depth** - Dimensional breakdowns, equity curve, cross-filtering, and parser coverage tracking

## Phase Details

### Phase 1: Foundation
**Goal**: Signals from the VIP Telegram group land correctly in PostgreSQL and the pipeline can be trusted before any dashboard is built
**Depends on**: Nothing (first phase)
**Requirements**: OPER-02, OPER-03, DB-01, DB-02, DB-03, DB-04, PARS-01, PARS-02, PARS-03, PARS-04, PARS-05, PARS-06, PARS-07, LIST-01, LIST-02, LIST-03, LIST-04, LIST-05, TERM-01, TERM-02, TERM-03
**Success Criteria** (what must be TRUE):
  1. Running `python listener.py` connects to the VIP group and prints a startup summary with total signals, greens, reds, and win rate
  2. A new signal from the Telegram group appears as a row in the signals table within seconds of being sent
  3. When a signal message is edited with a result (GREEN/RED), the existing database row is updated without creating a duplicate
  4. The listener can be stopped with Ctrl+C and restarted without losing any previously captured data
  5. A `.env` file holds all credentials; `.session` and `.env` are in `.gitignore` before the first commit
**Plans:** 7 plans

Plans:
- [x] 01-01-PLAN.md — Project bootstrap: .gitignore, .env config validation, DB schema, dependencies
- [x] 01-02-PLAN.md — Signal message parser (TDD): pure-function regex extraction of liga, entrada, horario, resultado, placar
- [x] 01-03-PLAN.md — Store repository layer: upsert_signal with ON CONFLICT, get_stats for terminal summary
- [x] 01-04-PLAN.md — Listener integration: Telethon event handlers, startup summary, graceful shutdown, auto-reconnect
- [x] 01-05-PLAN.md — Reestruturacao em pacote Python: helpertips/ + pyproject.toml + pip install -e .
- [x] 01-06-PLAN.md — Tabela parse_failures + rich terminal output (Panel, Table, RichHandler)
- [x] 01-07-PLAN.md — Fixtures reais do Telegram + ajuste de regex do parser

### Phase 2: Core Dashboard
**Goal**: Users can open a web dashboard and immediately answer "are these signals profitable?" with live data from PostgreSQL
**Depends on**: Phase 1
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07
**Success Criteria** (what must be TRUE):
  1. Opening the dashboard URL shows a card with total signals, greens, reds, win rate, and percentages drawn from the live database
  2. Selecting a liga from the filter updates all stats and charts to show only signals from that league
  3. Selecting an entrada from the filter updates all stats to show only signals of that bet type
  4. The ROI simulation card shows profit/loss for a configurable fixed stake applied to all filtered signals
  5. The signal history table lists past signals with pagination and pending signals (no result yet) are visually distinct
**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md — Dash dependencies + queries.py data layer (filtered stats, ROI calculation, signal history)
- [x] 02-02-PLAN.md — Dashboard layout and reactive callbacks (dark theme, KPI cards, filters, charts, AG Grid)
- [ ] 02-03-PLAN.md — Visual and functional verification checkpoint
**UI hint**: yes

### Phase 02.1: Market Config (INSERTED)

**Goal:** Implementar configuracao de mercados (principal + complementares) com calculo de stakes Martingale por tentativa, percentuais configuraveis via tabela PostgreSQL, e validacao independente de GREEN/RED por entrada complementar baseada no placar do sinal principal. Atualizar dashboard com cards separados de ROI principal e complementares.
**Requirements**: MKT-01, MKT-02, MKT-03, MKT-04, MKT-05, MKT-06, MKT-07
**Depends on:** Phase 2
**Canonical refs:** `/Users/luciano/Downloads/documentacao_entradas_mercado.md`
**Success Criteria** (what must be TRUE):
  1. ensure_schema() cria tabelas `mercados` e `complementares` no PostgreSQL com seed data de 2 mercados e 14 complementares
  2. Validacao de complementares por placar funciona: dado placar "3-2" e regra "over_3_5", retorna GREEN (total=5 > 3.5)
  3. Sinal RED (sem placar) faz todas complementares retornarem RED automaticamente
  4. Card ROI Complementares no dashboard mostra tabela de breakdown por mercado quando entrada filtrada
  5. Card mostra alerta "Selecione uma entrada" quando sem filtro de entrada
**Plans:** 2/4 plans executed

Plans:
- [x] 02.1-01-PLAN.md — Schema extension: tabelas mercados + complementares + seed data em ensure_schema()
- [x] 02.1-02-PLAN.md — Validacao de complementares por placar (TDD): _parse_placar, _REGRA_VALIDATORS, validar_complementar
- [ ] 02.1-03-PLAN.md — ROI complementares (TDD): get_complementares_config + calculate_roi_complementares
- [ ] 02.1-04-PLAN.md — Dashboard card ROI Complementares + verificacao visual

### Phase 3: Analytics Depth
**Goal**: Users can identify which leagues, bet types, time slots, and days of the week produce the best results, and track bankroll growth over time
**Depends on**: Phase 2
**Requirements**: ANAL-01, ANAL-02, ANAL-03, ANAL-04, ANAL-05, ANAL-06, ANAL-07, ANAL-08, OPER-01
**Success Criteria** (what must be TRUE):
  1. A heatmap shows win rate by time of day and a bar chart shows win rate by day of the week, both updating with active filters
  2. Applying combined filters (liga + entrada + period) produces a cross-dimensional breakdown of win rate and signal count
  3. The equity curve chart shows cumulative bankroll over time with a fixed stake, revealing winning and losing streaks visually
  4. A Gale analysis panel shows win rate at gale levels 1, 2, and 3, and a streak tracker shows the current and longest win/loss streaks
  5. The dashboard header or footer displays the parser coverage rate (percentage of messages successfully parsed)
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 2.1 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 7/7 | Complete |  |
| 2. Core Dashboard | 2/3 | In Progress | - |
| 2.1 Market Config | 0/4 | Not started | - |
| 3. Analytics Depth | 0/? | Not started | - |
