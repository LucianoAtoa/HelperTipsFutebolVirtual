# Requirements: HelperTips — v1.3 Análise Individual de Sinais

**Defined:** 2026-04-04
**Core Value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## v1.3 Requirements

Requirements para página dedicada de análise individual de sinais com breakdown de entradas.

### Estrutura Multi-Page

- [ ] **MPA-01**: Dashboard migrado para Dash Pages (`use_pages=True`) com layout principal + `dash.page_container`
- [ ] **MPA-02**: Página home (`pages/home.py`) renderiza o dashboard atual sem regressões visuais ou funcionais

### Página de Detalhe do Sinal

- [ ] **SIG-01**: Usuário pode clicar em um sinal no histórico (AG Grid) e navegar para a página de detalhe
- [ ] **SIG-02**: Página exibe card da entrada principal com mercado, odd, stake, resultado (GREEN/RED), horário e lucro/prejuízo
- [ ] **SIG-03**: Página exibe lista de cada entrada complementar com nome, odd, stake, resultado validado pelo placar (GREEN/RED), horário e lucro/prejuízo
- [ ] **SIG-04**: Página exibe totais consolidados: investido total, retorno total, lucro líquido
- [ ] **SIG-05**: Página tem botão para voltar ao dashboard
- [ ] **SIG-06**: Página trata sinais inexistentes/inválidos com mensagem amigável

## v1.2 Requirements (Complete)

### Listener Multi-Grupo

- [x] **LIST-01**: Listener escuta grupos Over 2.5 e Ambas Marcam simultaneamente via lista de group IDs no .env (TELEGRAM_GROUP_IDS=id1,id2)
- [x] **LIST-02**: Parser identifica mercado principal pelo conteúdo da "Entrada recomendada" na mensagem — campo `entrada` armazena "Over 2.5" ou "Ambas Marcam"

### Cálculo Financeiro

- [x] **FIN-01**: Cada sinal gera entradas complementares com stake proporcional (% da principal) e odds de referência configuráveis por mercado
- [x] **FIN-02**: Cálculo de P&L por entrada (investido, retorno, lucro/prejuízo líquido) com Martingale progressivo de 4 tentativas (1x, 2x, 4x, 8x)
- [x] **FIN-03**: Complementares têm configuração diferenciada por mercado — Over 2.5 (7 complementares com % específicos) vs Ambas Marcam (7 complementares com % distintos)

### Dashboard Redesign

- [x] **DASH-01**: Filtros globais fixos no topo (período: Hoje/Semana/Mês/Mês Passado/Personalizado/Toda a Vida, mercado: Todos/Over 2.5/Ambas Marcam, liga: Todas/Copa do Mundo/Euro Cup/Sul-Americana/Premier League) afetam todos os cards e gráficos
- [x] **DASH-02**: KPI cards: total sinais, taxa green (%), P&L total (R$) principal+complementar, ROI (%), melhor streak green, pior streak red
- [x] **DASH-03**: Seção configuração de mercados: painel read-only com principal (odd, stake, progressão) e tabela complementares (mercado, %, odd ref, stakes T1-T4)
- [x] **DASH-04**: Seção performance das entradas: tabela P&L por mercado (greens, reds, taxa, investido, retorno, P&L, ROI) com toggle percentual/quantidade/R$ e visão geral vs por mercado
- [x] **DASH-05**: Seção análise por liga: gráfico de barras empilhadas (P&L principal vs complementar) + tabela com taxa, P&L principal, P&L complementar, P&L total por liga
- [x] **DASH-06**: Seção evolução temporal: equity curve com 3 linhas sobrepostas (principal, complementar, total) controlado pelo filtro global de período
- [x] **DASH-07**: Seção análise de gale: donut chart de distribuição por tentativa (1ª-4ª) + tabela com quantidade, percentual e lucro médio por green

## Future Requirements

Deferred to future release.

### Navegação Avançada

- **NAV-01**: Deep-link por sinal (URL bookmarkável `/sinal/<id>`) — v1.4

### Resiliência

- **RESIL-01**: Utilitário de backfill para gaps de mensagens perdidas durante offline
- **RESIL-02**: Connection pool com limite configurável
- **RESIL-03**: Tratamento de FloodWaitError do Telegram

### Automação

- **AUTO-01**: Automação de apostas na Bet365 via Selenium/Playwright
- **AUTO-02**: Gestão de banca (stop loss/gain)
- **AUTO-03**: Alertas via Telegram pessoal

### Infra Avançada

- **INFRA-01**: HTTPS com certificado Let's Encrypt (requer domínio)
- **INFRA-02**: Monitoramento com CloudWatch ou similar
- **INFRA-03**: Deploy automático via GitHub Actions SSH

## Out of Scope

| Feature | Reason |
|---------|--------|
| Modal/popup em vez de página separada | Decisão do usuário por extensibilidade futura |
| Edição de sinais pela página de detalhe | Fora do escopo — dashboard é read-only |
| Docker / ECS / Kubernetes | Over-engineering para ferramenta pessoal; systemd é suficiente |
| RDS managed database | +$15-25/mês sem benefício real para uso pessoal |
| OAuth / autenticação avançada | HTTP Basic Auth é suficiente para 1 usuário |
| Edição de complementares via dashboard | Config via banco/código, dashboard é read-only |
| Odds em tempo real da Bet365 | Odds de referência estáticas baseadas em amostra |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| LIST-01 | Phase 9 | Complete |
| LIST-02 | Phase 9 | Complete |
| FIN-01 | Phase 10 | Complete |
| FIN-02 | Phase 10 | Complete |
| FIN-03 | Phase 10 | Complete |
| DASH-01 | Phase 11 | Complete |
| DASH-02 | Phase 11 | Complete |
| DASH-03 | Phase 12 | Complete |
| DASH-04 | Phase 12 | Complete |
| DASH-05 | Phase 13 | Complete |
| DASH-06 | Phase 13 | Complete |
| DASH-07 | Phase 13 | Complete |
| MPA-01 | — | Pending |
| MPA-02 | — | Pending |
| SIG-01 | — | Pending |
| SIG-02 | — | Pending |
| SIG-03 | — | Pending |
| SIG-04 | — | Pending |
| SIG-05 | — | Pending |
| SIG-06 | — | Pending |
