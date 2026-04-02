# HelperTips — Futebol Virtual

## What This Is

Sistema que conecta ao grupo **{VIP} ExtremeTips** no Telegram, captura sinais de apostas de futebol virtual da Bet365 em tempo real, armazena no PostgreSQL e fornece um dashboard web elaborado com estatísticas completas, filtros interativos, gráficos dinâmicos e simulação de ROI. Feito para o próprio usuário que hoje acompanha e aposta manualmente.

## Core Value

Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Escutar mensagens do grupo Telegram em tempo real (sinais novos e edições com resultado)
- [ ] Parsear mensagens extraindo: liga, entrada, horários, resultado (GREEN/RED), placares
- [ ] Salvar sinais e resultados no PostgreSQL com deduplicação
- [ ] Exibir estatísticas no terminal ao iniciar (total, greens, reds, taxa de acerto)
- [ ] Dashboard web elaborado com filtros interativos e gráficos dinâmicos
- [ ] Estatísticas completas cruzando todas as dimensões: liga, entrada, horário, período, dia da semana
- [ ] Percentuais de GREEN/RED por período e por entrada
- [ ] Simulação de ROI com stake fixa

### Out of Scope

- Automação de apostas na Bet365 via Selenium/Playwright — risco de banimento, complexidade alta, fase futura
- App mobile — web-first
- Múltiplos grupos do Telegram — foco no {VIP} ExtremeTips
- Notificações/alertas automáticos — fase futura

## Context

- O usuário hoje acompanha os sinais manualmente no Telegram e aposta na Bet365 sem registro histórico
- O objetivo é ter dados concretos para saber se os sinais realmente funcionam e quais padrões são mais lucrativos
- O grupo envia sinais como mensagens novas e edita a mesma mensagem para adicionar o resultado (GREEN/RED)
- Mensagens seguem um formato previsível com emojis, passível de parsing com regex
- Telethon é usado como client de usuário (não bot) para escutar grupos sem ser admin
- Na primeira execução do Telethon, é necessário autenticar via telefone + código no terminal

## Constraints

- **Stack**: Python 3.12+, Telethon 1.37, PostgreSQL 16, psycopg2-binary, python-dotenv — definido no guia
- **Telegram API**: Requer API ID e Hash do my.telegram.org — credenciais do próprio usuário
- **Sessão Telethon**: Gera arquivo .session que deve ficar no .gitignore
- **Formato mensagens**: Parsing depende do formato atual do grupo — se mudar, parser precisa atualizar

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Telethon (client de usuário) em vez de Bot API | Precisa escutar grupo sem ser admin | — Pending |
| PostgreSQL em vez de SQLite | Suporte a concorrência, pronto para AWS RDS futuro | — Pending |
| Dashboard web no v1 | Usuário quer análise visual elaborada desde o início | — Pending |

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
*Last updated: 2026-04-02 after initialization*
