# Requirements: HelperTips — Futebol Virtual

**Defined:** 2026-04-02
**Core Value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Listener

- [x] **LIST-01**: Sistema captura sinais novos do grupo Telegram em tempo real (events.NewMessage)
- [x] **LIST-02**: Sistema detecta edições de mensagens com resultado (events.MessageEdited)
- [x] **LIST-03**: Sistema deduplica sinais por telegram_msg_id (ON CONFLICT upsert)
- [x] **LIST-04**: Sistema ignora mensagens sem texto (imagens, stickers)
- [x] **LIST-05**: Sistema reconecta automaticamente após perda de conexão

### Parser

- [x] **PARS-01**: Parser extrai liga da mensagem do sinal
- [x] **PARS-02**: Parser extrai entrada recomendada (tipo de aposta)
- [x] **PARS-03**: Parser extrai horários dos jogos
- [x] **PARS-04**: Parser extrai resultado (GREEN/RED) de mensagens editadas
- [x] **PARS-05**: Parser extrai placares individuais quando disponíveis
- [x] **PARS-06**: Parser armazena texto original (raw_text) para recuperação em caso de falha
- [x] **PARS-07**: Parser registra taxa de cobertura (% de mensagens parseadas vs descartadas)

### Database

- [x] **DB-01**: Schema PostgreSQL para sinais com campos: liga, entrada, horários, resultado, placares, timestamps
- [x] **DB-02**: Upsert de sinais com deduplicação por telegram_msg_id
- [x] **DB-03**: Update de resultado quando mensagem é editada
- [x] **DB-04**: Chamadas ao banco não bloqueiam o event loop do asyncio (asyncio.to_thread)

### Terminal

- [x] **TERM-01**: Ao iniciar, exibe resumo: total de sinais, greens, reds, taxa de acerto
- [x] **TERM-02**: Ao iniciar, confirma conexão com grupo Telegram
- [x] **TERM-03**: Encerramento limpo com Ctrl+C

### Dashboard — Stats Core

- [x] **DASH-01**: Dashboard web com interface elaborada e responsiva
- [x] **DASH-02**: Card de estatísticas: total de sinais, greens, reds, taxa de acerto, percentuais
- [x] **DASH-03**: Simulação de ROI com stake fixa configurável
- [x] **DASH-04**: Filtro interativo por liga
- [x] **DASH-05**: Filtro interativo por entrada (tipo de aposta)
- [x] **DASH-06**: Lista de histórico de sinais paginada
- [x] **DASH-07**: Visualização de sinais pendentes (sem resultado)

### Market Config — Mercados e Complementares

- [x] **MKT-01**: Tabelas PostgreSQL `mercados` e `complementares` com seed data de 2 mercados principais e 14 complementares
- [x] **MKT-02**: Validação independente de GREEN/RED por entrada complementar baseada no placar do sinal principal
- [x] **MKT-03**: Cálculo de stakes Martingale para complementares (stake_comp = stake_principal * percentual * 2^(N-1))
- [x] **MKT-04**: Cálculo de ROI complementares puro Python com breakdown por mercado
- [x] **MKT-05**: Query get_complementares_config() para carregar configuração do banco
- [x] **MKT-06**: Card ROI Complementares no dashboard com tabela de breakdown por mercado
- [x] **MKT-07**: ROI total considera investimento principal + todas complementares

### Dashboard — Análises Avançadas

- [x] **ANAL-01**: Taxa de acerto por horário do dia (heatmap)
- [x] **ANAL-02**: Taxa de acerto por dia da semana
- [x] **ANAL-03**: Taxa de acerto por período (1T/2T/FT se aplicável)
- [x] **ANAL-04**: Análise cross-dimensional (filtros compostos: liga + entrada + horário + dia)
- [x] **ANAL-05**: Curva de equity (bankroll acumulado ao longo do tempo com stake fixa)
- [x] **ANAL-06**: Tracking de sequências (streaks) — atual e maior histórica
- [x] **ANAL-07**: Análise de Gale (martingale 1x/2x/3x) — taxa de recuperação por nível
- [x] **ANAL-08**: Gráfico de volume de sinais por dia/semana

### Operacional

- [x] **OPER-01**: Exibir taxa de cobertura do parser (% de mensagens parseadas com sucesso)
- [x] **OPER-02**: Arquivo .session no .gitignore antes do primeiro commit
- [x] **OPER-03**: Configuração via .env com validação de variáveis obrigatórias

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
| LIST-01 | Phase 1 | Complete |
| LIST-02 | Phase 1 | Complete |
| LIST-03 | Phase 1 | Complete |
| LIST-04 | Phase 1 | Complete |
| LIST-05 | Phase 1 | Complete |
| PARS-01 | Phase 1 | Complete |
| PARS-02 | Phase 1 | Complete |
| PARS-03 | Phase 1 | Complete |
| PARS-04 | Phase 1 | Complete |
| PARS-05 | Phase 1 | Complete |
| PARS-06 | Phase 1 | Complete |
| PARS-07 | Phase 1 | Complete |
| DB-01 | Phase 1 | Complete |
| DB-02 | Phase 1 | Complete |
| DB-03 | Phase 1 | Complete |
| DB-04 | Phase 1 | Complete |
| TERM-01 | Phase 1 | Complete |
| TERM-02 | Phase 1 | Complete |
| TERM-03 | Phase 1 | Complete |
| OPER-02 | Phase 1 | Complete |
| OPER-03 | Phase 1 | Complete |
| DASH-01 | Phase 2 | Complete |
| DASH-02 | Phase 2 | Complete |
| DASH-03 | Phase 2 | Complete |
| DASH-04 | Phase 2 | Complete |
| DASH-05 | Phase 2 | Complete |
| DASH-06 | Phase 2 | Complete |
| DASH-07 | Phase 2 | Complete |
| MKT-01 | Phase 2.1 | Complete |
| MKT-02 | Phase 2.1 | Complete |
| MKT-03 | Phase 2.1 | Complete |
| MKT-04 | Phase 2.1 | Complete |
| MKT-05 | Phase 2.1 | Complete |
| MKT-06 | Phase 2.1 | Complete |
| MKT-07 | Phase 2.1 | Complete |
| ANAL-01 | Phase 3 | Complete |
| ANAL-02 | Phase 3 | Complete |
| ANAL-03 | Phase 3 | Complete |
| ANAL-04 | Phase 3 | Complete |
| ANAL-05 | Phase 3 | Complete |
| ANAL-06 | Phase 3 | Complete |
| ANAL-07 | Phase 3 | Complete |
| ANAL-08 | Phase 3 | Complete |
| OPER-01 | Phase 3 | Complete |

**Coverage:**
- v1 requirements: 44 total
- Mapped to phases: 44
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-03 after Phase 02.1 planning*
