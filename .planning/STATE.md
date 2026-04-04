---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Multi-Market Analytics
status: verifying
stopped_at: Phase 11 context gathered
last_updated: "2026-04-04T14:35:44.115Z"
last_activity: 2026-04-04
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 4
  completed_plans: 4
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-04)

**Core value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.
**Current focus:** Phase 10 — Lógica Financeira

## Current Position

Phase: 11
Plan: Not started
Status: Phase complete — ready for verification
Last activity: 2026-04-04

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity (v1.0 baseline):**

- Total plans completed: 18
- Average duration: ~8 min/plan
- Total execution time: ~2.5 hours

**Velocity (v1.1):**

- Total plans completed: 10
- Average duration: ~9 min/plan
- Total execution time: ~1.5 hours

## Accumulated Context

### Decisions

Decisions archived in PROJECT.md Key Decisions table (v1.0 + v1.1 milestones).

- [Phase 09-listener-multi-grupo]: IDs fixos nos seeds de mercados (1=over_2_5, 2=ambas_marcam) via OVERRIDING SYSTEM VALUE para compatibilidade com ENTRADA_PARA_MERCADO_ID hardcoded
- [Phase 09-listener-multi-grupo]: Constraint UNIQUE(group_id, message_id) garante deduplicação multi-grupo; mesmo message_id em grupos diferentes gera rows distintas (LIST-01)
- [Phase 09]: Handler registrado via add_event_handler (nao decorator) para permitir registro apos filtragem dinamica de group_ids invalidos
- [Phase 09]: Fallback TELEGRAM_GROUP_ID mantido para compatibilidade retroativa sem breaking change (D-14)
- [Phase 10-l-gica-financeira]: _build_where mercado_id=None para zero breaking change; LEFT JOIN mercados em get_signals_com_placar para nao excluir sinais historicos sem mercado_id; ORDER BY ASC em get_signals_com_placar para calculo cronologico de P&L
- [Phase 10-l-gica-financeira]: calculate_equity_curve_breakdown implementada junto com calculate_pl_por_entrada para desbloquear imports TDD no arquivo de testes
- [Phase 10-l-gica-financeira]: Funcoes puras sem DB: complementares_por_mercado e odd_por_mercado recebidos como dict — chamador busca do banco via get_complementares_config e get_mercado_config

### Pending Todos

- [ ] Obter o Group ID do grupo "Ambas Marcam" no Telegram para configurar TELEGRAM_GROUP_IDS

### Blockers/Concerns

- EC2 t3.micro tem ~650MB headroom — monitorar RAM com listener multi-grupo (Phase 9)
- Dashboard redesign é breaking change — precisa de deploy coordenado após Phase 10 estar completa
- Group ID do grupo Ambas Marcam ainda não está no .env — necessário antes de testar Phase 9

## Session Continuity

Last session: 2026-04-04T14:35:44.112Z
Stopped at: Phase 11 context gathered
Resume file: .planning/phases/11-dashboard-funda-o/11-CONTEXT.md
