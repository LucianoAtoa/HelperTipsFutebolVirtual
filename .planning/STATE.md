---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Configurações de Mercado + Dashboard Ajustes
status: roadmap ready
stopped_at: null
last_updated: "2026-04-04"
last_activity: 2026-04-04
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-04)

**Core value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.
**Current focus:** v1.4 — Phase 16 ready to plan

## Current Position

Phase: 16 of 19 v1.4 (Navegação + Schema DB)
Plan: —
Status: Ready to plan
Last activity: 2026-04-04 — Roadmap v1.4 criado (Phases 16-19)

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

### Pending Todos

- [ ] Obter o Group ID do grupo "Ambas Marcam" no Telegram para configurar TELEGRAM_GROUP_IDS

### Blockers/Concerns

- Phase 16: Migration SQL deve ser idempotente — tabelas mercados e complementares existem, apenas adicionar colunas novas (stake_base, fator_progressao, max_tentativas em mercados)
- Phase 17: Preview de stakes T1-T4 em tempo real exige callback Dash sem round-trip ao banco — lógica de cálculo deve ser função pura testável
- Phase 18: Listener usa psycopg2 sync — leitura de config no handler assíncrono deve usar asyncio.to_thread() para não bloquear event loop

## Session Continuity

Last session: 2026-04-04
Stopped at: Roadmap v1.4 criado — Phases 16-19 definidas
Resume file: None
