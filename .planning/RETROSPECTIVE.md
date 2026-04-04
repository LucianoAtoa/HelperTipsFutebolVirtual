# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-04-03
**Phases:** 4 | **Plans:** 18 | **Tasks:** 26

### What Was Built
- Pipeline completo Telegram → PostgreSQL: listener Telethon, parser regex, store com upsert, schema com 4 tabelas
- Dashboard web Plotly Dash: dark theme, 5 KPI cards, 3 filtros, ROI com Gale, AG Grid com histórico
- Sistema de mercados complementares: 14 entradas com validação por placar, Martingale, ROI breakdown
- 3 abas de analytics: heatmap temporal, equity curve, gale analysis, streaks, volume, cross-dimensional
- Badge de cobertura do parser com modal de falhas

### What Worked
- TDD-first para parser e queries — testes escritos antes do código aceleraram desenvolvimento
- Separação clara de camadas (parser → store → queries → dashboard) — cada módulo testável isoladamente
- Inserção de Phase 2.1 mid-milestone sem interrupção — decimal numbering funcionou bem
- Modo yolo com auto_advance acelerou execução sem perda de qualidade
- Pure-Python functions (calculate_roi, calculate_equity_curve, calculate_streaks) sem dependência de DB — testes rápidos

### What Was Inefficient
- Phase 2.1 Plan 04 (dashboard card) levou 79min — maior outlier do milestone, provavelmente por complexidade de callback Dash
- VERIFICATION.md nunca criado para Phase 2.1 — gerou gaps no audit que são apenas documentais
- Nyquist validation ficou em draft para todas as fases — processo adicionado mas nunca executado
- Alguns SUMMARY frontmatter sem requirements_completed — inconsistência entre planos

### Patterns Established
- `_build_where()` helper para construção de WHERE clauses parameterizadas — reutilizado em 9 query functions
- `_build_*_table()` helpers para renderização condicional de tabelas DBC
- Lazy render via `active_tab` gate em callbacks de abas — evita queries desnecessárias
- Processos separados: listener.py (asyncio/Telethon) + dashboard.py (Dash) — sem mixing de event loops
- store.py sync-only, chamado via `asyncio.to_thread()` no listener
- `validar_complementar()` retorna RED conservadoramente para regra desconhecida

### Key Lessons
1. Criar VERIFICATION.md para TODAS as fases, incluindo fases inseridas (decimal) — evita gaps documentais no audit
2. Parser regex deve ser escrito contra mensagens reais capturadas — não assumir formato baseado em documentação
3. Dashboard callbacks complexos (muitos Outputs) são o principal gargalo de tempo — considerar split em callbacks menores
4. ensure_schema() com seed idempotente (INSERT ... SELECT WHERE NOT EXISTS) é padrão confiável para tabelas de configuração

### Cost Observations
- Model mix: ~70% sonnet (subagents), ~30% opus (orchestration)
- Sessions: ~5 sessions across 2 days
- Notable: 18 plans em ~2.5 horas de execução efetiva — média de 8 min/plan

---

## Milestone: v1.1 — Cloud Deploy

**Shipped:** 2026-04-04
**Phases:** 5 | **Plans:** 10 | **Tasks:** 17

### What Was Built
- Security audit: histórico git limpo de secrets, debug mode por env var, .env.example completo
- GitHub publication: repo público com CI (ruff lint + pytest) verde a cada push
- AWS infrastructure: EC2 t3.micro com PostgreSQL 16, budget alert $15/mês, backup S3 diário
- Listener deployment: systemd service 24/7 com Restart=on-failure, logging condicional TTY, notificação de falha via Telegram
- Dashboard deployment: gunicorn (2 workers) + nginx reverse proxy com HTTP Basic Auth na porta 80

### What Worked
- Padrão de deploy scripts numerados (01-07) em `deploy/` — idempotentes, replicáveis
- Checkpoint human-action para autenticação Telethon — não tenta automatizar o que requer humano
- Replicação do padrão systemd da Phase 7 para Phase 8 — consistência reduz erros
- Pesquisa antes do planejamento identificou pitfalls críticos (StartLimitBurst em [Unit], www-data vs nginx)
- Auto-advance pipeline (discuss → plan → execute) funcionou sem intervenção para Phase 8

### What Was Inefficient
- Phase 6 ficou com roadmap_complete=false (progress table desatualizada) — não bloqueou mas gerou ruído
- HUMAN-UAT.md criado com status partial para todas as fases de deploy — itens manuais nunca formalmente testados via /gsd:verify-work
- Porta 8050 no Security Group ficou como lembrete manual no script em vez de automação AWS CLI

### Patterns Established
- `deploy/XX-setup-*.sh` — scripts bash idempotentes com set -euo pipefail
- systemd unit files com `Restart=on-failure`, `StartLimitBurst` em `[Unit]` (não `[Service]`)
- Logging condicional: `sys.stdout.isatty()` para TTY (Rich) vs daemon (RotatingFileHandler)
- Logs em `/var/log/helpertips/` com logrotate compartilhado
- User dedicado `helpertips` para todos os serviços
- .htpasswd com credenciais lidas do .env (centralização de secrets)

### Key Lessons
1. Deploy scripts devem ser idempotentes — facilita re-runs e debugging
2. StartLimitBurst DEVE ficar em [Unit], não [Service] — ignorado silenciosamente se errado
3. Checkpoints human-action são a abordagem correta para autenticação interativa
4. gunicorn precisa de `server = app.server` exposto — verificar antes do unit file
5. www-data é o user nginx no Ubuntu (não "nginx") — impacta permissões .htpasswd

### Cost Observations
- Model mix: ~60% sonnet (subagents), ~40% opus (orchestration + planning)
- Sessions: ~3 sessions in 1 day
- Notable: 10 plans em ~1.5 hora efetiva — fase 8 auto-advance completo sem intervenção

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~5 | 4 | First milestone — established TDD, layer separation, yolo mode |
| v1.1 | ~3 | 5 | Deploy pipeline — idempotent scripts, systemd patterns, auto-advance |

### Cumulative Quality

| Milestone | Tests | LOC | Plans |
|-----------|-------|-----|-------|
| v1.0 | 132 | 5,050 | 18 |
| v1.1 | 138 | 15,386 | 28 |

### Top Lessons (Verified Across Milestones)

1. TDD-first com pure-Python functions acelera desenvolvimento e garante testabilidade
2. VERIFICATION.md é obrigatório para todas as fases — sem exceção
3. Deploy scripts idempotentes são o padrão correto para infra pessoal (replicáveis, debugáveis)
4. Pesquisa pré-planejamento identifica pitfalls que economizam horas de debugging em produção
