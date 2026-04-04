# Phase 11: Dashboard Fundacao - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 11-Dashboard Fundacao
**Areas discussed:** Estrategia de Reescrita, Componente de Filtro de Periodo, Posicionamento do Stake, Escopo dos KPIs
**Mode:** --auto (all decisions auto-selected from advisor recommendations)

---

## Estrategia de Reescrita

| Option | Description | Selected |
|--------|-------------|----------|
| Refatoracao incremental | Preservar layout existente, adicionar filtros globais e KPIs ao lado. Zero downtime mas risco de conflito de callback IDs e dois sistemas de filtro. | |
| Reescrita do zero nas fases 11-13 | Substituir app.layout, cada fase adiciona secoes novas. Perde analytics tabs temporariamente. | auto |

**User's choice:** [auto] Reescrita do zero nas fases 11-13
**Notes:** Ferramenta pessoal sem SLA, fases em sequencia continua, evita conflito de callback IDs e dois sistemas de state paralelos. Helpers reutilizaveis preservados seletivamente.

---

## Componente de Filtro de Periodo

| Option | Description | Selected |
|--------|-------------|----------|
| dbc.RadioItems com btn-check | Visual de botoes segmentados, value nativo no callback, requer CSS override para DARKLY. | auto |
| dbc.ButtonGroup | Total controle de estado, mais verboso, callback extra de estado ativo. | |
| dcc.Dropdown | Zero CSS, familiar, mas inconsistencia UX para filtro temporal. | |
| dbc.Tabs | Visual limpo, mas semantica errada (tabs separam conteudo, nao filtros). | |

**User's choice:** [auto] dbc.RadioItems com btn-check
**Notes:** Padrao amplamente adotado em dashboards analytics. 3-5 linhas de CSS override para contraste no DARKLY. DatePickerRange condicional para "Personalizado" via dbc.Collapse.

---

## Posicionamento do Stake

| Option | Description | Selected |
|--------|-------------|----------|
| Barra de filtros globais | Stake sempre visivel, mas confusao semantica filtro vs parametro de simulacao. | |
| Card separado abaixo dos filtros | Separacao clara filtro-de-dado vs parametro-de-simulacao, fluxo natural. | auto |
| Config panel colapsavel | Acessivel mas escondido por default, estado extra para gerenciar. | |

**User's choice:** [auto] Card de configuracao separado abaixo dos filtros
**Notes:** Stake nao e filtro — nao remove registros, muda calculo. Card separado preserva fluxo: filtrar dados → configurar simulacao → ler resultados.

---

## Escopo dos KPIs

| Option | Description | Selected |
|--------|-------------|----------|
| Substituir completamente (6 novos) | Layout limpo, perde Greens/Reds absolutos. | |
| Duas rows (5 atuais + nova row) | 10+ cards, density excessiva, scroll. | |
| Row unica hibrida (6 KPIs) | Total, Win Rate%, P&L total, ROI, Streaks. Equilibrado. | auto |

**User's choice:** [auto] Row unica hibrida com 6 KPIs
**Notes:** Greens/Reds absolutos implcitos no Win Rate. Alinhado ao DASH-02.

### Sub-decisao: P&L breakdown no card

| Option | Description | Selected |
|--------|-------------|----------|
| P&L com breakdown (principal/complementar/total) | Maximo info, card visualmente denso. | |
| P&L so total | Consistencia visual, breakdown na equity curve Phase 13. | auto |

**User's choice:** [auto] P&L so total
**Notes:** Breakdown principal/complementar/total e entregue naturalmente pela equity curve de 3 linhas na Phase 13.

---

## Claude's Discretion

- Organizacao interna do dashboard.py
- CSS override para contraste RadioItems no DARKLY
- Preservacao ou nao do AG Grid nesta fase
- Nomes de IDs dos componentes
- Estrategia de teste

## Deferred Ideas

- Analytics tabs (heatmap, equity, gale, streaks, volume) — Phases 12-13
- Toggle percentual/quantidade/R$ — Phase 12
- Donut chart gale — Phase 13
- Barras empilhadas P&L por liga — Phase 13
