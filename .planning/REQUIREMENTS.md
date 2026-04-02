# Requirements: HelperTips — Futebol Virtual

**Defined:** 2026-04-02
**Core Value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Listener

- [ ] **LIST-01**: Sistema captura sinais novos do grupo Telegram em tempo real (events.NewMessage)
- [ ] **LIST-02**: Sistema detecta edições de mensagens com resultado (events.MessageEdited)
- [ ] **LIST-03**: Sistema deduplica sinais por telegram_msg_id (ON CONFLICT upsert)
- [ ] **LIST-04**: Sistema ignora mensagens sem texto (imagens, stickers)
- [ ] **LIST-05**: Sistema reconecta automaticamente após perda de conexão

### Parser

- [ ] **PARS-01**: Parser extrai liga da mensagem do sinal
- [ ] **PARS-02**: Parser extrai entrada recomendada (tipo de aposta)
- [ ] **PARS-03**: Parser extrai horários dos jogos
- [ ] **PARS-04**: Parser extrai resultado (GREEN/RED) de mensagens editadas
- [ ] **PARS-05**: Parser extrai placares individuais quando disponíveis
- [ ] **PARS-06**: Parser armazena texto original (raw_text) para recuperação em caso de falha
- [ ] **PARS-07**: Parser registra taxa de cobertura (% de mensagens parseadas vs descartadas)

### Database

- [ ] **DB-01**: Schema PostgreSQL para sinais com campos: liga, entrada, horários, resultado, placares, timestamps
- [ ] **DB-02**: Upsert de sinais com deduplicação por telegram_msg_id
- [ ] **DB-03**: Update de resultado quando mensagem é editada
- [ ] **DB-04**: Chamadas ao banco não bloqueiam o event loop do asyncio (asyncio.to_thread)

### Terminal

- [ ] **TERM-01**: Ao iniciar, exibe resumo: total de sinais, greens, reds, taxa de acerto
- [ ] **TERM-02**: Ao iniciar, confirma conexão com grupo Telegram
- [ ] **TERM-03**: Encerramento limpo com Ctrl+C

### Dashboard — Stats Core

- [ ] **DASH-01**: Dashboard web com interface elaborada e responsiva
- [ ] **DASH-02**: Card de estatísticas: total de sinais, greens, reds, taxa de acerto, percentuais
- [ ] **DASH-03**: Simulação de ROI com stake fixa configurável
- [ ] **DASH-04**: Filtro interativo por liga
- [ ] **DASH-05**: Filtro interativo por entrada (tipo de aposta)
- [ ] **DASH-06**: Lista de histórico de sinais paginada
- [ ] **DASH-07**: Visualização de sinais pendentes (sem resultado)

### Dashboard — Análises Avançadas

- [ ] **ANAL-01**: Taxa de acerto por horário do dia (heatmap)
- [ ] **ANAL-02**: Taxa de acerto por dia da semana
- [ ] **ANAL-03**: Taxa de acerto por período (1T/2T/FT se aplicável)
- [ ] **ANAL-04**: Análise cross-dimensional (filtros compostos: liga + entrada + horário + dia)
- [ ] **ANAL-05**: Curva de equity (bankroll acumulado ao longo do tempo com stake fixa)
- [ ] **ANAL-06**: Tracking de sequências (streaks) — atual e maior histórica
- [ ] **ANAL-07**: Análise de Gale (martingale 1x/2x/3x) — taxa de recuperação por nível
- [ ] **ANAL-08**: Gráfico de volume de sinais por dia/semana

### Operacional

- [ ] **OPER-01**: Exibir taxa de cobertura do parser (% de mensagens parseadas com sucesso)
- [ ] **OPER-02**: Arquivo .session no .gitignore antes do primeiro commit
- [ ] **OPER-03**: Configuração via .env com validação de variáveis obrigatórias

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Automação

- **AUTO-01**: Automação de apostas na Bet365 via Selenium/Playwright
- **AUTO-02**: Gestão de banca (stop loss/gain)
- **AUTO-03**: Alertas via Telegram pessoal

### Resiliência

- **RESIL-01**: Utilitário de backfill para gaps de mensagens perdidas durante offline
- **RESIL-02**: Connection pool com limite configurável
- **RESIL-03**: Tratamento de FloodWaitError do Telegram

### Analytics v2

- **ANLV2-01**: Visualizador de mensagem raw ao lado dos campos parseados
- **ANLV2-02**: Suporte a múltiplos grupos do Telegram
- **ANLV2-03**: Tracking de odds (se disponível nas mensagens)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automação de apostas Bet365 | Risco de banimento, complexidade alta |
| App mobile | Web-first, dashboard responsivo cobre o caso |
| Múltiplos grupos Telegram | Foco no {VIP} ExtremeTips, complexidade desnecessária |
| OAuth / autenticação | Ferramenta pessoal, acesso localhost |
| Kelly Criterion | Requer probabilidade de acerto estável que estamos tentando descobrir |
| IA preditiva | Futebol virtual é RNG — ML encontra padrões em ruído |
| Push real-time no browser | Sinais são infrequentes, refresh manual/periódico suficiente |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LIST-01 | — | Pending |
| LIST-02 | — | Pending |
| LIST-03 | — | Pending |
| LIST-04 | — | Pending |
| LIST-05 | — | Pending |
| PARS-01 | — | Pending |
| PARS-02 | — | Pending |
| PARS-03 | — | Pending |
| PARS-04 | — | Pending |
| PARS-05 | — | Pending |
| PARS-06 | — | Pending |
| PARS-07 | — | Pending |
| DB-01 | — | Pending |
| DB-02 | — | Pending |
| DB-03 | — | Pending |
| DB-04 | — | Pending |
| TERM-01 | — | Pending |
| TERM-02 | — | Pending |
| TERM-03 | — | Pending |
| DASH-01 | — | Pending |
| DASH-02 | — | Pending |
| DASH-03 | — | Pending |
| DASH-04 | — | Pending |
| DASH-05 | — | Pending |
| DASH-06 | — | Pending |
| DASH-07 | — | Pending |
| ANAL-01 | — | Pending |
| ANAL-02 | — | Pending |
| ANAL-03 | — | Pending |
| ANAL-04 | — | Pending |
| ANAL-05 | — | Pending |
| ANAL-06 | — | Pending |
| ANAL-07 | — | Pending |
| ANAL-08 | — | Pending |
| OPER-01 | — | Pending |
| OPER-02 | — | Pending |
| OPER-03 | — | Pending |

**Coverage:**
- v1 requirements: 37 total
- Mapped to phases: 0
- Unmapped: 37 ⚠️

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-02 after initial definition*
