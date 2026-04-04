---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Análise Individual de Sinais
status: executing
stopped_at: Completed 15-p-gina-de-detalhe-do-sinal/15-01-PLAN.md
last_updated: "2026-04-04T20:27:23.917Z"
last_activity: 2026-04-04
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 13
  completed_plans: 13
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-04)

**Core value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.
**Current focus:** Phase 15 — p-gina-de-detalhe-do-sinal

## Current Position

Phase: 15
Plan: Not started
Status: Ready to execute
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

**Velocity (v1.2):**

- Total plans completed: 10 (2 plans × 5 phases)
- Average duration: ~10 min/plan
- Total execution time: ~1.7 hours

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
- [Phase 11-dashboard-funda-o]: try/except ImportError para _resolve_periodo: testes coletam sem erro ate implementacao no Plan 02
- [Phase 11-dashboard-funda-o]: CSS em helpertips/assets/: carregado automaticamente pelo Dash, zero configuracao adicional
- [Phase 11-dashboard-funda-o]: P&L total on-the-fly no callback master: principal + complementares somados. Complementares apenas quando mercado especifico selecionado.
- [Phase 11-dashboard-funda-o]: entrada como string passada diretamente para queries (nao mercado_id) — evita Pitfall 2 do RESEARCH
- [Phase 12-dashboard-mercados-e-performance]: Funcoes helper puras sem acesso ao banco testavel por TDD; analytics-placeholder substituido por IDs especificos no layout
- [Phase 12]: dbc.Table color='dark' em vez de dark=True: parametro dark nao existe em dbc 2.0.4
- [Phase 13-dashboard-an-lises-visuais]: aggregate_pl_por_tentativa ignora REDs: apenas greens entram no agrupamento por tentativa
- [Phase 13-dashboard-an-lises-visuais]: Builders Plotly retornam go.Figure() vazio para input vazio — sem erros, padrao consistente com Phases 11-12
- [Phase 13]: Calculo de signals_placar/comps/odds/pl_lista no nivel do callback (step 19) reutilizados por _build_phase13_section sem round-trips extras ao banco
- [Phase 13]: Aceitar segunda chamada a get_signals_com_placar em relacao a _build_performance_section como trade-off de simplicidade (dataset pequeno, sem impacto perceptivel)
- [Phase 14-migra-o-multi-page]: app.config em Dash 4.1.0 e dict (nao objeto): usar app.config.get() em testes MPA
- [Phase 14-migra-o-multi-page]: dash.register_page duplo registro em testes — usar >= 1 em vez de == 1 no test_home_page_registered
- [Phase 15-p-gina-de-detalhe-do-sinal]: placar=None em calculate_pl_detalhado_por_sinal -> complementares N/A com lucro=0 e investido=0 (diferente de validar_complementar que retorna RED para placar=None)
- [Phase 15-p-gina-de-detalhe-do-sinal]: stake_efetiva adicionada ao dict principal de calculate_pl_detalhado_por_sinal para expor winning_stake do Gale ao chamador

### Pending Todos

- [ ] Obter o Group ID do grupo "Ambas Marcam" no Telegram para configurar TELEGRAM_GROUP_IDS
- [ ] Phase 14: Confirmar localização atual de dashboard.py antes de planejar migração para pages/

### Blockers/Concerns

- EC2 t3.micro tem ~650MB headroom — monitorar RAM com listener multi-grupo (Phase 9)
- Phase 14 é etapa bloqueante: refatoração dashboard.py → pages/ deve ser validada localmente antes de deploy
- Pitfall gunicorn + pages/ folder resolution: `dash.Dash(__name__, ...)` deve já ser o padrão do projeto — confirmar durante Phase 14
- calculate_pl_por_entrada retorna totais agrupados (não por complementar individual) — Phase 15 precisa de nova função `calculate_pl_detalhado_por_sinal` em queries.py

## Session Continuity

Last session: 2026-04-04T19:33:13.019Z
Stopped at: Completed 15-p-gina-de-detalhe-do-sinal/15-01-PLAN.md
Resume file: None
