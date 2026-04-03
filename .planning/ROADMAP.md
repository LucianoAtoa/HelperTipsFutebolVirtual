# Roadmap: HelperTips — Futebol Virtual

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 + 2.1 (shipped 2026-04-03) — [archive](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1 Cloud Deploy** — Phases 4-8 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3 + 2.1) — SHIPPED 2026-04-03</summary>

- [x] Phase 1: Foundation (7/7 plans) — Telegram listener pipeline captures signals into PostgreSQL
- [x] Phase 2: Core Dashboard (3/3 plans) — Plotly Dash dashboard with stats, filters, ROI simulation
- [x] Phase 2.1: Market Config (4/4 plans) — Mercados complementares com validação por placar e Martingale
- [x] Phase 3: Analytics Depth (4/4 plans) — Heatmap, equity curve, gale analysis, cross-dimensional

</details>

### 🚧 v1.1 Cloud Deploy (In Progress)

**Milestone Goal:** Subir o HelperTips para a AWS com custo mínimo, garantindo segurança antes de expor na nuvem, e publicar o repositório no GitHub.

- [x] **Phase 4: Security Audit** - Repositório limpo de secrets, debug=False, documentação de segurança (completed 2026-04-03)
- [ ] **Phase 5: GitHub Publication** - Repositório público com CI/CD automatizado via GitHub Actions
- [ ] **Phase 6: AWS Infrastructure** - EC2 t3.micro provisionada com PostgreSQL, billing alert e credenciais seguras
- [ ] **Phase 7: Listener Deployment** - Listener rodando 24/7 via systemd com sessão Telethon autenticada
- [ ] **Phase 8: Dashboard & Proxy** - Dashboard acessível via nginx com HTTP Basic Auth

## Phase Details

### Phase 4: Security Audit
**Goal**: Repositório está limpo de secrets e pronto para ser publicado publicamente
**Depends on**: Phase 3 (v1.0 shipped)
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. `git log --all --full-diff -p -- .env '*.session'` retorna zero resultados — nenhum secret no histórico
  2. Dashboard abre sem expor o Flask debugger — `debug=False` ou controlado por variável de ambiente em produção
  3. `.env.example` lista todas as variáveis necessárias (Telegram, DB, AWS) sem valores reais
  4. README.md tem seção de setup local, seção de deploy e aviso explícito de segurança para o arquivo .session
**Plans**: 2 plans

Plans:
- [x] 04-01-PLAN.md — Auditoria git, correcao debug mode, .env.example e testes (SEC-01, SEC-02, SEC-03)
- [x] 04-02-PLAN.md — Criacao do README.md completo (SEC-04)

### Phase 5: GitHub Publication
**Goal**: Código publicado no GitHub com CI automatizado validando qualidade a cada push
**Depends on**: Phase 4
**Requirements**: GH-01, GH-02
**Success Criteria** (what must be TRUE):
  1. Repositório público no GitHub com `.gitignore` bloqueando `*.session`, `.env`, `__pycache__` e `*.pyc`
  2. Push para `main` dispara GitHub Actions que roda lint e testes — badge de status visível no README
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md — Configurar ruff lint, corrigir codigo existente, criar CI workflow e badge (GH-02)
- [ ] 05-02-PLAN.md — Publicar repositorio no GitHub, verificar CI verde (GH-01, GH-02)

### Phase 6: AWS Infrastructure
**Goal**: Instância EC2 provisionada e funcional com banco de dados, billing controlado e credenciais seguras
**Depends on**: Phase 5
**Requirements**: AWS-01, AWS-02, AWS-03, AWS-04, AWS-05
**Success Criteria** (what must be TRUE):
  1. EC2 t3.micro acessível via SSH com Elastic IP fixo e Security Group restrito a SSH + HTTP/HTTPS
  2. PostgreSQL rodando na instância com schema migrado — `SELECT COUNT(*) FROM sinais` executa sem erro
  3. Budget alert ativo no AWS Console — email enviado ao atingir $15/mês
  4. Credenciais (Telegram API, DB password) acessíveis para os processos mas ausentes de arquivos no repositório
  5. Arquivo `.session` com backup automático ou armazenado em volume persistente — survives reboot
**Plans**: TBD

Plans:
- [ ] 06-01: Provisionar EC2, Elastic IP, Security Group e configurar acesso SSH (AWS-01)
- [ ] 06-02: Instalar PostgreSQL na EC2, migrar schema, configurar billing alert (AWS-02, AWS-03)
- [ ] 06-03: Configurar credenciais seguras no servidor e backup do .session (AWS-04, AWS-05)

### Phase 7: Listener Deployment
**Goal**: Listener capturando sinais do Telegram 24/7 na EC2, sobrevivendo a crashes e reboots
**Depends on**: Phase 6
**Requirements**: DEP-05, DEP-01
**Success Criteria** (what must be TRUE):
  1. Autenticação Telethon interativa completada via SSH — arquivo `.session` gerado na EC2
  2. `systemctl status helpertips-listener` mostra `active (running)` após reboot do servidor
  3. Sinal capturado localmente aparece no banco na EC2 — listener está processando mensagens reais
**Plans**: TBD

Plans:
- [ ] 07-01: Autenticação interativa Telethon via SSH e conversão para systemd service (DEP-05, DEP-01)

### Phase 8: Dashboard & Proxy
**Goal**: Dashboard acessível publicamente via HTTP com proteção por senha, servido por stack de produção
**Depends on**: Phase 7
**Requirements**: DEP-02, DEP-03, DEP-04
**Success Criteria** (what must be TRUE):
  1. Acessar `http://<EC2-IP>` no browser pede usuário e senha antes de mostrar qualquer conteúdo
  2. Dashboard carrega com dados reais do banco — KPI cards com contagens corretas
  3. Reiniciar o servidor sobe dashboard automaticamente — `systemctl status helpertips-dashboard` mostra `active`
**Plans**: TBD

Plans:
- [ ] 08-01: Configurar gunicorn como systemd service para o dashboard (DEP-02)
- [ ] 08-02: Configurar nginx como reverse proxy com HTTP Basic Auth (DEP-03, DEP-04)
**UI hint**: yes

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 7/7 | Complete | 2026-04-02 |
| 2. Core Dashboard | v1.0 | 3/3 | Complete | 2026-04-03 |
| 2.1 Market Config | v1.0 | 4/4 | Complete | 2026-04-03 |
| 3. Analytics Depth | v1.0 | 4/4 | Complete | 2026-04-03 |
| 4. Security Audit | v1.1 | 2/2 | Complete   | 2026-04-03 |
| 5. GitHub Publication | v1.1 | 0/2 | Planned | - |
| 6. AWS Infrastructure | v1.1 | 0/3 | Not started | - |
| 7. Listener Deployment | v1.1 | 0/1 | Not started | - |
| 8. Dashboard & Proxy | v1.1 | 0/2 | Not started | - |
