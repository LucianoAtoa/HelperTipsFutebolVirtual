# HelperTips — Futebol Virtual

## What This Is

Sistema que conecta ao grupo **{VIP} ExtremeTips** no Telegram, captura sinais de apostas de futebol virtual da Bet365 em tempo real, armazena no PostgreSQL e fornece um dashboard web elaborado com estatísticas completas, filtros interativos, gráficos dinâmicos, simulação de ROI com Gale, e análises avançadas por dimensão. Deployed na AWS rodando 24/7.

## Core Value

Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## Current State

**Shipped:** v1.3 Análise Individual de Sinais (2026-04-04)
**Codebase:** ~17k LOC Python | 224 testes | ~205 commits
**Phase 15 complete:** Página de Detalhe do Sinal — breakdown P&L por entrada com navegação AG Grid
**Stack:** Python 3.12+, Telethon 1.42.0, PostgreSQL 16, psycopg2-binary, Plotly Dash 4.1.0, dash-bootstrap-components 2.0, gunicorn 25.x, nginx

**O que funciona (produção na EC2):**
- Listener Telethon captura sinais 24/7 como systemd service com restart automático
- Parser regex extrai liga, entrada, horário, resultado, placar, tentativa do formato real
- PostgreSQL com upsert e deduplicação por message_id
- Dashboard dark theme via gunicorn + nginx com HTTP Basic Auth
- KPI cards, filtros (liga/entrada/data), ROI com Gale
- 14 mercados complementares com validação por placar e Martingale
- 3 abas de analytics: Temporal (heatmap, equity, DOW), Gale & Streaks, Volume
- Página de detalhe do sinal com breakdown P&L por entrada (principal + complementares numeradas)
- Navegação AG Grid → detalhe via link markdown
- Badge de cobertura do parser com modal de falhas
- Backup diário automático (pg_dump + .session) para S3
- Budget alert AWS $15/mês
- GitHub CI (ruff lint + pytest) verde a cada push

## Requirements

### Validated

- ✓ Escutar mensagens do grupo Telegram em tempo real (sinais novos e edições com resultado) — v1.0
- ✓ Parsear mensagens extraindo: liga, entrada, horários, resultado (GREEN/RED), placares — v1.0
- ✓ Salvar sinais e resultados no PostgreSQL com deduplicação — v1.0
- ✓ Exibir estatísticas no terminal ao iniciar (total, greens, reds, taxa de acerto) — v1.0
- ✓ Dashboard web elaborado com filtros interativos e gráficos dinâmicos — v1.0
- ✓ Simulação de ROI com stake fixa e Gale — v1.0
- ✓ Estatísticas completas cruzando todas as dimensões — v1.0
- ✓ Percentuais de GREEN/RED por período e por entrada — v1.0
- ✓ Mercados complementares com validação independente por placar e Martingale — v1.0
- ✓ Analytics avançados: heatmap, equity curve, gale analysis, streaks, volume — v1.0
- ✓ Histórico git limpo de secrets — v1.1
- ✓ Dashboard debug mode controlado por env var — v1.1
- ✓ .env.example completo com todas as variáveis — v1.1
- ✓ README.md com setup, deploy e aviso de segurança — v1.1
- ✓ Repo público no GitHub com CI automatizado — v1.1
- ✓ EC2 t3.micro com Elastic IP e Security Group restrito — v1.1
- ✓ PostgreSQL 16 na EC2 com schema migrado — v1.1
- ✓ Budget alert AWS $15/mês — v1.1
- ✓ Credenciais protegidas (.env chmod 600) — v1.1
- ✓ Backup diário pg_dump + .session para S3 — v1.1
- ✓ Listener systemd 24/7 com Restart=on-failure — v1.1
- ✓ Autenticação Telethon interativa via SSH — v1.1
- ✓ Dashboard gunicorn systemd + nginx HTTP Basic Auth — v1.1
- ✓ Listener multi-grupo (Over 2.5 + Ambas Marcam simultaneamente) — v1.2 Phase 9

### Active

- Página Dash separada para análise individual de sinais — v1.3 Phase 15

### Validated (v1.2)

- ✓ Cálculo financeiro P&L com complementares, odds de referência e Martingale — v1.2 Phase 10
- ✓ Dashboard fundação: filtros globais (período/mercado/liga) e KPIs com P&L real — v1.2 Phase 11
- ✓ Dashboard mercados e performance: config read-only e tabela P&L por entrada com toggle — v1.2 Phase 12
- ✓ Dashboard análises visuais: análise por liga, equity curve, análise de gale — v1.2 Phase 13

## Current Milestone: v1.3 Análise Individual de Sinais

**Goal:** Criar página dedicada para análise detalhada de cada sinal, exibindo todas as entradas (principal + complementares) com resultados, horários e lucro/prejuízo. Página separada para acomodar futuras expansões.

**Target features:**
- Página Dash separada acessível ao clicar em um sinal no histórico
- Exibição da entrada principal: mercado, odd, stake, resultado (GREEN/RED), horário, lucro
- Exibição de cada entrada complementar: nome, odd, stake, resultado validado pelo placar, horário, lucro
- Totais consolidados: investido total, retorno total, lucro líquido
- Horário de cada entrada visível
- Estrutura extensível para futuras informações adicionais

### Out of Scope

- Automação de apostas na Bet365 via Selenium/Playwright — risco de banimento, complexidade alta
- App mobile — web-first, dashboard responsivo cobre o caso
- Múltiplos grupos do Telegram além de Over 2.5 e Ambas Marcam — foco nesses dois mercados
- Kelly Criterion — requer probabilidade de acerto estável
- IA preditiva — futebol virtual é RNG, ML encontra padrões em ruído
- Push real-time no browser — sinais infrequentes, refresh manual/periódico suficiente

## Context

- Shipped v1.0 MVP em 2 dias (2026-04-02 → 2026-04-03), v1.1 Cloud Deploy em 1 dia (2026-04-03 → 2026-04-04)
- Stack: Python 3.12+, Telethon 1.42.0, PostgreSQL 16, psycopg2-binary, Plotly Dash 4.1.0, dbc 2.0, gunicorn 25.x, nginx
- Listener e dashboard rodam como systemd services separados na EC2 (us-east-1, t3.micro)
- Parser calibrado contra formato real do grupo {VIP} ExtremeTips
- Deploy via scripts bash idempotentes em `deploy/` (01-07)
- Custo estimado: ~$12-13/mês (EC2 + EIP + EBS + S3 marginal)

## Constraints

- **Stack**: Python 3.12+, Telethon 1.42.0, PostgreSQL 16, psycopg2-binary, python-dotenv
- **Telegram API**: Requer API ID e Hash do my.telegram.org
- **Sessão Telethon**: .session no .gitignore, backup diário S3
- **Formato mensagens**: Parsing depende do formato atual do grupo
- **Infra**: EC2 t3.micro single-instance (pet, not cattle), sem Docker/K8s

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Telethon (client de usuário) em vez de Bot API | Precisa escutar grupo sem ser admin | ✓ Good — v1.0 |
| PostgreSQL em vez de SQLite | Suporte a concorrência, pronto para produção | ✓ Good — v1.0 |
| Plotly Dash + dbc para dashboard | Pure-Python, dark theme, responsive | ✓ Good — v1.0 |
| Processos separados (listener + dashboard) | Event loops incompatíveis | ✓ Good — v1.0 |
| EC2 t3.micro em us-east-1 | Free tier 12 meses, custo mínimo | ✓ Good — v1.1 |
| PostgreSQL local (sem RDS) | Zero custo adicional para uso pessoal | ✓ Good — v1.1 |
| systemd em vez de Docker | Simplicidade para ferramenta pessoal | ✓ Good — v1.1 |
| HTTP Basic Auth em vez de OAuth | Suficiente para 1 usuário | ✓ Good — v1.1 |
| gunicorn + nginx em vez de Dash dev server | Stack de produção, porta 80 | ✓ Good — v1.1 |
| IAM instance profile em vez de access keys | Sem credenciais estáticas no servidor | ✓ Good — v1.1 |
| Handler único multi-grupo com chats=[lista] | Telethon nativo, menor mudança, mesmo parser | ✓ Good — v1.2 |
| group_id + mercado_id no schema signals | Deduplicação correta entre grupos, FK para P&L | ✓ Good — v1.2 |
| Dash Pages (use_pages=True) em vez de single-page | Habilita URL routing para página de detalhe do sinal | ✓ Good — v1.3 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-04 after v1.3 milestone*
