---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Configurações de Mercado + Dashboard Ajustes
status: verifying
stopped_at: Completed 16-01-PLAN.md
last_updated: "2026-04-04T22:28:08.093Z"
last_activity: 2026-04-04
progress:
  total_phases: 11
  completed_phases: 8
  total_plans: 14
  completed_plans: 14
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-04)

**Core value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.
**Current focus:** Phase 16 — navega-o-schema-db

## Current Position

Phase: 16 (navega-o-schema-db) — EXECUTING
Plan: 1 of 1
Status: Phase complete — ready for verification
Last activity: 2026-04-04

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity (v1.3):**

- Total plans completed: 3 (Phase 14: 1, Phase 15: 2)
- Average duration: ~10 min/plan

**Velocity (v1.2 baseline):**

- Total plans completed: 10 (2 plans × 5 phases)
- Average duration: ~10 min/plan

## Accumulated Context

### Decisions

Decisions arquivadas em PROJECT.md Key Decisions table.

- [Phase 14]: app.config em Dash 4.1.0 é dict — usar app.config.get() em testes MPA
- [Phase 14]: dash.register_page duplo registro em testes — usar >= 1 em vez de == 1
- [Phase 15]: placar=None → complementares N/A com lucro=0 e investido=0
- [Phase 15]: stake_efetiva adicionada ao dict principal para expor winning_stake do Gale ao chamador
- [Phase 16-navega-o-schema-db]: dbc.NavLink active='exact' destaca tab ativa nativamente sem callback — funciona com Dash Pages + dbc 2.x
- [Phase 16-navega-o-schema-db]: ADD COLUMN IF NOT EXISTS para migrations idemptentes em ensure_schema — padrao Phase 16

### Pending Todos

- [ ] Obter o Group ID do grupo "Ambas Marcam" no Telegram para configurar TELEGRAM_GROUP_IDS

### Blockers/Concerns

- Phase 16: Migration SQL deve ser idempotente — tabelas mercados e complementares existem, apenas adicionar colunas novas (stake_base, fator_progressao, max_tentativas em mercados)
- Phase 17: Preview de stakes T1-T4 em tempo real exige callback Dash sem round-trip ao banco — lógica de cálculo deve ser função pura testável
- Phase 18: Listener usa psycopg2 sync — leitura de config no handler assíncrono deve usar asyncio.to_thread() para não bloquear event loop

## Session Continuity

Last session: 2026-04-04T22:28:08.090Z
Stopped at: Completed 16-01-PLAN.md
Resume file: None
