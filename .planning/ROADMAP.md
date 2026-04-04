# Roadmap: HelperTips — Futebol Virtual

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 + 2.1 (shipped 2026-04-03) — [archive](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Cloud Deploy** — Phases 4-8 (shipped 2026-04-04) — [archive](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2 Multi-Market Analytics** — Phases 9-13 (shipped 2026-04-04)
- ✅ **v1.3 Análise Individual de Sinais** — Phases 14-15 (shipped 2026-04-04) — [archive](milestones/v1.3-ROADMAP.md)
- 🚧 **v1.4 Configurações de Mercado + Dashboard Ajustes** — Phases 16-19 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3 + 2.1) — SHIPPED 2026-04-03</summary>

- [x] Phase 1: Foundation (7/7 plans) — Telegram listener pipeline captures signals into PostgreSQL
- [x] Phase 2: Core Dashboard (3/3 plans) — Plotly Dash dashboard with stats, filters, ROI simulation
- [x] Phase 2.1: Market Config (4/4 plans) — Mercados complementares com validação por placar e Martingale
- [x] Phase 3: Analytics Depth (4/4 plans) — Heatmap, equity curve, gale analysis, cross-dimensional

</details>

<details>
<summary>✅ v1.1 Cloud Deploy (Phases 4-8) — SHIPPED 2026-04-04</summary>

- [x] Phase 4: Security Audit (2/2 plans) — Repositório limpo de secrets, debug=False, documentação de segurança (completed 2026-04-03)
- [x] Phase 5: GitHub Publication (2/2 plans) — Repositório público com CI/CD automatizado via GitHub Actions (completed 2026-04-03)
- [x] Phase 6: AWS Infrastructure (3/3 plans) — EC2 t3.micro com PostgreSQL, billing alert, backup S3 (completed 2026-04-04)
- [x] Phase 7: Listener Deployment (1/1 plan) — Listener 24/7 via systemd com sessão Telethon autenticada (completed 2026-04-04)
- [x] Phase 8: Dashboard & Proxy (2/2 plans) — Dashboard via gunicorn + nginx com HTTP Basic Auth (completed 2026-04-04)

</details>

<details>
<summary>✅ v1.2 Multi-Market Analytics (Phases 9-13) — SHIPPED 2026-04-04</summary>

- [x] **Phase 9: Listener Multi-Grupo** — Listener escuta Over 2.5 e Ambas Marcam simultaneamente (completed 2026-04-04)
- [x] **Phase 10: Lógica Financeira** — Cálculo P&L com complementares diferenciados por mercado e Martingale 4 tentativas (completed 2026-04-04)
- [x] **Phase 11: Dashboard Fundação** — Filtros globais e KPIs com P&L que sustentam todo o redesign (completed 2026-04-04)
- [x] **Phase 12: Dashboard Mercados e Performance** — Config de mercados read-only e tabela P&L por entrada (completed 2026-04-04)
- [x] **Phase 13: Dashboard Análises Visuais** — Análise por liga, equity curve e análise de gale (completed 2026-04-04)

</details>

<details>
<summary>✅ v1.3 Análise Individual de Sinais (Phases 14-15) — SHIPPED 2026-04-04</summary>

- [x] **Phase 14: Migração Multi-Page** — Dashboard refatorado para Dash Pages com `use_pages=True` sem regressões (completed 2026-04-04)
- [x] **Phase 15: Página de Detalhe do Sinal** — Usuário clica em sinal no histórico e visualiza breakdown completo de P&L (completed 2026-04-04)

</details>

### 🚧 v1.4 Configurações de Mercado + Dashboard Ajustes (In Progress)

**Milestone Goal:** Página `/config` editável para odds/stakes dos mercados, listener usando config ativa do banco, e dashboard com KPI Total Investido e Performance por Mercado.

- [ ] **Phase 16: Navegação + Schema DB** — Menu entre Dashboard e Configurações + colunas de config no banco
- [ ] **Phase 17: Página de Configurações** — Formulário `/config` com preview em tempo real e persistência no banco
- [ ] **Phase 18: Listener Config-Aware** — Listener lê config ativa ao processar sinais, sem retroatividade
- [ ] **Phase 19: Dashboard Ajustes** — Remoção de seções obsoletas e adição de KPI Total Investido + Performance por Mercado

## Phase Details

### Phase 9: Listener Multi-Grupo
**Goal**: Listener captura sinais dos dois grupos Telegram simultaneamente sem perda de dados
**Depends on**: Phase 8 (listener já rodando em produção como systemd service)
**Requirements**: LIST-01, LIST-02
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Sinais de Over 2.5 e Ambas Marcam chegam no banco com campo `entrada` correto para cada mercado
  2. Configurar grupos via `TELEGRAM_GROUP_IDS=id1,id2` no .env sem alterar código
  3. Listener único roda como um único processo/service cobrindo ambos os grupos
  4. Parser identifica o mercado principal corretamente pela "Entrada recomendada" da mensagem
**Plans**: 2 plans
Plans:
- [x] 09-01-PLAN.md — Migration SQL (group_id, mercado_id) + store com _resolve_mercado_id e upsert atualizado
- [x] 09-02-PLAN.md — Listener multi-grupo com handler unico + .env.example atualizado

### Phase 10: Lógica Financeira
**Goal**: Cada sinal gera entradas complementares com P&L calculado corretamente por mercado e tentativa
**Depends on**: Phase 9 (ambos os mercados no banco)
**Requirements**: FIN-01, FIN-02, FIN-03
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Sinal Over 2.5 green gera 7 complementares com stakes % corretos (20%, 1%, 10%, 1%, 1%, 1%, 1%)
  2. Sinal Ambas Marcam green gera 7 complementares com stakes % distintos (10%, 1%, 5%, 1%, 1%, 1%, 1%)
  3. Tentativa 2 aplica fator 2x, tentativa 3 fator 4x, tentativa 4 fator 8x na stake base
  4. P&L de cada entrada é calculado corretamente: investido vs retorno (odd * stake) vs lucro líquido
  5. RED em qualquer tentativa registra prejuízo; GREEN registra lucro com a odd de referência correta
**Plans**: 2 plans
Plans:
- [x] 10-01-PLAN.md — Extensao de _build_where com mercado_id, get_signals_com_placar e get_mercado_config
- [x] 10-02-PLAN.md — calculate_pl_por_entrada e calculate_equity_curve_breakdown com testes completos

### Phase 11: Dashboard Fundação
**Goal**: Usuário acessa o dashboard com filtros globais operacionais e KPIs refletindo P&L real
**Depends on**: Phase 10 (dados financeiros no banco)
**Requirements**: DASH-01, DASH-02
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Selecionar "Hoje", "Esta Semana", "Este Mês", "Mês Passado" ou "Toda a Vida" atualiza todos os cards e gráficos imediatamente
  2. Selecionar "Personalizado" abre date picker com data início e data fim funcional
  3. Filtros de mercado (Todos / Over 2.5 / Ambas Marcam) e liga isolam dados corretamente
  4. KPI card P&L Total mostra valor em R$ somando principal e complementares do período filtrado
  5. KPI cards de streak (melhor green, pior red) refletem o período e mercado selecionados
**Plans**: 2 plans
Plans:
- [x] 11-01-PLAN.md — Testes v1.2 + CSS override DARKLY (Wave 1)
- [x] 11-02-PLAN.md — Reescrita dashboard.py layout + callbacks + verificacao visual (Wave 2)
**UI hint**: yes

### Phase 12: Dashboard Mercados e Performance
**Goal**: Usuário visualiza a configuração ativa dos mercados e analisa P&L por entrada em detalhe
**Depends on**: Phase 11 (filtros globais funcionando)
**Requirements**: DASH-03, DASH-04
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Painel de configuração mostra principal (odd, stake, progressão) e tabela de complementares com stakes T1-T4 calculados para Over 2.5 e Ambas Marcam
  2. Toggle Percentual / Quantidade / P&L (R$) muda a apresentação visual da tabela de performance
  3. Tabela de performance exibe greens, reds, taxa, investido, retorno, P&L e ROI para cada entrada
  4. Visão "Por mercado" filtra para Over 2.5 ou Ambas Marcam mostrando principal + cada complementar separadamente
**Plans**: 2 plans
Plans:
- [x] 12-01-PLAN.md — Testes TDD + helpers puros (stakes T1-T4, agregacao P&L, toggle colunas) + placeholders layout
- [x] 12-02-PLAN.md — Builder functions + callback master estendido + verificacao visual
**UI hint**: yes

### Phase 13: Dashboard Análises Visuais
**Goal**: Usuário analisa lucro por liga, evolução do saldo ao longo do tempo e distribuição dos greens por tentativa
**Depends on**: Phase 12 (seções anteriores do dashboard completas)
**Requirements**: DASH-05, DASH-06, DASH-07
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Gráfico de barras empilhadas mostra P&L principal vs complementar separados por liga, reativo ao filtro global
  2. Tabela de ligas exibe taxa, P&L principal, P&L complementar e P&L total por liga
  3. Equity curve exibe 3 linhas sobrepostas (principal, complementar, total) com períodos controlados pelo filtro global
  4. Donut chart mostra distribuição percentual de greens por tentativa (1ª a 4ª) com cores distintas
  5. Tabela de gale exibe quantidade, percentual e lucro médio por green para cada tentativa
**Plans**: 2 plans
Plans:
- [x] 13-01-PLAN.md — TDD testes + funcoes de agregacao (queries.py) + builders Plotly (dashboard.py)
- [x] 13-02-PLAN.md — Integracao callback master + _build_phase13_section + verificacao visual
**UI hint**: yes

### Phase 14: Migração Multi-Page
**Goal**: Dashboard refatorado para Dash Pages sem nenhuma regressão visual ou funcional no dashboard existente
**Depends on**: Phase 13 (dashboard completo e estável)
**Requirements**: MPA-01, MPA-02
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Dashboard existente abre no browser exatamente igual ao estado pré-migração (layout, filtros, gráficos, KPIs)
  2. URL `/` carrega `pages/home.py` com todos os callbacks do dashboard funcionando sem erros no console
  3. `use_pages=True` ativo em `dashboard.py` com `dash.page_container` no layout principal
  4. Nenhum callback existente quebra por circular import — `@callback` (não `@app.callback`) usado em `pages/home.py`
  5. `suppress_callback_exceptions=True` configurado no app para suportar callbacks de múltiplas páginas
**Plans**: 1 plan
Plans:
- [x] 14-01-PLAN.md — Migracao dashboard.py para shell + pages/home.py + testes atualizados
**UI hint**: yes

### Phase 15: Página de Detalhe do Sinal
**Goal**: Usuário clica em um sinal no histórico e visualiza breakdown completo de P&L (principal + cada complementar)
**Depends on**: Phase 14 (Dash Pages ativo com navegação via `dcc.Location`)
**Requirements**: SIG-01, SIG-02, SIG-03, SIG-04, SIG-05, SIG-06
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Clicar em qualquer linha do AG Grid navega para `/sinal?id=<n>` sem full page reload
  2. Página exibe card da entrada principal com mercado, odd, stake (com progressão Gale quando tentativa > 1), resultado (GREEN/RED), horário e lucro/prejuízo
  3. Página exibe uma linha por complementar com nome, odd, stake, resultado validado pelo placar (GREEN/RED/N/A), horário e lucro/prejuízo
  4. Totais consolidados no rodapé: investido total, retorno total e lucro líquido somando principal + todos os complementares
  5. Botão "Voltar" retorna ao dashboard preservando os filtros ativos
  6. Acessar `/sinal?id=<inexistente>` exibe mensagem amigável "Sinal não encontrado" sem erro 500
**Plans**: 2 plans
Plans:
- [x] 15-01-PLAN.md — TDD: get_sinal_detalhado + calculate_pl_detalhado_por_sinal em queries.py
- [x] 15-02-PLAN.md — pages/sinal.py layout + navegacao AG Grid + verificacao visual
**UI hint**: yes

### Phase 16: Navegação + Schema DB
**Goal**: Usuário consegue navegar entre Dashboard e Configurações pelo menu, e o banco tem as colunas necessárias para persistir config editável
**Depends on**: Phase 15 (Dash Pages com `use_pages=True` ativo)
**Requirements**: NAV-01
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Menu/tabs visível em todas as páginas permite alternar entre `/` (Dashboard) e `/config` (Configurações) com um clique
  2. Tab ativa fica destacada visualmente indicando a página atual
  3. Tabela `mercados` tem colunas `stake_base`, `fator_progressao` e `max_tentativas` sem perda de dados existentes
  4. Migração idempotente: rodar duas vezes não gera erro
**Plans**: TBD
**UI hint**: yes

### Phase 17: Página de Configurações
**Goal**: Usuário edita stake base, progressão, max tentativas, percentuais e odds de todos os mercados e salva no banco
**Depends on**: Phase 16 (schema DB com colunas de config + navegação para `/config`)
**Requirements**: CFG-01, CFG-02, CFG-03, CFG-04, CFG-05
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Página `/config` abre com valores atuais do banco (ou defaults se não houver config salva)
  2. Editar stake base, fator de progressão ou max tentativas atualiza o preview de stakes T1–T4 em tempo real sem salvar
  3. Editar percentual ou odd de qualquer complementar atualiza o total em risco no preview em tempo real
  4. Clicar em "Salvar" persiste todos os valores no banco e exibe confirmação visual de sucesso
  5. Recarregar a página após salvar exibe os valores recém-salvos (persistência confirmada)
**Plans**: TBD
**UI hint**: yes

### Phase 18: Listener Config-Aware
**Goal**: Listener lê a configuração ativa do banco ao processar cada novo sinal, usando stakes e odds atualizados
**Depends on**: Phase 17 (config persistida no banco via página `/config`)
**Requirements**: LIS-01, LIS-02
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Sinal capturado após salvar nova config usa a stake base e odds atualizadas (verificável via registro no banco)
  2. Sinais capturados antes da mudança de config mantêm os valores originais (não retroativo)
  3. Listener não quebra se config estiver ausente no banco — usa defaults hardcoded como fallback
**Plans**: TBD

### Phase 19: Dashboard Ajustes
**Goal**: Dashboard remove seções obsoletas e adiciona KPI Total Investido e Performance Individual por Mercado
**Depends on**: Phase 16 (navegação pronta; ajustes independentes de config e listener)
**Requirements**: DASH-08, DASH-09, DASH-10
**Success Criteria** (o que deve ser VERDADEIRO):
  1. Seções "Configuração de Mercados" e inputs de simulação ROI não aparecem mais no dashboard
  2. KPI card "Total Investido" no topo mostra soma das stakes (principal + complementares) do período filtrado, reagindo ao filtro de período/mercado
  3. Seção "Performance Individual por Mercado" exibe um card por mercado (Over 2.5, Ambas Marcam, cada complementar) com greens, reds, taxa, investido, retorno, P&L e ROI
  4. Cards de performance reagem ao filtro de período selecionado
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 7/7 | Complete | 2026-04-02 |
| 2. Core Dashboard | v1.0 | 3/3 | Complete | 2026-04-03 |
| 2.1 Market Config | v1.0 | 4/4 | Complete | 2026-04-03 |
| 3. Analytics Depth | v1.0 | 4/4 | Complete | 2026-04-03 |
| 4. Security Audit | v1.1 | 2/2 | Complete | 2026-04-03 |
| 5. GitHub Publication | v1.1 | 2/2 | Complete | 2026-04-03 |
| 6. AWS Infrastructure | v1.1 | 3/3 | Complete | 2026-04-04 |
| 7. Listener Deployment | v1.1 | 1/1 | Complete | 2026-04-04 |
| 8. Dashboard & Proxy | v1.1 | 2/2 | Complete | 2026-04-04 |
| 9. Listener Multi-Grupo | v1.2 | 2/2 | Complete | 2026-04-04 |
| 10. Lógica Financeira | v1.2 | 2/2 | Complete | 2026-04-04 |
| 11. Dashboard Fundação | v1.2 | 2/2 | Complete | 2026-04-04 |
| 12. Dashboard Mercados e Performance | v1.2 | 2/2 | Complete | 2026-04-04 |
| 13. Dashboard Análises Visuais | v1.2 | 2/2 | Complete | 2026-04-04 |
| 14. Migração Multi-Page | v1.3 | 1/1 | Complete | 2026-04-04 |
| 15. Página de Detalhe do Sinal | v1.3 | 2/2 | Complete | 2026-04-04 |
| 16. Navegação + Schema DB | v1.4 | 0/? | Not started | - |
| 17. Página de Configurações | v1.4 | 0/? | Not started | - |
| 18. Listener Config-Aware | v1.4 | 0/? | Not started | - |
| 19. Dashboard Ajustes | v1.4 | 0/? | Not started | - |
