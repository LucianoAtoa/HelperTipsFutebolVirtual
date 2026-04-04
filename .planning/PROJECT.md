# HelperTips — Futebol Virtual

## What This Is

Sistema que conecta ao grupo **{VIP} ExtremeTips** no Telegram, captura sinais de apostas de futebol virtual da Bet365 em tempo real, armazena no PostgreSQL e fornece um dashboard web elaborado com estatísticas completas, filtros interativos, gráficos dinâmicos, simulação de ROI com Gale, e análises avançadas por dimensão. Feito para o próprio usuário que hoje acompanha e aposta manualmente.

## Core Value

Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## Current State

**Shipped:** v1.0 MVP (2026-04-03)
**Codebase:** 5,050 LOC Python | 132 testes | 97 commits
**Stack:** Python 3.12+, Telethon 1.42.0, PostgreSQL 16, psycopg2-binary, Plotly Dash 4.1.0, dash-bootstrap-components 2.0

**O que funciona:**
- Listener Telethon captura sinais e resultados em tempo real do grupo {VIP} ExtremeTips
- Parser regex extrai liga, entrada, horário, resultado, placar, tentativa do formato real
- PostgreSQL com upsert e deduplicação por message_id
- Dashboard dark theme com KPI cards, filtros (liga/entrada/data), ROI com Gale
- 14 mercados complementares com validação por placar e Martingale
- 3 abas de analytics: Temporal (heatmap, equity, DOW), Gale & Streaks, Volume (volume, período, cross-dimensional)
- Badge de cobertura do parser com modal de falhas

## Requirements

### Validated

- ✓ Escutar mensagens do grupo Telegram em tempo real (sinais novos e edições com resultado) — v1.0
- ✓ Parsear mensagens extraindo: liga, entrada, horários, resultado (GREEN/RED), placares — v1.0
- ✓ Salvar sinais e resultados no PostgreSQL com deduplicação — v1.0
- ✓ Exibir estatísticas no terminal ao iniciar (total, greens, reds, taxa de acerto) — v1.0
- ✓ Dashboard web elaborado com filtros interativos e gráficos dinâmicos — v1.0
- ✓ Simulação de ROI com stake fixa e Gale — v1.0
- ✓ Estatísticas completas cruzando todas as dimensões: liga, entrada, horário, período, dia da semana — v1.0
- ✓ Percentuais de GREEN/RED por período e por entrada — v1.0
- ✓ Mercados complementares com validação independente por placar e Martingale — v1.0
- ✓ Analytics avançados: heatmap, equity curve, gale analysis, streaks, volume — v1.0

## Current Milestone: v1.1 Cloud Deploy

**Goal:** Subir o HelperTips para a AWS com custo mínimo, garantindo segurança antes de expor na nuvem, e publicar o repositório no GitHub.

**Target features:**
- Revisão de segurança (secrets, credenciais, exposição)
- Publicação no GitHub (repo, .gitignore, README)
- Deploy na AWS (listener + dashboard, custo mínimo)
- Configuração de infraestrutura para rodar 24/7

### Active

- Dashboard deploy na AWS (Dash + nginx reverse proxy 24/7)

### Validated (v1.1)

- ✓ Histórico git limpo de secrets — nenhum `.env` ou `.session` no histórico — Phase 4
- ✓ Dashboard debug mode controlado por variável de ambiente (`DASH_DEBUG`) — Phase 4
- ✓ `.env.example` completo com todas as variáveis necessárias (Telegram, DB, AWS) — Phase 4
- ✓ README.md com setup local, deploy e aviso de segurança sobre `.session` — Phase 4
- ✓ Repo público no GitHub com CI automatizado (ruff lint + pytest) — Phase 5
- ✓ `.gitignore` bloqueando `*.session`, `.env`, `__pycache__`, `*.pyc` — Phase 5
- ✓ GitHub Actions CI passa verde a cada push para main — Phase 5
- ✓ EC2 t3.micro provisionada com Elastic IP, Security Group restrito, swap 1GB — Phase 6
- ✓ PostgreSQL 16 instalado com role/banco/schema migrado na EC2 — Phase 6
- ✓ Budget alert AWS de $15/mês ativo no AWS Budgets — Phase 6
- ✓ Credenciais protegidas com .env chmod 600 no servidor — Phase 6
- ✓ Backup automático diário (pg_dump + .session) para S3 via IAM instance profile — Phase 6
- ✓ Listener Telethon rodando 24/7 como systemd service na EC2 com Restart=on-failure — Phase 7
- ✓ Autenticação interativa Telethon completada via SSH, .session gerado na EC2 — Phase 7
- ✓ Logging condicional TTY (Rich em dev, RotatingFileHandler em daemon) — Phase 7

### Out of Scope

- Automação de apostas na Bet365 via Selenium/Playwright — risco de banimento, complexidade alta, fase futura
- App mobile — web-first, dashboard responsivo cobre o caso
- Múltiplos grupos do Telegram — foco no {VIP} ExtremeTips
- Notificações/alertas automáticos — fase futura
- OAuth / autenticação — ferramenta pessoal, acesso localhost
- Kelly Criterion — requer probabilidade de acerto estável
- IA preditiva — futebol virtual é RNG, ML encontra padrões em ruído
- Push real-time no browser — sinais infrequentes, refresh manual/periódico suficiente

## Context

- Shipped v1.0 com 5,050 LOC Python, 132 testes, 4 fases executadas em 2 dias
- Stack: Python 3.12+, Telethon 1.42.0, PostgreSQL 16, psycopg2-binary, Plotly Dash 4.1.0, dbc 2.0
- Listener e dashboard rodam como processos separados (listener.py + dashboard.py)
- Parser calibrado contra formato real do grupo {VIP} ExtremeTips
- Listener rodando 24/7 na EC2 como systemd service, capturando sinais reais do Telegram

## Constraints

- **Stack**: Python 3.12+, Telethon 1.42.0, PostgreSQL 16, psycopg2-binary, python-dotenv — definido no guia
- **Telegram API**: Requer API ID e Hash do my.telegram.org — credenciais do próprio usuário
- **Sessão Telethon**: Gera arquivo .session que deve ficar no .gitignore
- **Formato mensagens**: Parsing depende do formato atual do grupo — se mudar, parser precisa atualizar

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Telethon (client de usuário) em vez de Bot API | Precisa escutar grupo sem ser admin | ✓ Good — v1.0 |
| PostgreSQL em vez de SQLite | Suporte a concorrência, pronto para AWS RDS futuro | ✓ Good — v1.0 |
| Plotly Dash + dbc para dashboard | Pure-Python, dark theme, responsive, callbacks reativos | ✓ Good — v1.0 |
| dbc.Tabs para analytics depth | 3 abas temáticas organizam 10+ componentes sem poluir a view | ✓ Good — v1.0 |
| Processos separados (listener + dashboard) | Telethon e Dash bloqueiam seus event loops respectivos | ✓ Good — v1.0 |
| Parser regex com gate GATE_PATTERN | Filtra mensagens não-sinal antes de qualquer processamento | ✓ Good — v1.0 |
| store.py sync-only com asyncio.to_thread | Simplicidade sem sacrificar non-blocking no listener | ✓ Good — v1.0 |
| Mercados complementares como tabelas PostgreSQL | Configuração editável sem redeploy | ✓ Good — v1.0 |
| regra_validacao como TEXT mapeado para lambdas | Seguro (sem eval), extensível, testável | ✓ Good — v1.0 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-04 after Phase 7 (Listener Deployment) complete*
