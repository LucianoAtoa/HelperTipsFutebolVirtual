# Requirements: HelperTips — v1.1 Cloud Deploy

**Defined:** 2026-04-03
**Core Value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## v1.1 Requirements

Requirements para deploy em produção na AWS. Cada um mapeia para fases do roadmap.

### Segurança

- [x] **SEC-01**: Histórico git auditado — nenhum secret (.env, .session, API keys) presente em commits antigos
- [x] **SEC-02**: Dashboard roda com `debug=False` em produção (elimina REPL remoto)
- [x] **SEC-03**: `.env.example` atualizado com todas as variáveis necessárias (inclusive AWS) sem valores reais
- [x] **SEC-04**: README.md com instruções de setup local, deploy, e aviso de segurança

### GitHub

- [ ] **GH-01**: Repositório publicado no GitHub com .gitignore correto (*.session, .env, __pycache__, *.pyc)
- [x] **GH-02**: GitHub Actions workflow roda lint + testes automaticamente em cada push

### Infraestrutura AWS

- [ ] **AWS-01**: EC2 t3.micro provisionado com Elastic IP e Security Group restrito (SSH + HTTP/HTTPS)
- [ ] **AWS-02**: PostgreSQL instalado e rodando na instância EC2 com schema migrado
- [ ] **AWS-03**: Budget alert configurado em $15/mês para evitar surpresas de custo
- [ ] **AWS-04**: Credenciais (Telegram API, DB) armazenadas de forma segura no servidor (SSM Parameter Store ou .env protegido)
- [ ] **AWS-05**: Backup periódico do arquivo .session para S3 ou volume persistente

### Deploy & Operação

- [ ] **DEP-01**: Listener rodando como systemd service com `Restart=on-failure` e `RestartSec=60`
- [ ] **DEP-02**: Dashboard rodando via gunicorn como systemd service com `Restart=on-failure`
- [ ] **DEP-03**: Nginx configurado como reverse proxy para o dashboard (porta 80/443 → localhost:8050)
- [ ] **DEP-04**: HTTP Basic Auth no nginx protege dashboard de acesso público não autorizado
- [ ] **DEP-05**: Primeira autenticação Telethon feita interativamente via SSH no EC2

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

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
| Docker / ECS / Kubernetes | Over-engineering para ferramenta pessoal; systemd é suficiente |
| RDS managed database | +$15-25/mês sem benefício real para uso pessoal |
| OAuth / Dash Enterprise auth | HTTP Basic Auth é suficiente para 1 usuário |
| Multi-region / alta disponibilidade | Ferramenta pessoal, downtime tolerável |
| Terraform / IaC | Infra simples (1 EC2), configuração manual é aceitável |
| Domínio próprio + SSL | Pode ser adicionado depois; HTTP com IP funciona para uso pessoal |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 4 | Complete |
| SEC-02 | Phase 4 | Complete |
| SEC-03 | Phase 4 | Complete |
| SEC-04 | Phase 4 | Complete |
| GH-01 | Phase 5 | Pending |
| GH-02 | Phase 5 | Complete |
| AWS-01 | Phase 6 | Pending |
| AWS-02 | Phase 6 | Pending |
| AWS-03 | Phase 6 | Pending |
| AWS-04 | Phase 6 | Pending |
| AWS-05 | Phase 6 | Pending |
| DEP-05 | Phase 7 | Pending |
| DEP-01 | Phase 7 | Pending |
| DEP-02 | Phase 8 | Pending |
| DEP-03 | Phase 8 | Pending |
| DEP-04 | Phase 8 | Pending |

**Coverage:**
- v1.1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-03 after roadmap creation*
